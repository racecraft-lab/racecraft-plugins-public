package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"

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

stdin:  one JSON object {"state": ..., "questions": {...}, "model": "...", "images": {...}}
stdout: the provider's JSON, only when the exit code is 0
stderr: a diagnostic that never carries a key, the request, or image bytes

Exit codes:
  0  answered, and the response passed validation
  2  request rejected locally (shape, option or score cap, context budget, or an image the backend would refuse)
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

	resolved := resolveConfiguredHops(cfg, os.LookupEnv)
	primary, fallback := resolved.sources()
	code := resolved.credentialExit()
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

	c, _, err := resolved.clients(stderr, io.Discard)
	if err != nil {
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
	notAnObject := errors.New(`stdin is not one JSON object of the form {"state": ..., "questions": {...}, "model": "..."}`)
	// Decode accepts a bare null into a struct and leaves it zero, so the
	// object is required here, before decoding. JSON allows only these four
	// whitespace bytes ahead of a value.
	if !bytes.HasPrefix(bytes.TrimLeft(b, " \t\r\n"), []byte("{")) {
		return in, notAnObject
	}
	dec := json.NewDecoder(bytes.NewReader(b))
	dec.DisallowUnknownFields()
	if err := dec.Decode(&in); err != nil {
		return in, notAnObject
	}
	if _, err := dec.Token(); err != io.EOF {
		return in, errors.New("stdin holds more than one JSON value; send exactly one request")
	}
	return in, nil
}
