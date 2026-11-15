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
	for _, tc := range []struct {
		name string
		err  error
	}{
		{"deadline", context.DeadlineExceeded},
		{"wrapped deadline", fmt.Errorf("typesafe: %w", context.DeadlineExceeded)},
		{"HTTP transport deadline", &url.Error{Op: "Post", URL: "https://backend.invalid", Err: context.DeadlineExceeded}},
		{"network deadline", &net.OpError{Op: "read", Net: "tcp", Err: context.DeadlineExceeded}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var network net.Error
			if !errors.As(tc.err, &network) || !network.Timeout() {
				t.Fatal("fixture must also satisfy net.Error and report a timeout")
			}
			reason, move := fallbackReason(tc.err)
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
				Timeout: tc.requestTimeout, Log: log,
			}
			c.HTTP = &http.Client{Transport: timeoutTransport(func(r *http.Request) (*http.Response, error) {
				primaryCalls++
				if primaryCalls == 1 {
					<-r.Context().Done()
					return nil, r.Context().Err()
				}
				return &http.Response{StatusCode: http.StatusOK, Body: io.NopCloser(strings.NewReader(noulReply)), Header: http.Header{}}, nil
			})}
			c.Fallback = &Client{
				Provider: providers["openrouter"], Model: "~typesafe/jev-latest",
				Timeout: time.Second,
				HTTP: &http.Client{Transport: timeoutTransport(func(*http.Request) (*http.Response, error) {
					fallbackCalls++
					return nil, errors.New("unexpected fallback call")
				})},
			}
			ctx, cancel := context.WithTimeout(context.Background(), tc.callerTimeout)
			defer cancel()
			if _, err := runEvaluate(ctx, c, simpleIn()); !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("want the request timeout, got %v", err)
			}
			if fallbackCalls != 0 || log.Len() != 0 {
				t.Fatalf("timeout called the fallback %d times; log %q", fallbackCalls, log.String())
			}
			c.Timeout = time.Second
			body, err := runEvaluate(context.Background(), c, simpleIn())
			if err != nil || string(body) != noulReply {
				t.Fatalf("next call: body %s, error %v", body, err)
			}
			if primaryCalls != 2 || fallbackCalls != 0 || log.Len() != 0 {
				t.Fatalf("calls: primary %d, fallback %d; log %q; want 2, 0 and no switch", primaryCalls, fallbackCalls, log.String())
			}
		})
	}
}
