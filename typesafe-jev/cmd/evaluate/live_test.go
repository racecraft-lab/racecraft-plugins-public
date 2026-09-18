package main

import (
	"context"
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Live tests call a real provider and cost real money, so they are skipped
// unless EVALUATE_LIVE=1 is set. CI never sets it, and there is no credential
// there to use if it did.
//
// Run one deliberately:
//
//	EVALUATE_LIVE=1 JEV_PROVIDER=openrouter \
//	  JEV_API_KEY_FILE="$HOME/.config/racecraft-jev/openrouter.key" \
//	  go test -count=1 -run TestLive -v ./cmd/evaluate
func liveConfig(t *testing.T) (Config, *Client) {
	t.Helper()
	if os.Getenv("EVALUATE_LIVE") != "1" {
		t.Skip("set EVALUATE_LIVE=1 to make a real, billed provider call")
	}
	cfg, err := resolveConfig(os.LookupEnv)
	if err != nil {
		t.Fatal(err)
	}
	c, err := newClient(cfg)
	if err != nil {
		t.Fatal(err)
	}
	return cfg, c
}

// LIVE-01, through this server rather than through curl: the same three
// primitives in one request, resolved config, real credential, real transport,
// and both validation passes.
func TestLiveThreePrimitives(t *testing.T) {
	cfg, c := liveConfig(t)
	t.Logf("backend=%s endpoint=%s model=%s credential=%s",
		cfg.Provider.Name, cfg.Provider.EndpointURL, cfg.Model, cfg.credentialSource())

	in := threePrimitives(t)
	in.Model = "" // let the configured default apply

	start := time.Now()
	body, err := runEvaluate(context.Background(), c, in)
	elapsed := time.Since(start)
	if err != nil {
		t.Fatalf("live call failed: %v", err)
	}
	t.Logf("latency: %s", elapsed)

	var resp struct {
		Model   string         `json:"model"`
		ID      string         `json:"id"`
		Answers map[string]any `json:"answers"`
		Usage   struct {
			InputTokens  int      `json:"input_tokens"`
			OutputTokens int      `json:"output_tokens"`
			Cost         *float64 `json:"cost"`
		} `json:"usage"`
	}
	if err := json.Unmarshal(body, &resp); err != nil {
		t.Fatalf("response is not JSON: %v", err)
	}

	// Every requested id comes back. runEvaluate already enforces this; the
	// assertion is here so a failure names what was missing.
	for id := range in.Questions {
		if _, ok := resp.Answers[id]; !ok {
			t.Errorf("no answer for %q", id)
		}
	}

	// An alias may resolve to a concrete model, so the returned id need not
	// repeat what was asked for. Record what actually ran.
	t.Logf("requested model: %s", c.Model)
	t.Logf("resolved model:  %s", resp.Model)
	if resp.Model == "" {
		t.Error("response named no model")
	}
	if resp.Usage.InputTokens == 0 && resp.Usage.OutputTokens == 0 {
		t.Error("response reported no token usage")
	}
	if resp.Usage.Cost != nil {
		t.Logf("cost: %g", *resp.Usage.Cost)
	} else {
		t.Log("cost: absent (optional on this backend)")
	}
	if resp.ID != "" {
		t.Logf("request id: %s", resp.ID)
	}

	// Metadata the provider sent must still be here: returning the raw bytes
	// is what keeps cost, ids, legends, and future fields from being dropped.
	for _, want := range []string{`"usage"`, `"answers"`} {
		if !strings.Contains(string(body), want) {
			t.Errorf("response is missing %s", want)
		}
	}
	t.Logf("raw response: %s", body)
}

// The stricter OpenRouter schema is enforced before a request is sent, so a
// structured instruction costs nothing to get wrong.
func TestLiveRejectsStructuredInstructionsOnOpenRouter(t *testing.T) {
	cfg, c := liveConfig(t)
	if cfg.Provider.Name != "openrouter" {
		t.Skipf("backend is %s; this check is about openrouter", cfg.Provider.Name)
	}

	_, err := runEvaluate(context.Background(), c, evaluateIn{
		State: "checkout is down",
		Questions: map[string]question{
			"impact": {
				Type:         "noul",
				Instructions: jsonValue(t, `{"question":"Is this customer impacting?"}`),
			},
		},
	})
	if err == nil {
		t.Fatal("structured instructions were accepted by the openrouter backend")
	}
	if !strings.Contains(err.Error(), "questions.impact.instructions") {
		t.Errorf("error should name the field path: %v", err)
	}
	t.Logf("rejected locally, no request made: %v", err)
}

// The closest thing to a client smoke test without touching a real client
// configuration: launch the *installed* binary through the plugin launcher,
// over real stdio, and make one billed call across the MCP protocol.
//
// This is the exact path Claude Code and Codex take, minus their UI.
func TestLiveThroughLauncherOverStdio(t *testing.T) {
	if os.Getenv("EVALUATE_LIVE") != "1" {
		t.Skip("set EVALUATE_LIVE=1 to make a real, billed provider call")
	}
	launcher := filepath.Join(repoRoot(t), "bin", "evaluate-launch")
	installed := filepath.Join(os.Getenv("HOME"), ".local", "libexec", "racecraft-jev", "evaluate")
	if _, err := os.Stat(installed); err != nil {
		t.Skipf("no installed binary at %s", installed)
	}

	ctx := context.Background()
	cmd := exec.Command(shellPath(t), launcher)
	cmd.Env = append(os.Environ(),
		"EVALUATE_BIN="+installed,
		"JEV_PROVIDER=openrouter",
		"JEV_MODEL=~typesafe/jev-latest",
		"JEV_REQUEST_TIMEOUT=45s",
	)
	cmd.Stderr = os.Stderr

	session, err := mcp.NewClient(testImpl, nil).Connect(ctx, &mcp.CommandTransport{Command: cmd}, nil)
	if err != nil {
		t.Fatalf("connecting to the installed server: %v", err)
	}
	defer session.Close()

	t.Logf("server instructions:\n%s", session.InitializeResult().Instructions)

	tools, err := session.ListTools(ctx, nil)
	if err != nil {
		t.Fatal(err)
	}
	if len(tools.Tools) != 1 || tools.Tools[0].Name != "evaluate" {
		t.Fatalf("tools = %+v", tools.Tools)
	}

	start := time.Now()
	res, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "evaluate",
		Arguments: map[string]any{
			"state": map[string]any{
				"incident": "A production checkout service is unavailable and customers cannot complete purchases.",
			},
			"questions": map[string]any{
				"customer_impact": map[string]any{
					"type":         "noul",
					"instructions": "Does the incident describe a customer-impacting service failure?",
				},
				"owner": map[string]any{
					"type":         "choice",
					"instructions": "Which team should initially investigate this incident?",
					"criteria": map[string]any{
						"billing":     "An invoice, charge, or refund dispute without a service outage.",
						"engineering": "A technical service failure that prevents a normal operation.",
						"sales":       "A question about purchasing, pricing, or a contract.",
						"unknown":     "The incident does not provide enough evidence to select a team.",
					},
				},
				"disruption": map[string]any{
					"type":         "score",
					"instructions": "Rate the operational disruption described by the incident.",
					"criteria": []any{
						"Minor disruption: the operation remains available.",
						"Major disruption: the operation is degraded or intermittently fails.",
						"Service unavailable: customers cannot complete the operation.",
					},
				},
			},
		},
	})
	if err != nil {
		t.Fatalf("tools/call over stdio: %v", err)
	}
	if res.IsError {
		t.Fatalf("tool error: %s", contentText(t, res))
	}
	t.Logf("latency over stdio: %s", time.Since(start))
	t.Logf("result: %s", contentText(t, res))

	for _, id := range []string{"customer_impact", "owner", "disruption"} {
		if !strings.Contains(contentText(t, res), `"`+id+`"`) {
			t.Errorf("result is missing the answer for %q", id)
		}
	}
}
