package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"
)

const ollamaTextRequest = `{"state":{"ticket":"checkout failed"},"questions":{"urgent":{"type":"noul","instructions":"Needs attention now?"},"label":{"type":"choice","instructions":"Which label?","criteria":{"bug":"Software error","billing":"Payment issue"}},"impact":{"type":"score","instructions":"How severe?","criteria":["low","medium","high"]}}}`

const ollamaTextReply = `{"model":"clef","answers":{"urgent":{"type":"noul","noul":0.9835},"label":{"type":"choice","choice":"bug","confidence":0.8906,"probabilities":{"billing":0.0125,"bug":0.9875}},"impact":{"type":"score","score":1.8,"confidence":0.7,"probabilities":{"0":0.05,"1":0.1,"2":0.85},"legend":{"0":"low","1":"medium","2":"high"}}},"usage":{"input_tokens":355,"output_tokens":0}}`

func ollamaCloudEnv(t *testing.T) string {
	t.Helper()
	home := isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "ollama")
	t.Setenv("OLLAMA_API_KEY", fixtureKey)
	return home
}

func fakeOllamaTransport(t *testing.T, fn backendFixtureTransport) {
	t.Helper()
	previous := http.DefaultTransport
	http.DefaultTransport = fn
	t.Cleanup(func() { http.DefaultTransport = previous })
}

func blockOllamaHTTP(t *testing.T) {
	t.Helper()
	fakeOllamaTransport(t, func(*http.Request) (*http.Response, error) {
		t.Error("local check must never make a network call")
		return nil, fmt.Errorf("unexpected HTTP call")
	})
}

func TestOllamaCloudGoldenTextRequestAndAnswers(t *testing.T) {
	ollamaCloudEnv(t)
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		body, err := io.ReadAll(req.Body)
		if err != nil {
			return nil, err
		}
		const golden = `{"state":{"ticket":"checkout failed"},"questions":{"impact":{"type":"score","instructions":"How severe?","criteria":["low","medium","high"]},"label":{"type":"choice","instructions":"Which label?","criteria":{"billing":"Payment issue","bug":"Software error"}},"urgent":{"type":"noul","instructions":"Needs attention now?"}},"model":"clef"}`
		if req.Method != "POST" || req.URL.String() != "https://ollama.com/v1/systemone" || string(body) != golden {
			t.Errorf("unexpected wire request: %s %s %s", req.Method, req.URL, body)
		}
		if req.Header.Get("Authorization") != "Bearer "+fixtureKey || req.Header.Get("Content-Type") != "application/json" {
			t.Error("cloud request needs Bearer authentication and JSON")
		}
		for _, header := range []string{headerDangerImages, headerDangerLong, "HTTP-Referer", "X-OpenRouter-Title"} {
			if req.Header.Get(header) != "" {
				t.Errorf("unexpected header %s", header)
			}
		}
		return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(ollamaTextReply))}, nil
	})
	got := runCallForTest(t, callOptions{}, ollamaTextRequest)
	if got.code != 0 || strings.TrimSpace(got.stdout) != ollamaTextReply || calls != 1 {
		t.Fatalf("exit=%d calls=%d stdout=%s stderr=%s", got.code, calls, got.stdout, got.stderr)
	}
}

func TestOllamaCloudCapabilityRoutesAndLocalExit(t *testing.T) {
	for name, input := range ollamaCapabilityRequests(t) {
		t.Run(name, func(t *testing.T) {
			checkOllamaRoute(t, input, false, name == "image")
			checkOllamaRoute(t, input, true, name == "image")
		})
	}
}

func checkOllamaRoute(t *testing.T, input evaluateIn, later, accepts bool) {
	t.Helper()
	ollamaCloudEnv(t)
	t.Setenv("JEV_IMAGES", "true")
	wantCode, wantCalls := 2, 0
	wantProvider := "openrouter"
	if later {
		t.Setenv("JEV_CHAIN", "ollama,openrouter")
		t.Setenv("OPENROUTER_API_KEY", fixtureKey)
		wantCode, wantCalls = 0, 1
	}
	if accepts {
		wantCode, wantCalls, wantProvider = 0, 1, "ollama"
	}
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		if req.URL.String() != providers[wantProvider].EndpointURL {
			t.Errorf("refused request reached %s", req.URL)
		}
		return ollamaRouteReply(req)
	})
	body, err := json.Marshal(input)
	if err != nil {
		t.Fatal(err)
	}
	got := runCallForTest(t, callOptions{}, string(body))
	if got.code != wantCode || calls != wantCalls {
		t.Fatalf("exit=%d calls=%d stderr=%s; want exit=%d calls=%d", got.code, calls, got.stderr, wantCode, wantCalls)
	}
}

func ollamaCapabilityRequests(t *testing.T) map[string]evaluateIn {
	t.Helper()
	many := simpleIn()
	many.Questions = make(map[string]question)
	for i := range 65 {
		many.Questions[fmt.Sprintf("q%d", i)] = question{Type: typeNoul, Instructions: "Judge this"}
	}
	one := simpleIn()
	one.Questions = map[string]question{"q": {Type: typeChoice, Instructions: "Choose", Criteria: map[string]any{"only": "Only option"}}}
	image := imageRequest(mustPNG(t, 280, 280), "png")
	box := imageRequest(mustPNG(t, 280, 280), "png")
	box.Questions = map[string]question{"q": {Type: typeBox, Instructions: "door"}}
	context := simpleIn()
	context.State = budgetText(66_000)
	body := simpleIn()
	// Model is outside the context estimate. This isolates the serialized
	// body cap without first tripping the smaller text budget.
	body.Model = strings.Repeat("m", 13<<20)
	spaced := simpleIn()
	spaced.Questions = map[string]question{"is this urgent?": {Type: typeNoul, Instructions: "Judge this"}}
	long := simpleIn()
	long.Questions = map[string]question{strings.Repeat("q", 101): {Type: typeNoul, Instructions: "Judge this"}}
	return map[string]evaluateIn{"box": box, "65 questions": many, "one option": one, "image": image, "context": context, "body": body,
		"id characters": spaced, "id length": long}
}

func ollamaRouteReply(req *http.Request) (*http.Response, error) {
	// Images are backend wire data, not the neutral input images map.
	var wire struct {
		Model     string              `json:"model"`
		Questions map[string]question `json:"questions"`
	}
	if err := json.NewDecoder(req.Body).Decode(&wire); err != nil {
		return nil, err
	}
	answers := make(map[string]any)
	for id, q := range wire.Questions {
		answer := map[string]any{"type": q.Type, "noul": 0.8}
		switch q.Type {
		case typeChoice:
			answer = map[string]any{"type": q.Type, "choice": "only"}
		case typeBox:
			answer = map[string]any{"type": q.Type, "box": map[string]float64{"top": 0.1, "left": 0.2, "bottom": 0.8, "right": 0.9}}
		}
		answers[id] = answer
	}
	body, err := json.Marshal(map[string]any{"model": wire.Model, "answers": answers, "usage": map[string]int{"input_tokens": 10, "output_tokens": 0}})
	return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(string(body)))}, err
}

func TestOllamaCloudPluginCredentialDiscoveryAndCheck(t *testing.T) {
	for _, key := range []string{fixtureKey, ""} {
		t.Run(fmt.Sprintf("usable=%v", key != ""), func(t *testing.T) {
			home := ollamaCloudEnv(t)
			writeDefaultKey(t, home, "ollama", key, 0600)
			blockOllamaHTTP(t)
			got := runCallForTest(t, callOptions{check: true, pluginDefaults: true}, "")
			var report checkReport
			if err := json.Unmarshal([]byte(got.stdout), &report); err != nil {
				t.Fatal(err)
			}
			wantCode, wantState := 0, "ok"
			if key == "" {
				wantCode, wantState = 4, "unusable"
			}
			if got.code != wantCode || report.Primary.Provider != "ollama" || report.Primary.Source != "default-file" || report.Primary.State != wantState {
				t.Fatalf("exit=%d report=%+v stderr=%s", got.code, report, got.stderr)
			}
		})
	}
}

func TestOllamaCloudImageRequestAnswers(t *testing.T) {
	ollamaCloudEnv(t)
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		if req.URL.String() != providers["ollama"].EndpointURL {
			t.Errorf("image request went to %s", req.URL)
		}
		return ollamaImageResponse(), nil
	})
	t.Setenv("JEV_IMAGES", "true")
	body, err := json.Marshal(imageRequest(mustPNG(t, 280, 280), "png"))
	if err != nil {
		t.Fatal(err)
	}
	got := runCallForTest(t, callOptions{}, string(body))
	if got.code != 0 || strings.TrimSpace(got.stdout) != noulOK || calls != 1 {
		t.Fatalf("exit=%d calls=%d stdout=%s stderr=%s", got.code, calls, got.stdout, got.stderr)
	}
}
