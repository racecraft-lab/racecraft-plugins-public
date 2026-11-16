package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Pin the credential verdict, CLI strictness, server drop rule and destination
// before consolidating their owners. Every file is a temporary fixture and the
// transport cannot send a request to a provider.
func TestResolutionBehaviorFixture(t *testing.T) {
	cases := []resolutionSourceCase{
		{"absent", "none", "absent", "", ""},
		{"empty-env", "none", "absent", "", ""},
		{"environment", "environment", "ok", "", fixtureKey},
		{"whitespace-env", "environment", "unusable", "has leading or trailing whitespace", " bad"},
		{"control-env", "environment", "unusable", "contains a control character", "bad\x01key"},
		{"placeholder-env", "environment", "unusable", "is an unexpanded ${...} placeholder", "${KEY}"},
		{"explicit-file", "explicit-file", "ok", "", fixtureKey + "\n"},
		{"default-file", "default-file", "ok", "", fixtureKey + "\r\n"},
		{"empty-path", "environment", "ok", "", fixtureKey},
		{"missing-file", "explicit-file", "unusable", "does not exist", fixtureKey + "\n"},
		{"empty-file", "explicit-file", "unusable", "is empty", ""},
		{"whitespace-file", "explicit-file", "unusable", "has leading or trailing whitespace", " bad\n"},
		{"control-file", "explicit-file", "unusable", "contains a control character", "bad\x00key"},
		{"placeholder-file", "explicit-file", "unusable", "is an unexpanded ${...} placeholder", "${KEY}\n"},
		{"oversized-file", "explicit-file", "unusable", "over the 8192 byte limit", strings.Repeat("x", maxKeyFileBytes+1)},
		{"directory", "explicit-file", "unusable", "is not a regular file", fixtureKey + "\n"},
		{"broken-default", "default-file", "unusable", "is empty", ""},
	}
	for _, primary := range []string{"typesafe", "openrouter"} {
		for _, role := range []string{"primary", "fallback"} {
			for _, tc := range cases {
				t.Run(primary+"/"+role+"/"+tc.kind, func(t *testing.T) {
					runResolutionFixture(t, primary, role, tc)
				})
			}
		}
	}
}

type resolutionSourceCase struct {
	kind, source, state, reason, contents string
}

func configureResolutionSource(t *testing.T, provider, fileVar string, tc resolutionSourceCase) {
	t.Helper()
	keyEnv := providers[provider].APIKeyEnv
	// The caller has already isolated HOME to a temporary fixture directory.
	home := os.Getenv("HOME")
	switch tc.source {
	case "none":
		if tc.kind == "empty-env" {
			t.Setenv(keyEnv, "")
		}
	case "environment":
		if tc.kind == "empty-path" {
			t.Setenv(fileVar, "")
		}
		t.Setenv(keyEnv, tc.contents)
	case "default-file":
		writeDefaultKey(t, home, provider, tc.contents, 0o600)
		t.Setenv(keyEnv, "ignored-environment-key")
	case "explicit-file":
		path := filepath.Join(home, "missing.key")
		if tc.kind == "directory" {
			path = t.TempDir()
		} else if tc.kind != "missing-file" {
			path = writeKeyFile(t, tc.contents, 0o600)
		}
		t.Setenv(fileVar, path)
		t.Setenv(keyEnv, "ignored-environment-key")
	}
}

func runResolutionFixture(t *testing.T, primary, role string, tc resolutionSourceCase) {
	t.Helper()
	isolateCallEnv(t)
	fallback := map[string]string{"typesafe": "openrouter", "openrouter": "typesafe"}[primary]
	t.Setenv("JEV_PROVIDER", primary)
	t.Setenv("JEV_FALLBACK_PROVIDER", fallback)
	provider, fileVar, other := primary, pluginKeyFileEnv, fallback
	if role == "fallback" {
		provider, fileVar, other = fallback, pluginFallbackFileEnv, primary
	}
	t.Setenv(providers[other].APIKeyEnv, fixtureKey)
	configureResolutionSource(t, provider, fileVar, tc)

	calls := 0
	wantProvider := provider
	if tc.state != "ok" {
		wantProvider = other
	} else {
		wantProvider = primary
	}
	original := http.DefaultTransport
	http.DefaultTransport = backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
		calls++
		if r.URL.String() != providers[wantProvider].EndpointURL || r.Header.Get("Authorization") != "Bearer "+fixtureKey {
			t.Error("request used the wrong backend or credential")
		}
		return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(validAnswer))}, nil
	})
	t.Cleanup(func() { http.DefaultTransport = original })

	expected := sourceStatus{Provider: provider, Source: tc.source, State: tc.state, reason: tc.reason}
	checked, called := checkResolutionCLI(t, role, expected, &calls)
	wantExit := checked.code
	log := checkResolutionServer(t, tc.state, wantExit, &calls)
	for _, output := range []string{checked.stdout, checked.stderr, called.stderr, log.String()} {
		if strings.Contains(output, fixtureKey) || strings.Contains(output, "ignored-environment-key") {
			t.Fatal("credential leaked in output")
		}
	}
}

func checkResolutionCLI(t *testing.T, role string, expected sourceStatus, callCount *int) (callResult, callResult) {
	t.Helper()
	provider, source, state, reason := expected.Provider, expected.Source, expected.State, expected.reason
	checked := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	wantExit := exitAnswered
	if state == "unusable" {
		wantExit = exitCredentialBroken
	}
	var report checkReport
	if err := json.Unmarshal([]byte(checked.stdout), &report); err != nil {
		t.Fatal(err)
	}
	status := report.Primary
	if role == "fallback" {
		if report.Fallback == nil {
			t.Fatal("missing fallback report")
		}
		status = *report.Fallback
	}
	calls := *callCount
	if checked.code != wantExit || report.Exit != wantExit || status.Provider != provider || status.Source != source || status.State != state || calls != 0 {
		t.Fatalf("check exit=%d report=%+v source=%+v calls=%d; want %d %s/%s", checked.code, report, status, calls, wantExit, source, state)
	}
	if reason != "" && !strings.Contains(checked.stderr, reason) {
		t.Fatalf("missing reason %q: %s", reason, checked.stderr)
	}
	called := runCallForTest(t, callOptions{pluginDefaults: true}, validRequest)
	calls = *callCount
	if called.code != wantExit || (wantExit == exitAnswered && calls != 1) || (wantExit != exitAnswered && calls != 0) {
		t.Fatalf("call exit=%d calls=%d; want exit=%d", called.code, calls, wantExit)
	}
	if state == "absent" && called.stderr != "" {
		t.Fatalf("absent hop produced a CLI diagnostic: %s", called.stderr)
	}
	return checked, called
}

func checkResolutionServer(t *testing.T, state string, wantExit int, callCount *int) *strings.Builder {
	t.Helper()
	cfg, err := resolveCallConfig(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	var log strings.Builder
	client, served, err := newClients(cfg, &log)
	if err != nil {
		t.Fatal(err)
	}
	wantLines := 0
	if state != "ok" {
		wantLines = 1
	}
	if strings.Count(log.String(), "\n") != wantLines {
		t.Fatalf("server drop log: %q; want %d lines", log.String(), wantLines)
	}
	session := connect(t, served, client)
	result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: map[string]any{
		"state": "fixture", "questions": map[string]any{"q": map[string]any{"type": "noul", "instructions": "Is this urgent?"}},
	}})
	if err != nil || result.IsError {
		t.Fatalf("server tool failed: result=%v err=%v", result, err)
	}
	calls := *callCount
	if calls != map[bool]int{true: 2, false: 1}[wantExit == exitAnswered] {
		t.Fatal("server did not make exactly one request")
	}
	return &log
}

func TestCallStillRejectsThePrimaryAsFallback(t *testing.T) {
	for _, provider := range []string{"typesafe", "openrouter"} {
		t.Run(provider, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_PROVIDER", provider)
			t.Setenv("JEV_FALLBACK_PROVIDER", provider)
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
			if got.code != 4 || got.stdout != "" || got.stderr != fmt.Sprintf("evaluate: JEV_FALLBACK_PROVIDER=%q is the primary backend; a fallback must be the other one\n", provider) {
				t.Fatalf("unexpected CLI result: %+v", got)
			}
		})
	}
}

// A discovered key path is validated at the same point as an explicit one,
// before later settings, even when HOME itself is relative.
func TestPluginDefaultKeyPathKeepsValidationPrecedence(t *testing.T) {
	for _, role := range []string{"primary", "fallback"} {
		t.Run(role, func(t *testing.T) {
			home := isolateCallEnv(t)
			pluginEnv(t)
			provider, fileVar := "typesafe", pluginKeyFileEnv
			if role == "fallback" {
				provider, fileVar = "openrouter", pluginFallbackFileEnv
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			}
			writeDefaultKey(t, home, provider, fixtureKey, 0o600)
			cwd, err := os.Getwd()
			if err != nil {
				t.Fatal(err)
			}
			relativeHome, err := filepath.Rel(cwd, home)
			if err != nil {
				t.Fatal(err)
			}
			t.Setenv("HOME", relativeHome)
			t.Setenv("JEV_IMAGES", "invalid")
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
			path := filepath.Join(relativeHome, filepath.FromSlash(pluginKeyDirectory), provider+".key")
			want := fmt.Sprintf("evaluate: %s=%q must be an absolute path\n", fileVar, path)
			if got.code != 4 || got.stdout != "" || got.stderr != want {
				t.Fatalf("exit=%d diagnostic=%q; want exit=4 diagnostic=%q", got.code, got.stderr, want)
			}
		})
	}
}
