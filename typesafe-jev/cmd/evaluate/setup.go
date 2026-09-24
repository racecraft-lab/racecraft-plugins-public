package main

import (
	_ "embed"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// goRunDir matches the temp directory `go run` builds into, deleted on exit.
var goRunDir = regexp.MustCompile(`/go-build\d+/`)

// serverName is what a client will call this server. Restricted so generated
// commands and TOML table headers need no escaping of their own.
var serverName = regexp.MustCompile(`^[A-Za-z0-9_-]+$`)

// evaluateBinary returns the absolute path clients should be pointed at.
func evaluateBinary() (string, error) {
	exe, err := os.Executable()
	if err != nil {
		return "", fmt.Errorf("finding current executable: %w", err)
	}
	if goRunDir.MatchString(exe) {
		return "", fmt.Errorf("refusing to configure %s: `go run` binaries are deleted on exit; build or install evaluate first", exe)
	}
	return exe, nil
}

// setupOptions is what the operator asked for on the command line.
type setupOptions struct {
	clients []string
	name    string
	keyFile string
}

// knownClients are the MCP clients this generator writes commands for. Claude
// Desktop is absent on purpose: it has no CLI, so "configuring" it meant
// rewriting a JSON file that also holds the user's preferences.
var knownClients = []string{"claude-code", "codex"}

func newMCPSetupCmd() *cobra.Command {
	var (
		opts   setupOptions
		dryRun bool
	)
	cmd := &cobra.Command{
		Use:   "mcp",
		Short: "Print the commands and config to register this binary with an agent",
		Long: "Print the commands and configuration needed to register this binary as an " +
			"MCP server.\n\nThis command changes nothing. It does not run a client CLI, edit a " +
			"configuration file, or read your API key. Review the output, then run it yourself.",
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, _ []string) error {
			// Refused rather than ignored. Accepting --dry-run=false and then
			// printing anyway would tell an operator their configuration had
			// been applied when nothing was written.
			if !dryRun {
				return fmt.Errorf("--dry-run=false is not supported: this command only ever prints configuration; run the printed commands yourself")
			}
			cfg, err := resolveConfig(os.LookupEnv)
			if err != nil {
				return err
			}
			exe, err := evaluateBinary()
			if err != nil {
				return err
			}
			return runMCPSetup(cmd.OutOrStdout(), cfg, exe, opts)
		},
	}
	cmd.Flags().StringArrayVar(&opts.clients, "client", nil,
		"client to generate for; repeatable ("+strings.Join(knownClients, ", ")+")")
	cmd.Flags().StringVar(&opts.name, "name", "",
		"server name to register (default jev-openrouter or jev-typesafe, by backend)")
	cmd.Flags().StringVar(&opts.keyFile, "key-file", "",
		"absolute path to the private key file to reference in the generated config")
	// Named for what it does, and the only mode there is. There is deliberately
	// no --apply in this release: see docs/upstream-baseline.md.
	cmd.Flags().BoolVar(&dryRun, "dry-run", true, "print configuration without changing anything (always on)")
	return cmd
}

// runMCPSetup writes the generated configuration to out. It never executes a
// client CLI or a shell, never touches a configuration file, and never reads
// or prints a credential value: only the path to one.
func runMCPSetup(out io.Writer, cfg Config, exe string, opts setupOptions) error {
	name, err := resolveServerName(opts.name, cfg.Provider)
	if err != nil {
		return err
	}
	keyFile, err := resolveSetupKeyFile(opts.keyFile, cfg.KeyFile)
	if err != nil {
		return err
	}
	clients, err := resolveClients(opts.clients)
	if err != nil {
		return err
	}
	if len(clients) == 0 {
		fmt.Fprintf(out, "No client selected. Re-run with one or more of:\n")
		for _, c := range knownClients {
			fmt.Fprintf(out, "  evaluate setup mcp --client %s\n", c)
		}
		fmt.Fprintf(out, "\nNothing was changed.\n")
		return nil
	}

	env := generatedEnv(cfg, keyFile)

	fmt.Fprintf(out, "# Generated configuration for %q. Nothing has been changed.\n", name)
	fmt.Fprintf(out, "# Review these, then run them yourself.\n\n")
	for _, client := range clients {
		switch client {
		case "claude-code":
			fmt.Fprint(out, claudeCodeSnippet(name, exe, env))
		case "codex":
			fmt.Fprint(out, codexSnippet(name, exe, env, cfg.Timeout))
		}
		fmt.Fprintln(out)
	}
	fmt.Fprint(out, credentialNote(cfg, keyFile))
	return nil
}

func resolveServerName(requested string, spec ProviderSpec) (string, error) {
	if requested == "" {
		// Not "evaluate" or "jev": a generated entry must not collide with one
		// an existing install already owns.
		return "jev-" + spec.Name, nil
	}
	if !serverName.MatchString(requested) {
		return "", fmt.Errorf("--name must contain only letters, numbers, underscores, and hyphens")
	}
	return requested, nil
}

func resolveSetupKeyFile(flag, fromEnv string) (string, error) {
	if flag == "" {
		// Falls back to whatever JEV_API_KEY_FILE already names, so generating
		// config for an existing setup reproduces it.
		return fromEnv, nil
	}
	if !filepath.IsAbs(flag) {
		return "", fmt.Errorf("--key-file must be an absolute path")
	}
	// Deliberately not read, and not required to exist: generating
	// configuration is not a reason to touch a credential.
	return flag, nil
}

func resolveClients(requested []string) ([]string, error) {
	var out []string
	for _, c := range requested {
		c = strings.TrimSpace(c)
		if c == "" {
			continue
		}
		if !contains(knownClients, c) {
			return nil, fmt.Errorf("unknown --client %q; use one of %s", c, strings.Join(knownClients, ", "))
		}
		if !contains(out, c) {
			out = append(out, c)
		}
	}
	return out, nil
}

func contains(haystack []string, needle string) bool {
	for _, s := range haystack {
		if s == needle {
			return true
		}
	}
	return false
}

type envPair struct{ key, value string }

// generatedEnv is a fixed whitelist of this server's own settings.
//
// It never enumerates the environment. Copying every TYPESAFE_*, OPENROUTER_*,
// or JEV_* variable found in the shell is how a key ends up written into
// ~/.claude.json, a backup of it, and sometimes a dotfiles repository.
func generatedEnv(cfg Config, keyFile string) []envPair {
	env := []envPair{
		{"JEV_PROVIDER", cfg.Provider.Name},
		{"JEV_MODEL", cfg.Model},
		{"JEV_REQUEST_TIMEOUT", cfg.Timeout.String()},
	}
	if cfg.MaxRetries != defaultMaxRetries {
		env = append(env, envPair{"JEV_MAX_RETRIES", fmt.Sprint(cfg.MaxRetries)})
	}
	if keyFile != "" {
		// The path, never the contents.
		env = append(env, envPair{"JEV_API_KEY_FILE", keyFile})
	}
	return env
}

func claudeCodeSnippet(name, exe string, env []envPair) string {
	var b strings.Builder
	b.WriteString("## Claude Code\n\n")
	b.WriteString("claude mcp list   # check the name is free before adding it\n\n")
	b.WriteString("claude mcp add " + shellQuote(name) + " \\\n")
	b.WriteString("  --scope user \\\n")
	b.WriteString("  --transport stdio \\\n")
	for _, p := range env {
		// One -e per pair: claude's -e is variadic, so several values after a
		// single flag can swallow the next argument.
		b.WriteString("  -e " + shellQuote(p.key+"="+p.value) + " \\\n")
	}
	b.WriteString("  -- " + shellQuote(exe) + " mcp\n\n")
	b.WriteString("claude mcp get " + shellQuote(name) + "\n")
	b.WriteString("# Rollback: claude mcp remove " + shellQuote(name) + " --scope user\n")
	return b.String()
}

func codexSnippet(name, exe string, env []envPair, timeout time.Duration) string {
	var b strings.Builder
	b.WriteString("## Codex\n\n")
	b.WriteString("codex mcp list   # `codex mcp add` overwrites an existing entry of the same name\n\n")
	b.WriteString("codex mcp add " + shellQuote(name) + " \\\n")
	for _, p := range env {
		b.WriteString("  --env " + shellQuote(p.key+"="+p.value) + " \\\n")
	}
	b.WriteString("  -- " + shellQuote(exe) + " mcp\n\n")
	b.WriteString("# Rollback: codex mcp remove " + shellQuote(name) + "\n\n")
	b.WriteString("# Equivalent ~/.codex/config.toml entry. Add only the keys you need to an\n")
	b.WriteString("# existing table; do not append a duplicate one.\n")
	b.WriteString("[mcp_servers." + name + "]\n")
	b.WriteString("command = " + tomlString(exe) + "\n")
	b.WriteString("args = [\"mcp\"]\n")
	b.WriteString("startup_timeout_sec = 10\n")
	fmt.Fprintf(&b, "tool_timeout_sec = %d\n\n", codexToolTimeout(timeout))
	b.WriteString("[mcp_servers." + name + ".env]\n")
	for _, p := range env {
		b.WriteString(p.key + " = " + tomlString(p.value) + "\n")
	}
	return b.String()
}

// codexToolTimeout returns the tool_timeout_sec to generate for a given
// request budget.
//
// A fixed 75 was wrong: JEV_REQUEST_TIMEOUT accepts up to five minutes, and a
// client that gives up at 75s while the server is still inside the budget it
// was handed turns a slow answer into a failed one. The margin covers process
// startup and the final response write, so the client is always the last to
// give up rather than the first.
func codexToolTimeout(timeout time.Duration) int {
	const marginSeconds = 30
	seconds := int(math.Ceil(timeout.Seconds()))
	if seconds < 1 {
		seconds = 1
	}
	return seconds + marginSeconds
}

// credentialNote explains where the key comes from, without printing one.
func credentialNote(cfg Config, keyFile string) string {
	if keyFile != "" {
		return fmt.Sprintf(
			"# The server reads its credential from %s at startup.\n"+
				"# That file is not read or created here. It must be a regular file readable\n"+
				"# only by you (chmod 600). Rotating the key means restarting the server.\n",
			keyFile)
	}
	return fmt.Sprintf(
		"# No key file configured, so the server will read %s from the environment\n"+
			"# the client launches it in. A client started from a desktop launcher does not\n"+
			"# inherit your shell, so add that variable to the client's own configuration, or\n"+
			"# re-run with --key-file for a path that does not depend on the environment.\n"+
			"# The key value is never printed here and must not be pasted into a config file\n"+
			"# you might commit.\n",
		cfg.Provider.APIKeyEnv)
}

// shellQuote renders s as one POSIX shell word. Single quotes stop the shell
// expanding what is inside, which matters for a model id like
// ~typesafe/jev-latest: unquoted, the leading tilde expands to a home
// directory.
func shellQuote(s string) string {
	return "'" + strings.ReplaceAll(s, "'", `'\''`) + "'"
}

// tomlString renders s as a TOML basic string. TOML and JSON agree on the
// escapes that matter here, and json.Marshal never fails on a string.
func tomlString(s string) string {
	b, _ := json.Marshal(s)
	return string(b)
}

//go:embed pi.ts
var piExtension string

// piDir returns pi's config directory. PI_CODING_AGENT_DIR wins, and a leading
// "~" is expanded because pi expands it too: taking it literally would make the
// override silently miss an existing install.
func piDir() (string, error) {
	dir := os.Getenv("PI_CODING_AGENT_DIR")
	// Only the tilde and default cases need a home directory; an explicit path
	// has to keep working where HOME is unset.
	if dir != "" && !strings.HasPrefix(dir, "~") {
		return dir, nil
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	switch {
	case dir == "":
		return filepath.Join(home, ".pi", "agent"), nil
	case dir == "~":
		return home, nil
	case strings.HasPrefix(dir, "~/"):
		return filepath.Join(home, dir[2:]), nil
	}
	return dir, nil
}

// runPiSetup installs the evaluate extension into pi. pi has no MCP client, so the
// extension registers `evaluate` as a native pi tool and speaks MCP to this
// binary itself.
func runPiSetup() error {
	exe, err := evaluateBinary()
	if err != nil {
		return err
	}
	dir, err := piDir()
	if err != nil {
		return err
	}
	if _, err := os.Stat(dir); err != nil {
		fmt.Println("➖ pi not found, skipped (see README to install by hand)")
		return nil
	}
	fmt.Println("🔎 pi detected")
	path, err := writePiExtension(dir, exe)
	if err != nil {
		return err
	}
	fmt.Printf("   wrote %s\n", path)

	fmt.Println("\n✅ Setup complete!")
	fmt.Println("Run /reload in pi, or restart it, to load the evaluate extension.")
	// Unlike the MCP clients, nothing is baked in: the extension reads the key
	// from the shell pi runs in, so a missing one is a hint, not a failure.
	if cfg, err := resolveConfig(os.LookupEnv); err != nil {
		fmt.Printf("\nNote: %v\n", err)
	} else if _, err := loadCredential(cfg); err != nil {
		fmt.Printf("\nNote: %v\n", err)
	}
	return nil
}

// writePiExtension renders the embedded extension into dir and returns its path.
func writePiExtension(dir, exe string) (string, error) {
	// json.Marshal, not a bare quoted placeholder: it escapes a path, or the
	// instructions' newlines and backticks, into a valid JS string literal.
	binary, err := json.Marshal(exe)
	if err != nil {
		return "", err
	}
	guide, err := json.Marshal(instructions)
	if err != nil {
		return "", err
	}
	src := strings.NewReplacer(
		"__EVALUATE_BINARY__", string(binary),
		"__EVALUATE_INSTRUCTIONS__", string(guide),
	).Replace(piExtension)

	out := filepath.Join(dir, "extensions")
	if err := os.MkdirAll(out, 0o755); err != nil {
		return "", err
	}
	path := filepath.Join(out, "evaluate.ts")
	if err := os.WriteFile(path, []byte(src), 0o600); err != nil {
		return "", err
	}
	// Both files register a tool named `evaluate`, so a leftover jev.ts from
	// before the rename would collide with the one just written. Removed after
	// the write, so a failed write leaves pi with the old extension, not none.
	if err := os.Remove(filepath.Join(out, "jev.ts")); err != nil && !errors.Is(err, os.ErrNotExist) {
		return path, err
	}
	return path, nil
}
