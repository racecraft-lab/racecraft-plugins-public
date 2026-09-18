package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// repoRoot returns the repository root from the package directory.
func repoRoot(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs(filepath.Join("..", ".."))
	if err != nil {
		t.Fatal(err)
	}
	return root
}

// shellPath resolves sh from PATH rather than assuming /bin/sh, and skips the
// test where no shell exists, so these run on more than one layout.
func shellPath(t *testing.T) string {
	t.Helper()
	sh, err := exec.LookPath("sh")
	if err != nil {
		t.Skipf("no sh on PATH: %v", err)
	}
	return sh
}

func readJSON(t *testing.T, path string) map[string]any {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("%s: %v", path, err)
	}
	var doc map[string]any
	if err := json.Unmarshal(b, &doc); err != nil {
		t.Fatalf("%s is not valid JSON: %v", path, err)
	}
	return doc
}

// Every manifest must parse and every path it points at must exist. A plugin
// that names a missing file fails at install time, in someone else's client,
// with an error that does not say which manifest was wrong.
func TestPluginManifestsResolve(t *testing.T) {
	root := repoRoot(t)

	for _, manifest := range []string{
		".claude-plugin/plugin.json",
		".claude-plugin/marketplace.json",
		".codex-plugin/plugin.json",
		"mcp/claude.json",
		".mcp.json",
	} {
		doc := readJSON(t, filepath.Join(root, manifest))
		if len(doc) == 0 {
			t.Errorf("%s is empty", manifest)
		}
	}

	for _, client := range []string{".claude-plugin/plugin.json", ".codex-plugin/plugin.json"} {
		doc := readJSON(t, filepath.Join(root, client))

		skills, _ := doc["skills"].([]any)
		if len(skills) == 0 {
			t.Errorf("%s declares no skills", client)
		}
		for i, entry := range skills {
			// Checked, not asserted: a non-string entry should name the file
			// and index that is wrong, rather than panicking somewhere in the
			// middle of the run.
			path, ok := entry.(string)
			if !ok {
				t.Errorf("%s: skills[%d] is %T, want a string", client, i, entry)
				continue
			}
			dir := filepath.Join(root, filepath.Clean(path))
			if info, err := os.Stat(dir); err != nil || !info.IsDir() {
				t.Errorf("%s: skills path %q does not resolve to a directory", client, path)
			}
		}

		servers, _ := doc["mcpServers"].(string)
		if servers == "" {
			t.Errorf("%s declares no mcpServers file", client)
			continue
		}
		if _, err := os.Stat(filepath.Join(root, filepath.Clean(servers))); err != nil {
			t.Errorf("%s: mcpServers path %q does not exist", client, servers)
		}
	}

	// Both clients must agree on the plugin name and version, or an operator
	// ends up with two differently-versioned installs of the same thing.
	claude := readJSON(t, filepath.Join(root, ".claude-plugin/plugin.json"))
	codex := readJSON(t, filepath.Join(root, ".codex-plugin/plugin.json"))
	for _, key := range []string{"name", "version", "repository"} {
		if claude[key] != codex[key] {
			t.Errorf("%s differs: claude=%v codex=%v", key, claude[key], codex[key])
		}
	}
}

// The MCP entries must launch the shipped launcher, name the backend
// explicitly, and carry no credential. A key in a committed manifest is a key
// in everyone's checkout.
func TestPluginMCPEntries(t *testing.T) {
	root := repoRoot(t)

	for _, tc := range []struct{ file, wantCommand string }{
		{"mcp/claude.json", "${CLAUDE_PLUGIN_ROOT}/bin/evaluate-launch"},
		{".mcp.json", "bin/evaluate-launch"},
	} {
		doc := readJSON(t, filepath.Join(root, tc.file))
		servers, _ := doc["mcpServers"].(map[string]any)
		if len(servers) != 1 {
			t.Errorf("%s: want exactly one server, got %d", tc.file, len(servers))
			continue
		}
		entry, _ := servers["jev"].(map[string]any)
		if entry == nil {
			t.Errorf("%s: no server named jev", tc.file)
			continue
		}
		if got, _ := entry["command"].(string); got != tc.wantCommand {
			t.Errorf("%s: command = %q, want %q", tc.file, got, tc.wantCommand)
		}

		env, _ := entry["env"].(map[string]any)
		if got, _ := env["JEV_PROVIDER"].(string); got != "openrouter" {
			t.Errorf("%s: JEV_PROVIDER = %q, want openrouter", tc.file, got)
		}
		// The binary's own default stays typesafe; the plugin opts in rather
		// than the server guessing from which keys are set.
		if providers["typesafe"].Name != "typesafe" {
			t.Fatal("provider table changed")
		}
		for key := range env {
			if strings.Contains(key, "API_KEY") && !strings.HasSuffix(key, "_FILE") {
				t.Errorf("%s: env carries a credential variable %q", tc.file, key)
			}
		}
		raw, err := os.ReadFile(filepath.Join(root, tc.file))
		if err != nil {
			t.Fatal(err)
		}
		for _, secretish := range []string{"sk-", "sk-or-", "Bearer "} {
			if strings.Contains(string(raw), secretish) {
				t.Errorf("%s looks like it contains a credential", tc.file)
			}
		}
	}
}

// The vendored skill must keep its upstream licence and provenance, and must
// carry the two Racecraft additions that make it agree with this server.
func TestVendoredSkillKeepsProvenance(t *testing.T) {
	root := filepath.Join(repoRoot(t), "shared-skills", "typesafe-ai")

	license, err := os.ReadFile(filepath.Join(root, "LICENSE"))
	if err != nil {
		t.Fatalf("vendored skill has no LICENSE: %v", err)
	}
	if !strings.Contains(string(license), "TypeSafe AI") {
		t.Error("LICENSE does not credit TypeSafe AI")
	}

	b, err := os.ReadFile(filepath.Join(root, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	skill := string(b)

	for _, want := range []string{
		"typesafe-ai/skills",      // where it came from
		"version 0.5.7",           // which version
		"Make the judgment now",   // the addition that routes to the tool
		"`evaluate`",              // names the tool
		"JEV_PROVIDER=openrouter", // the OpenRouter string constraint
		"Install this plugin",     // the collision warning
	} {
		if !strings.Contains(skill, want) {
			t.Errorf("vendored SKILL.md is missing %q", want)
		}
	}

	// Upstream's own guidance must survive the adaptation.
	for _, want := range []string{
		"System One",
		"docs.typesafe.ai/llms.txt",
		"no separate confidence",
	} {
		if !strings.Contains(skill, want) {
			t.Errorf("vendored SKILL.md lost upstream guidance %q", want)
		}
	}
}

// The launcher is the plugin's only moving part, so its two paths are checked
// against a fake binary rather than a real install.
func TestLauncherResolvesTheBinary(t *testing.T) {
	launcher := filepath.Join(repoRoot(t), "bin", "evaluate-launch")
	if info, err := os.Stat(launcher); err != nil || info.Mode().Perm()&0o111 == 0 {
		t.Fatalf("launcher missing or not executable: %v", err)
	}

	t.Run("missing binary reports on stderr and fails", func(t *testing.T) {
		cmd := exec.Command(shellPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+filepath.Join(t.TempDir(), "absent"))
		var stdout, stderr strings.Builder
		cmd.Stdout, cmd.Stderr = &stdout, &stderr

		err := cmd.Run()
		if err == nil {
			t.Fatal("want a non-zero exit when the binary is missing")
		}
		// Stdout carries the MCP protocol. A human-readable line there is a
		// frame the client cannot parse.
		if stdout.String() != "" {
			t.Errorf("launcher wrote to stdout: %q", stdout.String())
		}
		if !strings.Contains(stderr.String(), "install.sh") {
			t.Errorf("stderr should say how to install: %q", stderr.String())
		}
	})

	t.Run("present binary is exec'd with the key-file default", func(t *testing.T) {
		dir := t.TempDir()
		fake := filepath.Join(dir, "evaluate")
		script := "#!/bin/sh\necho \"args=$*\"\necho \"keyfile=$JEV_API_KEY_FILE\"\n"
		if err := os.WriteFile(fake, []byte(script), 0o755); err != nil {
			t.Fatal(err)
		}

		cmd := exec.Command(shellPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+fake, "HOME="+dir)
		out, err := cmd.Output()
		if err != nil {
			t.Fatalf("%v", err)
		}
		got := string(out)
		if !strings.Contains(got, "args=mcp") {
			t.Errorf("launcher did not pass `mcp`: %q", got)
		}
		if !strings.Contains(got, filepath.Join(dir, ".config", "racecraft-jev", "openrouter.key")) {
			t.Errorf("key-file default not applied: %q", got)
		}
	})

	t.Run("an explicit key file is not overridden", func(t *testing.T) {
		dir := t.TempDir()
		fake := filepath.Join(dir, "evaluate")
		if err := os.WriteFile(fake, []byte("#!/bin/sh\necho \"keyfile=$JEV_API_KEY_FILE\"\n"), 0o755); err != nil {
			t.Fatal(err)
		}
		cmd := exec.Command(shellPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+fake, "HOME="+dir,
			"JEV_API_KEY_FILE=/somewhere/else.key")
		out, err := cmd.Output()
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(out), "keyfile=/somewhere/else.key") {
			t.Errorf("launcher overrode an explicit key file: %q", out)
		}
	})
}
