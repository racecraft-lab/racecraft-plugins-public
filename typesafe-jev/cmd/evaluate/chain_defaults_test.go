package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"reflect"
	"strings"
	"testing"
)

// FB-01 at the call boundary: keys alone never opt a bare binary into a
// second backend. The plugin launcher explicitly opts into the two-hop default.
func TestCallBuiltInChainModes(t *testing.T) {
	for _, plugin := range []bool{false, true} {
		for _, status := range []int{200, 401} {
			t.Run(fmt.Sprintf("plugin=%t/status=%d", plugin, status), func(t *testing.T) {
				isolateCallEnv(t)
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
				t.Setenv("OPENROUTER_API_KEY", fixtureKey)
				var destinations, models []string
				old := http.DefaultTransport
				http.DefaultTransport = backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
					var wire struct{ Model string }
					if err := json.NewDecoder(r.Body).Decode(&wire); err != nil {
						return nil, err
					}
					destinations = append(destinations, r.URL.String())
					models = append(models, wire.Model)
					code := 200
					if r.URL.String() == providers["typesafe"].EndpointURL {
						code = status
					}
					return &http.Response{StatusCode: code, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(validAnswer))}, nil
				})
				t.Cleanup(func() { http.DefaultTransport = old })
				got := runCallForTest(t, callOptions{pluginDefaults: plugin}, validRequest)
				wantCode, wantOut := 0, validAnswer+"\n"
				wantDestinations := []string{providers["typesafe"].EndpointURL}
				wantModels := []string{"jev-latest"}
				if status == 401 {
					if plugin {
						wantDestinations = append(wantDestinations, providers["openrouter"].EndpointURL)
						wantModels = append(wantModels, "~typesafe/jev-latest")
					} else {
						wantCode, wantOut = 5, ""
						if !strings.Contains(got.stderr, "typesafe: HTTP 401") {
							t.Errorf("missing primary failure: %s", got.stderr)
						}
					}
				}
				if got.code != wantCode || got.stdout != wantOut || !reflect.DeepEqual(destinations, wantDestinations) || !reflect.DeepEqual(models, wantModels) {
					t.Fatalf("exit=%d stdout=%q destinations=%v models=%v; want exit=%d stdout=%q destinations=%v models=%v", got.code, got.stdout, destinations, models, wantCode, wantOut, wantDestinations, wantModels)
				}
			})
		}
	}
}

func TestCallCheckBuiltInChainModes(t *testing.T) {
	for _, plugin := range []bool{false, true} {
		t.Run(fmt.Sprintf("plugin=%t", plugin), func(t *testing.T) {
			args := []string{"call", "--check"}
			fallback := "null"
			if plugin {
				args = append(args, "--plugin-defaults")
				fallback = `{"provider":"openrouter","source":"none","state":"absent"}`
			}
			cmd := exec.Command(os.Args[0], args...)
			cmd.Env = []string{"HOME=" + t.TempDir(), asBinaryEnv + "=1", "TYPESAFE_API_KEY=" + fixtureKey}
			var stderr strings.Builder
			cmd.Stderr = &stderr
			out, err := cmd.Output()
			want := `{"exit":0,"primary":{"provider":"typesafe","source":"environment","state":"ok"},"fallback":` + fallback + "}\n"
			if err != nil || string(out) != want {
				t.Fatalf("error=%v report=%s stderr=%s; want %s", err, out, stderr.String(), want)
			}
		})
	}
}

func TestCallChainFileRequiresAbsoluteHome(t *testing.T) {
	for _, plugin := range []bool{false, true} {
		for _, home := range []string{"unset", "", "."} {
			t.Run(fmt.Sprintf("plugin=%t/HOME=%q", plugin, home), func(t *testing.T) {
				isolateCallEnv(t)
				cwd := t.TempDir()
				writeChainSetting(t, cwd, "openrouter")
				t.Chdir(cwd)
				if home == "unset" {
					if err := os.Unsetenv("HOME"); err != nil {
						t.Fatal(err)
					}
				} else {
					t.Setenv("HOME", home)
				}
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
				t.Setenv("OPENROUTER_API_KEY", fixtureKey)
				got := runCallForTest(t, callOptions{check: true, pluginDefaults: plugin}, "")
				var report checkReport
				if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
					t.Fatalf("call report: %v; result=%+v", err, got)
				}
				fallback := ""
				if report.Fallback != nil {
					fallback = report.Fallback.Provider
				}
				wantFallback := ""
				if plugin {
					wantFallback = "openrouter"
				}
				if got.code != 0 || report.Primary.Provider != "typesafe" || fallback != wantFallback {
					t.Fatalf("call: %+v; want primary=typesafe fallback=%s", got, wantFallback)
				}
			})
		}
	}
}

// FB-02 must hold through both runtime entry points, not only resolveConfig.
func TestRuntimeRejectsOrphanFallbackKeyFile(t *testing.T) {
	for _, tc := range []struct {
		name, source string
		plugin       bool
	}{
		{name: "bare built-in"},
		{name: "bare chain", source: "env"},
		{name: "plugin chain", source: "env", plugin: true},
		{name: "bare file", source: "file"},
		{name: "plugin file", source: "file", plugin: true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			calls := 0
			old := http.DefaultTransport
			http.DefaultTransport = backendFixtureTransport(func(*http.Request) (*http.Response, error) {
				calls++
				return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(validAnswer))}, nil
			})
			t.Cleanup(func() { http.DefaultTransport = old })
			keyFile := writeKeyFile(t, fixtureKey, 0600)
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("JEV_FALLBACK_API_KEY_FILE", keyFile)
			env := []string{"HOME=" + home, asBinaryEnv + "=1", "TYPESAFE_API_KEY=" + fixtureKey, "JEV_FALLBACK_API_KEY_FILE=" + keyFile}
			if tc.source == "env" {
				t.Setenv("JEV_CHAIN", "typesafe")
				env = append(env, "JEV_CHAIN=typesafe")
			} else if tc.source == "file" {
				writeChainSetting(t, home, "typesafe")
			}
			for _, check := range []bool{false, true} {
				got := runCallForTest(t, callOptions{check: check, pluginDefaults: tc.plugin}, validRequest)
				if got.code != 4 || got.stdout != "" || !strings.Contains(got.stderr, "set without JEV_FALLBACK_PROVIDER") {
					t.Errorf("call check=%t: %+v; want exit 4 and orphan fallback diagnostic", check, got)
				}
			}
			if calls != 0 {
				t.Errorf("orphan fallback made %d network calls; want none", calls)
			}
			args := []string{"mcp"}
			if tc.plugin {
				args = append(args, "--plugin-defaults")
			}
			cmd := exec.Command(os.Args[0], args...)
			cmd.Env = env
			var stdout, stderr strings.Builder
			cmd.Stdout, cmd.Stderr = &stdout, &stderr
			if err := cmd.Run(); err == nil || stdout.Len() != 0 || !strings.Contains(stderr.String(), "set without JEV_FALLBACK_PROVIDER") {
				t.Errorf("server error=%v stdout=%q stderr=%q; want orphan fallback startup failure", err, stdout.String(), stderr.String())
			}
		})
	}
}

func TestRuntimeChainPrecedenceInBothModes(t *testing.T) {
	for _, plugin := range []bool{false, true} {
		for _, source := range []string{"built-in", "file", "file with empty fallback", "env", "env with empty fallback"} {
			t.Run(fmt.Sprintf("plugin=%t/%s", plugin, source), func(t *testing.T) {
				home := isolateCallEnv(t)
				env := []string{"HOME=" + home, asBinaryEnv + "=1", "TYPESAFE_API_KEY=" + fixtureKey, "OPENROUTER_API_KEY=" + fixtureKey}
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
				t.Setenv("OPENROUTER_API_KEY", fixtureKey)
				wantPrimary, wantFallback := "typesafe", ""
				if plugin {
					wantFallback = "openrouter"
				}
				if source != "built-in" {
					wantPrimary, wantFallback = "openrouter", "typesafe"
					if strings.HasPrefix(source, "env") {
						writeChainSetting(t, home, "broken")
						t.Setenv("JEV_CHAIN", "openrouter,typesafe")
						env = append(env, "JEV_CHAIN=openrouter,typesafe")
					} else {
						writeChainSetting(t, home, "openrouter,typesafe")
					}
				}
				if strings.Contains(source, "empty fallback") {
					t.Setenv("JEV_FALLBACK_PROVIDER", "")
					env = append(env, "JEV_FALLBACK_PROVIDER=")
				}
				got := runCallForTest(t, callOptions{check: true, pluginDefaults: plugin}, "")
				var report checkReport
				if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
					t.Errorf("call report: %v; result=%+v", err, got)
				}
				fallback := ""
				if report.Fallback != nil {
					fallback = report.Fallback.Provider
				}
				if got.code != 0 || report.Primary.Provider != wantPrimary || fallback != wantFallback {
					t.Errorf("call: %+v; want primary=%s fallback=%s", got, wantPrimary, wantFallback)
				}
				args := []string{"mcp"}
				if plugin {
					args = append(args, "--plugin-defaults")
				}
				cmd := exec.Command(os.Args[0], args...)
				cmd.Env = env
				session, _ := connectLauncher(t, cmd)
				tools, err := session.ListTools(context.Background(), nil)
				if err != nil {
					t.Fatal(err)
				}
				wantNote := "Backend chain: " + wantPrimary
				if wantFallback != "" {
					wantNote += " -> " + wantFallback
				}
				wantNote += "."
				if len(tools.Tools) != 1 || !strings.Contains(tools.Tools[0].Description, wantNote) {
					t.Errorf("server must report %q; tools=%+v", wantNote, tools.Tools)
				}
			})
		}
	}
}
