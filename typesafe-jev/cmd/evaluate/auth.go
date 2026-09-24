package main

import (
	"errors"
	"fmt"
	"io"
	"os"
	"runtime"
	"strings"
	"syscall"
)

// maxKeyFileBytes bounds the key file. Real keys are well under a hundred
// bytes; anything near this limit is the wrong file.
const maxKeyFileBytes = 8 << 10

// credential is an API key. String redacts, so printing a struct that holds
// one with %v or %s cannot leak it into a log, an error, or a test failure.
// Use reveal at the single point where the header is built.
type credential string

func (c credential) String() string { return "[redacted]" }

func (c credential) reveal() string { return string(c) }

// loadCredential reads the key for cfg's backend, from the explicit key file
// when one is configured and otherwise from that backend's own environment
// variable.
//
// There is no fallback between the two, and no implicit one between backends:
// a fallback backend exists only when the operator names it, and it loads its
// own credential through this same function (see fallback.go). If the
// operator named a file, an unreadable file is fatal even when a usable
// environment key is sitting right there: quietly using a different credential
// would bill a different account than the one they configured.
//
// The key is read once. Rotating it means restarting the server, which for an
// MCP client means reconnecting it.
func loadCredential(cfg Config) (credential, error) {
	if cfg.KeyFile != "" {
		return readKeyFile(cfg.keyFileEnv(), cfg.KeyFile)
	}
	raw, ok := os.LookupEnv(cfg.Provider.APIKeyEnv)
	if !ok || raw == "" {
		return "", fmt.Errorf("%s: %w; set %s, or point %s at a private key file",
			cfg.Provider.Name, errNoCredential, cfg.Provider.APIKeyEnv, cfg.keyFileEnv())
	}
	key, err := parseKey(raw)
	if err != nil {
		return "", fmt.Errorf("%s: %s %w", cfg.Provider.Name, cfg.Provider.APIKeyEnv, err)
	}
	return key, nil
}

// readKeyFile reads a key from a private file. Every check is made against the
// opened file rather than the path, so a file swapped between the check and the
// read cannot slip past. envVar names the variable the path came from, such as
// JEV_FALLBACK_API_KEY_FILE, so each diagnostic points at the setting to fix.
func readKeyFile(envVar, path string) (credential, error) {
	// O_NONBLOCK, because os.Open on a named pipe blocks until a writer
	// appears, and it does so before any check below has run: the server would
	// hang at startup with no message rather than refusing a file that is not
	// a regular file. The flag changes nothing for a regular file, which is
	// the only kind this accepts anyway.
	f, err := os.OpenFile(path, os.O_RDONLY|syscall.O_NONBLOCK, 0)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			return "", fmt.Errorf("%s %s does not exist", envVar, path)
		}
		if errors.Is(err, os.ErrPermission) {
			return "", fmt.Errorf("%s %s is not readable", envVar, path)
		}
		return "", fmt.Errorf("%s %s: %w", envVar, path, err)
	}
	defer f.Close()

	info, err := f.Stat()
	if err != nil {
		return "", fmt.Errorf("%s %s: %w", envVar, path, err)
	}
	if !info.Mode().IsRegular() {
		return "", fmt.Errorf("%s %s is not a regular file", envVar, path)
	}
	// Protecting a plaintext file is not encryption; it only keeps other
	// local accounts from reading it. Windows does not carry these bits.
	if runtime.GOOS != "windows" && info.Mode().Perm()&0o077 != 0 {
		return "", fmt.Errorf("%s %s is readable by group or others (mode %04o); run: chmod 600 %s",
			envVar, path, info.Mode().Perm(), path)
	}
	if info.Size() > maxKeyFileBytes {
		return "", fmt.Errorf("%s %s is %d bytes, over the %d byte limit; this is probably not a key file",
			envVar, path, info.Size(), maxKeyFileBytes)
	}

	// One byte past the limit distinguishes "exactly at the limit" from
	// "truncated", for a file that grew after the stat above.
	b, err := io.ReadAll(io.LimitReader(f, maxKeyFileBytes+1))
	if err != nil {
		return "", fmt.Errorf("%s %s: %w", envVar, path, err)
	}
	if len(b) > maxKeyFileBytes {
		return "", fmt.Errorf("%s %s is over the %d byte limit", envVar, path, maxKeyFileBytes)
	}

	// A file written by an editor or a heredoc ends with a newline. That one
	// terminator is expected and removed; anything else is left in place for
	// parseKey to reject, rather than trimmed into a different credential.
	s := strings.TrimSuffix(string(b), "\n")
	s = strings.TrimSuffix(s, "\r")

	key, err := parseKey(s)
	if err != nil {
		return "", fmt.Errorf("%s %s %w", envVar, path, err)
	}
	return key, nil
}

// The reasons a candidate key is rejected. They are package-level values built
// from constants, so no error parseKey returns can be derived from the key it
// was given. That is the property TestKeyErrorsNeverQuoteTheValue asserts, and
// stating it in the type rather than in each return makes it checkable by
// reading one block instead of auditing every path.
var (
	errKeyEmpty       = errors.New("is empty")
	errKeyWhitespace  = errors.New("has leading or trailing whitespace")
	errKeyControlChar = errors.New("contains a control character")
	errKeyPlaceholder = errors.New("is an unexpanded ${...} placeholder")
)

// errNoCredential marks the one loadCredential failure that is not about a
// bad value: nothing was set at all. It lets a caller choose its own wording
// without reading the error text.
var errNoCredential = errors.New("no credential")

// parseKey validates a candidate key. It never includes the value in an error:
// an error message travels further than the operator expects.
//
// No provider key prefix is enforced. Key formats change, and a fork that
// guesses at one rejects a valid new key for no benefit.
func parseKey(s string) (credential, error) {
	if s == "" {
		return "", errKeyEmpty
	}
	if s != strings.TrimSpace(s) {
		// Not trimmed silently: leading or trailing space usually means a
		// copy-paste error, and sending the trimmed value would hide it.
		return "", errKeyWhitespace
	}
	// A header value cannot hold these, and a newline in particular would let
	// a malformed key inject a second header.
	for _, r := range s {
		if r < 0x20 || r == 0x7f {
			return "", errKeyControlChar
		}
	}
	// The usual sign that a config template was copied without substitution.
	if strings.HasPrefix(s, "${") && strings.HasSuffix(s, "}") {
		return "", errKeyPlaceholder
	}
	return credential(s), nil
}
