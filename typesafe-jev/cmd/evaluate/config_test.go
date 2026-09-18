package main

import (
	"errors"
	"fmt"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// envLookup builds a lookupFunc from a map, so a config test never reads, and
// never depends on, the developer's real shell.
func envLookup(kv map[string]string) lookupFunc {
	return func(k string) (string, bool) {
		v, ok := kv[k]
		return v, ok
	}
}

// providerAt copies a real provider spec but points it at a local test server,
// so tests exercise the shipped retry policy and headers without a shipped
// environment variable that could redirect production traffic.
func providerAt(name, url string) ProviderSpec {
	spec := providers[name]
	spec.EndpointURL = url
	return spec
}

func testClient(spec ProviderSpec, srv *httptest.Server) *Client {
	return &Client{
		Provider:   spec,
		Model:      spec.DefaultModel,
		APIKey:     "k",
		HTTP:       srv.Client(),
		Timeout:    10 * time.Second,
		MaxRetries: defaultMaxRetries,
		Backoff:    time.Millisecond,
	}
}

// writeKeyFile writes a key file with the given mode into a temp dir.
func writeKeyFile(t *testing.T, contents string, mode os.FileMode) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), "provider.key")
	if err := os.WriteFile(path, []byte(contents), mode); err != nil {
		t.Fatal(err)
	}
	// WriteFile respects umask, so set the mode explicitly.
	if err := os.Chmod(path, mode); err != nil {
		t.Fatal(err)
	}
	return path
}

// CFG-01, CFG-02: the backend comes from JEV_PROVIDER, never from which keys
// happen to be set. This is the behaviour that replaced upstream's route().
func TestResolveProviderIsExplicit(t *testing.T) {
	for _, tc := range []struct {
		name       string
		env        map[string]string
		wantURL    string
		wantKeyEnv string
		wantModel  string
	}{
		{
			name:       "unset defaults to typesafe",
			env:        map[string]string{},
			wantURL:    "https://api.typesafe.ai/v1/systemone",
			wantKeyEnv: "TYPESAFE_API_KEY",
			wantModel:  "jev-latest",
		},
		{
			// CFG-01: an OpenRouter key in the environment does not select
			// OpenRouter. Upstream would have routed this to OpenRouter.
			name:       "openrouter key present but provider unset",
			env:        map[string]string{"OPENROUTER_API_KEY": "o"},
			wantURL:    "https://api.typesafe.ai/v1/systemone",
			wantKeyEnv: "TYPESAFE_API_KEY",
			wantModel:  "jev-latest",
		},
		{
			// CFG-02: and a TypeSafe key present does not win back.
			name:       "openrouter selected with both keys set",
			env:        map[string]string{"JEV_PROVIDER": "openrouter", "TYPESAFE_API_KEY": "t", "OPENROUTER_API_KEY": "o"},
			wantURL:    "https://openrouter.ai/api/alpha/decisions",
			wantKeyEnv: "OPENROUTER_API_KEY",
			wantModel:  "~typesafe/jev-latest",
		},
		{
			name:       "typesafe selected explicitly",
			env:        map[string]string{"JEV_PROVIDER": "typesafe", "OPENROUTER_API_KEY": "o"},
			wantURL:    "https://api.typesafe.ai/v1/systemone",
			wantKeyEnv: "TYPESAFE_API_KEY",
			wantModel:  "jev-latest",
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			cfg, err := resolveConfig(envLookup(tc.env))
			if err != nil {
				t.Fatal(err)
			}
			if cfg.Provider.EndpointURL != tc.wantURL {
				t.Errorf("endpoint = %q, want %q", cfg.Provider.EndpointURL, tc.wantURL)
			}
			if cfg.Provider.APIKeyEnv != tc.wantKeyEnv {
				t.Errorf("key env = %q, want %q", cfg.Provider.APIKeyEnv, tc.wantKeyEnv)
			}
			if cfg.Model != tc.wantModel {
				t.Errorf("model = %q, want %q", cfg.Model, tc.wantModel)
			}
		})
	}
}

// CFG-04: a provider value that is not a known backend fails loudly, rather
// than falling back to a default that bills a different account.
func TestResolveProviderRejectsUnknown(t *testing.T) {
	for _, v := range []string{"", "  ", "openrouterr", "OpenRouter", "typesafe ai", "anthropic"} {
		_, err := resolveConfig(envLookup(map[string]string{"JEV_PROVIDER": v}))
		if err == nil {
			t.Errorf("JEV_PROVIDER=%q: want an error", v)
		}
	}
}

// CFG-05, CFG-06: JEV_MODEL overrides the backend default and is passed
// through byte for byte, tilde and all.
func TestResolveModel(t *testing.T) {
	for _, tc := range []struct{ provider, model, want string }{
		{"openrouter", "", "~typesafe/jev-latest"},
		{"openrouter", "~typesafe/jev-2026-01-01", "~typesafe/jev-2026-01-01"},
		// No prefix is added for OpenRouter or stripped for TypeSafe: a
		// mismatched id should surface as a readable 404, not a silent rewrite.
		{"openrouter", "jev-latest", "jev-latest"},
		{"typesafe", "~typesafe/jev-latest", "~typesafe/jev-latest"},
		{"typesafe", "", "jev-latest"},
	} {
		e := map[string]string{"JEV_PROVIDER": tc.provider}
		if tc.model != "" {
			e["JEV_MODEL"] = tc.model
		}
		cfg, err := resolveConfig(envLookup(e))
		if err != nil {
			t.Fatalf("%+v: %v", tc, err)
		}
		if cfg.Model != tc.want {
			t.Errorf("%+v: model = %q, want %q", tc, cfg.Model, tc.want)
		}
	}

	if _, err := resolveConfig(envLookup(map[string]string{"JEV_MODEL": "   "})); err == nil {
		t.Error("whitespace-only JEV_MODEL: want an error")
	}
}

// CFG-07: bad timeouts and retry counts fail at startup, before a provider is
// ever contacted.
func TestResolveTimeoutAndRetries(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Timeout != defaultTimeout || cfg.MaxRetries != defaultMaxRetries {
		t.Fatalf("defaults = %v/%d, want %v/%d", cfg.Timeout, cfg.MaxRetries, defaultTimeout, defaultMaxRetries)
	}

	cfg, err = resolveConfig(envLookup(map[string]string{"JEV_REQUEST_TIMEOUT": "90s", "JEV_MAX_RETRIES": "0"}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Timeout != 90*time.Second || cfg.MaxRetries != 0 {
		t.Fatalf("got %v/%d", cfg.Timeout, cfg.MaxRetries)
	}

	for _, bad := range []map[string]string{
		{"JEV_REQUEST_TIMEOUT": "soon"},
		{"JEV_REQUEST_TIMEOUT": "0"},
		{"JEV_REQUEST_TIMEOUT": "-5s"},
		{"JEV_REQUEST_TIMEOUT": "10m"},
		{"JEV_MAX_RETRIES": "many"},
		{"JEV_MAX_RETRIES": "-1"},
		{"JEV_MAX_RETRIES": "6"},
		{"JEV_API_KEY_FILE": "relative/provider.key"},
		{"JEV_API_KEY_FILE": "   "},
	} {
		if _, err := resolveConfig(envLookup(bad)); err == nil {
			t.Errorf("%v: want an error", bad)
		}
	}
}

// CFG-03: an OpenRouter process with only a TypeSafe key fails before any
// network call, and never reaches for the other backend's credential.
func TestCredentialDoesNotCrossBackends(t *testing.T) {
	t.Setenv("TYPESAFE_API_KEY", "typesafe-secret")
	os.Unsetenv("OPENROUTER_API_KEY")

	cfg, err := resolveConfig(envLookup(map[string]string{"JEV_PROVIDER": "openrouter"}))
	if err != nil {
		t.Fatal(err)
	}
	_, err = loadCredential(cfg)
	if err == nil {
		t.Fatal("want an error, got a credential")
	}
	if strings.Contains(err.Error(), "typesafe-secret") {
		t.Fatalf("error leaked the other backend's key: %v", err)
	}
	if !strings.Contains(err.Error(), "OPENROUTER_API_KEY") {
		t.Errorf("error should name the expected variable: %v", err)
	}
}

// KEY-01: an explicit key file wins over an environment key, so the operator's
// stated credential is the one used.
func TestKeyFileWinsOverEnvironment(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "from-environment")
	path := writeKeyFile(t, "from-file\n", 0o600)

	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER":     "openrouter",
		"JEV_API_KEY_FILE": path,
	}))
	if err != nil {
		t.Fatal(err)
	}
	key, err := loadCredential(cfg)
	if err != nil {
		t.Fatal(err)
	}
	if key.reveal() != "from-file" {
		t.Fatalf("key = %q, want the file's value", key.reveal())
	}
}

// KEY-02: a named-but-unusable key file is fatal even when an environment key
// would work. Falling back would bill an account the operator did not choose.
func TestKeyFileFailureDoesNotFallBack(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "from-environment")

	cases := map[string]string{
		"missing":     filepath.Join(t.TempDir(), "absent.key"),
		"empty":       writeKeyFile(t, "", 0o600),
		"blank":       writeKeyFile(t, "\n", 0o600),
		"group read":  writeKeyFile(t, "k\n", 0o640),
		"world read":  writeKeyFile(t, "k\n", 0o604),
		"placeholder": writeKeyFile(t, "${OPENROUTER_API_KEY}\n", 0o600),
		"padded":      writeKeyFile(t, "  k  \n", 0o600),
		"two lines":   writeKeyFile(t, "k\nsecond\n", 0o600),
		"oversized":   writeKeyFile(t, strings.Repeat("x", maxKeyFileBytes+1), 0o600),
	}
	for name, path := range cases {
		t.Run(name, func(t *testing.T) {
			cfg, err := resolveConfig(envLookup(map[string]string{
				"JEV_PROVIDER":     "openrouter",
				"JEV_API_KEY_FILE": path,
			}))
			if err != nil {
				t.Fatal(err)
			}
			key, err := loadCredential(cfg)
			if err == nil {
				t.Fatalf("want an error, got %q", key.reveal())
			}
			if strings.Contains(err.Error(), "from-environment") {
				t.Fatalf("fell back to the environment key: %v", err)
			}
		})
	}
}

// KEY-03: a rejected key never appears in the error explaining the rejection.
func TestKeyErrorsNeverQuoteTheValue(t *testing.T) {
	const sentinel = "sk-sentinel-must-not-appear"
	for _, contents := range []string{sentinel + " \n", sentinel + "\nsecond\n"} {
		path := writeKeyFile(t, contents, 0o600)
		cfg, _ := resolveConfig(envLookup(map[string]string{"JEV_API_KEY_FILE": path}))
		_, err := loadCredential(cfg)
		if err == nil {
			t.Fatalf("%q: want an error", contents)
		}
		if strings.Contains(err.Error(), sentinel) {
			t.Fatalf("error quoted the key: %v", err)
		}
	}
}

// The same property on the environment path, which the key-file cases above
// never reach. This is the flow CodeQL's go/clear-text-logging rule reports:
// os.LookupEnv(APIKeyEnv) feeds parseKey, whose error is wrapped and printed
// by `evaluate setup pi`. The value must not survive that trip, and every
// rejection reason is exercised rather than one representative case.
func TestEnvironmentKeyErrorsNeverQuoteTheValue(t *testing.T) {
	const sentinel = "sk-sentinel-must-not-appear"
	for name, value := range map[string]string{
		"trailing whitespace": sentinel + " ",
		"leading whitespace":  " " + sentinel,
		"embedded newline":    sentinel + "\nsecond",
		"control character":   sentinel + "\x01",
		"delete character":    sentinel + "\x7f",
		"placeholder":         "${" + sentinel + "}",
	} {
		t.Run(name, func(t *testing.T) {
			// envLookup, not os.LookupEnv: resolveConfig's contract is that a
			// test never reads the developer's shell. The value still has to
			// reach os.LookupEnv inside loadCredential, so it is also set in
			// the process environment, scoped to this subtest.
			cfg, err := resolveConfig(envLookup(map[string]string{
				"JEV_PROVIDER": "openrouter",
			}))
			if err != nil {
				t.Fatal(err)
			}
			t.Setenv(cfg.Provider.APIKeyEnv, value)

			_, err = loadCredential(cfg)
			if err == nil {
				t.Fatalf("%q: want an error", value)
			}
			if strings.Contains(err.Error(), sentinel) {
				t.Fatalf("error quoted the key: %v", err)
			}
			// The variable's name is the useful part and is not a secret.
			if !strings.Contains(err.Error(), "OPENROUTER_API_KEY") {
				t.Errorf("error should name the variable: %v", err)
			}
		})
	}
}

// Each rejection reason is a package-level value, so no error parseKey returns
// can carry the key it was handed. Building one inside the function from the
// candidate would defeat the test above without failing it, because a future
// edit could interpolate the value into a message that still matches no
// sentinel this test happens to use.
func TestKeyRejectionReasonsAreConstant(t *testing.T) {
	const sentinel = "sk-another-sentinel"
	for _, s := range []string{
		"", sentinel + " ", " " + sentinel, sentinel + "\n",
		sentinel + "\x00", "${" + sentinel + "}",
	} {
		_, err := parseKey(s)
		if err == nil {
			t.Fatalf("parseKey(%q) should fail", s)
		}
		switch {
		case errors.Is(err, errKeyEmpty),
			errors.Is(err, errKeyWhitespace),
			errors.Is(err, errKeyControlChar),
			errors.Is(err, errKeyPlaceholder):
		default:
			t.Errorf("parseKey(%q) returned an ad-hoc error %v, not one of the fixed reasons", s, err)
		}
	}
}

// KEY-04: the one newline an editor or heredoc leaves behind is expected, in
// either line ending, and does not change the credential.
func TestKeyFileAcceptsOneTerminator(t *testing.T) {
	for _, contents := range []string{"sk-abc123", "sk-abc123\n", "sk-abc123\r\n"} {
		path := writeKeyFile(t, contents, 0o600)
		cfg, err := resolveConfig(envLookup(map[string]string{"JEV_API_KEY_FILE": path}))
		if err != nil {
			t.Fatal(err)
		}
		key, err := loadCredential(cfg)
		if err != nil {
			t.Fatalf("%q: %v", contents, err)
		}
		if key.reveal() != "sk-abc123" {
			t.Errorf("%q: key = %q", contents, key.reveal())
		}
	}
}

// A credential must redact itself under the verbs that reach logs and test
// output, or one careless %v prints a key.
func TestCredentialRedactsWhenPrinted(t *testing.T) {
	c := credential("sk-secret-value")
	for _, got := range []string{c.String(), fmt.Sprint(c), fmt.Sprintf("%v", c), fmt.Sprintf("%s", c)} {
		if strings.Contains(got, "sk-secret-value") {
			t.Fatalf("credential printed as %q", got)
		}
	}
	if c.reveal() != "sk-secret-value" {
		t.Fatal("reveal must return the real value")
	}
}

// A Config carries no secret, so printing one in a diagnostic is safe.
func TestConfigHoldsNoSecret(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "sk-secret-value")
	path := writeKeyFile(t, "sk-file-value\n", 0o600)
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER":     "openrouter",
		"JEV_API_KEY_FILE": path,
	}))
	if err != nil {
		t.Fatal(err)
	}
	printed := fmt.Sprintf("%+v %s", cfg, cfg.credentialSource())
	for _, secret := range []string{"sk-secret-value", "sk-file-value"} {
		if strings.Contains(printed, secret) {
			t.Fatalf("config printed a secret: %s", printed)
		}
	}
	if !strings.Contains(printed, path) {
		t.Errorf("credentialSource should name the path: %s", printed)
	}
}
