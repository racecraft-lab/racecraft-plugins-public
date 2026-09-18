// Command evaluate is an MCP stdio server for running TypeSafe Jev prompts.
package main

import (
	"context"
	"fmt"
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
	err := newRootCmd().ExecuteContext(ctx)
	stop()
	if err != nil {
		fmt.Fprintln(os.Stderr, "evaluate:", err)
		os.Exit(1)
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
	mcpCmd := &cobra.Command{Use: "mcp", Short: "Run the MCP server over stdio", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, _ []string) error {
		return serve(cmd.Context())
	}}
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
		setupCmd,
		&cobra.Command{Use: "update", Short: "Update evaluate to the latest release", Args: cobra.NoArgs, RunE: func(cmd *cobra.Command, _ []string) error {
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
// TypeSafe's own documentation, and the TypeSafe agent skill built from it,
// teach structured instructions and criteria. That is correct for the direct
// API and wrong for OpenRouter, whose Decisions schema types those fields as
// strings. Saying so up front turns a rejected call into one that is never
// written that way.
func backendNote(cfg Config) string {
	note := "\nBackend: " + cfg.Provider.Name + ". Calling this tool sends the state and questions" +
		" you pass to that provider, which bills for the call."
	if cfg.Provider.Name == "openrouter" {
		note += "\nThis backend accepts only strings for instructions and for every criteria" +
			" description. Structured objects or arrays, and null option descriptions, are" +
			" supported by the TypeSafe backend and rejected here."
	}
	return note
}

func serve(ctx context.Context) error {
	cfg, err := resolveConfig(os.LookupEnv)
	if err != nil {
		return err
	}
	c, err := newClient(cfg)
	if err != nil {
		return err
	}
	// Nothing is printed here: stdout carries the MCP protocol, and a startup
	// banner on it is a protocol error.
	return newServer(cfg, c).Run(ctx, &mcp.StdioTransport{})
}
