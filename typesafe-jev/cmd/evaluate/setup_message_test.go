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
	for _, tc := range []struct {
		name, chain string
		want        []string
		wantNone    []string
	}{
		{
			name: "built-in chain",
			want: []string{
				"no TypeSafe or OpenRouter credential",
				"a TypeSafe key in ~/.config/racecraft-jev/typesafe.key, or an OpenRouter key in ~/.config/racecraft-jev/openrouter.key",
			},
			wantNone: []string{"Ollama"},
		},
		{
			name:     "ollama only",
			chain:    "ollama",
			want:     []string{"no Ollama Cloud credential", "an Ollama Cloud key in ~/.config/racecraft-jev/ollama.key"},
			wantNone: []string{"TypeSafe", "OpenRouter"},
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			isolateCallEnv(t)
			if tc.chain != "" {
				t.Setenv("JEV_CHAIN", tc.chain)
			}
			resolved, err := resolveHops(os.LookupEnv, true)
			if err != nil {
				t.Fatal(err)
			}
			if code := resolved.credentialExit(); code != exitUnconfigured {
				t.Fatalf("credentialExit = %d, want exitUnconfigured", code)
			}
			text := setupInstructions(resolved)
			for _, want := range append(tc.want, "chmod 600", "Reconnect") {
				if !strings.Contains(text, want) {
					t.Errorf("setup text does not say %q:\n%s", want, text)
				}
			}
			for _, unwanted := range tc.wantNone {
				if strings.Contains(text, unwanted) {
					t.Errorf("setup text names %q:\n%s", unwanted, text)
				}
			}
			if !strings.Contains(text, missingCredentials(resolved)) {
				t.Errorf("the log line and the setup text name different backends: %q", missingCredentials(resolved))
			}
		})
	}
}
