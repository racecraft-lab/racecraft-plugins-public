package main

import (
	"context"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// add registers a tool whose handler returns raw text (usually TypeSafe JSON).
// A returned error becomes a tool result with IsError set.
func add[In any](s *mcp.Server, t *mcp.Tool, fn func(ctx context.Context, in In) ([]byte, error)) {
	mcp.AddTool(s, t, func(ctx context.Context, _ *mcp.CallToolRequest, in In) (*mcp.CallToolResult, any, error) {
		b, err := fn(ctx, in)
		if err != nil {
			return nil, nil, err
		}
		return &mcp.CallToolResult{Content: []mcp.Content{&mcp.TextContent{Text: string(b)}}}, nil, nil
	})
}

type question struct {
	Type         string `json:"type" jsonschema:"noul (probability a yes/no condition holds), choice (one option from the criteria map), or score (probability-weighted position on ordered criteria levels)"`
	Instructions any    `json:"instructions" jsonschema:"the judgment to make, with its full meaning; a string, or an object/array for definitions, contrasts, and examples"`
	Criteria     any    `json:"criteria,omitempty" jsonschema:"noul: optional {\"true\": ..., \"false\": ...} descriptions; choice (required): map of option to description or null; score (required): ordered array of at least 2 level descriptions"`
}

type evaluateIn struct {
	State     any                 `json:"state" jsonschema:"content to judge: plain text, or a JSON object/array with named fields"`
	Questions map[string]question `json:"questions" jsonschema:"map of question id to question; answers come back under the same ids, which are not sent to the model"`
	Model     string              `json:"model,omitempty" jsonschema:"model to use; defaults to the latest Jev on whichever endpoint is configured"`
}

// registerTools adds the one `evaluate` tool.
//
// There was a second, narrower schema here that typed instructions as a plain
// string for OpenRouter, because its Decisions schemas did. They no longer do:
// both backends accept a string, an object, or an array. Exporting the narrow
// shape now would hide a capability the backend has, which is the same failure
// as advertising one it lacks, so one schema serves both.
func registerTools(s *mcp.Server, _ Config, c *Client) {
	add(s, evaluateTool(), func(ctx context.Context, in evaluateIn) ([]byte, error) {
		return runEvaluate(ctx, c, in)
	})
}

// runEvaluate validates, sends, and validates the reply. The schema the client
// enforced is a convenience, not a boundary, so everything is checked again
// here.
func runEvaluate(ctx context.Context, c *Client, in evaluateIn) ([]byte, error) {
	if c.Fallback != nil {
		return runWithFallback(ctx, c, in)
	}
	return runOn(ctx, c, in)
}

// runOn is one evaluation on one backend.
func runOn(ctx context.Context, c *Client, in evaluateIn) ([]byte, error) {
	// Precedence: the tool call's model, then JEV_MODEL, then the backend
	// default. c.Model already holds the resolved second and third of those.
	//
	// An explicit model passes through exactly as given. A "~typesafe/" prefix
	// is neither added nor stripped: a mismatched id becomes a 404 the agent
	// can read, which beats a silent rewrite to a model nobody asked for.
	if in.Model == "" {
		in.Model = c.Model
	}
	if err := validateRequest(c.Provider, in); err != nil {
		return nil, &requestInvalidError{err}
	}
	body, err := c.Evaluate(ctx, in)
	if err != nil {
		return nil, err
	}
	if err := validateResponse(c.Provider, in, body); err != nil {
		return nil, &responseInvalidError{err}
	}
	// The provider's own bytes, unknown fields and all. Rebuilding a narrower
	// struct here would quietly drop cost, usage, provider, ids, legends, and
	// whatever the next schema revision adds.
	return body, nil
}

func evaluateTool() *mcp.Tool {
	return &mcp.Tool{
		Name: "evaluate",
		Description: "Jev is a fast structured-decision model: unstructured state in, typed answers " +
			"(noul, choice, score) with calibrated confidence out; 70-500ms, schema-enforced. " +
			"Use for classification, routing, scoring, extraction, branching, guardrails/judging, " +
			"and map-reduce over large data — wherever hand-written logic is too brittle or latency matters. " +
			"Not for prose, code, or free-form text: the answer space must be enumerable up front (max 255 options). " +
			"Calling this sends the supplied state and questions to an external provider and may incur charges; " +
			"the read-only hint means it changes nothing locally, not that it is free or private.",
		Annotations: &mcp.ToolAnnotations{ReadOnlyHint: true},
	}
}
