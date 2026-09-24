package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

// simpleIn is the smallest valid call, for tests about transport rather than
// about validation.
func simpleIn() evaluateIn {
	return evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "urgent?"}},
	}
}

const noulReply = `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":0.9}}}`

// HTTP-05: statuses that will fail the same way next time are not retried. A
// replay of a 402 or a 401 only wastes the deadline; a replay of a 400 can
// still be billed.
func TestNoRetryOnTerminalStatuses(t *testing.T) {
	for _, status := range []int{400, 401, 402, 403, 404, 413, 422} {
		var calls atomic.Int64
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			calls.Add(1)
			w.WriteHeader(status)
			w.Write([]byte(`{"error":{"code":` + itoa(status) + `,"message":"nope"}}`))
		}))

		c := testClient(providerAt("openrouter", srv.URL), srv)
		_, err := c.Evaluate(context.Background(), simpleIn())
		srv.Close()

		if err == nil {
			t.Errorf("%d: want an error", status)
		}
		if calls.Load() != 1 {
			t.Errorf("%d: made %d attempts, want 1", status, calls.Load())
		}
		if err != nil && strings.Contains(err.Error(), "nope") {
			t.Errorf("%d: echoed the provider's message: %v", status, err)
		}
	}
}

// HTTP-06: each backend retries the statuses it documents as transient, and
// only those. 529 is TypeSafe's overload status and is not in OpenRouter's
// documented set; 503 is documented on the Decisions path.
func TestRetryPolicyIsPerBackend(t *testing.T) {
	for _, tc := range []struct {
		provider  string
		status    int
		wantCalls int
	}{
		{"typesafe", 429, 2},
		{"typesafe", 529, 2},
		{"typesafe", 503, 1},
		{"openrouter", 429, 2},
		{"openrouter", 503, 2},
		// 524 and 529 joined OpenRouter's documented Decisions statuses when
		// it republished the path; both are transient, so both are retried.
		{"openrouter", 524, 2},
		{"openrouter", 529, 2},
		{"openrouter", 500, 1},
		{"openrouter", 502, 1},
	} {
		var calls atomic.Int64
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			calls.Add(1)
			if calls.Load() == 1 {
				w.WriteHeader(tc.status)
				return
			}
			w.Write([]byte(noulReply))
		}))

		c := testClient(providerAt(tc.provider, srv.URL), srv)
		_, err := c.Evaluate(context.Background(), simpleIn())
		srv.Close()

		if calls.Load() != int64(tc.wantCalls) {
			t.Errorf("%s %d: made %d attempts, want %d", tc.provider, tc.status, calls.Load(), tc.wantCalls)
		}
		if tc.wantCalls > 1 && err != nil {
			t.Errorf("%s %d: %v", tc.provider, tc.status, err)
		}
	}
}

// JEV_MAX_RETRIES=0 means one attempt, and the default of 3 means at most four.
func TestAttemptCountIsBounded(t *testing.T) {
	for retries, want := range map[int]int{0: 1, 1: 2, 3: 4} {
		var calls atomic.Int64
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			calls.Add(1)
			w.WriteHeader(http.StatusTooManyRequests)
		}))

		c := testClient(providerAt("openrouter", srv.URL), srv)
		c.MaxRetries = retries
		if _, err := c.Evaluate(context.Background(), simpleIn()); err == nil {
			t.Errorf("retries=%d: want an error", retries)
		}
		srv.Close()

		if calls.Load() != int64(want) {
			t.Errorf("retries=%d: made %d attempts, want %d", retries, calls.Load(), want)
		}
	}
}

// HTTP-07: Retry-After is honoured in both documented forms, and a malformed
// or past value falls back to the ordinary backoff rather than to zero.
func TestRetryAfterParsing(t *testing.T) {
	now := time.Date(2026, 9, 18, 12, 0, 0, 0, time.UTC)
	for _, tc := range []struct {
		header string
		want   time.Duration
		ok     bool
	}{
		{"", 0, false},
		{"5", 5 * time.Second, true},
		{"0", 0, true},
		{"-3", 0, false},
		{"soon", 0, false},
		{"Fri, 18 Sep 2026 12:00:30 GMT", 30 * time.Second, true},
		// A date already past lifts no minimum, but it is still a valid header.
		{"Fri, 18 Sep 2026 11:59:00 GMT", 0, true},
	} {
		got, ok := retryAfter(tc.header, now)
		if ok != tc.ok || got != tc.want {
			t.Errorf("retryAfter(%q) = %v, %v; want %v, %v", tc.header, got, ok, tc.want, tc.ok)
		}
	}
}

// A valid Retry-After is a minimum wait, not a ceiling to negotiate down.
// Waiting less than the server asked for is how a client earns a longer limit.
func TestRetryAfterIsAMinimumNotACeiling(t *testing.T) {
	now := time.Now()
	if got := backoffFor(time.Millisecond, "30", now); got != 30*time.Second {
		t.Errorf("a long Retry-After was capped down to %v", got)
	}
	// A short header does not shrink an already longer backoff.
	if got := backoffFor(10*time.Second, "1", now); got < 5*time.Second {
		t.Errorf("a short Retry-After shrank the backoff to %v", got)
	}
	// With no header, jitter stays inside the delay window.
	for range 50 {
		got := backoffFor(time.Second, "", now)
		if got < 500*time.Millisecond || got > time.Second {
			t.Fatalf("jittered wait %v outside [500ms, 1s]", got)
		}
	}
}

// HTTP-08: when the wait would not fit in the remaining budget, the call stops
// there instead of sleeping past the deadline and making one more doomed
// attempt on the way out.
func TestRetryStopsWhenWaitExceedsDeadline(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Header().Set("Retry-After", "600")
		w.WriteHeader(http.StatusTooManyRequests)
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	c.Timeout = 2 * time.Second

	start := time.Now()
	_, err := c.Evaluate(context.Background(), simpleIn())
	elapsed := time.Since(start)

	if err == nil {
		t.Fatal("want an error")
	}
	if !strings.Contains(err.Error(), "retry later") {
		t.Errorf("error should say the budget is spent: %v", err)
	}
	if calls.Load() != 1 {
		t.Errorf("made %d attempts, want 1", calls.Load())
	}
	if elapsed > time.Second {
		t.Errorf("waited %v before giving up; it should not sleep at all", elapsed)
	}
}

// HTTP-03: a redirect on an authenticated request is refused, so neither the
// credential nor the state reaches a host that is not the configured endpoint.
func TestRedirectIsRefused(t *testing.T) {
	var secondHostSawAuth, secondHostSawBody atomic.Bool
	second := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		secondHostSawAuth.Store(r.Header.Get("Authorization") != "")
		buf := make([]byte, 1)
		n, _ := r.Body.Read(buf)
		secondHostSawBody.Store(n > 0)
		w.Write([]byte(noulReply))
	}))
	defer second.Close()

	first := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Redirect(w, r, second.URL, http.StatusTemporaryRedirect)
	}))
	defer first.Close()

	c := testClient(providerAt("openrouter", first.URL), first)
	// The shipped transport, not httptest's: the refusal lives there.
	c.HTTP = newHTTPClient()

	_, err := c.Evaluate(context.Background(), simpleIn())
	if err == nil {
		t.Fatal("followed a redirect on an authenticated request")
	}
	if !strings.Contains(err.Error(), "refusing redirect") {
		t.Errorf("unexpected error: %v", err)
	}
	if secondHostSawAuth.Load() || secondHostSawBody.Load() {
		t.Errorf("redirect target received auth=%v body=%v", secondHostSawAuth.Load(), secondHostSawBody.Load())
	}
}

// HTTP-04: an oversized response is a distinct error, not a body silently
// truncated at the cap and then parsed as if it were complete.
func TestOversizedResponseIsRejected(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Write([]byte(`{"answers":{"q":{"type":"noul","noul":0.5,"pad":"`))
		chunk := strings.Repeat("x", 1<<20)
		for range (maxBody >> 20) + 1 {
			w.Write([]byte(chunk))
		}
		w.Write([]byte(`"}}}`))
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	_, err := c.Evaluate(context.Background(), simpleIn())
	if err == nil {
		t.Fatal("accepted an oversized response")
	}
	if !strings.Contains(err.Error(), "exceeds") {
		t.Errorf("error should name the size limit: %v", err)
	}
}

// HTTP-09: a cancelled call returns promptly and makes no further request.
func TestCancellationStopsRetries(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Header().Set("Retry-After", "2")
		w.WriteHeader(http.StatusTooManyRequests)
	}))
	defer srv.Close()

	ctx, cancel := context.WithCancel(context.Background())
	c := testClient(providerAt("openrouter", srv.URL), srv)

	// Cancel while the client is waiting out the Retry-After.
	go func() {
		time.Sleep(50 * time.Millisecond)
		cancel()
	}()

	start := time.Now()
	_, err := c.Evaluate(ctx, simpleIn())
	if err == nil {
		t.Fatal("want a cancellation error")
	}
	if elapsed := time.Since(start); elapsed > time.Second {
		t.Errorf("took %v to notice cancellation", elapsed)
	}
	if calls.Load() != 1 {
		t.Errorf("made %d attempts after cancellation, want 1", calls.Load())
	}
}

// HTTP-10: a transport failure is ambiguous. The request may have been
// received and billed, so it is reported rather than blindly replayed.
func TestTransportFailureIsNotReplayed(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		// Hijack and close without a response: the client sees a broken
		// connection, not a status it could classify.
		hj, ok := w.(http.Hijacker)
		if !ok {
			t.Error("test server does not support hijacking")
			return
		}
		conn, _, err := hj.Hijack()
		if err != nil {
			t.Error(err)
			return
		}
		conn.Close()
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	if _, err := c.Evaluate(context.Background(), simpleIn()); err == nil {
		t.Fatal("want a transport error")
	}
	if calls.Load() != 1 {
		t.Errorf("replayed an ambiguous failure: %d attempts", calls.Load())
	}
}

// SEC-01: a forced failure never prints the credential or the state.
func TestFailuresLeakNeitherKeyNorState(t *testing.T) {
	const (
		keySentinel   = "sk-must-not-appear"
		stateSentinel = "patient-record-4471"
	)
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// A hostile or careless provider echoing the request back.
		body := make([]byte, 2048)
		n, _ := r.Body.Read(body)
		w.WriteHeader(http.StatusBadRequest)
		w.Write([]byte(`{"error":{"message":"rejected: ` + string(body[:n]) + `"}}`))
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	c.APIKey = keySentinel

	in := simpleIn()
	in.State = stateSentinel
	_, err := c.Evaluate(context.Background(), in)
	if err == nil {
		t.Fatal("want an error")
	}
	for _, secret := range []string{keySentinel, stateSentinel} {
		if strings.Contains(err.Error(), secret) {
			t.Fatalf("error leaked %q: %v", secret, err)
		}
	}
}

// A request larger than the local cap is refused before it is sent.
func TestOversizedRequestIsRefusedLocally(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Write([]byte(noulReply))
	}))
	defer srv.Close()

	in := simpleIn()
	in.State = strings.Repeat("x", maxRequestBody+1)

	c := testClient(providerAt("openrouter", srv.URL), srv)
	if _, err := c.Evaluate(context.Background(), in); err == nil {
		t.Fatal("sent an oversized request")
	}
	if calls.Load() != 0 {
		t.Errorf("made %d requests for an oversized body", calls.Load())
	}
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	var b []byte
	for n > 0 {
		b = append([]byte{byte('0' + n%10)}, b...)
		n /= 10
	}
	return string(b)
}
