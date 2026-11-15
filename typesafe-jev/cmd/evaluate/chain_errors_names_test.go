package main

import (
	"errors"
	"io"
	"os"
	"strings"
	"testing"
)

// With three hops and none able to start, the error names every hop.
func TestNoHopStartsNamesEveryHop(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,ollama")
	resolved, err := resolveHops(os.LookupEnv, false)
	if err != nil {
		t.Fatal(err)
	}
	_, _, err = startChain(resolved, io.Discard, io.Discard)
	if err == nil {
		t.Fatal("want a start-up error")
	}
	for _, want := range []string{"typesafe", "the openrouter fallback cannot start either", "the ollama fallback cannot start either"} {
		if !strings.Contains(err.Error(), want) {
			t.Errorf("error %q is missing %q", err, want)
		}
	}
}

// A session moved past two hops names both as failed, not only the first.
func TestMovedSessionNamesEveryFailedHop(t *testing.T) {
	r := &chainRunner{hops: []*Client{{Provider: providers["typesafe"]}, {Provider: providers["openrouter"]}, {Provider: providers["ollama"]}}}
	r.current.Store(2)
	err := r.onTheFallback(&requestInvalidError{errors.New("too many questions")})
	if want := "this session is on the ollama fallback since typesafe and openrouter failed; too many questions"; err.Error() != want {
		t.Errorf("got %q, want %q", err, want)
	}
}
