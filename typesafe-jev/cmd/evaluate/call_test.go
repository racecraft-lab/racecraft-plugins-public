package main

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
)

// fixtureKey is a key-shaped value that must never appear in anything `call`
// writes. It is not a real credential.
const fixtureKey = "tsk-fixture-7f3a-must-not-appear"

const validAnswer = `{"model":"jev-latest","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":0.42}}}`

const validRequest = `{"state":"checkout is down","questions":{"q":{"type":"noul","instructions":"Is this urgent?"}}}`

// credentialEnv lists every variable that decides a backend or a credential.
// Each call test clears all of them first, so a key on the developer's machine
// can neither make a "no key" case pass nor turn a test into a billed call.
var credentialEnv = []string{
	"JEV_PROVIDER", "JEV_MODEL", "JEV_FALLBACK_PROVIDER",
	"JEV_API_KEY_FILE", "JEV_FALLBACK_API_KEY_FILE",
	"JEV_REQUEST_TIMEOUT", "JEV_MAX_RETRIES",
	"TYPESAFE_API_KEY", "OPENROUTER_API_KEY",
}

// isolateCallEnv unsets every credential variable and points HOME at an empty
// directory, which it returns. The originals come back after the test.
func isolateCallEnv(t *testing.T) string {
	t.Helper()
	for _, name := range credentialEnv {
		t.Setenv(name, "") // registers the restore
		os.Unsetenv(name)
	}
	home := t.TempDir()
	t.Setenv("HOME", home)
	// No retries: a retried 5xx would wait a real second per attempt.
	t.Setenv("JEV_MAX_RETRIES", "0")
	return home
}

// pluginEnv sets what both plugin manifests set.
func pluginEnv(t *testing.T) {
	t.Helper()
	t.Setenv("JEV_PROVIDER", "typesafe")
	t.Setenv("JEV_FALLBACK_PROVIDER", "openrouter")
}

// writeDefaultKey writes home/.config/racecraft-jev/<provider>.key.
func writeDefaultKey(t *testing.T, home, provider, contents string, mode os.FileMode) string {
	t.Helper()
	dir := filepath.Join(home, ".config", "racecraft-jev")
	if err := os.MkdirAll(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, provider+".key")
	if err := os.WriteFile(path, []byte(contents), mode); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(path, mode); err != nil {
		t.Fatal(err)
	}
	return path
}

// countingBackend answers every request with status and body, and counts them.
type countingBackend struct {
	*httptest.Server
	hits atomic.Int32
}

func newCountingBackend(t *testing.T, status int, body string) *countingBackend {
	t.Helper()
	b := &countingBackend{}
	b.Server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		b.hits.Add(1)
		io.Copy(io.Discard, r.Body)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(status)
		io.WriteString(w, body)
	}))
	t.Cleanup(b.Close)
	return b
}

// retargetTo points both backends at local servers. A nil server leaves that
// backend alone.
func retargetTo(primary, fallback *countingBackend) func(*Config) {
	return func(cfg *Config) {
		if primary != nil {
			cfg.Provider.EndpointURL = primary.URL
		}
		if fallback != nil && cfg.Fallback != nil {
			cfg.Fallback.Provider.EndpointURL = fallback.URL
		}
	}
}

type callResult struct {
	code           int
	stdout, stderr string
}

func runCallForTest(t *testing.T, opts callOptions, stdin string) callResult {
	t.Helper()
	var stdout, stderr strings.Builder
	code := runCall(context.Background(), opts, strings.NewReader(stdin), &stdout, &stderr)
	return callResult{code, stdout.String(), stderr.String()}
}

// CALL-01: every exit code in the contract, each from the situation it names.
func TestCallExitCodes(t *testing.T) {
	for _, tc := range []struct {
		name  string
		setup func(t *testing.T, home string)
		// primary and fallback are the local backends' replies. An empty
		// primaryBody means the primary is not a local server at all.
		primaryStatus  int
		primaryBody    string
		fallbackStatus int
		fallbackBody   string
		stdin          string
		want           int
		wantStderr     string
	}{
		{
			name: "answered from the default key file",
			setup: func(t *testing.T, home string) {
				writeDefaultKey(t, home, "typesafe", fixtureKey+"\n", 0o600)
			},
			primaryStatus: 200, primaryBody: validAnswer,
			stdin: validRequest, want: exitAnswered,
		},
		{
			// The 0.8.0 launcher always set a default key-file path, which
			// stopped the server from reading the environment variable.
			name: "answered from the environment alone",
			setup: func(t *testing.T, home string) {
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			},
			primaryStatus: 200, primaryBody: validAnswer,
			stdin: validRequest, want: exitAnswered,
		},
		{
			name: "answered by the fallback when only its key exists",
			setup: func(t *testing.T, home string) {
				writeDefaultKey(t, home, "openrouter", fixtureKey+"\n", 0o600)
			},
			primaryStatus: 500, primaryBody: `{}`,
			fallbackStatus: 200, fallbackBody: validAnswer,
			stdin: validRequest, want: exitAnswered,
		},
		{
			name:  "request that is not JSON",
			setup: func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			stdin: `{"state": "unterminated`, want: exitRequestInvalid,
			wantStderr: "not one JSON object",
		},
		{
			name:  "request with an unknown field",
			setup: func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			stdin: `{"state":"s","questions":{"q":{"type":"noul","instructions":"i"}},"apiKey":"x"}`,
			want:  exitRequestInvalid,
		},
		{
			name:  "two requests on stdin",
			setup: func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			stdin: validRequest + validRequest, want: exitRequestInvalid,
		},
		{
			name:  "request with no questions",
			setup: func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			stdin: `{"state":"s","questions":{}}`, want: exitRequestInvalid,
			wantStderr: "questions must not be empty",
		},
		{
			name:  "request over the option cap",
			setup: func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			stdin: overCapRequest(), want: exitRequestInvalid,
		},
		{
			name:  "nothing configured",
			setup: func(t *testing.T, home string) {},
			stdin: validRequest, want: exitUnconfigured,
			wantStderr: "no credential is configured",
		},
		{
			name: "an explicit key file that does not exist",
			setup: func(t *testing.T, home string) {
				t.Setenv("JEV_API_KEY_FILE", filepath.Join(home, "absent.key"))
			},
			stdin: validRequest, want: exitCredentialBroken,
			wantStderr: "does not exist",
		},
		{
			name: "a default key file readable by others",
			setup: func(t *testing.T, home string) {
				writeDefaultKey(t, home, "typesafe", fixtureKey+"\n", 0o644)
			},
			stdin: validRequest, want: exitCredentialBroken,
			wantStderr: "chmod 600",
		},
		{
			name: "an environment key that is a placeholder",
			setup: func(t *testing.T, home string) {
				t.Setenv("TYPESAFE_API_KEY", "${TYPESAFE_API_KEY}")
			},
			stdin: validRequest, want: exitCredentialBroken,
			wantStderr: "placeholder",
		},
		{
			// A broken source the operator set up is an error even while the
			// other one works. The MCP server still serves the primary here;
			// see TestServerStillServesPastABrokenFallback.
			name: "a working primary beside a broken fallback key file",
			setup: func(t *testing.T, home string) {
				writeDefaultKey(t, home, "typesafe", fixtureKey+"\n", 0o600)
				writeDefaultKey(t, home, "openrouter", fixtureKey+"\n", 0o644)
			},
			primaryStatus: 200, primaryBody: validAnswer,
			stdin: validRequest, want: exitCredentialBroken,
		},
		{
			name:  "an unknown backend",
			setup: func(t *testing.T, home string) { t.Setenv("JEV_PROVIDER", "elsewhere") },
			stdin: validRequest, want: exitCredentialBroken,
		},
		{
			name:          "a provider error",
			setup:         func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			primaryStatus: 500, primaryBody: `{}`,
			stdin: validRequest, want: exitProviderFailed,
		},
		{
			// The provider refusing the key is a provider answer, not a
			// local verdict on the credential source: --check cannot see it.
			name:          "a provider that refuses the key",
			setup:         func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			primaryStatus: 401, primaryBody: `{}`,
			stdin: validRequest, want: exitProviderFailed,
		},
		{
			name:          "a response that is not a judgment",
			setup:         func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			primaryStatus: 200, primaryBody: `{"answers":{}}`,
			stdin: validRequest, want: exitResponseInvalid,
		},
		{
			name:          "a response missing the asked question",
			setup:         func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) },
			primaryStatus: 200, primaryBody: `{"model":"m","usage":{},"answers":{"other":{"type":"noul","noul":0.1}}}`,
			stdin: validRequest, want: exitResponseInvalid,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			pluginEnv(t)
			tc.setup(t, home)

			var primary, fallback *countingBackend
			if tc.primaryBody != "" {
				primary = newCountingBackend(t, tc.primaryStatus, tc.primaryBody)
			}
			if tc.fallbackBody != "" {
				fallback = newCountingBackend(t, tc.fallbackStatus, tc.fallbackBody)
			}
			// A backend the case did not set up must never be reached. Point
			// it at a server that fails the test if it is.
			refuse := newCountingBackend(t, 599, `{}`)
			if primary == nil {
				primary = refuse
			}
			if fallback == nil {
				fallback = refuse
			}

			got := runCallForTest(t, callOptions{pluginDefaults: true, retarget: retargetTo(primary, fallback)}, tc.stdin)
			if got.code != tc.want {
				t.Fatalf("exit = %d, want %d; stderr: %s", got.code, tc.want, got.stderr)
			}
			if tc.wantStderr != "" && !strings.Contains(got.stderr, tc.wantStderr) {
				t.Errorf("stderr %q does not say %q", got.stderr, tc.wantStderr)
			}
			if tc.want == exitAnswered {
				if strings.TrimSpace(got.stdout) != validAnswer {
					t.Errorf("stdout = %q, want the provider's JSON", got.stdout)
				}
			} else if got.stdout != "" {
				t.Errorf("stdout carries %q on a failure", got.stdout)
			}
			if tc.want == exitRequestInvalid || tc.want == exitUnconfigured || tc.want == exitCredentialBroken {
				if n := primary.hits.Load() + fallback.hits.Load(); n != 0 {
					t.Errorf("a local failure made %d network calls", n)
				}
			}
			if n := refuse.hits.Load(); n != 0 {
				t.Errorf("an unconfigured backend was called %d times", n)
			}
		})
	}
}

// overCapRequest builds a choice question with one option too many.
func overCapRequest() string {
	criteria := map[string]any{}
	for i := 0; i <= maxChoiceOptions; i++ {
		criteria["option_"+itoa(i)] = nil
	}
	b, _ := json.Marshal(map[string]any{
		"state":     "s",
		"questions": map[string]any{"q": map[string]any{"type": "choice", "instructions": "pick", "criteria": criteria}},
	})
	return string(b)
}

// CALL-02: an explicit key-file path that is absent is a broken configuration
// (4); the plugin's default path being absent means nothing is configured (3).
func TestCallExplicitVersusDefaultPath(t *testing.T) {
	home := isolateCallEnv(t)
	pluginEnv(t)

	got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	if got.code != exitUnconfigured {
		t.Fatalf("default path absent: exit = %d, want %d", got.code, exitUnconfigured)
	}

	t.Setenv("JEV_API_KEY_FILE", filepath.Join(home, ".config", "racecraft-jev", "typesafe.key"))
	got = runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	if got.code != exitCredentialBroken {
		t.Fatalf("explicit path absent: exit = %d, want %d", got.code, exitCredentialBroken)
	}
}

// CALL-03: --check makes no network call, and its report records whether each
// key-file path was the operator's or the plugin's default.
func TestCallCheckReportsTheSourceWithoutANetworkCall(t *testing.T) {
	for _, tc := range []struct {
		name         string
		setup        func(t *testing.T, home string)
		wantExit     int
		wantPrimary  string
		wantFallback string
	}{
		{
			name: "default file",
			setup: func(t *testing.T, home string) {
				writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600)
			},
			wantExit: exitAnswered, wantPrimary: "default-file/ok", wantFallback: "none/absent",
		},
		{
			name: "explicit file",
			setup: func(t *testing.T, home string) {
				t.Setenv("JEV_API_KEY_FILE", writeKeyFile(t, fixtureKey, 0o600))
			},
			wantExit: exitAnswered, wantPrimary: "explicit-file/ok", wantFallback: "none/absent",
		},
		{
			name:     "environment",
			setup:    func(t *testing.T, home string) { t.Setenv("OPENROUTER_API_KEY", fixtureKey) },
			wantExit: exitAnswered, wantPrimary: "none/absent", wantFallback: "environment/ok",
		},
		{
			// An explicit empty value is treated as unset, as the server does.
			name:     "empty explicit path",
			setup:    func(t *testing.T, home string) { t.Setenv("JEV_API_KEY_FILE", "") },
			wantExit: exitUnconfigured, wantPrimary: "none/absent", wantFallback: "none/absent",
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			pluginEnv(t)
			tc.setup(t, home)
			backend := newCountingBackend(t, 200, validAnswer)

			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true, retarget: retargetTo(backend, backend)}, validRequest)
			if got.code != tc.wantExit {
				t.Fatalf("exit = %d, want %d; stderr: %s", got.code, tc.wantExit, got.stderr)
			}
			if n := backend.hits.Load(); n != 0 {
				t.Errorf("--check made %d network calls", n)
			}
			var report checkReport
			if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
				t.Fatalf("check report %q: %v", got.stdout, err)
			}
			if report.Exit != tc.wantExit {
				t.Errorf("report exit = %d", report.Exit)
			}
			if p := report.Primary.Source + "/" + report.Primary.State; p != tc.wantPrimary {
				t.Errorf("primary = %s, want %s", p, tc.wantPrimary)
			}
			if report.Fallback == nil {
				t.Fatal("the plugin's fallback is missing from the report")
			}
			if f := report.Fallback.Source + "/" + report.Fallback.State; f != tc.wantFallback {
				t.Errorf("fallback = %s, want %s", f, tc.wantFallback)
			}
		})
	}
}

// CALL-04: without --plugin-defaults, a key file at the default path is not
// read. Only the plugin opts in to that path.
func TestCallWithoutPluginDefaultsIgnoresTheDefaultPath(t *testing.T) {
	home := isolateCallEnv(t)
	pluginEnv(t)
	writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600)

	got := runCallForTest(t, callOptions{check: true}, "")
	if got.code != exitUnconfigured {
		t.Fatalf("exit = %d, want %d", got.code, exitUnconfigured)
	}
}

// CALL-05: the MCP server keeps its own rule for a broken fallback: it drops
// the fallback with a line on stderr and serves the primary. `call --check`
// reports the same situation as 4. The divergence is deliberate: the check is
// what a doctor reads, and a key file the operator set up must not be passed
// over silently, while a running server that can answer should.
func TestServerStillServesPastABrokenFallback(t *testing.T) {
	home := isolateCallEnv(t)
	pluginEnv(t)
	writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600)
	writeDefaultKey(t, home, "openrouter", fixtureKey, 0o644)

	cfg, err := resolveCallConfig(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	var log strings.Builder
	c, served, err := newClients(cfg, &log)
	if err != nil {
		t.Fatalf("the server refused to start: %v", err)
	}
	if served.Provider.Name != "typesafe" || c.Fallback != nil {
		t.Errorf("served %s with fallback %v", served.Provider.Name, c.Fallback)
	}
	if !strings.Contains(log.String(), "fallback is off") {
		t.Errorf("the dropped fallback was not reported: %q", log.String())
	}
	if got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, ""); got.code != exitCredentialBroken {
		t.Errorf("check exit = %d, want %d", got.code, exitCredentialBroken)
	}
}

// CALL-06: no output of `call`, on any path, carries the key. The backends
// here echo the Authorization header back, which is the worst a provider
// could do.
func TestCallNeverPrintsTheKey(t *testing.T) {
	echo := func(status int) *countingBackend {
		b := &countingBackend{}
		b.Server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			b.hits.Add(1)
			w.WriteHeader(status)
			io.WriteString(w, `{"id":"req-1","error":{"message":"bad key `+r.Header.Get("Authorization")+`"}}`)
		}))
		t.Cleanup(b.Close)
		return b
	}
	for _, tc := range []struct {
		name  string
		setup func(t *testing.T, home string)
		reply *countingBackend
		check bool
		stdin string
	}{
		{"check with a good file", func(t *testing.T, home string) { writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600) }, nil, true, ""},
		{"check with an exposed file", func(t *testing.T, home string) { writeDefaultKey(t, home, "typesafe", fixtureKey, 0o644) }, nil, true, ""},
		{"check with a padded environment key", func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", " "+fixtureKey) }, nil, true, ""},
		{"provider refuses the key", func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) }, echo(401), false, validRequest},
		{"provider errors", func(t *testing.T, home string) { writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600) }, echo(500), false, validRequest},
		{"provider answers with junk", func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) }, echo(200), false, validRequest},
		{"request quotes the key", func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) }, nil, false, `{"state":"` + fixtureKey + `","questions":{}}`},
		{"malformed request quotes the key", func(t *testing.T, home string) { t.Setenv("TYPESAFE_API_KEY", fixtureKey) }, nil, false, `{"` + fixtureKey},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			pluginEnv(t)
			tc.setup(t, home)
			reply := tc.reply
			if reply == nil {
				reply = newCountingBackend(t, 599, `{}`)
			}
			got := runCallForTest(t, callOptions{check: tc.check, pluginDefaults: true, retarget: retargetTo(reply, reply)}, tc.stdin)
			if strings.Contains(got.stdout, fixtureKey) || strings.Contains(got.stderr, fixtureKey) {
				t.Errorf("exit %d printed the key:\nstdout: %s\nstderr: %s", got.code, got.stdout, got.stderr)
			}
		})
	}
}
