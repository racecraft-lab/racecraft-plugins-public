package main

import (
	"context"
	"encoding/json"
	"io"
	"net"
	"net/http"
	"os"
	"reflect"
	"strings"
	"syscall"
	"testing"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

func TestOllamaLocalCheckNeedsNoCredential(t *testing.T) {
	blockOllamaHTTP(t)
	got := checkCallWithEnv(t, callOptions{check: true, pluginDefaults: true}, map[string]string{"JEV_CHAIN": "ollama-local"})
	if got.code != 0 {
		t.Fatalf("keyless check exit=%d stderr=%s", got.code, got.stderr)
	}
	var report checkReport
	if err := json.NewDecoder(strings.NewReader(got.stdout)).Decode(&report); err != nil {
		t.Fatal(err)
	}
	if report.Primary.Provider != "ollama-local" || report.Primary.Source != "none" || report.Primary.State != "ok" {
		t.Fatalf("keyless credential report=%+v", report)
	}
}

func TestOllamaLocalChainFailures(t *testing.T) {
	for _, tc := range []struct {
		name   string
		status int
		err    error
		skip   bool
	}{
		{"refused", 0, &net.OpError{Op: "dial", Net: "tcp", Err: syscall.ECONNREFUSED}, false},
		{"gateway", 502, nil, false},
		{"unavailable", 503, nil, false},
		{"path", 404, nil, false},
		{"unauthorized", 401, nil, true},
		{"credit", 402, nil, true},
		{"forbidden", 403, nil, true},
		{"throttle", 429, nil, true},
		{"server", 500, nil, true},
		{"other server", 504, nil, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var calls []string
			var log strings.Builder
			transport := backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				calls = append(calls, req.URL.Host)
				switch req.URL.Host {
				case "localhost:11434":
					if tc.err != nil {
						return nil, tc.err
					}
					return ollamaStatusReply(tc.status), nil
				case "ollama.com":
					return ollamaStatusReply(200), nil
				default:
					return ollamaStatusReply(401), nil
				}
			})
			session := ollamaChainSession(t, "openrouter,typesafe,ollama-local,ollama", transport, &log)
			result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: simpleIn()})
			if err != nil {
				t.Fatal(err)
			}
			want := []string{"openrouter.ai", "api.typesafe.ai", "localhost:11434"}
			if !tc.skip {
				want = append(want, "ollama.com")
			}
			if result.IsError != tc.skip || !reflect.DeepEqual(calls, want) {
				t.Fatalf("error=%v calls=%v; want error=%v calls=%v; result=%s", result.IsError, calls, tc.skip, want, contentText(t, result))
			}
			if !tc.skip && contentText(t, result) != noulReply {
				t.Fatalf("answer=%s", contentText(t, result))
			}
		})
	}
}

func ollamaChainSession(t *testing.T, chain string, transport backendFixtureTransport, log io.Writer) *mcp.ClientSession {
	t.Helper()
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", chain)
	for _, name := range []string{"OPENROUTER_API_KEY", "TYPESAFE_API_KEY", "OLLAMA_API_KEY"} {
		t.Setenv(name, fixtureKey)
	}
	fakeOllamaTransport(t, transport)
	resolved, err := resolveHops(os.LookupEnv, false)
	if err != nil {
		t.Fatal(err)
	}
	runner, cfg, err := startChain(resolved, log, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	return connect(t, cfg, runner)
}

func ollamaStatusReply(status int) *http.Response {
	return fixtureHTTPResponse(status, noulReply)
}

func TestOllamaAccountSkipPersistsPastAnotherAccount(t *testing.T) {
	for _, chain := range []string{"ollama-local,openrouter,ollama,typesafe", "ollama,openrouter,ollama-local,typesafe"} {
		t.Run(chain, func(t *testing.T) {
			var calls []string
			var log strings.Builder
			routerCalls := 0
			transport := backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				calls = append(calls, req.URL.Host)
				switch req.URL.Host {
				case "openrouter.ai":
					routerCalls++
					if routerCalls == 1 {
						return ollamaStatusReply(200), nil
					}
					return ollamaStatusReply(401), nil
				case "api.typesafe.ai":
					return ollamaStatusReply(200), nil
				default:
					return ollamaStatusReply(402), nil
				}
			})
			session := ollamaChainSession(t, chain, transport, &log)
			for range 3 {
				result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: simpleIn()})
				if err != nil || result.IsError || contentText(t, result) != noulReply {
					t.Fatalf("call result=%v err=%v", result, err)
				}
			}
			first := "localhost:11434"
			if strings.HasPrefix(chain, "ollama,") {
				first = "ollama.com"
			}
			want := []string{first, "openrouter.ai", "openrouter.ai", "api.typesafe.ai", "api.typesafe.ai"}
			if !reflect.DeepEqual(calls, want) || strings.Count(log.String(), "rest of this session") != 2 {
				t.Fatalf("calls=%v log=%s; want calls=%v and two moves", calls, &log, want)
			}
		})
	}
}

func TestOllamaLocalIgnoresKeyFileSettings(t *testing.T) {
	for _, tc := range []struct{ chain, setting string }{
		{"ollama-local", "JEV_API_KEY_FILE"},
		{"openrouter,ollama-local", "JEV_FALLBACK_API_KEY_FILE"},
	} {
		t.Run(tc.chain, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", tc.chain)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv(tc.setting, "invalid-relative-key-file")
			blockOllamaHTTP(t)
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
			if got.code != 0 {
				t.Fatalf("keyless hop rejected irrelevant key file: exit=%d stderr=%s", got.code, got.stderr)
			}
		})
	}
}

func TestOllamaLocalGoldenRequestHasNoAuthorization(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "ollama-local")
	// Even a configured credential must never leave for the daemon.
	t.Setenv("OLLAMA_API_KEY", fixtureKey)
	var sent *http.Request
	var body []byte
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		sent = req
		var err error
		body, err = io.ReadAll(req.Body)
		return fixtureHTTPResponse(200, ollamaTextReply), err
	})
	got := runCallForTest(t, callOptions{}, ollamaTextRequest)
	if calls != 1 || sent == nil {
		t.Fatalf("want one intercepted daemon request, got %d", calls)
	}
	const golden = `{"state":{"ticket":"checkout failed"},"questions":{"impact":{"type":"score","instructions":"How severe?","criteria":["low","medium","high"]},"label":{"type":"choice","instructions":"Which label?","criteria":{"billing":"Payment issue","bug":"Software error"}},"urgent":{"type":"noul","instructions":"Needs attention now?"}},"model":"clef:cloud"}`
	if sent.Method != "POST" || sent.URL.String() != "http://localhost:11434/v1/systemone" || string(body) != golden {
		t.Errorf("unexpected daemon request: %s %s %s", sent.Method, sent.URL, body)
	}
	if _, present := sent.Header["Authorization"]; present {
		t.Error("daemon request must omit Authorization entirely")
	}
	if got.code != 0 || strings.TrimSpace(got.stdout) != ollamaTextReply {
		t.Fatalf("exit=%d stdout=%s stderr=%s", got.code, got.stdout, got.stderr)
	}
}

func TestOllamaRoutedAccountFailureStaysCallOnly(t *testing.T) {
	var calls []string
	var log strings.Builder
	session := ollamaChainSession(t, "typesafe,ollama-local,ollama,openrouter", func(req *http.Request) (*http.Response, error) {
		calls = append(calls, req.URL.Host)
		if req.URL.Host == "localhost:11434" {
			return ollamaStatusReply(402), nil
		}
		return ollamaStatusReply(200), nil
	}, &log)
	large := simpleIn()
	large.State = budgetText(33_000)
	for _, in := range []evaluateIn{large, simpleIn()} {
		result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: in})
		if err != nil || result.IsError || contentText(t, result) != noulReply {
			t.Fatalf("routed result=%v err=%v", result, err)
		}
	}
	want := []string{"localhost:11434", "openrouter.ai", "api.typesafe.ai"}
	if !reflect.DeepEqual(calls, want) || log.Len() != 0 {
		t.Fatalf("calls=%v log=%s; want calls=%v with no session move", calls, &log, want)
	}
}
