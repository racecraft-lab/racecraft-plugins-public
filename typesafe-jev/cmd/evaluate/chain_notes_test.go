package main

import (
	"context"
	"io"
	"net/http"
	"os"
	"strings"
	"sync"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func TestLoadedChainNotesDropUnusableMiddleHop(t *testing.T) {
	ollamaCloudEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,ollama")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	resolved, err := resolveHops(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	chain, cfg, err := startChain(resolved, io.Discard, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	session := connect(t, cfg, chain)
	listed, err := session.ListTools(context.Background(), nil)
	if err != nil || len(listed.Tools) != 1 {
		t.Fatalf("tools=%v error=%v", listed, err)
	}
	for surface, note := range map[string]string{
		"instructions": session.InitializeResult().Instructions,
		"tool":         listed.Tools[0].Description,
	} {
		if !strings.Contains(note, "Backend: typesafe, with ollama as fallback.") || strings.Contains(note, "openrouter") {
			t.Errorf("%s names an unloaded hop: %s", surface, note)
		}
	}
	if !strings.Contains(session.InitializeResult().Instructions, "Ollama serves Clef") {
		t.Error("instructions omit the loaded later hop's answer contract")
	}
}

func TestConcurrentThreeHopMovesKeepToolNoteCurrent(t *testing.T) {
	ollamaCloudEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,ollama")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	resolved, err := resolveHops(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	for range 60 {
		checkConcurrentServingNote(t, resolved)
	}
}

func checkConcurrentServingNote(t *testing.T, resolved resolvedHops) {
	t.Helper()
	chain, cfg, err := startChain(resolved, io.Discard, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	for i, hop := range chain.hops {
		hop.HTTP = &http.Client{Transport: backendFixtureTransport(func(*http.Request) (*http.Response, error) {
			status := 401
			if i == 2 {
				status = 200
			}
			return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
		})}
	}
	session := connect(t, cfg, chain)
	start := make(chan struct{})
	var callers sync.WaitGroup
	for range 16 {
		callers.Go(func() {
			<-start
			result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: simpleIn()})
			if err != nil || result.IsError {
				t.Errorf("call result=%v error=%v", result, err)
			}
		})
	}
	close(start)
	callers.Wait()
	listed, err := session.ListTools(context.Background(), nil)
	if err != nil || len(listed.Tools) != 1 {
		t.Fatalf("tools=%v error=%v", listed, err)
	}
	if note := listed.Tools[0].Description; !strings.Contains(note, "Serving hop: ollama.") {
		t.Fatalf("tool note went stale after concurrent moves: %s", note)
	}
}

func TestBackendChainIsListedOnce(t *testing.T) {
	for _, tc := range []struct {
		names []string
		want  string
	}{
		{[]string{"typesafe"}, "Backend: typesafe."},
		{[]string{"typesafe", "openrouter"}, "Backend: typesafe, with openrouter as fallback."},
		{[]string{"openrouter", "typesafe", "ollama-local", "ollama"}, "Backend: openrouter, then typesafe, then ollama-local, then ollama."},
	} {
		names := tc.names
		t.Run(strings.Join(names, ","), func(t *testing.T) {
			configs := make([]Config, len(names))
			chain := &chainRunner{}
			for i, name := range names {
				spec := providers[name]
				configs[i] = Config{Provider: spec}
				chain.hops = append(chain.hops, &Client{Provider: spec})
			}
			cfg := configs[0]
			cfg.AdditionalHops = configs[1:]
			session := connect(t, cfg, chain)
			listed, err := session.ListTools(context.Background(), nil)
			if err != nil || len(listed.Tools) != 1 {
				t.Fatalf("tools=%v error=%v", listed, err)
			}
			for surface, note := range map[string]string{
				"instructions": session.InitializeResult().Instructions,
				"tool":         listed.Tools[0].Description,
			} {
				if strings.Count(note, "Backend:") != 1 || strings.Contains(note, "Backend chain:") || !strings.Contains(note, tc.want) {
					t.Errorf("%s must contain %q exactly once and no duplicate chain line", surface, tc.want)
				}
			}
		})
	}
}
