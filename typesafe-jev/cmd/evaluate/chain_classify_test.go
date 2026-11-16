package main

import (
	"context"
	"errors"
	"fmt"
	"net"
	"net/url"
	"syscall"
	"testing"
)

// The internal seam agreed in the spec: deadline provenance wins over HTTP
// status and net.Error. A dial deadline alone still means unreachable.
func TestClassify(t *testing.T) {
	deadline := &url.Error{Op: "Post", URL: "https://backend.invalid", Err: context.DeadlineExceeded}
	var network net.Error
	if !errors.As(deadline, &network) || !network.Timeout() {
		t.Fatal("deadline fixture must also satisfy net.Error")
	}
	for _, tc := range []struct {
		name   string
		err    error
		effect chainEffect
		reason string
	}{
		{"whole request deadline", &chainFailure{err: deadline, requestErr: context.DeadlineExceeded}, failCall, "timeout"},
		{"whole deadline before hop deadline", &chainFailure{err: deadline, requestErr: context.DeadlineExceeded, hopErr: context.DeadlineExceeded}, failCall, "timeout"},
		{"whole deadline before account status", &chainFailure{err: &statusErr{Status: 429}, requestErr: context.DeadlineExceeded}, failCall, "timeout"},
		{"hop deadline", &chainFailure{err: deadline, hopErr: context.DeadlineExceeded}, nextHopForCall, "timeout"},
		{"hop deadline before account status", &chainFailure{err: &statusErr{Status: 429}, hopErr: context.DeadlineExceeded}, nextHopForCall, "timeout"},
		{"cancelled request", &chainFailure{err: deadline, requestErr: context.Canceled}, failCall, ""},
		{"refused connection", &net.OpError{Op: "dial", Net: "tcp", Err: syscall.ECONNREFUSED}, moveSession, "unreachable"},
		{"network reset", &net.OpError{Op: "read", Net: "tcp", Err: syscall.ECONNRESET}, moveSession, "unreachable"},
		{"dial deadline on live request", deadline, moveSession, "unreachable"},
		{"path", &statusErr{Status: 404}, moveSession, "HTTP 404"},
		{"daemon gateway", &chainFailure{err: &statusErr{Status: 502}, daemon: true}, moveSession, "HTTP 502"},
		{"daemon unavailable", &chainFailure{err: &statusErr{Status: 503}, daemon: true}, moveSession, "HTTP 503"},
		{"daemon other server error", &chainFailure{err: &statusErr{Status: 500}, daemon: true}, moveAccount, "HTTP 500"},
		{"unauthorized", &statusErr{Status: 401}, moveAccount, "HTTP 401"},
		{"credit", &statusErr{Status: 402}, moveAccount, "HTTP 402"},
		{"forbidden", &statusErr{Status: 403}, moveAccount, "HTTP 403"},
		{"rate limit", &statusErr{Status: 429}, moveAccount, "HTTP 429"},
		{"server error", &statusErr{Status: 500}, moveAccount, "HTTP 500"},
		{"gateway on current non-daemon backends", &statusErr{Status: 502}, moveAccount, "HTTP 502"},
		{"unavailable on current non-daemon backends", &statusErr{Status: 503}, moveAccount, "HTTP 503"},
		{"bad request", &statusErr{Status: 400}, failCall, "HTTP 400"},
		{"body limit", &statusErr{Status: 413}, failCall, "HTTP 413"},
		{"shape", &statusErr{Status: 422}, failCall, "HTTP 422"},
		{"other status", &statusErr{Status: 409}, failCall, "HTTP 409"},
		{"local rejection", &requestInvalidError{errors.New("shape")}, failCall, ""},
		{"invalid reply", &responseInvalidError{errors.New("answer")}, failCall, ""},
		{"other error", errors.New("other"), failCall, ""},
	} {
		t.Run(tc.name, func(t *testing.T) {
			// Wrapping must not change the decision.
			for _, err := range []error{tc.err, fmt.Errorf("backend: %w", tc.err)} {
				got := classify(err)
				if got.effect != tc.effect || got.reason != tc.reason {
					t.Fatalf("classify(%v) = %+v; want effect=%v reason=%q", err, got, tc.effect, tc.reason)
				}
			}
		})
	}
}
