package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// Hops 3 and 4 have no key-file variable: JEV_API_KEY_FILE belongs to hop 1,
// so a later hop never reads it and its diagnostics never name it.
func TestLaterHopsNeverUseThePrimaryKeyFileVariable(t *testing.T) {
	home := isolateCallEnv(t)
	primaryKey := filepath.Join(t.TempDir(), "typesafe.key")
	if err := os.WriteFile(primaryKey, []byte(fixtureKey), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,ollama")
	t.Setenv("JEV_API_KEY_FILE", primaryKey)

	t.Run("absent", func(t *testing.T) {
		resolved, err := resolveHops(os.LookupEnv, true)
		if err != nil {
			t.Fatal(err)
		}
		hop := resolved.hops[2]
		if hop.config.KeyFile != "" {
			t.Fatalf("hop 3 key file = %q, want none", hop.config.KeyFile)
		}
		msg := hop.loaded.err.Error()
		if strings.Contains(msg, "JEV_API_KEY_FILE") || !strings.Contains(msg, "OLLAMA_API_KEY") ||
			!strings.Contains(msg, "~/"+pluginKeyDirectory+"/ollama.key") {
			t.Errorf("hop 3 diagnostic = %q", msg)
		}
	})

	t.Run("unusable default file", func(t *testing.T) {
		dir := filepath.Join(home, filepath.FromSlash(pluginKeyDirectory))
		if err := os.MkdirAll(dir, 0o700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "ollama.key"), []byte(fixtureKey), 0o644); err != nil {
			t.Fatal(err)
		}
		resolved, err := resolveHops(os.LookupEnv, true)
		if err != nil {
			t.Fatal(err)
		}
		hop := resolved.hops[2]
		if !hop.config.KeyFileDefaulted || hop.loaded.err == nil {
			t.Fatalf("want the discovered file rejected, got %+v", hop.loaded.status)
		}
		msg := hop.loaded.err.Error()
		if strings.Contains(msg, "JEV_API_KEY_FILE") || !strings.Contains(msg, "default key file") {
			t.Errorf("hop 3 diagnostic = %q", msg)
		}
	})
}
