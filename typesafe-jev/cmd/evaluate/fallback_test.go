package main

import (
	"context"
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

// recordingBackend answers every call with status and reply, and counts the
// calls and remembers the model each one named.
type recordingBackend struct {
	srv    *httptest.Server
	calls  atomic.Int32
	models chan string
}

func newRecordingBackend(t *testing.T, status int, reply string) *recordingBackend {
	t.Helper()
	b := &recordingBackend{models: make(chan string, 16)}
	b.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		b.calls.Add(1)
		var body struct {
			Model string `json:"model"`
		}
		_ = json.NewDecoder(r.Body).Decode(&body)
		b.models <- body.Model
		w.WriteHeader(status)
		w.Write([]byte(reply))
	}))
	t.Cleanup(b.srv.Close)
	return b
}

// withFallback builds a TypeSafe primary answering primaryStatus and an
// OpenRouter fallback answering 200, and returns the primary.
func withFallback(t *testing.T, primaryStatus int) (*Client, *recordingBackend, *recordingBackend, *strings.Builder) {
	t.Helper()
	primary := newRecordingBackend(t, primaryStatus, `{"error":{"message":"no"}}`)
	fallback := newRecordingBackend(t, http.StatusOK, noulReply)
	c := testClient(providerAt("typesafe", primary.srv.URL), primary.srv)
	c.MaxRetries = 0
	c.Fallback = testClient(providerAt("openrouter", fallback.srv.URL), fallback.srv)
	log := &strings.Builder{}
	c.Log = log
	return c, primary, fallback, log
}

// FB-01: unset means no fallback. A refused key fails the call exactly as it
// always has, and nothing else is contacted.
func TestNoFallbackUnlessConfigured(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{"JEV_PROVIDER": "typesafe"}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Fallback != nil {
		t.Fatalf("a fallback appeared without JEV_FALLBACK_PROVIDER: %+v", cfg.Fallback)
	}
	c, primary, fallback, _ := withFallback(t, http.StatusUnauthorized)
	c.Fallback = nil
	if _, err := runEvaluate(context.Background(), c, simpleIn()); err == nil || !strings.Contains(err.Error(), "typesafe: HTTP 401") {
		t.Fatalf("want the primary's 401, got %v", err)
	}
	if primary.calls.Load() != 1 || fallback.calls.Load() != 0 {
		t.Errorf("calls: primary %d, fallback %d; want 1, 0", primary.calls.Load(), fallback.calls.Load())
	}
}

// FB-02: the fallback is named explicitly, must be a known backend, and must
// be the other one; its key file follows the primary's rules.
func TestFallbackConfig(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER":              "typesafe",
		"JEV_FALLBACK_PROVIDER":     "openrouter",
		"JEV_FALLBACK_API_KEY_FILE": "/keys/openrouter.key",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Fallback == nil || cfg.Fallback.Provider.Name != "openrouter" || cfg.Fallback.KeyFile != "/keys/openrouter.key" {
		t.Fatalf("fallback = %+v", cfg.Fallback)
	}
	if got := cfg.fallbackConfig(); got.Model != "~typesafe/jev-latest" || got.Timeout != cfg.Timeout {
		t.Errorf("fallback client config = %+v; want OpenRouter's default model and the primary's timeout", got)
	}
	for _, tc := range []struct {
		env  map[string]string
		want string
	}{
		{map[string]string{"JEV_FALLBACK_PROVIDER": "typesafe"}, "is the primary backend"},
		{map[string]string{"JEV_FALLBACK_PROVIDER": "anthropic"}, "not a known backend"},
		{map[string]string{"JEV_FALLBACK_API_KEY_FILE": "/keys/openrouter.key"}, "without JEV_FALLBACK_PROVIDER"},
		{map[string]string{"JEV_FALLBACK_PROVIDER": "openrouter", "JEV_FALLBACK_API_KEY_FILE": "relative.key"}, "must be an absolute path"},
	} {
		if _, err := resolveConfig(envLookup(tc.env)); err == nil || !strings.Contains(err.Error(), tc.want) {
			t.Errorf("%v: err = %v, want it to contain %q", tc.env, err, tc.want)
		}
	}
}

// FB-03: a refused credential moves the call to the fallback once, the model
// id is the fallback's own, and every later call stays there.
func TestRefusedKeySwitchesOnceAndStays(t *testing.T) {
	for _, status := range []int{401, 402, 403, 404, 429, 500, 503} {
		c, primary, fallback, log := withFallback(t, status)
		in := simpleIn()
		in.Model = "jev-latest"
		for call := 0; call < 3; call++ {
			body, err := runEvaluate(context.Background(), c, in)
			if err != nil {
				t.Fatalf("HTTP %d call %d: %v", status, call, err)
			}
			if !strings.Contains(string(body), `"noul":0.9`) {
				t.Errorf("HTTP %d: body %s", status, body)
			}
		}
		if primary.calls.Load() != 1 || fallback.calls.Load() != 3 {
			t.Errorf("HTTP %d: calls primary %d, fallback %d; want 1, 3", status, primary.calls.Load(), fallback.calls.Load())
		}
		if got := <-fallback.models; got != "~typesafe/jev-latest" {
			t.Errorf("HTTP %d: fallback got model %q, want its own default", status, got)
		}
		if n := strings.Count(log.String(), "using the openrouter fallback"); n != 1 {
			t.Errorf("HTTP %d: switch logged %d times: %q", status, n, log.String())
		}
	}
}

// FB-04: a request the primary rejected by shape fails the same way anywhere,
// so it is returned as it is and nothing else is called or billed.
func TestShapeRejectionNeverSwitches(t *testing.T) {
	for _, status := range []int{400, 413, 422} {
		c, _, fallback, log := withFallback(t, status)
		if _, err := runEvaluate(context.Background(), c, simpleIn()); err == nil {
			t.Fatalf("HTTP %d: want an error", status)
		}
		if fallback.calls.Load() != 0 || log.Len() != 0 {
			t.Errorf("HTTP %d: fallback called %d times, log %q", status, fallback.calls.Load(), log.String())
		}
	}
	// A local validation refusal never reaches either backend.
	c, primary, fallback, _ := withFallback(t, http.StatusOK)
	bad := simpleIn()
	bad.Questions = map[string]question{}
	if _, err := runEvaluate(context.Background(), c, bad); err == nil {
		t.Fatal("want a local refusal")
	}
	if primary.calls.Load()+fallback.calls.Load() != 0 {
		t.Error("a locally refused request reached a backend")
	}
}

// FB-05: an unreachable primary is a switch too.
func TestUnreachablePrimarySwitches(t *testing.T) {
	c, primary, fallback, _ := withFallback(t, http.StatusOK)
	primary.srv.Close()
	if _, err := runEvaluate(context.Background(), c, simpleIn()); err != nil {
		t.Fatal(err)
	}
	if fallback.calls.Load() != 1 {
		t.Errorf("fallback calls = %d, want 1", fallback.calls.Load())
	}
}

// FB-05b: a primary that resets the connection while its answer is being
// read never answered either, so it switches too.
func TestResetMidResponseSwitches(t *testing.T) {
	c, primary, fallback, _ := withFallback(t, http.StatusOK)
	primary.srv.Config.Handler = http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Length", "1000")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"model":`))
		w.(http.Flusher).Flush()
		conn, _, err := w.(http.Hijacker).Hijack()
		if err != nil {
			t.Error(err)
			return
		}
		// Linger 0 makes the close a reset rather than a clean end of stream.
		conn.(*net.TCPConn).SetLinger(0)
		conn.Close()
	})
	if _, err := runEvaluate(context.Background(), c, simpleIn()); err != nil {
		t.Fatal(err)
	}
	if fallback.calls.Load() != 1 {
		t.Errorf("fallback calls = %d, want 1", fallback.calls.Load())
	}
}

// FB-06: at start, a primary whose key cannot be loaded serves on the
// fallback; a fallback whose key cannot be loaded is dropped; neither is an
// error naming both. No key is ever printed.
func TestStartupPicksWhatCanServe(t *testing.T) {
	good := writeKeyFile(t, "sk-test-good\n", 0o600)
	missing := "/nonexistent/key"
	base := Config{Provider: providers["typesafe"], Model: "jev-latest", Timeout: defaultTimeout}
	fb := func(file string) *FallbackConfig {
		return &FallbackConfig{Provider: providers["openrouter"], KeyFile: file}
	}

	for _, tc := range []struct {
		name, primaryKey, fallbackKey, serving, wantLog string
		fallbackArmed                                   bool
	}{
		{"both", good, good, "typesafe", "", true},
		{"primary missing", missing, good, "openrouter", "using the openrouter fallback", false},
		{"fallback missing", good, missing, "typesafe", "the openrouter fallback is off", false},
	} {
		cfg := base
		cfg.KeyFile, cfg.Fallback = tc.primaryKey, fb(tc.fallbackKey)
		log := &strings.Builder{}
		c, served, err := newClients(cfg, log)
		if err != nil {
			t.Fatalf("%s: %v", tc.name, err)
		}
		if c.Provider.Name != tc.serving || served.Provider.Name != tc.serving {
			t.Errorf("%s: serving %s (config %s), want %s", tc.name, c.Provider.Name, served.Provider.Name, tc.serving)
		}
		if (c.Fallback != nil) != tc.fallbackArmed || (served.Fallback != nil) != tc.fallbackArmed {
			t.Errorf("%s: fallback armed = %v, want %v", tc.name, c.Fallback != nil, tc.fallbackArmed)
		}
		if !strings.Contains(log.String(), tc.wantLog) || strings.Contains(log.String(), "sk-test") {
			t.Errorf("%s: log %q", tc.name, log.String())
		}
	}
	cfg := base
	cfg.KeyFile, cfg.Fallback = missing, fb(missing)
	if _, _, err := newClients(cfg, &strings.Builder{}); err == nil || !strings.Contains(err.Error(), "the openrouter fallback cannot start either") {
		t.Errorf("want an error naming both, got %v", err)
	}
}

// FB-07: the server's instructions name both destinations and who bills, and
// carry OpenRouter's omission note because it may be the one that answers.
func TestInstructionsNameTheFallback(t *testing.T) {
	cfg := Config{Provider: providers["typesafe"], Fallback: &FallbackConfig{Provider: providers["openrouter"]}}
	note := backendNote(cfg)
	for _, want := range []string{"Backend: typesafe, with openrouter as fallback", "the provider that answers bills for the call", "may omit confidence and probabilities"} {
		if !strings.Contains(note, want) {
			t.Errorf("note missing %q:\n%s", want, note)
		}
	}
}
