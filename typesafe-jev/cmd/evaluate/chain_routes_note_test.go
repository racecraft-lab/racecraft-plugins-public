package main

import (
	"strings"
	"testing"
)

// The trust sentence names capability routes: state reaches the fallback when
// the first backend cannot take a request, not only when it fails.
func TestInstructionsNameCapabilityRoutes(t *testing.T) {
	cfg := Config{Provider: providers["typesafe"], Fallback: &FallbackConfig{Provider: providers["openrouter"]}}
	if note := backendNote(cfg); !strings.Contains(note, "or cannot take the request") {
		t.Errorf("note does not name capability routes:\n%s", note)
	}
}
