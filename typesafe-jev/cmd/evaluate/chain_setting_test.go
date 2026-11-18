package main

import (
	"context"
	"encoding/json"
	"fmt"
	"github.com/modelcontextprotocol/go-sdk/mcp"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
	"time"
)

// Configuration is observed through evaluate call, with an isolated HOME and
// synthetic credentials. --check must never issue an HTTP request.
func TestCallChainSettingWins(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "openrouter,typesafe")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	var report checkReport
	if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
		t.Fatal(err)
	}
	if got.code != 0 || report.Primary.Provider != "openrouter" || report.Fallback == nil || report.Fallback.Provider != "typesafe" {
		t.Fatalf("JEV_CHAIN ignored: exit=%d report=%+v stderr=%q", got.code, report, got.stderr)
	}
}

func TestCallChainResolutionOrder(t *testing.T) {
	for _, tc := range []struct {
		name, chain, primary, fallback, file, wantPrimary, wantFallback string
	}{
		{name: "built-in", wantPrimary: "typesafe", wantFallback: "openrouter"},
		{name: "file", file: "openrouter,typesafe\n", wantPrimary: "openrouter", wantFallback: "typesafe"},
		{name: "legacy beats file", primary: "typesafe", fallback: "openrouter", file: "broken", wantPrimary: "typesafe", wantFallback: "openrouter"},
		{name: "legacy one hop", primary: "openrouter", file: "broken", wantPrimary: "openrouter"},
		{name: "chain beats file", chain: "openrouter,typesafe", file: "broken", wantPrimary: "openrouter", wantFallback: "typesafe"},
		{name: "chain one hop", chain: "typesafe", wantPrimary: "typesafe"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			home := isolateCallEnv(t)
			if tc.file != "" {
				writeChainSetting(t, home, tc.file)
			}
			for key, value := range map[string]string{"JEV_CHAIN": tc.chain, "JEV_PROVIDER": tc.primary, "JEV_FALLBACK_PROVIDER": tc.fallback} {
				if value != "" {
					t.Setenv(key, value)
				}
			}
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
			var report checkReport
			if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
				t.Fatal(err)
			}
			fallback := ""
			if report.Fallback != nil {
				fallback = report.Fallback.Provider
			}
			if got.code != 0 || report.Primary.Provider != tc.wantPrimary || fallback != tc.wantFallback {
				t.Fatalf("exit=%d primary=%s fallback=%s stderr=%s", got.code, report.Primary.Provider, fallback, got.stderr)
			}
		})
	}
}

func writeChainSetting(t *testing.T, home, contents string) {
	t.Helper()
	fixture := writeDefaultKey(t, home, "chain", contents, 0600)
	if err := os.Rename(fixture, filepath.Join(filepath.Dir(fixture), "chain")); err != nil {
		t.Fatal(err)
	}
}

func TestCallRejectsBadChainAtStartup(t *testing.T) {
	for _, tc := range []struct{ name, chain, want string }{
		{"unknown", "missing", "unknown provider"},
		{"repeat", "typesafe,typesafe", "repeats provider"},
		{"empty entry", "typesafe,,openrouter", "empty hop"},
		{"empty setting", "", "empty hop"},
		{"fifth hop", "typesafe,openrouter,a,b,c", "at most four"},
		{"mix primary", "typesafe", "cannot be combined"},
		{"mix fallback", "typesafe", "cannot be combined"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", tc.chain)
			if tc.name == "mix primary" {
				t.Setenv("JEV_PROVIDER", "typesafe")
			}
			if tc.name == "mix fallback" {
				t.Setenv("JEV_FALLBACK_PROVIDER", "openrouter")
			}
			got := runCallForTest(t, callOptions{check: true}, "")
			if got.code != 4 || got.stdout != "" || !strings.Contains(got.stderr, tc.want) {
				t.Fatalf("bad startup: %+v", got)
			}
		})
	}
}

// The third row is synthetic: Ollama is deliberately not enabled by this layer.
func TestThreeHopSessionMovesDownAndKeepsModels(t *testing.T) {
	isolateCallEnv(t)
	third := providers["typesafe"]
	third.Name = "fixture-third"
	third.BillingAccount = third.Name
	third.EndpointURL = "https://third.invalid/decide"
	third.DefaultModel = "third-default"
	providers[third.Name] = third
	t.Cleanup(func() { delete(providers, third.Name) })
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,fixture-third")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	t.Setenv("JEV_MODEL", "configured-first")
	resolved, err := resolveHops(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	var log strings.Builder
	chain, cfg, err := startChain(resolved, &log, &log)
	if err != nil {
		t.Fatal(err)
	}
	var visited, models []string
	secondCalls := 0
	transport := backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
		var wire struct{ Model string }
		if err := json.NewDecoder(r.Body).Decode(&wire); err != nil {
			return nil, err
		}
		visited = append(visited, r.URL.String())
		models = append(models, wire.Model)
		status := 200
		switch r.URL.String() {
		case providers["typesafe"].EndpointURL:
			status = 401
		case providers["openrouter"].EndpointURL:
			secondCalls++
			if secondCalls > 1 {
				status = 403
			}
		}
		return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
	})
	for _, hop := range chain.hops {
		hop.HTTP = &http.Client{Transport: transport}
	}
	session := connect(t, cfg, chain)
	for range 3 {
		result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: evaluateIn{State: "fixture", Questions: simpleIn().Questions, Model: "tool-first"}})
		if err != nil || result.IsError {
			t.Fatalf("result=%v error=%v log=%s", result, err, log.String())
		}
	}
	want := []string{providers["typesafe"].EndpointURL, providers["openrouter"].EndpointURL, providers["openrouter"].EndpointURL, third.EndpointURL, third.EndpointURL}
	if !reflect.DeepEqual(visited, want) || !reflect.DeepEqual(models, []string{"tool-first", "~typesafe/jev-latest", "~typesafe/jev-latest", "third-default", "third-default"}) || strings.Count(log.String(), "\n") != 2 {
		t.Fatalf("visits=%v models=%v log=%s", visited, models, log.String())
	}
}

func TestChainThirdCredentialIsStrictButServerDropsIt(t *testing.T) {
	home := isolateCallEnv(t)
	third := providers["typesafe"]
	third.Name = "fixture-third"
	third.APIKeyEnv = "FIXTURE_THIRD_KEY"
	providers[third.Name] = third
	t.Cleanup(func() { delete(providers, third.Name) })
	t.Setenv(third.APIKeyEnv, "")
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,fixture-third")
	writeDefaultKey(t, home, "typesafe", fixtureKey, 0600)
	writeDefaultKey(t, home, "openrouter", fixtureKey, 0600)
	writeDefaultKey(t, home, third.Name, "", 0600)
	got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	if got.code != 4 || !strings.Contains(got.stderr, "fixture-third") {
		t.Fatalf("check lost third credential: %+v", got)
	}
	resolved, err := resolveHops(os.LookupEnv, true)
	if err != nil {
		t.Fatal(err)
	}
	var log strings.Builder
	chain, _, err := startChain(resolved, &log, &log)
	if err != nil || len(chain.hops) != 2 || strings.Count(log.String(), "\n") != 1 || !strings.Contains(log.String(), "fixture-third") {
		t.Fatalf("server did not drop exactly one hop: err=%v log=%q", err, log.String())
	}
}

func TestChainInstructionsStayFixedWhileToolNoteUpdatesAfterMove(t *testing.T) {
	var log strings.Builder
	var primaryCalls, fallbackCalls int
	transport := backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
		status := 200
		if r.URL.String() == providers["typesafe"].EndpointURL {
			primaryCalls++
			status = 429
		} else {
			fallbackCalls++
		}
		return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
	})
	chain := &chainRunner{log: &log, hops: []*Client{
		{Provider: providers["typesafe"], Model: "jev-latest", Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
		{Provider: providers["openrouter"], Model: "~typesafe/jev-latest", Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
	}}
	session := connect(t, Config{Provider: providers["typesafe"]}, chain)
	initialInstructions := session.InitializeResult().Instructions
	check := func(serving string) {
		t.Helper()
		got := session.InitializeResult().Instructions
		if got != initialInstructions || !strings.Contains(got, "Backend chain: typesafe -> openrouter.") {
			t.Errorf("instructions must keep the fixed hop order: %q", got)
		}
		if strings.Contains(got, "Serving hop:") {
			t.Errorf("initialize instructions must never name a serving hop (currently %s)", serving)
		}
		listed, err := session.ListTools(context.Background(), nil)
		if err != nil {
			t.Fatal(err)
		}
		if len(listed.Tools) != 1 || !strings.Contains(listed.Tools[0].Description, "Backend chain: typesafe -> openrouter") || !strings.Contains(listed.Tools[0].Description, "Serving hop: "+serving) {
			t.Fatalf("backend note missing serving %s: %+v", serving, listed.Tools)
		}
	}
	check("typesafe")
	for range 2 {
		result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: simpleIn()})
		if err != nil || result.IsError {
			t.Fatalf("result=%v error=%v", result, err)
		}
		check("openrouter")
	}
	if primaryCalls != 1 || fallbackCalls != 2 {
		t.Fatalf("calls primary=%d fallback=%d; want 1 and 2", primaryCalls, fallbackCalls)
	}
}

func TestChainModelsStayOnConfiguredFirstHop(t *testing.T) {
	for _, dropFirst := range []bool{false, true} {
		t.Run(fmt.Sprint(dropFirst), func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", "typesafe,openrouter")
			t.Setenv("JEV_MODEL", "operator-first")
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			if !dropFirst {
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			}
			var sent []string
			old := http.DefaultTransport
			http.DefaultTransport = backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
				var wire struct{ Model string }
				if err := json.NewDecoder(r.Body).Decode(&wire); err != nil {
					return nil, err
				}
				sent = append(sent, wire.Model)
				return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(validAnswer))}, nil
			})
			t.Cleanup(func() { http.DefaultTransport = old })
			got := runCallForTest(t, callOptions{}, validRequest)
			want := "operator-first"
			if dropFirst {
				want = "~typesafe/jev-latest"
			}
			if got.code != 0 || !reflect.DeepEqual(sent, []string{want}) {
				t.Fatalf("exit=%d models=%v stderr=%s", got.code, sent, got.stderr)
			}
		})
	}
}

func TestDefaultChainKeepsFirstModel(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	old := http.DefaultTransport
	http.DefaultTransport = backendFixtureTransport(func(r *http.Request) (*http.Response, error) {
		var wire struct{ Model string }
		if err := json.NewDecoder(r.Body).Decode(&wire); err != nil {
			return nil, err
		}
		if r.URL.String() != "https://api.typesafe.ai/v1/systemone" || wire.Model != "jev-latest" {
			t.Errorf("default destination=%s model=%s", r.URL, wire.Model)
		}
		return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(validAnswer))}, nil
	})
	t.Cleanup(func() { http.DefaultTransport = old })
	got := runCallForTest(t, callOptions{}, validRequest)
	if got.code != 0 {
		t.Fatalf("default call: %+v", got)
	}
}

func TestPluginLeavesChainSelectionToRuntime(t *testing.T) {
	for _, file := range []string{"plugin/mcp/claude.json", "plugin/.mcp.json"} {
		doc := readJSON(t, filepath.Join(repoRoot(t), file))
		entry := doc["mcpServers"].(map[string]any)["jev"].(map[string]any)
		env := entry["env"].(map[string]any)
		for _, key := range []string{"JEV_CHAIN", "JEV_PROVIDER", "JEV_FALLBACK_PROVIDER", "JEV_MODEL"} {
			if _, set := env[key]; set {
				t.Errorf("%s pins %s and masks operator configuration", file, key)
			}
		}
	}
}

func TestSetupGeneratesChainInsteadOfLegacyPair(t *testing.T) {
	home := isolateCallEnv(t)
	writeChainSetting(t, home, "openrouter,typesafe")
	cfg, err := resolveHopConfig(os.LookupEnv, false)
	if err != nil {
		t.Fatal(err)
	}
	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"claude-code", "codex"}})
	if !strings.Contains(got, "JEV_CHAIN=openrouter,typesafe") || !strings.Contains(got, `JEV_CHAIN = "openrouter,typesafe"`) || strings.Contains(got, "JEV_PROVIDER") || strings.Contains(got, "JEV_FALLBACK_PROVIDER") {
		t.Fatalf("setup does not emit only chain configuration: %s", got)
	}
}

func TestFourHopKeysKeepPositionalOverridesAndDiscovery(t *testing.T) {
	home := isolateCallEnv(t)
	for _, name := range []string{"fixture-third", "fixture-fourth"} {
		row := providers["typesafe"]
		row.Name = name
		row.APIKeyEnv = "FIXTURE_UNUSED_KEY"
		providers[name] = row
		t.Cleanup(func() { delete(providers, name) })
		writeDefaultKey(t, home, name, fixtureKey, 0600)
	}
	t.Setenv("FIXTURE_UNUSED_KEY", "")
	t.Setenv("JEV_CHAIN", "typesafe,openrouter,fixture-third,fixture-fourth")
	t.Setenv("JEV_API_KEY_FILE", writeKeyFile(t, fixtureKey, 0600))
	t.Setenv("JEV_FALLBACK_API_KEY_FILE", writeKeyFile(t, fixtureKey, 0600))
	got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
	var report struct{ Hops []sourceStatus }
	if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
		t.Fatal(err)
	}
	if got.code != 0 || len(report.Hops) != 4 {
		t.Fatalf("four-hop check: %+v", got)
	}
	for i, hop := range report.Hops {
		want := "explicit-file"
		if i > 1 {
			want = "default-file"
		}
		if hop.Source != want || hop.State != "ok" {
			t.Errorf("hop %d=%+v want %s/ok", i+1, hop, want)
		}
	}
}
