package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
)

// A fallback is the operator's explicit choice of a second backend
// (JEV_FALLBACK_PROVIDER), never an inference from which keys are set. With
// none configured, a failure goes to the agent exactly as it always has.
//
// When one is configured, a call moves to it only when the primary will not
// serve this credential, or cannot be reached: a status in fallbackStatus
// after the primary's own retries, or a transport failure. The failed call is
// sent again to the fallback, and every later call in the session stays there,
// so one session never alternates between two accounts. A request the primary
// rejected by shape (400, 413, 422) or that failed local validation fails the
// same way anywhere, so it never moves.

// fallbackStatus reports whether a primary's HTTP status means the backend is
// not serving this credential now: a dead or unfunded key (401, 402, 403), a
// moved endpoint (404), throttling (429), or an outage (5xx).
func fallbackStatus(status int) bool {
	switch status {
	case 401, 402, 403, 404, 429:
		return true
	}
	return status >= 500
}

// fallbackReason names why err should move a call to the fallback, or returns
// false when it should not.
func fallbackReason(err error) (string, bool) {
	var status *statusErr
	if errors.As(err, &status) {
		return fmt.Sprintf("HTTP %d", status.Status), fallbackStatus(status.Status)
	}
	// A request that never got an answer: refused or dropped before a response
	// (*url.Error), or reset while the response was being read (net.Error).
	var transport *url.Error
	var network net.Error
	if errors.As(err, &transport) || errors.As(err, &network) {
		return "unreachable", true
	}
	return "", false
}

// runWithFallback runs one evaluation on the primary, or on the fallback once
// the session has switched. Both share one deadline, the primary's timeout:
// a client that aborts a tool call after a fixed time would otherwise kill a
// fallback that was given a fresh budget of its own.
//
// The request's model names the primary's id, which differs per backend, so
// the fallback runs its own default instead.
func runWithFallback(ctx context.Context, c *Client, in evaluateIn) ([]byte, error) {
	ctx, cancel := context.WithTimeout(ctx, c.Timeout)
	defer cancel()
	onFallback := in
	onFallback.Model = ""
	if c.switched.Load() {
		return runOn(ctx, c.Fallback, onFallback)
	}
	body, err := runOn(ctx, c, in)
	if err == nil || ctx.Err() != nil {
		return body, err
	}
	reason, ok := fallbackReason(err)
	if !ok {
		return nil, err
	}
	if c.switched.CompareAndSwap(false, true) {
		log := c.Log
		if log == nil {
			log = os.Stderr
		}
		fmt.Fprintf(log, "evaluate: %s refused or failed the call (%s); using the %s fallback for the rest of this session\n",
			c.Provider.Name, reason, c.Fallback.Provider.Name)
	}
	return runOn(ctx, c.Fallback, onFallback)
}
