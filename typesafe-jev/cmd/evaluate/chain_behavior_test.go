package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net"
	"net/http"
	"strings"
	"sync"
	"sync/atomic"
	"syscall"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type chainBehaviorCase struct {
	name   string
	status int
	err    error
	move   bool
}

// Pin the two-hop contract through the real MCP handler before extracting
// session state. Every HTTP request is intercepted; no backend is contacted.
func TestChainBehaviorFixture(t *testing.T) {
	for _, primary := range []string{"typesafe", "openrouter"} {
		for _, tc := range []chainBehaviorCase{
			{"answered", 200, nil, false},
			{"shape", 400, nil, false},
			{"key", 401, nil, true},
			{"credit", 402, nil, true},
			{"forbidden", 403, nil, true},
			{"path", 404, nil, true},
			{"body", 413, nil, false},
			{"validation", 422, nil, false},
			{"throttle", 429, nil, true},
			{"outage", 500, nil, true},
			{"unavailable", 503, nil, true},
			{"connection refused", 0, &net.OpError{Op: "dial", Net: "tcp", Err: syscall.ECONNREFUSED}, true},
		} {
			t.Run(primary+"/"+tc.name, func(t *testing.T) {
				checkChainBehavior(t, primary, tc)
			})
		}
	}
}

func checkChainBehavior(t *testing.T, primary string, tc chainBehaviorCase) {
	t.Helper()
	fallback := map[string]string{"typesafe": "openrouter", "openrouter": "typesafe"}[primary]
	calls := map[string]int{}
	var log strings.Builder
	transport := chainBehaviorTransport(t, primary, fallback, tc, calls)
	client := &chainRunner{log: &log, hops: []*Client{
		{Provider: providers[primary], Model: providers[primary].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
		{Provider: providers[fallback], Model: providers[fallback].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
	}}
	cfg := Config{Provider: providers[primary], Fallback: &FallbackConfig{Provider: providers[fallback]}}
	session := connect(t, cfg, client)
	checkChainReplies(t, session, tc)
	wantPrimary, wantFallback, wantLog := 2, 0, ""
	if tc.move {
		wantPrimary, wantFallback = 1, 2
		reason := fmt.Sprintf("HTTP %d", tc.status)
		if tc.err != nil {
			reason = "unreachable"
		}
		wantLog = fmt.Sprintf("evaluate: %s refused or failed the call (%s); using the %s fallback for the rest of this session\n", primary, reason, fallback)
	}
	if calls[primary] != wantPrimary || calls[fallback] != wantFallback || log.String() != wantLog {
		t.Fatalf("calls=%v log=%q; want primary=%d fallback=%d log=%q", calls, log.String(), wantPrimary, wantFallback, wantLog)
	}
}

func chainBehaviorTransport(t *testing.T, primary, fallback string, tc chainBehaviorCase, calls map[string]int) backendFixtureTransport {
	t.Helper()
	return backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
		provider := primary
		if r.URL.String() == providers[fallback].EndpointURL {
			provider = fallback
		}
		calls[provider]++
		var sent struct{ Model string }
		if err := json.NewDecoder(r.Body).Decode(&sent); err != nil {
			return nil, err
		}
		wantModel := "caller-model"
		if provider == fallback {
			wantModel = providers[fallback].DefaultModel
		}
		if sent.Model != wantModel {
			t.Errorf("%s received model %q, want %q", provider, sent.Model, wantModel)
		}
		if provider == primary && tc.err != nil {
			return nil, tc.err
		}
		status := 200
		if provider == primary {
			status = tc.status
		}
		return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
	})
}

func checkChainReplies(t *testing.T, session *mcp.ClientSession, tc chainBehaviorCase) {
	t.Helper()
	for range 2 {
		result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: evaluateIn{
			State: "fixture", Questions: simpleIn().Questions, Model: "caller-model",
		}})
		if err != nil {
			t.Fatal(err)
		}
		wantError := tc.status != 200 && !tc.move
		if result.IsError != wantError {
			t.Fatalf("tool error=%v, want %v: %s", result.IsError, wantError, contentText(t, result))
		}
		if !wantError && contentText(t, result) != noulReply {
			t.Fatalf("reply changed: %s", contentText(t, result))
		}
	}
}

func TestConcurrentChainFailuresLogOneMove(t *testing.T) {
	const count = 8
	var primaryCalls, fallbackCalls atomic.Int32
	arrived := make(chan struct{}, count)
	release := make(chan struct{})
	var log strings.Builder
	primary := &Client{Provider: providers["typesafe"], Model: "jev-latest", Timeout: 5 * time.Second}
	primary.HTTP = &http.Client{Transport: backendFixtureTransport(func(*http.Request) (*http.Response, error) {
		primaryCalls.Add(1)
		arrived <- struct{}{}
		<-release
		return &http.Response{StatusCode: 401, Header: http.Header{}, Body: io.NopCloser(strings.NewReader("{}"))}, nil
	})}
	fallback := &Client{Provider: providers["openrouter"], Model: "~typesafe/jev-latest", Timeout: 5 * time.Second,
		HTTP: &http.Client{Transport: backendFixtureTransport(func(*http.Request) (*http.Response, error) {
			fallbackCalls.Add(1)
			return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
		})},
	}
	session := connect(t, Config{Provider: providers["typesafe"]}, &chainRunner{hops: []*Client{primary, fallback}, log: &log})
	var wg sync.WaitGroup
	for range count {
		wg.Add(1)
		go func() {
			defer wg.Done()
			result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: simpleIn()})
			if err != nil || result.IsError {
				t.Errorf("concurrent call: result=%v err=%v", result, err)
			}
		}()
	}
	// Release all failed primaries together; no call can observe the move early.
	for range count {
		select {
		case <-arrived:
		case <-time.After(5 * time.Second):
			close(release)
			wg.Wait()
			t.Fatal("concurrent calls did not reach the transport")
		}
	}
	close(release)
	wg.Wait()
	if primaryCalls.Load() != count || fallbackCalls.Load() != count || strings.Count(log.String(), "using the openrouter fallback") != 1 {
		t.Fatalf("calls primary=%d fallback=%d log=%q", primaryCalls.Load(), fallbackCalls.Load(), log.String())
	}
}
