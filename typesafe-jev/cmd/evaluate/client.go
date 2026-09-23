package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"math/rand/v2"
	"net/http"
	"slices"
	"strconv"
	"strings"
	"sync/atomic"
	"time"
)

// maxBody caps response size so an oversized reply cannot exhaust memory.
const maxBody = 16 << 20

// maxRequestBody caps the serialized request. This is a local safety policy to
// keep a runaway state object from being sent, not a published provider limit.
const maxRequestBody = 16 << 20

const (
	attributionURL   = "https://github.com/racecraft-lab/typesafe-mcp"
	attributionTitle = "Racecraft Jev MCP"
)

// Client calls a Jev evaluation endpoint: the TypeSafe API directly, or
// OpenRouter's Decisions router. Both take the same request body.
type Client struct {
	// Provider carries the endpoint, the retry policy, and the backend name
	// that appears in errors. It is fixed for the life of the process: a tool
	// call cannot redirect a request to another backend.
	Provider ProviderSpec
	// Model is the configured default, used when a call names none.
	Model string
	// APIKey redacts itself when printed. Only attempt reveals it.
	APIKey credential

	HTTP *http.Client
	// Timeout bounds the whole evaluation: every attempt plus every wait
	// between them, not each attempt separately.
	Timeout time.Duration
	// MaxRetries is the number of *additional* attempts, so 0 means one.
	MaxRetries int
	// Backoff is the first retry delay; it doubles each attempt.
	Backoff time.Duration

	// Fallback is the operator's opt-in second backend (JEV_FALLBACK_PROVIDER),
	// or nil. See fallback.go.
	Fallback *Client
	// Log receives the one line written when calls switch to Fallback. It is
	// stderr in production: stdout carries the MCP protocol.
	Log io.Writer
	// switched is set once and never cleared, so one session never alternates
	// between backends.
	switched atomic.Bool
}

// newHTTPClient returns the transport used for provider calls.
//
// Redirects are refused. A redirect on an authenticated inference request
// would resend the Authorization header, and the state being judged, to a host
// that is not the configured endpoint.
func newHTTPClient() *http.Client {
	return &http.Client{
		CheckRedirect: func(req *http.Request, _ []*http.Request) error {
			return fmt.Errorf("refusing redirect to %s: an authenticated request is never forwarded to another host", req.URL.Host)
		},
	}
}

// Evaluate posts a request and returns the raw response JSON, including any
// fields this server does not recognize.
func (c *Client) Evaluate(ctx context.Context, req any) ([]byte, error) {
	body, err := json.Marshal(req)
	if err != nil {
		return nil, err
	}
	if len(body) > maxRequestBody {
		return nil, fmt.Errorf("%s: request is %d bytes, over the %d byte limit; send less state or fewer questions",
			c.Provider.Name, len(body), maxRequestBody)
	}

	// One deadline for the whole evaluation. Retry waits are spent from the
	// same budget, so a caller's timeout means what it says.
	ctx, cancel := context.WithTimeout(ctx, c.Timeout)
	defer cancel()
	deadline, _ := ctx.Deadline()

	delay := c.Backoff
	for attempt := 0; ; attempt++ {
		b, status, header, err := c.attempt(ctx, body)
		if err != nil {
			return nil, err
		}
		if status/100 == 2 {
			return b, nil
		}
		// Only the statuses this backend documents as transient, and only
		// while attempts remain. Authentication, credit, validation, payload,
		// and not-found failures would fail the same way and bill again.
		if !slices.Contains(c.Provider.RetryStatuses, status) || attempt >= c.MaxRetries {
			return nil, c.statusError(status, b)
		}

		wait := backoffFor(delay, header, time.Now())
		// Stop rather than sleep past the deadline and then make one more
		// doomed attempt on the way out.
		if remaining := time.Until(deadline); wait >= remaining {
			return nil, &statusErr{Status: status, text: fmt.Sprintf("%s: HTTP %d; the next retry would not fit in the %s budget; retry later",
				c.Provider.Name, status, c.Timeout)}
		}
		if err := sleep(ctx, wait); err != nil {
			return nil, err
		}
		delay *= 2
	}
}

// sleep waits for d, or returns early if the call is cancelled.
func sleep(ctx context.Context, d time.Duration) error {
	t := time.NewTimer(d)
	defer t.Stop()
	select {
	case <-ctx.Done():
		return ctx.Err()
	case <-t.C:
		return nil
	}
}

// backoffFor decides how long to wait before the next attempt.
//
// A valid Retry-After is a minimum, not a ceiling: waiting less than a server
// asked for is how a client turns a rate limit into a longer one. So the wait
// is whichever is larger, the header or the backoff.
func backoffFor(delay time.Duration, header string, now time.Time) time.Duration {
	wait := jitter(delay)
	if after, ok := retryAfter(header, now); ok && after > wait {
		return after
	}
	return wait
}

// jitter spreads retries over the second half of the delay window, so several
// clients that were rate limited together do not return in lockstep.
func jitter(delay time.Duration) time.Duration {
	if delay <= 0 {
		return 0
	}
	half := delay / 2
	return half + time.Duration(rand.Int64N(int64(half)+1))
}

// retryAfter parses a Retry-After header in either documented form: a count of
// seconds, or an HTTP date.
//
// OpenRouter's OpenAPI document declares no Retry-After header for these
// statuses. Honouring one that arrives anyway is correct HTTP behaviour, and
// costs nothing when it never does.
func retryAfter(header string, now time.Time) (time.Duration, bool) {
	header = strings.TrimSpace(header)
	if header == "" {
		return 0, false
	}
	if secs, err := strconv.Atoi(header); err == nil {
		if secs < 0 {
			return 0, false
		}
		return time.Duration(secs) * time.Second, true
	}
	when, err := http.ParseTime(header)
	if err != nil {
		return 0, false
	}
	// A date already in the past means the server is ready now, which is a
	// valid answer: it lifts no minimum, so the backoff alone applies.
	if d := when.Sub(now); d > 0 {
		return d, true
	}
	return 0, true
}

// attempt makes one HTTP request and returns the body, the status, and the
// Retry-After header if there was one.
func (c *Client) attempt(ctx context.Context, body []byte) ([]byte, int, string, error) {
	r, err := http.NewRequestWithContext(ctx, http.MethodPost, c.Provider.EndpointURL, bytes.NewReader(body))
	if err != nil {
		return nil, 0, "", err
	}
	r.Header.Set("Authorization", "Bearer "+c.APIKey.reveal())
	r.Header.Set("Content-Type", "application/json")
	if c.Provider.Attribution {
		// Fixed values. Never derived from a local path or repository content.
		r.Header.Set("HTTP-Referer", attributionURL)
		r.Header.Set("X-OpenRouter-Title", attributionTitle)
	}

	resp, err := c.HTTP.Do(r)
	if err != nil {
		// Transport errors are never retried: an ambiguous failure may already
		// have been received and billed, and replaying it would charge twice.
		return nil, 0, "", fmt.Errorf("%s: %w", c.Provider.Name, err)
	}
	defer resp.Body.Close()

	b, err := io.ReadAll(io.LimitReader(resp.Body, maxBody+1))
	if err != nil {
		return nil, 0, "", fmt.Errorf("%s: reading response: %w", c.Provider.Name, err)
	}
	if len(b) > maxBody {
		return nil, 0, "", fmt.Errorf("%s: response exceeds the %d byte limit", c.Provider.Name, maxBody)
	}
	return b, resp.StatusCode, resp.Header.Get("Retry-After"), nil
}

// statusError turns a non-2xx response into a message the agent can act on.
//
// The provider's own error text is deliberately not included: it may quote the
// submitted state back, and an error travels further than the input did.
func (c *Client) statusError(status int, body []byte) error {
	remedy := remedyFor(status)
	if id := requestID(body); id != "" {
		return &statusErr{Status: status, text: fmt.Sprintf("%s: HTTP %d; %s (request %s)", c.Provider.Name, status, remedy, id)}
	}
	return &statusErr{Status: status, text: fmt.Sprintf("%s: HTTP %d; %s", c.Provider.Name, status, remedy)}
}

// statusErr is a provider's non-2xx answer. The text is what the agent reads;
// the status is what a configured fallback decides on, so neither has to be
// parsed back out of the other.
type statusErr struct {
	Status int
	text   string
}

func (e *statusErr) Error() string { return e.text }

func remedyFor(status int) string {
	switch status {
	case http.StatusBadRequest, http.StatusUnprocessableEntity:
		return "the provider rejected the request shape; check question types and criteria"
	case http.StatusUnauthorized:
		return "check the configured credential"
	case http.StatusPaymentRequired:
		return "check credits or the key's spending limit"
	case http.StatusForbidden:
		return "the credential is valid but not permitted to make this call"
	case http.StatusNotFound:
		// Not asserted as a bad model: the alpha endpoint may also move.
		return "verify the endpoint and the selected model"
	case http.StatusRequestEntityTooLarge:
		return "the request is too large for the provider; send less state"
	case http.StatusTooManyRequests:
		return "rate limited; retry later"
	default:
		if status >= 500 {
			return "the provider reported a server error; retry later"
		}
		return "unexpected status from the provider"
	}
}

// requestID pulls a provider request id out of a response body, when there is
// one, so a failure can be correlated without quoting the whole response.
func requestID(body []byte) string {
	var env struct {
		ID    string `json:"id"`
		Error struct {
			ID string `json:"id"`
		} `json:"error"`
	}
	if json.Unmarshal(body, &env) != nil {
		return ""
	}
	if env.ID != "" {
		return env.ID
	}
	return env.Error.ID
}
