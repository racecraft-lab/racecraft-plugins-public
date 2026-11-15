package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type chainEffect uint8

const (
	failCall chainEffect = iota
	nextHopForCall
	moveSession
	moveAccount
)

// chainOutcome separates a call's result from the scope of an error's effect.
// The runner owns moves; an HTTP client knows only its one backend.
type chainOutcome struct {
	effect chainEffect
	reason string
}

// chainFailure carries deadline provenance into the pure classifier. An error
// matching DeadlineExceeded alone may be a dial timeout on a still-live call.
type chainFailure struct {
	err        error
	requestErr error
	hopErr     error
	// Daemon provenance is supplied by the caller, never inferred from a
	// provider name here. No daemon is enabled in this prefactor.
	daemon bool
}

func (e *chainFailure) Error() string { return e.err.Error() }
func (e *chainFailure) Unwrap() error { return e.err }

func classify(err error) chainOutcome {
	var failure *chainFailure
	if errors.As(err, &failure) {
		if errors.Is(failure.requestErr, context.DeadlineExceeded) {
			return chainOutcome{failCall, "timeout"}
		}
		if failure.requestErr != nil {
			return chainOutcome{effect: failCall}
		}
		if errors.Is(failure.hopErr, context.DeadlineExceeded) {
			return chainOutcome{nextHopForCall, "timeout"}
		}
	}
	var status *statusErr
	if errors.As(err, &status) {
		out := chainOutcome{reason: fmt.Sprintf("HTTP %d", status.Status)}
		switch {
		case status.Status == 404 || (failure != nil && failure.daemon && (status.Status == 502 || status.Status == 503)):
			out.effect = moveSession
		case status.Status == 401, status.Status == 402, status.Status == 403, status.Status == 429, status.Status >= 500:
			out.effect = moveAccount
		}
		return out
	}
	var transport *url.Error
	var network net.Error
	if errors.As(err, &transport) || errors.As(err, &network) {
		return chainOutcome{moveSession, "unreachable"}
	}
	return chainOutcome{effect: failCall}
}

// chainRunner owns the session's position and move log. Clients carry only
// per-backend HTTP settings. A moving failure advances the index before the
// next hop prepares, independently of that request's capability route.
type chainRunner struct {
	hops           []*Client
	current        atomic.Int32
	log            io.Writer
	credentialCode int
	moveMu         sync.Mutex
	logMu          sync.Mutex
	onMove         func()
	// firstDropped keeps model overrides tied to the configured first hop.
	firstDropped bool
}

// startChain retains the credential verdict even if no hop can start, so
// --check can report it without evaluating a call or losing a dropped hop.
func startChain(resolved resolvedHops, log, startupLog io.Writer) (*chainRunner, Config, error) {
	r := &chainRunner{log: log, credentialCode: resolved.credentialExit()}
	hops, cfg, err := resolved.clients(startupLog)
	r.hops = hops
	r.firstDropped = len(resolved.hops) > 0 && resolved.hops[0].loaded.err != nil
	return r, cfg, err
}

func (r *chainRunner) credentialExit() int { return r.credentialCode }

func (r *chainRunner) servingHop() *Client { return r.hops[r.current.Load()] }

// evaluate routes local hop refusals without moving the session. A failure on
// the session's own hop moves it before the next hop is prepared, so a failure
// and a capability route compose. All hops share the request deadline.
func (r *chainRunner) evaluate(ctx context.Context, in evaluateIn) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, r.hops[0].Timeout)
	defer cancel()
	start := int(r.current.Load())
	if start > 0 || r.firstDropped {
		in = fallbackRequest(in)
	}
	shaped, err := shapeRequest(in)
	if err != nil {
		local := &requestInvalidError{err}
		if start > 0 {
			return nil, r.onTheFallback(local)
		}
		return nil, local
	}
	var networkErr error
	sessionHop := start
	for i := start; i < len(r.hops); i++ {
		if i > start {
			shaped.in = fallbackRequest(shaped.in)
		}
		p, local := prepareForHop(r.hops[i], shaped)
		if local != nil {
			reported := local
			if networkErr != nil {
				reported = fmt.Errorf("%w; the %s fallback cannot take this request: %v", networkErr, r.hops[i].Provider.Name, local)
			}
			var refusal *hopRefusalError
			if !errors.As(local, &refusal) {
				err = reported
				break
			}
			if networkErr != nil || err == nil {
				err = reported
			}
			continue
		}
		hopCtx := ctx
		cancelHop := func() {}
		limit := r.hops[i].HopTimeout
		if limit == 0 {
			limit = defaultHopTimeout
		}
		deadline, _ := ctx.Deadline()
		if time.Until(deadline) > limit && r.hasLaterHop(i, shaped) {
			hopCtx, cancelHop = context.WithTimeout(ctx, limit)
		}
		body, failure := send(hopCtx, r.hops[i], p)
		hopErr := hopCtx.Err()
		cancelHop()
		if requestErr := ctx.Err(); requestErr != nil {
			failure = requestErr
		}
		if failure == nil {
			return body, nil
		}
		// A retry that cannot fit (or finishes at the hop boundary) still
		// carries the backend's status. Only a timeout without that status
		// takes a call-only route; the whole deadline above always wins.
		var status *statusErr
		if errors.As(failure, &status) {
			hopErr = nil
		}
		err, networkErr = failure, failure
		out := classify(&chainFailure{err: failure, requestErr: ctx.Err(), hopErr: hopErr})
		if out.effect == nextHopForCall {
			sessionHop = -1
			continue
		}
		if out.effect != moveSession && out.effect != moveAccount {
			break
		}
		if i == sessionHop && i+1 < len(r.hops) {
			r.move(int32(i), int32(i+1), out.reason)
			sessionHop = i + 1
		}
	}
	if start > 0 {
		err = r.onTheFallback(err)
	}
	return nil, err
}

// hasLaterHop checks reachability locally, using the same preparation and
// shared image cache as routing. A later refusal cannot shorten the last able
// hop's time. Other errors stop routing when that hop is reached.
func (r *chainRunner) hasLaterHop(after int, shaped shapedCall) bool {
	shaped.in = fallbackRequest(shaped.in)
	for _, hop := range r.hops[after+1:] {
		_, err := prepareForHop(hop, shaped)
		if err == nil {
			return true
		}
		var refusal *hopRefusalError
		if !errors.As(err, &refusal) {
			return false
		}
	}
	return false
}

// move only advances the hop that actually failed. Concurrent failures of an
// older hop cannot move a session again; only the CAS winner writes the log.
func (r *chainRunner) move(from, to int32, reason string) {
	r.moveMu.Lock()
	for {
		current := r.current.Load()
		if current != from || to <= current {
			r.moveMu.Unlock()
			return
		}
		if r.current.CompareAndSwap(current, to) {
			onMove := r.onMove
			r.moveMu.Unlock()
			// Keep writers serialized without holding up session moves or MCP I/O.
			r.logMu.Lock()
			log := r.log
			if log == nil {
				log = os.Stderr
			}
			fmt.Fprintf(log, "evaluate: %s refused or failed the call (%s); using the %s fallback for the rest of this session\n",
				r.hops[from].Provider.Name, reason, r.hops[to].Provider.Name)
			r.logMu.Unlock()
			if onMove != nil {
				onMove()
			}
			return
		}
	}
}

// fallbackRequest keeps the caller's primary model off the second backend.
func fallbackRequest(in evaluateIn) evaluateIn {
	in.Model = ""
	return in
}

func (r *chainRunner) onTheFallback(err error) error {
	var local *requestInvalidError
	if !errors.As(err, &local) {
		return err
	}
	return &requestInvalidError{fmt.Errorf("this session is on the %s fallback since %s failed; %w",
		r.servingHop().Provider.Name, r.hops[0].Provider.Name, local.err)}
}

// backendNote reports the fixed loaded order for MCP.
func (r *chainRunner) backendNote() string {
	names := make([]string, len(r.hops))
	for i, hop := range r.hops {
		names[i] = hop.Provider.Name
	}
	return "\nBackend chain: " + strings.Join(names, " -> ") + "."
}
