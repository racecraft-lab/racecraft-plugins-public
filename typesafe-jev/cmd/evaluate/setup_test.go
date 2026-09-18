package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func setupConfig(t *testing.T, provider, keyFile string) Config {
	t.Helper()
	e := map[string]string{"JEV_PROVIDER": provider}
	if keyFile != "" {
		e["JEV_API_KEY_FILE"] = keyFile
	}
	cfg, err := resolveConfig(envLookup(e))
	if err != nil {
		t.Fatal(err)
	}
	return cfg
}

func generate(t *testing.T, cfg Config, exe string, opts setupOptions) string {
	t.Helper()
	var out strings.Builder
	if err := runMCPSetup(&out, cfg, exe, opts); err != nil {
		t.Fatal(err)
	}
	return out.String()
}

// SET-01: the generated commands name the requested clients, server name, and
// key-file path, and are quoted so a shell reproduces them exactly.
func TestSetupGeneratesBothClients(t *testing.T) {
	const keyFile = "/Users/someone/.config/racecraft-jev/openrouter.key"
	cfg := setupConfig(t, "openrouter", keyFile)
	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{
		clients: []string{"claude-code", "codex"},
		name:    "jev-openrouter",
		keyFile: keyFile,
	})

	for _, want := range []string{
		"claude mcp add 'jev-openrouter'",
		"codex mcp add 'jev-openrouter'",
		"-- '/opt/racecraft/evaluate' mcp",
		"'JEV_PROVIDER=openrouter'",
		"'JEV_API_KEY_FILE=" + keyFile + "'",
		"[mcp_servers.jev-openrouter]",
		"claude mcp remove 'jev-openrouter' --scope user",
		"codex mcp remove 'jev-openrouter'",
	} {
		if !strings.Contains(got, want) {
			t.Errorf("output is missing %q:\n%s", want, got)
		}
	}

	// The model id starts with a tilde, which an unquoted shell word would
	// expand to a home directory.
	if !strings.Contains(got, `'JEV_MODEL=~typesafe/jev-latest'`) {
		t.Errorf("model is not shell-quoted:\n%s", got)
	}
}

// SET-02: a key set in the parent environment must not reach the generated
// configuration. Copying it there writes it into a file with ordinary
// permissions, and into every backup of that file.
func TestSetupNeverPrintsASecret(t *testing.T) {
	const secret = "sk-or-v1-must-not-appear"
	t.Setenv("OPENROUTER_API_KEY", secret)
	t.Setenv("TYPESAFE_API_KEY", secret)
	t.Setenv("TYPESAFE_SOMETHING_ELSE", secret)

	keyFile := writeKeyFile(t, secret+"\n", 0o600)
	cfg := setupConfig(t, "openrouter", keyFile)

	for _, opts := range []setupOptions{
		{clients: []string{"claude-code"}},
		{clients: []string{"codex"}},
		{clients: []string{"claude-code", "codex"}, keyFile: keyFile},
	} {
		got := generate(t, cfg, "/opt/racecraft/evaluate", opts)
		if strings.Contains(got, secret) {
			t.Fatalf("generated config contains the key:\n%s", got)
		}
		// Nor the bulk-captured variables upstream copied wholesale.
		for _, leaked := range []string{"TYPESAFE_SOMETHING_ELSE", "OPENROUTER_API_KEY="} {
			if strings.Contains(got, leaked) {
				t.Errorf("generated config captured %q:\n%s", leaked, got)
			}
		}
		// The path is fine; the contents are not.
		if !strings.Contains(got, keyFile) {
			t.Errorf("output should reference the key-file path:\n%s", got)
		}
	}
}

// SET-03: no client means guidance, and a malformed name or relative key-file
// path is an error. Neither produces configuration.
func TestSetupRejectsBadInputAndDefaultsSafely(t *testing.T) {
	cfg := setupConfig(t, "openrouter", "")

	none := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{})
	if !strings.Contains(none, "No client selected") || strings.Contains(none, "claude mcp add") {
		t.Errorf("no client should print guidance only:\n%s", none)
	}

	for _, opts := range []setupOptions{
		{clients: []string{"claude-code"}, name: "jev openrouter"},
		{clients: []string{"claude-code"}, name: "jev/openrouter"},
		{clients: []string{"claude-code"}, name: "jev;rm -rf /"},
		{clients: []string{"claude-code"}, keyFile: "relative/openrouter.key"},
		{clients: []string{"claude-desktop"}},
		{clients: []string{"cursor"}},
	} {
		var out strings.Builder
		if err := runMCPSetup(&out, cfg, "/opt/racecraft/evaluate", opts); err == nil {
			t.Errorf("%+v: want an error, got:\n%s", opts, out.String())
		}
	}

	// The default name is per backend and collides with neither upstream's
	// "evaluate" entry nor the pre-rename "jev" one.
	for provider, want := range map[string]string{
		"openrouter": "jev-openrouter",
		"typesafe":   "jev-typesafe",
	} {
		got := generate(t, setupConfig(t, provider, ""), "/opt/racecraft/evaluate",
			setupOptions{clients: []string{"claude-code"}})
		if !strings.Contains(got, "claude mcp add '"+want+"'") {
			t.Errorf("%s default name is not %q:\n%s", provider, want, got)
		}
		for _, colliding := range []string{"add 'evaluate'", "add 'jev'"} {
			if strings.Contains(got, colliding) {
				t.Errorf("%s generated a colliding name (%s)", provider, colliding)
			}
		}
	}
}

// SET-04: generating configuration changes nothing on disk. Upstream's setup
// ran the client CLIs and rewrote Claude Desktop's config file, which also
// holds the user's preferences.
func TestSetupMutatesNothing(t *testing.T) {
	home := t.TempDir()
	t.Setenv("HOME", home)
	t.Setenv("CLAUDE_CONFIG_DIR", home)

	files := map[string]string{
		".claude.json": `{"mcpServers":{"lumi":{"command":"/bin/lumi"}},"preferences":{"theme":"dark"}}`,
		"config.toml":  "[mcp_servers.other]\ncommand = \"/bin/other\"\n",
		"claude_desktop_config.json": `{"mcpServers":{"evaluate":{"command":"/old"}},` +
			`"preferences":{"sidebarMode":"chat"}}`,
	}
	before := map[string]string{}
	for name, body := range files {
		path := filepath.Join(home, name)
		if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
			t.Fatal(err)
		}
		before[path] = body
	}

	cfg := setupConfig(t, "openrouter", "")
	generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"claude-code", "codex"}})

	for path, want := range before {
		got, err := os.ReadFile(path)
		if err != nil {
			t.Fatalf("%s: %v", path, err)
		}
		if string(got) != want {
			t.Errorf("%s was modified:\n got %s\nwant %s", path, got, want)
		}
	}

	entries, err := os.ReadDir(home)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != len(files) {
		t.Errorf("setup created or removed files: %d entries, want %d", len(entries), len(files))
	}
}

// The generated Codex snippet has to be a table an operator can paste. Quoting
// a Windows-style path with backslashes is the case a naive quoter gets wrong.
func TestCodexSnippetEscapesPaths(t *testing.T) {
	cfg := setupConfig(t, "openrouter", "")
	got := generate(t, cfg, `C:\Program Files\racecraft\evaluate.exe`,
		setupOptions{clients: []string{"codex"}})

	var command string
	for _, line := range strings.Split(got, "\n") {
		if after, ok := strings.CutPrefix(line, "command = "); ok {
			command = after
			break
		}
	}
	if command == "" {
		t.Fatalf("no command line in:\n%s", got)
	}
	var decoded string
	if err := json.Unmarshal([]byte(command), &decoded); err != nil {
		t.Fatalf("command %s is not a valid quoted string: %v", command, err)
	}
	if decoded != `C:\Program Files\racecraft\evaluate.exe` {
		t.Errorf("command decoded to %q", decoded)
	}
}

// KEY-05: generating configuration works with no credential available at all.
// It is a documentation command, not a reason to touch a secret.
func TestSetupNeedsNoCredential(t *testing.T) {
	t.Setenv("OPENROUTER_API_KEY", "")
	t.Setenv("TYPESAFE_API_KEY", "")

	// A key file that exists but cannot be read must not be opened either.
	unreadable := writeKeyFile(t, "k\n", 0o000)
	cfg := setupConfig(t, "openrouter", unreadable)

	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"claude-code"}})
	if !strings.Contains(got, "claude mcp add") {
		t.Errorf("setup failed without a credential:\n%s", got)
	}
}

// A non-default timeout or retry count is carried into the generated config,
// so the printed commands reproduce the environment they were generated in.
func TestSetupCarriesTunedSettings(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER":        "openrouter",
		"JEV_REQUEST_TIMEOUT": "90s",
		"JEV_MAX_RETRIES":     "1",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Timeout != 90*time.Second {
		t.Fatalf("timeout = %v", cfg.Timeout)
	}
	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"claude-code"}})
	for _, want := range []string{"'JEV_REQUEST_TIMEOUT=1m30s'", "'JEV_MAX_RETRIES=1'"} {
		if !strings.Contains(got, want) {
			t.Errorf("output is missing %q:\n%s", want, got)
		}
	}
}

// The generated Codex tool timeout has to exceed the server's own request
// budget. A fixed 75 seconds was wrong: JEV_REQUEST_TIMEOUT accepts up to five
// minutes, and a client that gives up first turns a slow answer into a failure.
func TestCodexToolTimeoutExceedsRequestBudget(t *testing.T) {
	for _, timeout := range []time.Duration{
		time.Second, 45 * time.Second, 90 * time.Second, maxTimeout,
	} {
		got := codexToolTimeout(timeout)
		if float64(got) <= timeout.Seconds() {
			t.Errorf("timeout %s: tool_timeout_sec %d does not exceed it", timeout, got)
		}
	}

	// And it reaches the generated snippet rather than being hard-coded.
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER":        "openrouter",
		"JEV_REQUEST_TIMEOUT": "5m",
	}))
	if err != nil {
		t.Fatal(err)
	}
	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"codex"}})
	if !strings.Contains(got, "tool_timeout_sec = 330") {
		t.Errorf("a 5m budget should generate tool_timeout_sec = 330:\n%s", got)
	}
	if strings.Contains(got, "tool_timeout_sec = 75") {
		t.Error("tool_timeout_sec is still hard-coded at 75")
	}
}

// --dry-run=false is refused rather than ignored. Accepting it and printing
// anyway would tell an operator their configuration had been applied.
func TestSetupRefusesDryRunFalse(t *testing.T) {
	cmd := newMCPSetupCmd()
	cmd.SetArgs([]string{"--client", "claude-code", "--dry-run=false"})
	var out strings.Builder
	cmd.SetOut(&out)
	cmd.SetErr(&out)

	if err := cmd.Execute(); err == nil {
		t.Fatalf("--dry-run=false was accepted; output:\n%s", out.String())
	}
}
