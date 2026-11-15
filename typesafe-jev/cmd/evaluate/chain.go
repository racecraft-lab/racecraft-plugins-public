package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/url"
	"os"
	"sync/atomic"
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
// per-backend HTTP settings. This prefactor still runs today's one or two hops.
type chainRunner struct {
	hops           []*Client
	current        atomic.Int32
	log            io.Writer
	credentialCode int
}

// startChain retains the credential verdict even if no hop can start, so
// --check can report it without evaluating a call or losing a dropped hop.
func startChain(resolved resolvedHops, log, startupLog io.Writer) (*chainRunner, Config, error) {
	r := &chainRunner{log: log, credentialCode: resolved.credentialExit()}
	hops, cfg, err := resolved.clients(startupLog)
	r.hops = hops
	return r, cfg, err
}

func (r *chainRunner) credentialExit() int { return r.credentialCode }

func (r *chainRunner) servingHop() *Client { return r.hops[r.current.Load()] }

// evaluate keeps the existing two-hop contract. A call moves to the fallback
// only when the primary will not serve this credential (401, 402, 403), has
// moved (404), is throttling (429) or is down (5xx) after its own retries, or
// cannot be reached. The session then stays there, so one session never
// alternates between two accounts. A request rejected by shape (400, 413, 422)
// or by local validation fails the same way anywhere, so it never moves.
//
// The backends' local gates differ (image limits, context budgets), so the
// fallback checks the request before the session moves (FB-08). One it cannot
// take leaves the session on the primary, and the caller sees the primary's
// failure, whose class decides the exit code, rather than a local rejection
// after a network call was made.
//
// Both hops share the primary's deadline: a client that aborts a tool call
// after a fixed time would otherwise kill a fallback given a fresh budget.
func (r *chainRunner) evaluate(ctx context.Context, in evaluateIn) ([]byte, error) {
	if len(r.hops) == 1 {
		return runOn(ctx, r.hops[0], in)
	}
	ctx, cancel := context.WithTimeout(ctx, r.hops[0].Timeout)
	defer cancel()

	onFallback := fallbackRequest(in)
	if r.current.Load() != 0 {
		body, err := runOn(ctx, r.servingHop(), onFallback)
		return body, r.onTheFallback(err)
	}
	body, err := runOn(ctx, r.hops[0], in)
	if err == nil {
		return body, nil
	}
	out := classify(&chainFailure{err: err, requestErr: ctx.Err()})
	if out.effect != moveSession && out.effect != moveAccount {
		return body, err
	}
	p, local := prepare(r.hops[1], onFallback)
	if local != nil {
		return nil, fmt.Errorf("%w; the %s fallback cannot take this request: %v", err, r.hops[1].Provider.Name, local)
	}
	r.move(0, 1, out.reason)
	return send(ctx, r.hops[1], p)
}

// move only advances the hop that actually failed. Concurrent failures of an
// older hop cannot move a session again; only the CAS winner writes the log.
func (r *chainRunner) move(from, to int32, reason string) {
	for {
		current := r.current.Load()
		if current != from || to <= current {
			return
		}
		if r.current.CompareAndSwap(current, to) {
			log := r.log
			if log == nil {
				log = os.Stderr
			}
			fmt.Fprintf(log, "evaluate: %s refused or failed the call (%s); using the %s fallback for the rest of this session\n",
				r.hops[from].Provider.Name, reason, r.hops[to].Provider.Name)
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
