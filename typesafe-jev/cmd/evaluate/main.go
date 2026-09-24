// Command evaluate is an MCP stdio server for running TypeSafe Jev prompts.
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"os"
	"os/signal"
	"runtime/debug"
	"syscall"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
	"github.com/spf13/cobra"
)

// version is set by release builds via -ldflags "-X main.version=...".
var version = "dev"

func init() {
	if info, ok := debug.ReadBuildInfo(); ok && version == "dev" && info.Main.Version != "" && info.Main.Version != "(devel)" {
		version = info.Main.Version
	}
}

const instructions = `The evaluate tool runs Jev, a TypeSafe System One model that returns typed judgments and probabilities, not generated text.
- Question types: noul (probability a yes/no condition holds), choice (one option from a criteria map), score (probability-weighted position on ordered criteria levels).
- Ask one narrow judgment per question. Question ids are NOT sent to the model, so instructions must carry the full meaning.
- Put everything the judgment needs in state; prefer a JSON object with named fields, and reference nested fields with backticked paths like ` + "`ticket.messages[0].text`" + `.
- Batch independent questions over the same state into one call; they run in parallel and cannot see each other's answers.
- Include a no-match option in a choice when nothing may fit. Score levels must describe concrete situations.
- A noul near 0.5 means uncertain, not medium intensity. Confidence measures how concentrated the distribution is, not correctness.
Docs: https://docs.typesafe.ai/llms.txt`

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	code := execute(ctx, os.Args[1:])
	stop()
	os.Exit(code)
}

// execute runs the command line args and returns the process exit code. Most
// failures exit 1; `call` chooses its own codes, and has usually said what went
// wrong already.
func execute(ctx context.Context, args []string) int {
	root := newRootCmd()
	root.SetArgs(args)
	err := root.ExecuteContext(ctx)
	var exit *exitCodeError
	switch {
	case err == nil:
		return 0
	case errors.As(err, &exit):
		if exit.text != "" {
			fmt.Fprintln(os.Stderr, "evaluate:", exit.text)
		}
		return exit.code
	default:
		fmt.Fprintln(os.Stderr, "evaluate:", err)
		return 1
	}
}

func newRootCmd() *cobra.Command {
	root := &cobra.Command{
		Use:     "evaluate",
		Short:   "MCP server for TypeSafe Jev prompts",
		Version: version,
		// Stdout carries the MCP protocol; main reports errors on stderr.
		SilenceUsage:  true,
		SilenceErrors: true,
	}
	root.SetVersionTemplate("{{.Version}}\n")
	var pluginDefaults bool
	mcpCmd := &cobra.Command{Use: "mcp", Short: "Run the MCP server over stdio", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, _ []string) error {
		return serve(cmd.Context(), pluginDefaults)
	}}
	mcpCmd.Flags().BoolVar(&pluginDefaults, "plugin-defaults", false,
		"default each unset key-file path to "+pluginKeyDirectory+"/<provider>.key, only when that file exists")
	// Args+RunE, not a bare parent: cobra checks Runnable before validating args,
	// so without both `evaluate setup typo` prints help and exits 0.
	setupCmd := &cobra.Command{
		Use:   "setup",
		Short: "Register this binary with your agents",
		Args:  cobra.NoArgs,
		RunE:  func(cmd *cobra.Command, _ []string) error { return cmd.Help() },
	}
	setupCmd.AddCommand(
		newMCPSetupCmd(),
		&cobra.Command{
			Use:   "pi",
			Short: "Install the evaluate extension for pi",
			Args:  cobra.NoArgs,
			RunE: func(*cobra.Command, []string) error {
				return runPiSetup()
			},
		},
	)
	root.AddCommand(
		mcpCmd,
		newCallCmd(),
		setupCmd,
		&cobra.Command{Use: "update", Short: "Update evaluate to the newest typesafe-jev release", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, _ []string) error {
			return runUpdate(cmd.Context())
		}},
		newVersionCmd(),
	)
	return root
}

func newVersionCmd() *cobra.Command {
	var verbose bool
	cmd := &cobra.Command{
		Use:   "version",
		Short: "Print the version",
		Args:  cobra.NoArgs,
		Run: func(cmd *cobra.Command, _ []string) {
			out := cmd.OutOrStdout()
			if !verbose {
				fmt.Fprintln(out, version)
				return
			}
			// Which build this is and where it came from, so an operator can
			// tell a Racecraft install from an upstream one without a network
			// call or a credential.
			fmt.Fprintln(out, "version:   ", version)
			fmt.Fprintln(out, "repository:", githubRepo)
			fmt.Fprintln(out, "commit:    ", buildCommit())
		},
	}
	cmd.Flags().BoolVar(&verbose, "verbose", false, "also print the source repository and build commit")
	return cmd
}

// buildCommit reports the VCS revision stamped into the binary, or "unknown"
// for a build made outside a repository.
func buildCommit() string {
	info, ok := debug.ReadBuildInfo()
	if !ok {
		return "unknown"
	}
	for _, s := range info.Settings {
		if s.Key == "vcs.revision" {
			return s.Value
		}
	}
	return "unknown"
}

// newClient builds the HTTP client for cfg. The credential is loaded here and
// nowhere else, so there is exactly one place a key enters the process.
//
// Unlike the version this fork was taken from, the backend comes from
// JEV_PROVIDER rather than from whichever API key happens to be set. Which
// credentials are lying around in a shell should not decide where state is
// sent, or which account pays for it. See docs/upstream-baseline.md.
func newClient(cfg Config) (*Client, error) {
	key, err := loadCredential(cfg)
	if err != nil {
		return nil, err
	}
	return &Client{
		Provider:   cfg.Provider,
		Model:      cfg.Model,
		APIKey:     key,
		Timeout:    cfg.Timeout,
		MaxRetries: cfg.MaxRetries,
		HTTP:       newHTTPClient(),
		Backoff:    time.Second,
	}, nil
}

// newClients builds the primary client and, when the operator configured one,
// its fallback. It returns the Config that describes what will actually serve,
// so the server's instructions name the destination in force.
//
// A primary whose credential cannot be loaded, such as a missing key file,
// starts on the fallback outright. A fallback whose credential cannot be
// loaded is dropped with a line on log, and the primary serves alone. Only
// when neither loads does the server refuse to start, naming both.
func newClients(cfg Config, log io.Writer) (*Client, Config, error) {
	primary, primaryErr := newClient(cfg)
	if cfg.Fallback == nil {
		return primary, cfg, primaryErr
	}
	fallbackCfg := cfg.fallbackConfig()
	fallback, fallbackErr := newClient(fallbackCfg)
	switch {
	case primaryErr == nil && fallbackErr == nil:
		primary.Fallback = fallback
		primary.Log = log
		return primary, cfg, nil
	case primaryErr == nil:
		fmt.Fprintf(log, "evaluate: the %s fallback is off: %v\n", fallbackCfg.Provider.Name, fallbackErr)
		cfg.Fallback = nil
		return primary, cfg, nil
	case fallbackErr == nil:
		fmt.Fprintf(log, "evaluate: %v; using the %s fallback\n", primaryErr, fallbackCfg.Provider.Name)
		return fallback, fallbackCfg, nil
	default:
		return nil, cfg, fmt.Errorf("%w; the %s fallback cannot start either: %v", primaryErr, fallbackCfg.Provider.Name, fallbackErr)
	}
}

// newServer registers the tools for cfg's backend against c. Split out from
// serve so a test can drive the real registration without a transport or a
// provider.
func newServer(cfg Config, c *Client) *mcp.Server {
	s := mcp.NewServer(
		&mcp.Implementation{Name: "evaluate", Version: version},
		&mcp.ServerOptions{Instructions: instructions + backendNote(cfg)},
	)
	registerTools(s, cfg, c)
	return s
}

// backendNote appends what differs about the configured backend.
//
// The structured instructions and criteria that TypeSafe's documentation, and
// the agent skill built from it, teach now work on both backends, so there is
// no longer a warning to give about writing them.
//
// What does still differ is the reply. OpenRouter's Decisions schemas mark
// confidence and probabilities optional on choice and score answers, where
// TypeSafe always sends them. An agent that branches on a number which is
// simply absent misreads the answer, so the note says so up front.
func backendNote(cfg Config) string {
	note := "\nBackend: " + cfg.Provider.Name + ". Calling this tool sends the state and questions" +
		" you pass to that provider, which bills for the call."
	if cfg.Fallback != nil {
		note = "\nBackend: " + cfg.Provider.Name + ", with " + cfg.Fallback.Provider.Name + " as fallback." +
			" Calling this tool sends the state and questions you pass to " + cfg.Provider.Name +
			", or to " + cfg.Fallback.Provider.Name + " when " + cfg.Provider.Name + " refuses its credential" +
			" or is unavailable; the provider that answers bills for the call."
	}
	if cfg.Provider.Name == "openrouter" || (cfg.Fallback != nil && cfg.Fallback.Provider.Name == "openrouter") {
		note += "\nThis backend may omit confidence and probabilities from a choice or score" +
			" answer, which the TypeSafe backend always sends. Treat an absent field as" +
			" absent: do not substitute a default before branching on it."
	}
	return note
}

// setupInstructions is what the plugin's server says, with no tools, when no
// credential source is configured at all.
const setupInstructions = `Jev has no TypeSafe or OpenRouter credential on this machine, so this server offers no tools.
To enable the evaluate tool:
1. Put a TypeSafe key in ~/.config/racecraft-jev/typesafe.key, or an OpenRouter key in ~/.config/racecraft-jev/openrouter.key, readable only by you (chmod 600).
2. Reconnect this MCP server.
Until then, make any judgment yourself in the ordinary way.`

// newSetupServer is the server `mcp --plugin-defaults` runs when nothing is
// configured: connected, with no tools, and instructions that say how to set
// Jev up. A user without a key then sees a server that explains itself
// rather than one that failed to start.
func newSetupServer() *mcp.Server {
	return mcp.NewServer(
		&mcp.Implementation{Name: "evaluate", Version: version},
		&mcp.ServerOptions{
			Instructions: setupInstructions,
			// Advertised, with an empty list, so a client that asks for tools
			// gets none rather than an error.
			Capabilities: &mcp.ServerCapabilities{Tools: &mcp.ToolCapabilities{}},
		},
	)
}

// serve runs the MCP server over stdio. With pluginDefaults it also applies
// the plugin's key-file defaults and, when no credential source exists at
// all, serves the setup instructions instead of refusing to start. A source
// that exists but is broken still refuses, naming the fix.
func serve(ctx context.Context, pluginDefaults bool) error {
	cfg, err := resolveCallConfig(os.LookupEnv, pluginDefaults)
	if err != nil {
		return err
	}
	if pluginDefaults {
		primary, fallback := classifySources(cfg, os.LookupEnv)
		if credentialExit(primary, fallback) == exitUnconfigured {
			fmt.Fprintln(os.Stderr, "evaluate: no TypeSafe or OpenRouter credential is configured; serving setup instructions with no tools")
			return newSetupServer().Run(ctx, &mcp.StdioTransport{})
		}
	}
	c, cfg, err := newClients(cfg, os.Stderr)
	if err != nil {
		return err
	}
	// Nothing is printed here: stdout carries the MCP protocol, and a startup
	// banner on it is a protocol error.
	return newServer(cfg, c).Run(ctx, &mcp.StdioTransport{})
}
