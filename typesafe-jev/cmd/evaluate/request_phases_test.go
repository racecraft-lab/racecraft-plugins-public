package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
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
			writeImageFixture(t, path, data)
			in := imageRequest(nil, "png")
			in.Images["door"] = imageSource{Path: path}
			transport, count := imageOnceTransport(t, primary, fallback, path, data)
			chain := &chainRunner{log: io.Discard, hops: []*Client{
				{Provider: withImages(providers[primary]), Model: providers[primary].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
				{Provider: withImages(providers[fallback]), Model: providers[fallback].DefaultModel, Timeout: time.Second, HTTP: &http.Client{Transport: transport}},
			}}
			session := connect(t, Config{Provider: chain.hops[0].Provider}, chain)
			result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: in})
			if err != nil {
				t.Fatal(err)
			}
			calls := *count
			if result.IsError || contentText(t, result) != noulOK || calls != 2 {
				t.Fatalf("calls=%d; result=%s; isError=%v", calls, contentText(t, result), result.IsError)
			}
		})
	}
}

func imageOnceTransport(t *testing.T, primary, fallback, path string, data []byte) (backendFixtureTransport, *int) {
	t.Helper()
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
		checkOriginalImage(t, provider, body, data)
		return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulOK))}, nil
	})
	return transport, &calls
}

func checkOriginalImage(t *testing.T, provider string, body map[string]any, data []byte) {
	t.Helper()
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

type requestRejectionCase struct {
	name     string
	in       evaluateIn
	want     func(string) string
	oldModel bool
}

// Universal shape errors now precede hop refusals (ADR 0028). Keep the
// parent fixture strict at both entry points, with only replaced contracts
// updated; no locally refused call may reach or move either hop.
func TestRequestPrecedenceMatchesParent(t *testing.T) {
	for _, tc := range requestPrecedenceCases(t) {
		runTestMatrix(t, []string{"typesafe", "openrouter"}, []bool{false, true}, func(primary string, fallback bool) string {
			return fmt.Sprintf("%s/%s/fallback=%v", tc.name, primary, fallback)
		}, func(t *testing.T, primary string, fallback bool) {
			checkRequestPrecedence(t, tc, primary, fallback)
		})
	}
}

func requestPrecedenceCases(t *testing.T) []requestRejectionCase {
	t.Helper()
	dir := t.TempDir()
	missing := filepath.Join(dir, "missing.png")
	malformed := filepath.Join(dir, "malformed.png")
	writeImageFixture(t, malformed, []byte("not an image"))
	tiny := filepath.Join(dir, "tiny.png")
	writeImageFixture(t, tiny, mustPNG(t, 100, 100))
	large := filepath.Join(dir, "large.png")
	data := append(mustPNG(t, 280, 280), make([]byte, 9<<20)...)
	writeImageFixture(t, large, data)
	cases := precedenceQuestionCases()
	cases = append(cases, precedenceImageCases(missing, malformed, tiny, large)...)
	return append(cases, precedenceBoxCases(missing, malformed)...)
}

func precedenceQuestionCases() []requestRejectionCase {
	options := map[string]any{" ": nil}
	for i := 1; i < 256; i++ {
		options[fmt.Sprintf("option%d", i)] = nil
	}
	levels := []any{42, "1", "2", "3", "4", "5", "6", "7", "8", "9", "10"}
	questions := func(a, b question) evaluateIn {
		return evaluateIn{State: "fixture", Questions: map[string]question{"a": a, "b": b}}
	}
	cases := []requestRejectionCase{
		{"choice before missing type", questions(question{Type: typeChoice, Instructions: "judge", Criteria: map[string]any{}}, question{Instructions: "judge"}), func(string) string { return "questions.b.type is required; use noul, choice, score, or box" }, false},
		{"score before missing instructions", questions(question{Type: typeScore, Instructions: "judge", Criteria: []any{"one"}}, question{Type: typeNoul}), func(string) string { return "questions.b.instructions is required" }, false},
		{"score bound before entry", evaluateIn{State: "fixture", Questions: map[string]question{"a": {Type: typeScore, Instructions: "judge", Criteria: levels}}}, func(string) string { return "questions.a.criteria[0] must be a string, object, or array" }, false},
		{"choice bound before name", evaluateIn{State: "fixture", Questions: map[string]question{"a": {Type: typeChoice, Instructions: "judge", Criteria: options}}}, func(string) string { return "questions.a.criteria has a blank option name" }, false},
	}
	return cases
}

func precedenceImageCases(missing, malformed, tiny, large string) []requestRejectionCase {
	imageInput := func(state any, images map[string]imageSource) evaluateIn {
		return evaluateIn{State: state, Questions: simpleIn().Questions, Images: images}
	}
	cases := []requestRejectionCase{
		{"context before malformed image", imageInput([]any{budgetText(300_000), "door"}, map[string]imageSource{"door": {Path: malformed}}), func(p string) string {
			if p == "typesafe" {
				return "the request is about 300012 tokens, over the 64000 the model accepts; send less state or fewer questions"
			}
			return "the request is about 300012 tokens, over the 262144 the model accepts; send less state or fewer questions"
		}, false},
		{"dimensions before unreadable", imageInput([]any{"a", "b"}, map[string]imageSource{"a": {Path: tiny}, "b": {Path: missing}}), func(p string) string {
			if p == "typesafe" {
				return "images.a: sides are 100 by 100 pixels, outside the 280-1568 range this backend accepts"
			}
			return "images.a: sides are 100 by 100 pixels, outside the 256-1568 range this backend accepts"
		}, false},
		{"dimensions before malformed", imageInput([]any{"a", "b"}, map[string]imageSource{"a": {Path: tiny}, "b": {Path: malformed}}), func(p string) string {
			if p == "typesafe" {
				return "images.a: sides are 100 by 100 pixels, outside the 280-1568 range this backend accepts"
			}
			return "images.a: sides are 100 by 100 pixels, outside the 256-1568 range this backend accepts"
		}, false},
		{"expanded budget before unreadable", imageInput([]any{"a", "a", "a", "a", "b"}, map[string]imageSource{"a": {Path: large}, "b": {Path: missing}}), func(p string) string {
			if p == "typesafe" {
				return "images together are over the 33554432 byte expanded request limit, which adds an image again for each use; send fewer or smaller images, or reference each one fewer times"
			}
			return "images together are over the 33554432 byte request limit once base64-encoded; send fewer or smaller images, or reference each one fewer times"
		}, false},
		{"body budget before unreadable", imageInput([]any{"a", "b", "c", "d"}, map[string]imageSource{"a": {Path: large}, "b": {Path: large}, "c": {Path: large}, "d": {Path: missing}}), func(string) string {
			return "images together are over the 33554432 byte request limit once base64-encoded; send fewer or smaller images, or reference each one fewer times"
		}, false},
	}
	return cases
}

func precedenceBoxCases(missing, malformed string) []requestRejectionCase {
	box := func(images map[string]imageSource, state any) evaluateIn {
		return evaluateIn{State: state, Questions: map[string]question{"a": {Type: typeBox, Instructions: "find door"}}, Images: images}
	}
	var cases []requestRejectionCase
	// All model aliases here are the parent's explicit Jev 1.13 refusals.
	for _, tc := range []struct {
		name   string
		images map[string]imageSource
		state  any
	}{
		{"box before missing file", map[string]imageSource{"door": {Path: missing}}, "door"},
		{"box before malformed file", map[string]imageSource{"door": {Path: malformed}}, "door"},
		{"box before no image", nil, "fixture"},
		{"box before unreferenced image", map[string]imageSource{"door": {Path: malformed}}, "fixture"},
	} {
		cases = append(cases, requestRejectionCase{tc.name, box(tc.images, tc.state), func(p string) string {
			model := "jev-1.13.0"
			if p == "openrouter" {
				model = "typesafe/jev-1.13"
			}
			return "model " + model + " is Jev 1.13, which rejects box questions; use jev-latest or jev-1.14.0 on TypeSafe, or typesafe/jev-1.14 or ~typesafe/jev-latest on OpenRouter"
		}, true})
	}
	return cases
}

func checkRequestPrecedence(t *testing.T, tc requestRejectionCase, primary string, fallback bool) {
	t.Helper()
	isolateCallEnv(t)
	t.Setenv("JEV_IMAGES", "true")
	t.Setenv("JEV_LONG_CONTEXT", "false")
	t.Setenv("JEV_PROVIDER", primary)
	t.Setenv(providers[primary].APIKeyEnv, fixtureKey)
	other := map[string]string{"typesafe": "openrouter", "openrouter": "typesafe"}[primary]
	if fallback {
		t.Setenv("JEV_FALLBACK_PROVIDER", other)
		t.Setenv(providers[other].APIKeyEnv, fixtureKey)
	}
	in := tc.in
	if tc.oldModel {
		in.Model = "jev-1.13.0"
		if primary == "openrouter" {
			in.Model = "typesafe/jev-1.13"
		}
	}
	p, f := newCountingBackend(t, 401, "{}"), newCountingBackend(t, 200, validAnswer)
	input, err := json.Marshal(in)
	if err != nil {
		t.Fatal(err)
	}
	want := precedenceRouteDiagnostic(tc, primary, other, fallback)
	result := runCallForTest(t, callOptions{retarget: retargetTo(p, f)}, string(input))
	if result.code != 2 || result.stdout != "" || result.stderr != "evaluate: "+want+"\n" {
		t.Errorf("call = %+v; want exit 2 and %q", result, want)
	}
	spec := withImages(providerAt(primary, p.URL))
	chain := &chainRunner{log: io.Discard, hops: []*Client{{Provider: spec, Model: spec.DefaultModel, Timeout: time.Second, HTTP: p.Client()}}}
	if fallback {
		fs := withImages(providerAt(other, f.URL))
		chain.hops = append(chain.hops, &Client{Provider: fs, Model: fs.DefaultModel, Timeout: time.Second, HTTP: f.Client()})
	}
	session := connect(t, Config{Provider: spec}, chain)
	got, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: in})
	if err != nil {
		t.Fatal(err)
	}
	if !got.IsError || contentText(t, got) != want {
		t.Errorf("MCP isError=%v message=%q; want %q", got.IsError, contentText(t, got), want)
	}
	if p.hits.Load() != 0 || f.hits.Load() != 0 || chain.current.Load() != 0 {
		t.Errorf("locally refused call reached or moved hops: %d/%d, current=%d", p.hits.Load(), f.hits.Load(), chain.current.Load())
	}
}

func precedenceRouteDiagnostic(tc requestRejectionCase, primary, other string, fallback bool) string {
	want := tc.want(primary)
	switch tc.name {
	case "context before malformed image", "dimensions before unreadable", "dimensions before malformed", "expanded budget before unreadable", "body budget before unreadable":
		if fallback {
			want = fmt.Sprintf("no backend can take this request: %s: %s; %s: %s", primary, want, other, tc.want(other))
		}
	case "box before no image":
		want = "a box question needs an image in the request"
	case "box before unreferenced image":
		want = "images.door is not referenced from state, instructions, or criteria"
	case "box before missing file":
		if fallback {
			want = "images.door: the image file cannot be read"
		}
	case "box before malformed file":
		if fallback {
			want = "images.door: not a PNG, JPEG, or WebP"
		}
	}
	return want
}

// Wrap the filesystem read seam on this call only. Later sources must never
// be read, even when their contents would otherwise be valid.
func TestRefusedRequestLeavesLaterImageUnread(t *testing.T) {
	for _, provider := range []string{"typesafe", "openrouter"} {
		for _, refusal := range []string{"box model", "dimensions", "expanded budget", "body budget"} {
			t.Run(provider+"/"+refusal, func(t *testing.T) {
				path := filepath.Join(t.TempDir(), "later.png")
				data := mustPNG(t, 280, 280)
				writeImageFixture(t, path, data)
				in := refusedImageRequest(t, provider, refusal, path, data)
				spec := withImages(providers[provider])
				shaped, err := shapeRequest(in)
				if err != nil {
					t.Fatal(err)
				}
				shaped.images.read = func(name string, src imageSource, limit int, haystack string) (preparedImage, error) {
					if src.Path == path {
						t.Fatal("refused request read a later image")
					}
					return readOneImage(name, src, limit, haystack)
				}
				_, err = prepareForHop(&Client{Provider: spec, Model: spec.DefaultModel}, shaped)
				var hop *hopRefusalError
				if !errors.As(err, &hop) {
					t.Fatalf("want earlier hop refusal, got %v", err)
				}
			})
		}
	}
}

func refusedImageRequest(t *testing.T, provider, refusal, path string, data []byte) evaluateIn {
	t.Helper()
	in := evaluateIn{State: []any{"a", "b"}, Questions: simpleIn().Questions, Images: map[string]imageSource{"b": {Path: path}}}
	switch refusal {
	case "box model":
		in.Questions = map[string]question{"q": {Type: typeBox, Instructions: "find"}}
		in.Model = "jev-1.13.0"
		if provider == "openrouter" {
			in.Model = "typesafe/jev-1.13"
		}
	case "dimensions":
		in.Images["a"] = imageSource{DataBase64: b64(mustPNG(t, 100, 100))}
	case "expanded budget":
		in.State = []any{"a", "a", "a", "a", "b"}
		in.Images["a"] = imageSource{DataBase64: b64(append(data, make([]byte, 9<<20)...))}
	case "body budget":
		in.State = []any{"a", "aa", "ab", "b"}
		encoded := b64(append(data, make([]byte, 9<<20)...))
		for _, name := range []string{"a", "aa", "ab"} {
			in.Images[name] = imageSource{DataBase64: encoded}
		}
	}
	return in
}

func TestInternalPreparationErrorsNeverRefuseAHop(t *testing.T) {
	for _, tc := range []struct {
		name   string
		change func(*ProviderSpec)
		want   string
	}{
		{"wire format", func(spec *ProviderSpec) { spec.WireFormat = imageWireFormat(255) }, "internal: typesafe has no supported image wire format"},
		{"image limits", func(spec *ProviderSpec) { spec.ImageLimits = imageBounds{} }, "internal: typesafe has no image limits"},
		{"context budget", func(spec *ProviderSpec) { spec.RequestTokens = 0 }, "internal: typesafe has no context budget"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			spec := withImages(typesafeSpec)
			tc.change(&spec)
			_, err := prepare(&Client{Provider: spec, Model: spec.DefaultModel}, imageRequest(mustPNG(t, 280, 280), "png"))
			var hop *hopRefusalError
			var shape *requestShapeError
			if err == nil || err.Error() != tc.want || errors.As(err, &hop) || errors.As(err, &shape) {
				t.Fatalf("internal error = %T %v; want unclassified %q", err, err, tc.want)
			}
		})
	}
}

func writeImageFixture(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
}

// prepare resolves the model, validates, and encodes. It makes no network
// call, and every error it returns is a *requestInvalidError.
func prepare(c *Client, in evaluateIn) (preparedCall, error) {
	shaped, err := shapeRequest(in)
	if err != nil {
		return preparedCall{}, &requestInvalidError{err}
	}
	return prepareForHop(c, shaped)
}
