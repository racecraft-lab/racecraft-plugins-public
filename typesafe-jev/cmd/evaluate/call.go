package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

// The exit codes of `evaluate call`. They are the whole contract with a
// caller that cannot read stderr: each one names a different action, and none
// of them carries a value.
const (
	exitAnswered         = 0 // answered, and the response passed validation
	exitRequestInvalid   = 2 // the request was rejected locally, before any network call
	exitUnconfigured     = 3 // no credential source is configured for the primary or the fallback
	exitCredentialBroken = 4 // a credential source is configured but cannot be used
	exitProviderFailed   = 5 // provider or transport error, or timeout, after the client's own retries
	exitResponseInvalid  = 6 // the provider answered, but the answer failed validation
)

// The plugin's key-file defaults, relative to the home directory, and the two
// variables they fill in.
const (
	pluginKeyDirectory    = ".config/racecraft-jev"
	pluginKeyFileEnv      = "JEV_API_KEY_FILE"
	pluginFallbackFileEnv = "JEV_FALLBACK_API_KEY_FILE"
)

// exitCodeError ends the process with code. main prints the text, when there
// is any, and exits with the code instead of the generic 1.
type exitCodeError struct {
	code int
	text string
}

func (e *exitCodeError) Error() string { return e.text }

// requestInvalidError marks a request that failed local validation, and
// responseInvalidError a provider answer that failed it. Both keep the wrapped
// text exactly, so the MCP tool reports what it always has; only `call` looks
// at the type, to choose an exit code.
type requestInvalidError struct{ err error }

func (e *requestInvalidError) Error() string { return e.err.Error() }
func (e *requestInvalidError) Unwrap() error { return e.err }

type responseInvalidError struct{ err error }

func (e *responseInvalidError) Error() string { return e.err.Error() }
func (e *responseInvalidError) Unwrap() error { return e.err }

// callOptions are the flags of `evaluate call`.
type callOptions struct {
	check          bool
	pluginDefaults bool
	// retarget lets a test point the resolved backends at a local server. It is
	// nil in the shipped command.
	retarget func(*Config)
}

func newCallCmd() *cobra.Command {
	var opts callOptions
	cmd := &cobra.Command{
		Use:   "call",
		Short: "Run one evaluation: a JSON request on stdin, the provider's JSON on stdout",
		Long: `Run one evaluation through the same path as the MCP tool, including the
fallback backend and both validations.

stdin:  one JSON object {"state": ..., "questions": {...}, "model": "..."}
stdout: the provider's JSON, only when the exit code is 0
stderr: a diagnostic that never carries a key or the request

Exit codes:
  0  answered, and the response passed validation
  2  request rejected locally (shape, option cap, context budget)
  3  no credential source configured for the primary or the fallback
  4  a credential source is configured but unusable
  5  provider or transport error, or timeout
  6  the response failed validation

--check loads the configuration and credentials, makes no network call, and
exits 0, 3, or 4. It prints the value-free credential status as JSON.`,
		Args: func(_ *cobra.Command, args []string) error {
			if len(args) > 0 {
				return &exitCodeError{code: exitRequestInvalid, text: "call takes no arguments; send the request on stdin"}
			}
			return nil
		},
		RunE: func(cmd *cobra.Command, _ []string) error {
			code := runCall(cmd.Context(), opts, cmd.InOrStdin(), cmd.OutOrStdout(), cmd.ErrOrStderr())
			if code != exitAnswered {
				return &exitCodeError{code: code}
			}
			return nil
		},
	}
	cmd.SetFlagErrorFunc(func(_ *cobra.Command, err error) error {
		return &exitCodeError{code: exitRequestInvalid, text: err.Error()}
	})
	cmd.Flags().BoolVar(&opts.check, "check", false, "load the configuration and credentials without a network call")
	cmd.Flags().BoolVar(&opts.pluginDefaults, "plugin-defaults", false,
		"default each unset key-file path to "+pluginKeyDirectory+"/<provider>.key, only when that file exists")
	return cmd
}

// sourceStatus is the value-free state of one backend's credential source.
type sourceStatus struct {
	Provider string `json:"provider"`
	// Source is where the key comes from: "explicit-file" (the operator set the
	// path), "default-file" (--plugin-defaults found the file), "environment",
	// or "none".
	Source string `json:"source"`
	// State is "ok", "absent" (nothing configured), or "unusable" (configured,
	// and cannot be used).
	State string `json:"state"`
	// reason says why a source is unusable. It names a path or a variable and
	// never a value, and it goes to stderr only.
	reason string
}

// checkReport is what `call --check` prints on stdout.
type checkReport struct {
	Exit     int           `json:"exit"`
	Primary  sourceStatus  `json:"primary"`
	Fallback *sourceStatus `json:"fallback"`
}

// runCall is `evaluate call`. It returns the exit code, and writes the
// provider's JSON to stdout only on success.
func runCall(ctx context.Context, opts callOptions, stdin io.Reader, stdout, stderr io.Writer) int {
	cfg, err := resolveCallConfig(os.LookupEnv, opts.pluginDefaults)
	if err != nil {
		// An unknown backend or a relative key path is a configuration that
		// was set and cannot be used, which is what exit 4 means.
		fmt.Fprintln(stderr, "evaluate:", err)
		return exitCredentialBroken
	}
	if opts.retarget != nil {
		opts.retarget(&cfg)
	}

	primary, fallback := classifySources(cfg, os.LookupEnv)
	code := credentialExit(primary, fallback)
	for _, s := range []*sourceStatus{&primary, fallback} {
		if s != nil && s.State == "unusable" {
			fmt.Fprintf(stderr, "evaluate: %s credential (%s) is unusable: %s\n", s.Provider, s.Source, s.reason)
		}
	}
	if code == exitUnconfigured {
		fmt.Fprintf(stderr, "evaluate: no credential is configured; create ~/%s/%s.key (mode 600) or set %s\n",
			pluginKeyDirectory, cfg.Provider.Name, cfg.Provider.APIKeyEnv)
	}

	if opts.check {
		report := checkReport{Exit: code, Primary: primary, Fallback: fallback}
		b, err := json.Marshal(report)
		if err != nil {
			fmt.Fprintln(stderr, "evaluate: encoding the check report:", err)
			return exitCredentialBroken
		}
		fmt.Fprintln(stdout, string(b))
		return code
	}
	if code != exitAnswered {
		return code
	}

	in, err := readCallRequest(stdin)
	if err != nil {
		fmt.Fprintln(stderr, "evaluate:", err)
		return exitRequestInvalid
	}

	// Sources found absent are dropped before the clients are built, so the
	// one that is present serves without a second, noisier diagnosis.
	if primary.State == "absent" && cfg.Fallback != nil {
		cfg = cfg.fallbackConfig()
	} else if fallback != nil && fallback.State == "absent" {
		cfg.Fallback = nil
	}
	c, _, err := newClients(cfg, stderr)
	if err != nil {
		// The file changed between the check and the load.
		fmt.Fprintln(stderr, "evaluate:", err)
		return exitCredentialBroken
	}

	body, err := runEvaluate(ctx, c, in)
	if err != nil {
		fmt.Fprintln(stderr, "evaluate:", err)
		var reqErr *requestInvalidError
		var respErr *responseInvalidError
		switch {
		case errors.As(err, &reqErr):
			return exitRequestInvalid
		case errors.As(err, &respErr):
			return exitResponseInvalid
		default:
			return exitProviderFailed
		}
	}
	if _, err := stdout.Write(append(bytes.TrimRight(body, "\n"), '\n')); err != nil {
		fmt.Fprintln(stderr, "evaluate: writing the response:", err)
		return exitProviderFailed
	}
	return exitAnswered
}

// credentialExit turns two source states into the exit code --check reports.
// A source that is configured and unusable is an error even when the other
// one works: a broken key the operator set up must not be quietly passed over.
func credentialExit(primary sourceStatus, fallback *sourceStatus) int {
	if primary.State == "unusable" || (fallback != nil && fallback.State == "unusable") {
		return exitCredentialBroken
	}
	if primary.State == "ok" || (fallback != nil && fallback.State == "ok") {
		return exitAnswered
	}
	return exitUnconfigured
}

// resolveCallConfig resolves the configuration, first applying the plugin's
// key-file defaults when asked to.
func resolveCallConfig(look lookupFunc, pluginDefaults bool) (Config, error) {
	if !pluginDefaults {
		return resolveConfig(look)
	}
	withDefaults, defaulted := pluginDefaultLookup(look, homeDir(look))
	cfg, err := resolveConfig(withDefaults)
	if err != nil {
		return cfg, err
	}
	cfg.KeyFileDefaulted = defaulted[pluginKeyFileEnv]
	if cfg.Fallback != nil {
		cfg.Fallback.KeyFileDefaulted = defaulted[pluginFallbackFileEnv]
	}
	return cfg, nil
}

// homeDir is $HOME, or the platform's home directory when HOME is unset.
func homeDir(look lookupFunc) string {
	if home, ok := look("HOME"); ok && home != "" {
		return home
	}
	home, _ := os.UserHomeDir()
	return home
}

// pluginDefaultLookup wraps look so that each unset key-file variable points at
// the plugin's default key file for that backend, but only when something is
// at that path. It reports which variables it filled in.
//
// A default for a file that does not exist would be worse than none: an
// explicit key file stops the environment variable from being read at all, so
// an operator whose key lives only in TYPESAFE_API_KEY could never
// authenticate through the plugin. That was the launcher's behaviour through
// 0.8.0.
func pluginDefaultLookup(look lookupFunc, home string) (lookupFunc, map[string]bool) {
	filled := map[string]string{}
	if home != "" {
		dir := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory))
		primary := "typesafe"
		if raw, set := look("JEV_PROVIDER"); set {
			primary = strings.TrimSpace(raw)
		}
		defaultKeyFile(look, filled, pluginKeyFileEnv, dir, primary)
		if raw, set := look("JEV_FALLBACK_PROVIDER"); set && strings.TrimSpace(raw) != "" {
			defaultKeyFile(look, filled, pluginFallbackFileEnv, dir, strings.TrimSpace(raw))
		}
	}
	defaulted := map[string]bool{}
	for name := range filled {
		defaulted[name] = true
	}
	return func(name string) (string, bool) {
		if path, ok := filled[name]; ok {
			return path, true
		}
		return look(name)
	}, defaulted
}

// defaultKeyFile records dir/<provider>.key for name when name is unset or
// empty, the provider is a known backend, and something exists at the path.
// Whether that something is a usable key file is for readKeyFile to decide.
func defaultKeyFile(look lookupFunc, filled map[string]string, name, dir, provider string) {
	if raw, set := look(name); set && raw != "" {
		return
	}
	if _, known := providers[provider]; !known {
		return
	}
	path := filepath.Join(dir, provider+".key")
	if _, err := os.Lstat(path); err == nil {
		filled[name] = path
	}
}

// classifySources reports the state of the primary's credential source and,
// when a fallback is configured, the fallback's. It reads each key exactly as
// the server would and keeps only the verdict.
func classifySources(cfg Config, look lookupFunc) (sourceStatus, *sourceStatus) {
	primary := classifySource(cfg.Provider, cfg.KeyFile, cfg.KeyFileDefaulted, look)
	if cfg.Fallback == nil {
		return primary, nil
	}
	fallback := classifySource(cfg.Fallback.Provider, cfg.Fallback.KeyFile, cfg.Fallback.KeyFileDefaulted, look)
	return primary, &fallback
}

func classifySource(spec ProviderSpec, keyFile string, defaulted bool, look lookupFunc) sourceStatus {
	s := sourceStatus{Provider: spec.Name}
	if keyFile != "" {
		s.Source = "explicit-file"
		if defaulted {
			s.Source = "default-file"
		}
		if _, err := readKeyFile(keyFile); err != nil {
			s.State, s.reason = "unusable", err.Error()
			return s
		}
		s.State = "ok"
		return s
	}
	raw, set := look(spec.APIKeyEnv)
	if !set || raw == "" {
		s.Source, s.State = "none", "absent"
		return s
	}
	s.Source = "environment"
	if _, err := parseKey(raw); err != nil {
		s.State, s.reason = "unusable", spec.APIKeyEnv+" "+err.Error()
		return s
	}
	s.State = "ok"
	return s
}

// readCallRequest reads one request object from r. It reads at most
// maxRequestBody bytes, and its errors are fixed text: a JSON decoder's own
// messages can quote the input, which may be the private state being judged.
func readCallRequest(r io.Reader) (evaluateIn, error) {
	var in evaluateIn
	b, err := io.ReadAll(io.LimitReader(r, maxRequestBody+1))
	if err != nil {
		return in, errors.New("reading the request from stdin failed")
	}
	if len(b) > maxRequestBody {
		return in, fmt.Errorf("the request on stdin is over the %d byte limit", maxRequestBody)
	}
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&in); err != nil {
		return in, errors.New(`stdin is not one JSON object of the form {"state": ..., "questions": {...}, "model": "..."}`)
	}
	if _, err := dec.Token(); err != io.EOF {
		return in, errors.New("stdin holds more than one JSON value; send exactly one request")
	}
	return in, nil
}
