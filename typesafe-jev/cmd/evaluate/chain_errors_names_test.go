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

// A session moved past two hops names each hop that ran and failed, and
// leaves out a hop skipped for its billing account, which never ran.
func TestMovedSessionNamesEveryFailedHop(t *testing.T) {
	for name, tc := range map[string]struct {
		hops    []string
		skipped uint32
		want    string
	}{
		"both ran":     {[]string{"typesafe", "openrouter", "ollama"}, 0, "this session is on the ollama fallback since typesafe and openrouter failed; refused"},
		"account skip": {[]string{"ollama-local", "ollama", "typesafe"}, 1 << 1, "this session is on the typesafe fallback since ollama-local failed; refused"},
	} {
		t.Run(name, func(t *testing.T) {
			r := &chainRunner{}
			for _, hop := range tc.hops {
				r.hops = append(r.hops, &Client{Provider: providers[hop]})
			}
			r.current.Store(2)
			r.skipped.Store(tc.skipped)
			if err := r.onTheFallback(&requestInvalidError{errors.New("refused")}); err.Error() != tc.want {
				t.Errorf("got %q, want %q", err, tc.want)
			}
		})
	}
}
