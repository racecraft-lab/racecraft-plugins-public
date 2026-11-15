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
	for _, primary := range []string{"typesafe", "openrouter"} {
		for _, role := range []string{"primary", "fallback"} {
			for _, kind := range []string{
				"absent", "empty-env", "environment", "whitespace-env", "control-env", "placeholder-env",
				"explicit-file", "default-file", "empty-path", "missing-file", "empty-file", "whitespace-file",
				"control-file", "placeholder-file", "oversized-file", "directory", "broken-default",
			} {
				t.Run(primary+"/"+role+"/"+kind, func(t *testing.T) {
					home := isolateCallEnv(t)
					fallback := map[string]string{"typesafe": "openrouter", "openrouter": "typesafe"}[primary]
					t.Setenv("JEV_PROVIDER", primary)
					t.Setenv("JEV_FALLBACK_PROVIDER", fallback)
					provider, fileVar, other := primary, pluginKeyFileEnv, fallback
					if role == "fallback" {
						provider, fileVar, other = fallback, pluginFallbackFileEnv, primary
					}
					t.Setenv(providers[other].APIKeyEnv, fixtureKey)
					keyEnv := providers[provider].APIKeyEnv
					source, state, reason := "explicit-file", "unusable", ""
					switch kind {
					case "absent", "empty-env":
						source, state = "none", "absent"
						if kind == "empty-env" {
							t.Setenv(keyEnv, "")
						}
					case "environment":
						t.Setenv(keyEnv, fixtureKey)
						source, state = "environment", "ok"
					case "whitespace-env", "control-env", "placeholder-env":
						values := map[string]string{"whitespace-env": " bad", "control-env": "bad\x01key", "placeholder-env": "${KEY}"}
						t.Setenv(keyEnv, values[kind])
						source = "environment"
						reason = map[string]string{"whitespace-env": "has leading or trailing whitespace", "control-env": "contains a control character", "placeholder-env": "is an unexpanded ${...} placeholder"}[kind]
					case "default-file", "broken-default":
						contents := fixtureKey + "\r\n"
						source, state = "default-file", "ok"
						if kind == "broken-default" {
							contents, state, reason = "", "unusable", "is empty"
						}
						writeDefaultKey(t, home, provider, contents, 0o600)
						t.Setenv(keyEnv, "ignored-environment-key")
					case "empty-path":
						t.Setenv(fileVar, "")
						t.Setenv(keyEnv, fixtureKey)
						source, state = "environment", "ok"
					default:
						contents := fixtureKey + "\n"
						state = "unusable"
						switch kind {
						case "explicit-file":
							state = "ok"
						case "empty-file":
							contents, reason = "", "is empty"
						case "whitespace-file":
							contents, reason = " bad\n", "has leading or trailing whitespace"
						case "control-file":
							contents, reason = "bad\x00key", "contains a control character"
						case "placeholder-file":
							contents, reason = "${KEY}\n", "is an unexpanded ${...} placeholder"
						case "oversized-file":
							contents, reason = strings.Repeat("x", maxKeyFileBytes+1), "over the 8192 byte limit"
						case "missing-file":
							reason = "does not exist"
						case "directory":
							reason = "is not a regular file"
						}
						path := filepath.Join(home, "missing.key")
						if kind == "directory" {
							path = t.TempDir()
						} else if kind != "missing-file" {
							path = writeKeyFile(t, contents, 0o600)
						}
						t.Setenv(fileVar, path)
						t.Setenv(keyEnv, "ignored-environment-key")
					}

					calls := 0
					wantProvider := provider
					if state != "ok" {
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
					if checked.code != wantExit || report.Exit != wantExit || status.Provider != provider || status.Source != source || status.State != state || calls != 0 {
						t.Fatalf("check exit=%d report=%+v source=%+v calls=%d; want %d %s/%s", checked.code, report, status, calls, wantExit, source, state)
					}
					if reason != "" && !strings.Contains(checked.stderr, reason) {
						t.Fatalf("missing reason %q: %s", reason, checked.stderr)
					}
					called := runCallForTest(t, callOptions{pluginDefaults: true}, validRequest)
					if called.code != wantExit || (wantExit == exitAnswered && calls != 1) || (wantExit != exitAnswered && calls != 0) {
						t.Fatalf("call exit=%d calls=%d; want exit=%d", called.code, calls, wantExit)
					}
					if state == "absent" && called.stderr != "" {
						t.Fatalf("absent hop produced a CLI diagnostic: %s", called.stderr)
					}

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
					if calls != map[bool]int{true: 2, false: 1}[wantExit == exitAnswered] {
						t.Fatal("server did not make exactly one request")
					}
					for _, output := range []string{checked.stdout, checked.stderr, called.stderr, log.String()} {
						if strings.Contains(output, fixtureKey) || strings.Contains(output, "ignored-environment-key") {
							t.Fatal("credential leaked in output")
						}
					}
				})
			}
		}
	}
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
