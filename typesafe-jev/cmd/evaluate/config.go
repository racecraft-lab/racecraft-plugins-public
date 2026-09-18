package main

import (
	"fmt"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

// ProviderSpec is the non-secret description of an evaluation backend. The
// credential itself never lives here: see credentials.go.
type ProviderSpec struct {
	// Name is the JEV_PROVIDER value that selects this backend.
	Name string
	// EndpointURL is the complete URL to POST to, not a base to append to.
	EndpointURL string
	// APIKeyEnv is the only environment variable this backend reads a key
	// from. A backend never falls back to another backend's variable.
	APIKeyEnv string
	// DefaultModel applies when neither the tool call nor JEV_MODEL names one.
	DefaultModel string
	// Attribution is sent as fixed HTTP-Referer / X-OpenRouter-Title headers
	// when set. It is a constant, never derived from local paths or content.
	Attribution bool
	// RetryStatuses are the HTTP statuses worth a second attempt on this
	// backend. See docs/provider-contracts.md: this is fork policy, not a
	// provider guarantee.
	RetryStatuses []int
}

// providers is the closed set of backends. Adding a URL here is the only way
// to change where a request goes; there is deliberately no environment
// variable that points the server at an arbitrary host.
var providers = map[string]ProviderSpec{
	"typesafe": {
		Name:         "typesafe",
		EndpointURL:  "https://api.typesafe.ai/v1/systemone",
		APIKeyEnv:    "TYPESAFE_API_KEY",
		DefaultModel: "jev-latest",
		// 529 is TypeSafe's overload status, which upstream already retried.
		RetryStatuses: []int{429, 529},
	},
	"openrouter": {
		Name:         "openrouter",
		EndpointURL:  "https://openrouter.ai/api/alpha/decisions",
		APIKeyEnv:    "OPENROUTER_API_KEY",
		DefaultModel: "~typesafe/jev-latest",
		Attribution:  true,
		// 503 is documented on the Decisions path; 529 is not.
		RetryStatuses: []int{429, 503},
	},
}

const (
	defaultTimeout    = 45 * time.Second
	maxTimeout        = 5 * time.Minute
	defaultMaxRetries = 3
	maxMaxRetries     = 5
)

// Config is everything needed to serve, except the credential. It holds no
// secret, so it is safe to print in a diagnostic.
type Config struct {
	Provider   ProviderSpec
	Model      string
	Timeout    time.Duration
	MaxRetries int
	// KeyFile is an absolute path, or "" to use the provider's environment
	// variable. The path is not a secret; the file's contents are.
	KeyFile string
}

// lookupFunc reports a variable's value and whether it was set at all. The
// distinction matters: an unset JEV_PROVIDER selects the default, while one
// explicitly set to blank is a mistake worth reporting.
type lookupFunc func(string) (string, bool)

// resolveConfig builds the server's configuration from the environment. It is
// pure apart from the injected lookup, so tests never depend on the developer's
// shell.
func resolveConfig(look lookupFunc) (Config, error) {
	var cfg Config

	spec, err := resolveProvider(look)
	if err != nil {
		return cfg, err
	}
	cfg.Provider = spec

	if cfg.Model, err = resolveModel(look, spec); err != nil {
		return cfg, err
	}
	if cfg.Timeout, err = resolveTimeout(look); err != nil {
		return cfg, err
	}
	if cfg.MaxRetries, err = resolveMaxRetries(look); err != nil {
		return cfg, err
	}
	if cfg.KeyFile, err = resolveKeyFile(look); err != nil {
		return cfg, err
	}
	return cfg, nil
}

// resolveProvider selects the backend. Selection is explicit: which API keys
// happen to be set in the environment never decides where a request goes, or
// which account it bills.
func resolveProvider(look lookupFunc) (ProviderSpec, error) {
	raw, set := look("JEV_PROVIDER")
	if !set {
		return providers["typesafe"], nil
	}
	name := strings.TrimSpace(raw)
	if name == "" {
		return ProviderSpec{}, fmt.Errorf("JEV_PROVIDER is set but blank; unset it for the default (typesafe) or name one of %s", providerNames())
	}
	spec, ok := providers[name]
	if !ok {
		// Deliberately not a fuzzy match: silently correcting a misspelling
		// could send state and billing to a backend nobody chose.
		return ProviderSpec{}, fmt.Errorf("JEV_PROVIDER=%q is not a known backend; use one of %s", name, providerNames())
	}
	return spec, nil
}

func providerNames() string {
	names := make([]string, 0, len(providers))
	for n := range providers {
		names = append(names, n)
	}
	sort.Strings(names)
	return strings.Join(names, ", ")
}

// resolveModel applies JEV_MODEL. A tool call's own model argument outranks
// this and is applied later, per request.
func resolveModel(look lookupFunc, spec ProviderSpec) (string, error) {
	raw, set := look("JEV_MODEL")
	if !set || raw == "" {
		return spec.DefaultModel, nil
	}
	if strings.TrimSpace(raw) == "" {
		return "", fmt.Errorf("JEV_MODEL is whitespace only; unset it for the backend default (%s)", spec.DefaultModel)
	}
	// Returned exactly as given. A "~typesafe/" prefix is neither added nor
	// stripped: guessing at model ids turns a clear 404 into a mystery.
	return raw, nil
}

func resolveTimeout(look lookupFunc) (time.Duration, error) {
	raw, set := look("JEV_REQUEST_TIMEOUT")
	if !set || raw == "" {
		return defaultTimeout, nil
	}
	d, err := time.ParseDuration(strings.TrimSpace(raw))
	if err != nil {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q is not a duration such as 45s or 2m", raw)
	}
	if d <= 0 {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q must be positive", raw)
	}
	if d > maxTimeout {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q is above the %s ceiling", raw, maxTimeout)
	}
	return d, nil
}

func resolveMaxRetries(look lookupFunc) (int, error) {
	raw, set := look("JEV_MAX_RETRIES")
	if !set || raw == "" {
		return defaultMaxRetries, nil
	}
	n, err := strconv.Atoi(strings.TrimSpace(raw))
	if err != nil {
		return 0, fmt.Errorf("JEV_MAX_RETRIES=%q is not a whole number", raw)
	}
	if n < 0 || n > maxMaxRetries {
		return 0, fmt.Errorf("JEV_MAX_RETRIES=%q is outside the accepted range 0-%d", raw, maxMaxRetries)
	}
	return n, nil
}

func resolveKeyFile(look lookupFunc) (string, error) {
	raw, set := look("JEV_API_KEY_FILE")
	if !set || raw == "" {
		return "", nil
	}
	path := strings.TrimSpace(raw)
	if path == "" {
		return "", fmt.Errorf("JEV_API_KEY_FILE is whitespace only; unset it to use the provider's environment variable")
	}
	// Absolute only. A client launches this server with an unpredictable
	// working directory, so a relative path would resolve somewhere nobody
	// intended, or nowhere at all.
	if !filepath.IsAbs(path) {
		return "", fmt.Errorf("JEV_API_KEY_FILE=%q must be an absolute path", path)
	}
	return path, nil
}

// credentialSource names where the key will be read from, for a diagnostic
// that must not print the key itself.
func (c Config) credentialSource() string {
	if c.KeyFile != "" {
		return "file " + c.KeyFile
	}
	return "environment " + c.Provider.APIKeyEnv
}
