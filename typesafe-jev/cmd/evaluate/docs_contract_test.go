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
