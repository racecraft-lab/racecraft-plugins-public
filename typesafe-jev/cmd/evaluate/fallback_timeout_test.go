package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"strings"
	"testing"
	"time"
)

func TestFallbackReasonClassifiesDeadlineAsTimeout(t *testing.T) {
	ctx, cancel := context.WithDeadline(context.Background(), time.Unix(1, 0))
	defer cancel()
	for _, tc := range []struct {
		name string
		err  error
	}{
		{"deadline", ctx.Err()},
		{"wrapped deadline", fmt.Errorf("typesafe: %w", context.DeadlineExceeded)},
		{"HTTP transport deadline", &url.Error{Op: "Post", URL: "https://backend.invalid", Err: context.DeadlineExceeded}},
		{"network deadline", &net.OpError{Op: "read", Net: "tcp", Err: context.DeadlineExceeded}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var network net.Error
			if !errors.As(tc.err, &network) || !network.Timeout() {
				t.Fatal("fixture must also satisfy net.Error and report a timeout")
			}
			reason, move := fallbackReason(ctx, tc.err)
			if reason != "timeout" || move {
				t.Fatalf("deadline classified as (%q, %v); want (\"timeout\", false)", reason, move)
			}
		})
	}
}

type timeoutTransport func(*http.Request) (*http.Response, error)

func (f timeoutTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	return f(r)
}

func TestDialTimeoutMovesSessionToFallback(t *testing.T) {
	primaryCalls, fallbackCalls := 0, 0
	log := &strings.Builder{}
	transport := &http.Transport{DialContext: func(ctx context.Context, network, address string) (net.Conn, error) {
		primaryCalls++
		// An already-expired dial deadline fails before any connection is made.
		dialer := &net.Dialer{Deadline: time.Unix(1, 0)}
		return dialer.DialContext(ctx, network, address)
	}}
	t.Cleanup(transport.CloseIdleConnections)
	c := &Client{
		Provider: providerAt("typesafe", "http://127.0.0.1:1"), Model: "jev-latest",
		Timeout: time.Minute,
		HTTP:    &http.Client{Transport: transport},
	}
	chain := &chainRunner{log: log, hops: []*Client{c, {
		Provider: providers["openrouter"], Model: "~typesafe/jev-latest",
		Timeout: time.Minute,
		HTTP: &http.Client{Transport: timeoutTransport(func(*http.Request) (*http.Response, error) {
			fallbackCalls++
			return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(noulReply)), Header: http.Header{}}, nil
		})},
	},
	}}
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	_, err := runOn(ctx, c, simpleIn())
	if !errors.Is(err, context.DeadlineExceeded) || ctx.Err() != nil {
		t.Fatalf("want a dial deadline error with a live call context, got error %v, context %v", err, ctx.Err())
	}
	if reason, move := fallbackReason(ctx, err); reason != "unreachable" || !move {
		t.Errorf("dial timeout classified as (%q, %v); want (\"unreachable\", true)", reason, move)
	}
	for call := 0; call < 2; call++ {
		body, err := runEvaluate(ctx, chain, simpleIn())
		if err != nil || string(body) != noulReply {
			t.Errorf("call %d: body %s, error %v; want fallback reply", call, body, err)
		}
	}
	// One classification probe, one failed call, then the session stays moved.
	if primaryCalls != 2 || fallbackCalls != 2 {
		t.Errorf("calls: primary %d, fallback %d; want 2, 2", primaryCalls, fallbackCalls)
	}
	wantLog := "evaluate: typesafe refused or failed the call (unreachable); using the openrouter fallback for the rest of this session\n"
	if log.String() != wantLog {
		t.Errorf("switch log %q; want %q", log.String(), wantLog)
	}
}

// Pin the request-deadline guard before changing timeout classification. A
// timed-out call must not send state to the fallback or move later calls there.
func TestRequestTimeoutKeepsThePrimary(t *testing.T) {
	for _, tc := range []struct {
		name                          string
		callerTimeout, requestTimeout time.Duration
	}{
		{"request budget", time.Second, 10 * time.Millisecond},
		{"caller deadline", 10 * time.Millisecond, time.Second},
	} {
		t.Run(tc.name, func(t *testing.T) {
			primaryCalls, fallbackCalls := 0, 0
			log := &strings.Builder{}
			c := &Client{
				Provider: providers["typesafe"], Model: "jev-latest",
				Timeout: tc.requestTimeout,
			}
			c.HTTP = &http.Client{Transport: timeoutTransport(func(r *http.Request) (*http.Response, error) {
				primaryCalls++
				if primaryCalls == 1 {
					<-r.Context().Done()
					return nil, r.Context().Err()
				}
				return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(noulReply)), Header: http.Header{}}, nil
			})}
			fallback := &Client{
				Provider: providers["openrouter"], Model: "~typesafe/jev-latest",
				Timeout: time.Second,
				HTTP: &http.Client{Transport: timeoutTransport(func(*http.Request) (*http.Response, error) {
					fallbackCalls++
					return nil, errors.New("unexpected fallback call")
				})},
			}
			chain := &chainRunner{hops: []*Client{c, fallback}, log: log}
			ctx, cancel := context.WithTimeout(context.Background(), tc.callerTimeout)
			defer cancel()
			if _, err := runEvaluate(ctx, chain, simpleIn()); !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("want the request timeout, got %v", err)
			}
			if fallbackCalls != 0 || log.Len() != 0 {
				t.Fatalf("timeout called the fallback %d times; log %q", fallbackCalls, log.String())
			}
			c.Timeout = time.Second
			body, err := runEvaluate(context.Background(), chain, simpleIn())
			if err != nil || string(body) != noulReply {
				t.Fatalf("next call: body %s, error %v", body, err)
			}
			if primaryCalls != 2 || fallbackCalls != 0 || log.Len() != 0 {
				t.Fatalf("calls: primary %d, fallback %d; log %q; want 2, 0 and no switch", primaryCalls, fallbackCalls, log.String())
			}
		})
	}
}
