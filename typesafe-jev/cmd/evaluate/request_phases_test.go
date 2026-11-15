package main

import (
	"context"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Pin the public local-rejection contract before separating its two phases.
// These literals are today's diagnostics, not output derived from a validator.
func TestRequestRejectionCompatibilityFixture(t *testing.T) {
	for _, provider := range []string{"typesafe", "openrouter"} {
		for _, tc := range []struct {
			name string
			in   evaluateIn
			want string
		}{
			{"state", evaluateIn{Questions: simpleIn().Questions}, "state is required"},
			{"questions", evaluateIn{State: "fixture"}, "questions must not be empty"},
			{"model", evaluateIn{State: "fixture", Model: " ", Questions: simpleIn().Questions}, "model is whitespace only; omit it to use the configured default"},
			{"type", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Instructions: "judge"}}}, "questions.q.type is required; use noul, choice, score, or box"},
			{"instructions", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Type: typeNoul}}}, "questions.q.instructions is required"},
			{"choice", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Type: typeChoice, Instructions: "judge", Criteria: map[string]any{}}}}, "questions.q.criteria must name at least one option"},
			{"score", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Type: typeScore, Instructions: "judge", Criteria: []any{"one"}}}}, "questions.q.criteria needs at least 2 ordered levels"},
			{"images disabled", imageRequest([]byte("not an image"), ""), "images and box questions are disabled; set JEV_IMAGES=true to send them"},
		} {
			t.Run(provider+"/"+tc.name, func(t *testing.T) {
				spec := providers[provider]
				_, err := prepare(&Client{Provider: spec, Model: spec.DefaultModel}, tc.in)
				var local *requestInvalidError
				if !errors.As(err, &local) || err.Error() != tc.want {
					t.Fatalf("local error = %T %v; want requestInvalidError: %s", err, err, tc.want)
				}

				isolateCallEnv(t)
				t.Setenv("JEV_PROVIDER", provider)
				t.Setenv(spec.APIKeyEnv, fixtureKey)
				backend := newCountingBackend(t, 200, validAnswer)
				input, err := json.Marshal(tc.in)
				if err != nil {
					t.Fatal(err)
				}
				result := runCallForTest(t, callOptions{retarget: retargetTo(backend, nil)}, string(input))
				if result.code != 2 || result.stdout != "" || result.stderr != "evaluate: "+tc.want+"\n" || backend.hits.Load() != 0 {
					t.Fatalf("call = %+v; requests=%d", result, backend.hits.Load())
				}
			})
		}
	}
}

// The source disappears after the primary receives it. The fallback must use
// the same bytes, encoded in its own format, without opening the path again.
func TestCallReadsImagesOnceAcrossHops(t *testing.T) {
	for _, primary := range []string{"typesafe", "openrouter"} {
		t.Run(primary, func(t *testing.T) {
			fallback := map[string]string{"typesafe": "openrouter", "openrouter": "typesafe"}[primary]
			data := mustPNG(t, 280, 280)
			path := filepath.Join(t.TempDir(), "photo.png")
			if err := os.WriteFile(path, data, 0o600); err != nil {
				t.Fatal(err)
			}
			in := imageRequest(nil, "png")
			in.Images["door"] = imageSource{Path: path}
			calls := 0
			transport := backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				calls++
				var body map[string]any
				if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
					return nil, err
				}
				provider := primary
				status := 401
				if calls == 1 {
					if err := os.Remove(path); err != nil {
						return nil, err
					}
				} else {
					provider, status = fallback, 200
				}
				if req.URL.String() != providers[provider].EndpointURL {
					t.Errorf("request %d went to %s", calls, req.URL)
				}
				photo := body["state"].(map[string]any)["photo"]
				if provider == "typesafe" {
					ref := photo.(string)
					asset := body["assets"].(map[string]any)[ref].(map[string]any)
					if asset["data_base64"] != b64(data) || asset["format"] != "png" {
						t.Error("TypeSafe did not receive the original PNG")
					}
				} else {
					part := photo.(map[string]any)
					if part["image_url"].(map[string]any)["url"] != "data:image/png;base64,"+b64(data) {
						t.Error("OpenRouter did not receive the original PNG")
					}
				}
				return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulOK))}, nil
			})
			chain := &chainRunner{log: io.Discard, hops: []*Client{
				{Provider: withImages(providers[primary]), Model: providers[primary].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
				{Provider: withImages(providers[fallback]), Model: providers[fallback].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
			}}
			session := connect(t, Config{Provider: chain.hops[0].Provider}, chain)
			result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: in})
			if err != nil {
				t.Fatal(err)
			}
			if result.IsError || contentText(t, result) != noulOK || calls != 2 {
				t.Fatalf("calls=%d; result=%s; isError=%v", calls, contentText(t, result), result.IsError)
			}
		})
	}
}

func TestRequestPhasesReturnDifferentTypedErrors(t *testing.T) {
	for _, tc := range []struct {
		name  string
		in    evaluateIn
		spec  ProviderSpec
		shape bool
	}{
		{"missing state", evaluateIn{Questions: simpleIn().Questions}, typesafeSpec, true},
		{"invalid instructions", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Type: typeNoul, Instructions: 42}}}, typesafeSpec, true},
		{"choice minimum", evaluateIn{State: "fixture", Questions: map[string]question{"q": {Type: typeChoice, Instructions: "judge", Criteria: map[string]any{}}}}, typesafeSpec, false},
		{"context budget", evaluateIn{State: budgetText(100_000), Questions: simpleIn().Questions}, typesafeSpec, false},
		{"image dimensions", imageRequest(mustPNG(t, 256, 320), "png"), withImages(typesafeSpec), false},
		{"malformed image", imageRequest([]byte("not an image"), ""), withImages(typesafeSpec), true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, err := prepare(&Client{Provider: tc.spec, Model: tc.spec.DefaultModel}, tc.in)
			var local *requestInvalidError
			var shape *requestShapeError
			var hop *hopRefusalError
			if !errors.As(err, &local) || errors.As(err, &shape) != tc.shape || errors.As(err, &hop) == tc.shape {
				t.Fatalf("error=%T %v; want local rejection with shape=%v", err, err, tc.shape)
			}
		})
	}
}

// An oversized file is a hop limit even when its bytes are not an image. The
// size diagnostic must win, as it did before the phase split.
func TestOversizedImageKeepsItsLimitDiagnostic(t *testing.T) {
	path := filepath.Join(t.TempDir(), "oversized.png")
	f, err := os.Create(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := f.Truncate(maxImageBytes + 1); err != nil {
		f.Close()
		t.Fatal(err)
	}
	if err := f.Close(); err != nil {
		t.Fatal(err)
	}
	in := imageRequest(nil, "")
	in.Images["door"] = imageSource{Path: path}
	spec := withImages(typesafeSpec)
	_, err = prepare(&Client{Provider: spec, Model: spec.DefaultModel}, in)
	var hop *hopRefusalError
	if !errors.As(err, &hop) || err.Error() != "images.door: the file is 16777217 bytes, over the 16777216 byte limit" {
		t.Fatalf("error=%v; want the existing per-file limit diagnostic", err)
	}
}
