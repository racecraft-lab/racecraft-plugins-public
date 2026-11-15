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

// A chain of three or more hops names every hop in order, and each distinct
// answer note appears once.
func TestInstructionsNameEveryHopInOrder(t *testing.T) {
	cfg := Config{Provider: providers["typesafe"], Fallback: &FallbackConfig{Provider: providers["openrouter"]},
		AdditionalHops: []Config{{Provider: providers["ollama"]}}}
	note := backendNote(cfg)
	if !strings.Contains(note, "Backend: typesafe, then openrouter, then ollama.") ||
		!strings.Contains(note, "or to the next backend in that order") {
		t.Errorf("note does not list the chain:\n%s", note)
	}
	if n := strings.Count(note, providers["ollama"].AnswerNote); n != 1 {
		t.Errorf("ollama answer note appears %d times:\n%s", n, note)
	}
}
