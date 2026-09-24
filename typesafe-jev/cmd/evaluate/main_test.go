package main

import (
	"context"
	"os"
	"testing"
)

// asBinaryEnv, set in a child's environment, makes the test binary run its
// arguments as the evaluate binary. Launcher tests point EVALUATE_BIN at the
// test binary, so they run the real command logic without a build step.
const asBinaryEnv = "EVALUATE_TEST_AS_BINARY"

func TestMain(m *testing.M) {
	if os.Getenv(asBinaryEnv) == "1" {
		os.Exit(execute(context.Background(), os.Args[1:]))
	}
	os.Exit(m.Run())
}
