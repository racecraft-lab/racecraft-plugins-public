package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"reflect"
	"strings"
	"testing"
)

func TestOllamaCloudStructuredEntryCapabilityRoutes(t *testing.T) {
	for _, tc := range []struct {
		name, question, answer string
	}{
		{"noul true object", `{"type":"noul","instructions":"Judge","criteria":{"true":{"when":"yes"},"false":"no"}}`, `{"type":"noul","noul":0.8}`},
		{"noul false object", `{"type":"noul","instructions":"Judge","criteria":{"true":"yes","false":{"when":"no"}}}`, `{"type":"noul","noul":0.8}`},
		{"noul true array", `{"type":"noul","instructions":"Judge","criteria":{"true":["yes"],"false":"no"}}`, `{"type":"noul","noul":0.8}`},
		{"noul false array", `{"type":"noul","instructions":"Judge","criteria":{"true":"yes","false":["no"]}}`, `{"type":"noul","noul":0.8}`},
		{"choice array", `{"type":"choice","instructions":"Choose","criteria":{"a":["yes"],"b":"no"}}`, `{"type":"choice","choice":"a"}`},
		{"score array", `{"type":"score","instructions":"Rate","criteria":["low",["high"]]}`, `{"type":"score","score":0.5}`},
		{"noul instructions object", `{"type":"noul","instructions":{"ask":"Judge"}}`, `{"type":"noul","noul":0.8}`},
		{"noul instructions array", `{"type":"noul","instructions":["Judge"]}`, `{"type":"noul","noul":0.8}`},
		{"choice instructions object", `{"type":"choice","instructions":{"ask":"Choose"},"criteria":{"a":"yes","b":"no"}}`, `{"type":"choice","choice":"a"}`},
		{"choice instructions array", `{"type":"choice","instructions":["Choose"],"criteria":{"a":"yes","b":"no"}}`, `{"type":"choice","choice":"a"}`},
		{"score instructions object", `{"type":"score","instructions":{"ask":"Rate"},"criteria":["low","high"]}`, `{"type":"score","score":0.5}`},
		{"score instructions array", `{"type":"score","instructions":["Rate"],"criteria":["low","high"]}`, `{"type":"score","score":0.5}`},
	} {
		t.Run(tc.name, func(t *testing.T) {
			t.Run("routes", func(t *testing.T) {
				checkOllamaEntryCall(t, tc.question, tc.answer, "ollama,openrouter", "openrouter", 0)
			})
			t.Run("local exit", func(t *testing.T) {
				checkOllamaEntryCall(t, tc.question, tc.answer, "ollama", "", 2)
			})
		})
	}
}

func TestOllamaCloudObjectChoiceAndScoreStillAnswer(t *testing.T) {
	for _, tc := range []struct {
		name, question, answer string
	}{
		{"choice object", `{"type":"choice","instructions":"Choose","criteria":{"a":{"when":"yes"},"b":{"when":"no"}}}`, `{"type":"choice","choice":"a","confidence":0.8,"probabilities":{"a":0.9,"b":0.1}}`},
		{"score object", `{"type":"score","instructions":"Rate","criteria":[{"level":"low"},{"level":"high"}]}`, `{"type":"score","score":0.5,"confidence":0.8,"probabilities":{"0":0.5,"1":0.5},"legend":{"0":{"level":"low"},"1":{"level":"high"}}}`},
	} {
		t.Run(tc.name, func(t *testing.T) {
			checkOllamaEntryCall(t, tc.question, tc.answer, "ollama,openrouter", "ollama", 0)
		})
	}
}

// Exercise the CLI and real chain; only the HTTP boundary is replaced. No
// request can escape this transport, including a request to the wrong hop.
func checkOllamaEntryCall(t *testing.T, questionJSON, answer, chain, wantBackend string, wantCode int) {
	t.Helper()
	ollamaCloudEnv(t)
	t.Setenv("JEV_CHAIN", chain)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	calls := make(map[string]int)
	var wantQuestion question
	if err := json.Unmarshal([]byte(questionJSON), &wantQuestion); err != nil {
		t.Fatal(err)
	}
	reply := fmt.Sprintf(`{"model":"fixture","answers":{"q":%s},"usage":{"input_tokens":10,"output_tokens":0}}`, answer)
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls[req.URL.Host]++
		var sent evaluateIn
		if err := json.NewDecoder(req.Body).Decode(&sent); err != nil {
			return nil, err
		}
		if !reflect.DeepEqual(sent.Questions["q"], wantQuestion) {
			t.Errorf("sent question=%+v; want unchanged question=%+v", sent.Questions["q"], wantQuestion)
		}
		return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(reply))}, nil
	})
	input := fmt.Sprintf(`{"state":"ticket","questions":{"q":%s}}`, questionJSON)
	got := runCallForTest(t, callOptions{}, input)
	wantCalls := make(map[string]int)
	if wantBackend != "" {
		req, err := http.NewRequest("POST", providers[wantBackend].EndpointURL, nil)
		if err != nil {
			t.Fatal(err)
		}
		wantCalls[req.URL.Host] = 1
		if strings.TrimSpace(got.stdout) != reply {
			t.Errorf("stdout=%s; want answered reply %s", got.stdout, reply)
		}
	}
	if got.code != wantCode || !reflect.DeepEqual(calls, wantCalls) {
		t.Fatalf("exit=%d requests=%v stderr=%s; want exit=%d requests=%v", got.code, calls, got.stderr, wantCode, wantCalls)
	}
}
