package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// repoDoc reads a document by its path from the repository root, with runs of
// whitespace collapsed so a wrapped sentence still matches. A missing file
// fails the test: a doc contract never passes on nothing.
func repoDoc(t *testing.T, path string) string {
	t.Helper()
	data, err := os.ReadFile(filepath.Join("..", "..", "..", filepath.FromSlash(path)))
	if err != nil {
		t.Fatalf("reading %s: %v", path, err)
	}
	return strings.Join(strings.Fields(string(data)), " ")
}

// requireDocText fails for each wanted passage the document lacks.
func requireDocText(t *testing.T, path string, wants ...string) {
	t.Helper()
	doc := repoDoc(t, path)
	for _, want := range wants {
		if !strings.Contains(doc, want) {
			t.Errorf("%s does not contain %q", path, want)
		}
	}
}

// #1436: the request-shape owner holds the universal shape; per-hop limits
// live with the backend rows (ADR 0028).
func TestAgentsNamesUniversalRequestShapeOwner(t *testing.T) {
	doc := repoDoc(t, "AGENTS.md")
	if strings.Contains(doc, "the one request shape both backends take") {
		t.Error("AGENTS.md still says the request-shape owner holds the one shape both backends take")
	}
	requireDocText(t, "AGENTS.md", "`validation.go` for universal request shape and `config.go` for backend specs and per-hop limits")
}

// The CLI names any chain hop, including chains longer than a provider pair.
func TestCallHelpNamesBackendChain(t *testing.T) {
	if !strings.Contains(newCallCmd().Long, "no credential source configured for a backend in the chain") {
		t.Error("call help must describe exit 3 without assuming a primary/fallback pair")
	}
}
