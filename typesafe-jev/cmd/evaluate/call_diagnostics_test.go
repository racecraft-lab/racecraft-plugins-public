package main

import (
	"strings"
	"testing"
)

func TestCallSetupDiagnostics(t *testing.T) {
	for _, tc := range []struct {
		name, chain, fallbackFile, want string
		pluginDefaults                  bool
		code                            int
	}{
		{
			name:  "bare call ignores default key and names both absent hops",
			chain: "typesafe,openrouter", code: exitUnconfigured,
			want: "evaluate: typesafe: no credential; set TYPESAFE_API_KEY, or point JEV_API_KEY_FILE at a private key file\n" +
				"evaluate: openrouter: no credential; set OPENROUTER_API_KEY, or point JEV_FALLBACK_API_KEY_FILE at a private key file\n",
		},
		{
			name: "one-hop chain with fallback key file", chain: "typesafe",
			fallbackFile: "/x", code: exitCredentialBroken,
			want: "evaluate: JEV_FALLBACK_API_KEY_FILE needs a second hop in JEV_CHAIN\n",
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			writeDefaultKey(t, home, "typesafe", fixtureKey, 0o600)
			t.Setenv("JEV_CHAIN", tc.chain)
			t.Setenv("JEV_FALLBACK_API_KEY_FILE", tc.fallbackFile)
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: tc.pluginDefaults}, "")
			if got.code != tc.code || got.stderr != tc.want {
				t.Fatalf("result = %+v, want exit %d and stderr %q", got, tc.code, tc.want)
			}
			if strings.Contains(got.stderr, fixtureKey) {
				t.Fatal("diagnostic contains the fixture key")
			}
		})
	}
}
