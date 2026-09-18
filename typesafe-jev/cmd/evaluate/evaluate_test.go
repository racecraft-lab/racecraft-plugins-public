package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestEvaluate(t *testing.T) {
	calls := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		calls++
		if r.URL.Path != "/v1/systemone" || r.Header.Get("Authorization") != "Bearer k" {
			t.Errorf("bad request: %s %q", r.URL.Path, r.Header.Get("Authorization"))
		}
		var in evaluateIn
		if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
			t.Fatal(err)
		}
		switch in.State {
		case "busy":
			if calls == 1 {
				w.WriteHeader(529)
				return
			}
		case "bad":
			w.WriteHeader(http.StatusUnprocessableEntity)
			w.Write([]byte(`{"detail":"criteria required"}`))
			return
		}
		w.Write([]byte(`{"model":"` + in.Model + `","answers":{"q":{"type":"noul","noul":0.9}}}`))
	}))
	defer srv.Close()
	c := testClient(providerAt("typesafe", srv.URL+"/v1/systemone"), srv)
	req := evaluateIn{Model: "jev-latest", Questions: map[string]question{"q": {Type: "noul", Instructions: "urgent?"}}}

	req.State = "busy"
	b, err := c.Evaluate(context.Background(), req)
	if err != nil || !strings.Contains(string(b), `"noul":0.9`) || calls != 2 {
		t.Fatalf("retry: calls=%d b=%s err=%v", calls, b, err)
	}

	// A rejected request reports the status and a remedy, but not the
	// provider's own error text. Upstream echoed the body; that text can quote
	// the submitted state back, and an error travels further than the input did.
	req.State = "bad"
	_, err = c.Evaluate(context.Background(), req)
	if err == nil {
		t.Fatal("422: want an error")
	}
	if !strings.Contains(err.Error(), "HTTP 422") {
		t.Errorf("422: error should name the status: %v", err)
	}
	if strings.Contains(err.Error(), "criteria required") {
		t.Errorf("422: error echoed the provider's body: %v", err)
	}
}

// The endpoint is taken verbatim, so a route's full URL reaches the server.
func TestEvaluatePostsToURL(t *testing.T) {
	var got string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		got = r.URL.Path
		w.Write([]byte(`{}`))
	}))
	defer srv.Close()
	c := testClient(providerAt("openrouter", srv.URL+"/api/alpha/decisions"), srv)
	if _, err := c.Evaluate(context.Background(), evaluateIn{State: "x"}); err != nil {
		t.Fatal(err)
	}
	if got != "/api/alpha/decisions" {
		t.Fatalf("path = %q", got)
	}
}

// TestRoute, TestSetupEnv, TestSetupCommands, and TestSetupClaudeDesktop covered
// behaviour this fork removed: key-presence routing, bulk environment capture,
// and setup that edits client config. Their replacements are in config_test.go
// and setup_test.go.

// A tar member named "evaluate" that is a symlink (or any other non-regular entry)
// must not be extracted and installed over the running binary.
func TestExtractBinaryRejectsNonRegularMember(t *testing.T) {
	var buf bytes.Buffer
	gw := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gw)
	if err := tw.WriteHeader(&tar.Header{
		Name:     "evaluate",
		Typeflag: tar.TypeSymlink,
		Linkname: "/etc/passwd",
		Mode:     0o777,
	}); err != nil {
		t.Fatal(err)
	}
	for _, closer := range []func() error{tw.Close, gw.Close} {
		if err := closer(); err != nil {
			t.Fatal(err)
		}
	}

	if err := extractBinaryFromTar(buf.Bytes(), "evaluate", io.Discard); err == nil || !strings.Contains(err.Error(), "not a regular file") {
		t.Fatalf("expected non-regular member to be rejected, got %v", err)
	}
}

func TestWritePiExtension(t *testing.T) {
	dir := t.TempDir()
	// A pre-rename install: both files would register the tool `evaluate`.
	legacy := filepath.Join(dir, "extensions", "jev.ts")
	if err := os.MkdirAll(filepath.Dir(legacy), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(legacy, []byte("// old"), 0o600); err != nil {
		t.Fatal(err)
	}
	path, err := writePiExtension(dir, `/bin/je"v`)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(legacy); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("legacy jev.ts kept: %v", err)
	}
	if want := filepath.Join(dir, "extensions", "evaluate.ts"); path != want {
		t.Fatalf("path = %q, want %q", path, want)
	}
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	src := string(b)
	// The quote in the path must come back escaped, not as a broken literal.
	if !strings.Contains(src, `const BINARY = "/bin/je\"v"`) {
		t.Fatalf("binary path not rendered: %s", src)
	}
	if !strings.Contains(src, "A noul near 0.5 means uncertain") {
		t.Fatal("instructions not rendered")
	}
	if strings.Contains(src, "__EVALUATE_") {
		t.Fatal("placeholder left behind")
	}
}

func TestPiDir(t *testing.T) {
	home, err := os.UserHomeDir()
	if err != nil {
		t.Fatal(err)
	}
	for _, tc := range []struct{ env, want string }{
		{"", filepath.Join(home, ".pi", "agent")},
		// pi expands "~" itself, so taking it literally would miss a real install.
		{"~", home},
		{"~/.pi/agent", filepath.Join(home, ".pi", "agent")},
		{"/tmp/pi", "/tmp/pi"},
	} {
		t.Setenv("PI_CODING_AGENT_DIR", tc.env)
		got, err := piDir()
		if err != nil {
			t.Fatal(err)
		}
		if got != tc.want {
			t.Errorf("piDir() with %q = %q, want %q", tc.env, got, tc.want)
		}
	}
	// An absolute override must not need a home directory: sanitized
	// environments (env -i PI_CODING_AGENT_DIR=...) have none.
	t.Setenv("HOME", "")
	t.Setenv("PI_CODING_AGENT_DIR", "/tmp/pi")
	if got, err := piDir(); err != nil || got != "/tmp/pi" {
		t.Errorf("piDir() without HOME = %q, %v, want %q, nil", got, err, "/tmp/pi")
	}
}
