package main

import (
	"context"
	"testing"
)

// Adapt existing one-backend fixtures and chain fixtures to the same real
// runner. HTTP remains the only fake boundary; there is no hop interface.
func testChain(c any) *chainRunner {
	switch c := c.(type) {
	case *Client:
		return &chainRunner{hops: []*Client{c}}
	case *chainRunner:
		return c
	default:
		panic("expected a client or a chain fixture")
	}
}

func runEvaluate(ctx context.Context, c any, in evaluateIn) ([]byte, error) {
	return testChain(c).evaluate(ctx, in)
}

// Keep the timeout regression's existing reason/move assertions against the
// new classifier, with the same request-context provenance as the runner.
func fallbackReason(ctx context.Context, err error) (string, bool) {
	out := classify(&chainFailure{err: err, requestErr: ctx.Err()})
	return out.reason, out.effect == moveSession || out.effect == moveAccount
}

// runTestMatrix runs every pair in order with caller-owned names and checks.
func runTestMatrix[A, B any](t *testing.T, rows []A, columns []B, name func(A, B) string, check func(*testing.T, A, B)) {
	t.Helper()
	for _, row := range rows {
		for _, column := range columns {
			t.Run(name(row, column), func(t *testing.T) {
				check(t, row, column)
			})
		}
	}
}
