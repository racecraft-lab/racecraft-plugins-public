package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

type backendFixtureTransport func(*http.Request) (*http.Response, error)

func (f backendFixtureTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	return f(r)
}

// These literal fixtures pin the existing uncapped question count and the
// one-option choice accepted by both backends before moving limits into rows.
// Requests go through the MCP tool; the transport cannot reach a real backend.
func TestBackendBehaviorFixture(t *testing.T) {
	for _, provider := range []string{"typesafe", "openrouter"} {
		for _, count := range []int{1, 256} {
			t.Run(fmt.Sprintf("%s/%d questions", provider, count), func(t *testing.T) {
				questions, reply := backendBehaviorFixture(t, count)
				spec := providers[provider]
				cfg := Config{Provider: spec, Model: spec.DefaultModel, Timeout: time.Second}
				calls := 0
				client := &Client{
					Provider: spec, Model: spec.DefaultModel, APIKey: "fixture-key", Timeout: time.Second,
					HTTP: &http.Client{Transport: backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
						calls++
						if err := checkBackendFixtureRequest(t, r, spec, count); err != nil {
							return nil, err
						}
						return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(string(reply)))}, nil
					})},
				}
				session := connect(t, cfg, client)
				result, err := session.CallTool(context.Background(), &mcp.CallToolParams{
					Name: "evaluate", Arguments: map[string]any{"state": "fixture", "questions": questions},
				})
				if err != nil {
					t.Fatal(err)
				}
				if result.IsError || calls != 1 {
					t.Fatalf("result=%+v calls=%d; want one answered request", result, calls)
				}
			})
		}
	}
}

func backendBehaviorFixture(t *testing.T, count int) (map[string]any, []byte) {
	t.Helper()
	questions := map[string]any{}
	answers := map[string]any{}
	for i := range count {
		id := fmt.Sprintf("q%d", i)
		questions[id] = map[string]any{
			"type": "choice", "instructions": "Choose the only option",
			"criteria": map[string]any{"only": "The only option"},
		}
		answers[id] = map[string]any{"type": "choice", "choice": "only"}
	}
	reply, err := json.Marshal(map[string]any{
		"model": "fixture", "usage": map[string]int{"input_tokens": 1, "output_tokens": 1},
		"answers": answers,
	})
	if err != nil {
		t.Fatal(err)
	}
	return questions, reply
}

func checkBackendFixtureRequest(t *testing.T, r *http.Request, spec ProviderSpec, count int) error {
	t.Helper()
	if r.URL.String() != spec.EndpointURL || r.Header.Get("Authorization") != "Bearer fixture-key" {
		t.Errorf("unexpected endpoint or auth: %s", r.URL)
	}
	var sent struct {
		Model     string         `json:"model"`
		Questions map[string]any `json:"questions"`
	}
	if err := json.NewDecoder(r.Body).Decode(&sent); err != nil {
		return err
	}
	if sent.Model != spec.DefaultModel || len(sent.Questions) != count {
		t.Errorf("sent model=%q questions=%d", sent.Model, len(sent.Questions))
	}
	return nil
}
