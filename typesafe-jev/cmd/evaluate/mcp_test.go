package main

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

var testImpl = &mcp.Implementation{Name: "evaluate-test", Version: "test"}

// connect runs the real server registration over the SDK's in-memory
// transports, so a test drives the shipped tool rather than a stand-in.
func connect(t *testing.T, cfg Config, c *Client) *mcp.ClientSession {
	t.Helper()
	ctx := context.Background()

	serverTransport, clientTransport := mcp.NewInMemoryTransports()
	serverSession, err := newServer(cfg, c).Connect(ctx, serverTransport, nil)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { serverSession.Close() })

	clientSession, err := mcp.NewClient(testImpl, nil).Connect(ctx, clientTransport, nil)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { clientSession.Close() })
	return clientSession
}

// backendFor wires a config and client at a local mock endpoint.
func backendFor(t *testing.T, provider string, srv *httptest.Server) (Config, *Client) {
	t.Helper()
	spec := providerAt(provider, srv.URL)
	cfg := Config{
		Provider:   spec,
		Model:      spec.DefaultModel,
		Timeout:    10 * time.Second,
		MaxRetries: 0,
	}
	return cfg, testClient(spec, srv)
}

func mockBackend(t *testing.T, reply string) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Write([]byte(reply))
	}))
	t.Cleanup(srv.Close)
	return srv
}

// MCP-01: initialize and tools/list work against the pinned SDK, and the
// exported schema is the one the selected backend actually accepts. A
// description claiming "string" while the schema says "any" is not a
// restriction, so this asserts on the schema the agent receives.
func TestToolsListExportsBackendSchema(t *testing.T) {
	// Both backends accept a string, an object, or an array for instructions,
	// so neither schema may pin the field to "string". The narrow OpenRouter
	// shape this once asserted would now hide a capability the backend has.
	for _, tc := range []struct {
		provider      string
		wantType      string
		wantStructure bool
	}{
		{"typesafe", "", true},
		{"openrouter", "", true},
	} {
		t.Run(tc.provider, func(t *testing.T) {
			srv := mockBackend(t, noulReply)
			cfg, c := backendFor(t, tc.provider, srv)
			session := connect(t, cfg, c)

			res, err := session.ListTools(context.Background(), nil)
			if err != nil {
				t.Fatal(err)
			}
			if len(res.Tools) != 1 || res.Tools[0].Name != "evaluate" {
				t.Fatalf("tools = %+v; want exactly one named evaluate", res.Tools)
			}

			schema, err := json.Marshal(res.Tools[0].InputSchema)
			if err != nil {
				t.Fatal(err)
			}
			instructions := instructionsSchema(t, schema)

			gotType, _ := instructions["type"].(string)
			if gotType != tc.wantType {
				t.Errorf("instructions type = %q, want %q\nschema: %s", gotType, tc.wantType, schema)
			}
			// The schema must keep advertising structure, or agents stop
			// sending input both backends document and callers already use.
			if tc.wantStructure && gotType == "string" {
				t.Errorf("%s schema narrowed to a string: %s", tc.provider, schema)
			}
			for _, arg := range []string{"state", "questions", "model"} {
				if !strings.Contains(string(schema), `"`+arg+`"`) {
					t.Errorf("schema is missing the %q argument: %s", arg, schema)
				}
			}
		})
	}
}

// instructionsSchema digs out the question instructions subschema.
func instructionsSchema(t *testing.T, schema []byte) map[string]any {
	t.Helper()
	var doc map[string]any
	if err := json.Unmarshal(schema, &doc); err != nil {
		t.Fatal(err)
	}
	props, _ := doc["properties"].(map[string]any)
	questions, _ := props["questions"].(map[string]any)
	question, _ := questions["additionalProperties"].(map[string]any)
	qProps, _ := question["properties"].(map[string]any)
	instructions, ok := qProps["instructions"].(map[string]any)
	if !ok {
		t.Fatalf("no instructions subschema in %s", schema)
	}
	return instructions
}

// MCP-01: a tools/call round trip returns the provider's own JSON.
func TestToolsCallReturnsProviderJSON(t *testing.T) {
	const reply = `{"id":"gen-1","model":"typesafe/jev-x","usage":{"input_tokens":9,"output_tokens":3,"cost":0.0001},` +
		`"answers":{"customer_impact":{"type":"noul","noul":0.98}}}`
	srv := mockBackend(t, reply)
	cfg, c := backendFor(t, "openrouter", srv)
	session := connect(t, cfg, c)

	res, err := session.CallTool(context.Background(), &mcp.CallToolParams{
		Name: "evaluate",
		Arguments: map[string]any{
			"state": "checkout is down",
			"questions": map[string]any{
				"customer_impact": map[string]any{
					"type":         "noul",
					"instructions": "Does this describe a customer-impacting failure?",
				},
			},
		},
	})
	if err != nil {
		t.Fatal(err)
	}
	if res.IsError {
		t.Fatalf("tool reported an error: %+v", res.Content)
	}
	text := contentText(t, res)
	for _, keep := range []string{`"noul":0.98`, `"cost":0.0001`, `"gen-1"`} {
		if !strings.Contains(text, keep) {
			t.Errorf("result dropped %s: %s", keep, text)
		}
	}
}

// MCP-02: a runtime failure comes back as a tool error, not a fabricated
// low-confidence answer, and the session stays usable afterwards.
func TestToolErrorDoesNotKillTheSession(t *testing.T) {
	fail := true
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		if fail {
			w.WriteHeader(http.StatusPaymentRequired)
			w.Write([]byte(`{"error":{"code":402,"message":"Insufficient credits"}}`))
			return
		}
		w.Write([]byte(noulReply))
	}))
	defer srv.Close()

	cfg, c := backendFor(t, "openrouter", srv)
	session := connect(t, cfg, c)

	args := map[string]any{
		"state":     "x",
		"questions": map[string]any{"q": map[string]any{"type": "noul", "instructions": "urgent?"}},
	}

	res, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: args})
	if err != nil {
		t.Fatal(err)
	}
	if !res.IsError {
		t.Fatal("a 402 was reported as a successful judgment")
	}
	text := contentText(t, res)
	if !strings.Contains(text, "402") {
		t.Errorf("error should name the status: %s", text)
	}
	// No invented answer alongside the failure.
	if strings.Contains(text, `"noul"`) {
		t.Errorf("error result carried a fabricated answer: %s", text)
	}

	// The same session still works once the backend recovers.
	fail = false
	res, err = session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: args})
	if err != nil {
		t.Fatal(err)
	}
	if res.IsError {
		t.Fatalf("session unusable after an earlier tool error: %s", contentText(t, res))
	}
}

func contentText(t *testing.T, res *mcp.CallToolResult) string {
	t.Helper()
	var b strings.Builder
	for _, c := range res.Content {
		if tc, ok := c.(*mcp.TextContent); ok {
			b.WriteString(tc.Text)
		}
	}
	return b.String()
}

// Test-only wiring for the stdio helper below. These names exist in the test
// binary only: the shipped executable has no environment variable that can
// point it at another endpoint.
const (
	stdioHelperEnv   = "EVALUATE_TEST_STDIO_HELPER"
	stdioEndpointEnv = "EVALUATE_TEST_STDIO_ENDPOINT"
	stdioProviderEnv = "EVALUATE_TEST_STDIO_PROVIDER"
)

// TestStdioHelperProcess is not a test. Re-executed as a child process, it
// runs the real server over real stdio, so MCP-03 and MCP-04 are checked
// against the actual transport rather than an in-memory stand-in.
func TestStdioHelperProcess(t *testing.T) {
	if os.Getenv(stdioHelperEnv) != "1" {
		return
	}
	spec := providers[os.Getenv(stdioProviderEnv)]
	spec.EndpointURL = os.Getenv(stdioEndpointEnv)
	cfg := Config{Provider: spec, Model: spec.DefaultModel, Timeout: 10 * time.Second}
	c := &Client{
		Provider: spec,
		Model:    spec.DefaultModel,
		APIKey:   "test-key",
		HTTP:     newHTTPClient(),
		Timeout:  10 * time.Second,
		Backoff:  time.Millisecond,
	}
	err := newServer(cfg, c).Run(context.Background(), &mcp.StdioTransport{})
	// Exit before the testing package writes its own summary to stdout, which
	// would be a protocol frame the client cannot parse.
	if err != nil {
		os.Exit(1)
	}
	os.Exit(0)
}

// MCP-03, MCP-04: over real stdio, the child speaks protocol on stdout and
// nothing else, and shuts down cleanly when the transport closes.
func TestStdioTransportRoundTrip(t *testing.T) {
	srv := mockBackend(t, `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":0.42}}}`)
	ctx := context.Background()

	cmd := exec.Command(os.Args[0], "-test.run=TestStdioHelperProcess")
	cmd.Env = append(os.Environ(),
		stdioHelperEnv+"=1",
		stdioProviderEnv+"=openrouter",
		stdioEndpointEnv+"="+srv.URL,
	)
	// Anything the child writes to stderr is visible in test output; stdout
	// belongs to the protocol.
	cmd.Stderr = os.Stderr

	session, err := mcp.NewClient(testImpl, nil).Connect(ctx, &mcp.CommandTransport{Command: cmd}, nil)
	if err != nil {
		t.Fatal(err)
	}

	tools, err := session.ListTools(ctx, nil)
	if err != nil {
		t.Fatalf("tools/list over stdio: %v", err)
	}
	if len(tools.Tools) != 1 || tools.Tools[0].Name != "evaluate" {
		t.Fatalf("tools over stdio = %+v", tools.Tools)
	}

	res, err := session.CallTool(ctx, &mcp.CallToolParams{
		Name: "evaluate",
		Arguments: map[string]any{
			"state":     "checkout is down",
			"questions": map[string]any{"q": map[string]any{"type": "noul", "instructions": "urgent?"}},
		},
	})
	if err != nil {
		t.Fatalf("tools/call over stdio: %v", err)
	}
	if res.IsError {
		t.Fatalf("tool error over stdio: %s", contentText(t, res))
	}
	if !strings.Contains(contentText(t, res), `"noul":0.42`) {
		t.Errorf("unexpected result: %s", contentText(t, res))
	}

	// Closing the session closes the child's stdin. A clean shutdown means the
	// process exits on EOF rather than being killed on the way out.
	if err := session.Close(); err != nil {
		t.Errorf("closing the stdio session: %v", err)
	}
}

// The server's instructions are what both clients read before the agent writes
// a question. They must say which backend is configured, that a call costs
// money, and, for OpenRouter, that a choice or score answer may arrive without
// confidence or probabilities.
//
// The structured form the official TypeSafe agent skill teaches now works on
// both backends, so no instruction may talk an agent out of using it.
func TestServerInstructionsNameTheBackend(t *testing.T) {
	for _, tc := range []struct {
		provider string
		wantAll  []string
		wantNone []string
	}{
		{
			provider: "openrouter",
			wantAll: []string{
				"Backend: openrouter",
				"bills for the call",
				"may omit confidence and probabilities",
				"Treat an absent field as absent",
			},
			// Structure is accepted here now. A leftover string-only warning
			// would talk agents out of a form the backend supports.
			wantNone: []string{"accepts only strings", "rejected here"},
		},
		{
			provider: "typesafe",
			wantAll:  []string{"Backend: typesafe", "bills for the call"},
			// This backend always sends both fields, so the omission note must
			// not leak onto it.
			wantNone: []string{"accepts only strings", "may omit confidence"},
		},
	} {
		t.Run(tc.provider, func(t *testing.T) {
			srv := mockBackend(t, noulReply)
			cfg, c := backendFor(t, tc.provider, srv)
			session := connect(t, cfg, c)

			got := session.InitializeResult().Instructions
			for _, want := range tc.wantAll {
				if !strings.Contains(got, want) {
					t.Errorf("instructions missing %q:\n%s", want, got)
				}
			}
			for _, unwanted := range tc.wantNone {
				if strings.Contains(got, unwanted) {
					t.Errorf("instructions wrongly contain %q:\n%s", unwanted, got)
				}
			}
			// Upstream's question-design guidance must survive either way.
			if !strings.Contains(got, "A noul near 0.5 means uncertain") {
				t.Errorf("base guidance lost:\n%s", got)
			}
		})
	}
}
