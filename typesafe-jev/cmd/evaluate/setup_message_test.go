package main

import (
	"os"
	"strings"
	"testing"
)

// The setup text names the backends the configured chain is missing a key
// for. A chain of only Ollama hops used to be told it lacked a TypeSafe or
// OpenRouter key, which it never needed.
func TestSetupInstructionsNameTheChainsMissingKeys(t *testing.T) {
	builtIn := unconfiguredSetupText(t, "")
	requireSetupText(t, builtIn, true,
		"no TypeSafe or OpenRouter credential",
		"a TypeSafe key in ~/.config/racecraft-jev/typesafe.key, or an OpenRouter key in ~/.config/racecraft-jev/openrouter.key")
	requireSetupText(t, builtIn, false, "Ollama")

	ollamaOnly := unconfiguredSetupText(t, "ollama")
	requireSetupText(t, ollamaOnly, true,
		"no Ollama Cloud credential", "an Ollama Cloud key in ~/.config/racecraft-jev/ollama.key")
	requireSetupText(t, ollamaOnly, false, "TypeSafe", "OpenRouter")
}

// unconfiguredSetupText resolves chain (the built-in one when empty) with no
// keys anywhere and returns the setup text. It also checks that the stderr
// line's backend names appear in that text, since both come from one source.
func unconfiguredSetupText(t *testing.T, chain string) string {
	t.Helper()
	isolateCallEnv(t)
	if chain != "" {
		t.Setenv("JEV_CHAIN", chain)
	}
	resolved, err := resolveHops(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	if code := resolved.credentialExit(); code != exitUnconfigured {
		t.Fatalf("credentialExit = %d, want exitUnconfigured", code)
	}
	text := setupInstructions(resolved)
	requireSetupText(t, text, true, "chmod 600", "Reconnect", missingCredentials(resolved))
	return text
}

// requireSetupText fails for each passage whose presence in text is not want.
func requireSetupText(t *testing.T, text string, want bool, passages ...string) {
	t.Helper()
	for _, passage := range passages {
		if strings.Contains(text, passage) != want {
			t.Errorf("setup text containing %q is %v, want %v:\n%s", passage, !want, want, text)
		}
	}
}
