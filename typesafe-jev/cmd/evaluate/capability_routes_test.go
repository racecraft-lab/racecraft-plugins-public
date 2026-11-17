package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"
	"time"

	"github.com/modelcontextprotocol/go-sdk/mcp"
)

// Every hop has an intercepted transport, including the synthetic third hop
// used to exercise composition before additional providers are registered.
func capabilitySession(t *testing.T, specs []ProviderSpec, statuses []int) (*mcp.ClientSession, []int, *strings.Builder) {
	t.Helper()
	hits := make([]int, len(specs))
	log := new(strings.Builder)
	chain := &chainRunner{log: log}
	for i, spec := range specs {
		chain.hops = append(chain.hops, &Client{
			Provider: spec, Model: spec.DefaultModel, Timeout: 5 * time.Second,
			HTTP: &http.Client{Transport: backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				hits[i]++
				var sent evaluateIn
				if err := json.NewDecoder(req.Body).Decode(&sent); err != nil {
					return nil, err
				}
				if i > 0 && sent.Model != spec.DefaultModel {
					t.Errorf("hop %d received model %q, want %q", i, sent.Model, spec.DefaultModel)
				}
				answers := make(map[string]any)
				for id, q := range sent.Questions {
					answer := map[string]any{"type": q.Type, "noul": 0.42}
					if q.Type == typeChoice {
						answer = map[string]any{"type": q.Type, "choice": "only"}
					}
					answers[id] = answer
				}
				body, err := json.Marshal(map[string]any{"model": "fixture", "usage": map[string]int{}, "answers": answers})
				if err != nil {
					return nil, err
				}
				return &http.Response{StatusCode: statuses[i], Header: http.Header{}, Body: io.NopCloser(strings.NewReader(string(body)))}, nil
			})},
		})
	}
	return connect(t, Config{Provider: specs[0]}, chain), hits, log
}

func TestCapabilityRouteChecksEachRowsLimits(t *testing.T) {
	for _, limit := range []string{"questions", "choice minimum", "question type", "request context", "question context", "body", "image count", "image bytes", "total image bytes", "image dimensions", "image opt-in", "image trust"} {
		t.Run(limit, func(t *testing.T) {
			first, second := withImages(typesafeSpec), withImages(providers["openrouter"])
			in := simpleIn()
			wantAnswer := `"noul":0.42`
			if strings.HasPrefix(limit, "image") || limit == "total image bytes" {
				in = imageRequest(mustPNG(t, 280, 280), "png")
			}
			switch limit {
			case "questions":
				first.Limits.Questions = 1
				in.Questions = map[string]question{"a": {Type: typeNoul, Instructions: "judge"}, "b": {Type: typeNoul, Instructions: "judge"}}
			case "choice minimum":
				first.Limits.ChoiceMin = 2
				in.Questions = map[string]question{"q": {Type: typeChoice, Instructions: "judge", Criteria: map[string]any{"only": "only option"}}}
				wantAnswer = `"choice":"only"`
			case "question type":
				first.QuestionTypes = []string{typeChoice}
			case "request context":
				first.RequestTokens = 1
			case "question context":
				first.QuestionTokens = 1
			case "body":
				first.Limits.BodyBytes = 1
			case "image count":
				first.Limits.Images = 1
				in.Images["second"] = in.Images["door"]
				in.State = []any{"door", "second"}
			case "image bytes":
				first.Limits.ImageBytes = 1
			case "total image bytes":
				first.Limits.TotalImageBytes = 1
			case "image dimensions":
				first.ImageLimits.MinSide = 300
			case "image opt-in":
				first.AllowImages = false
			case "image trust":
				first.ImageTrust = imageTrust(0)
			}
			session, hits, log := capabilitySession(t, []ProviderSpec{first, second}, []int{200, 200})
			capabilityCall(t, session, in, false, wantAnswer)
			if fmt.Sprint(hits) != "[0 1]" || log.Len() != 0 {
				t.Fatalf("hits=%v log=%q; want only the able hop and no move", hits, log.String())
			}
		})
	}
}

func capabilityCall(t *testing.T, session *mcp.ClientSession, in evaluateIn, wantError bool, contains string) {
	t.Helper()
	result, err := session.CallTool(context.Background(), &mcp.CallToolParams{Name: "evaluate", Arguments: in})
	if err != nil {
		t.Fatal(err)
	}
	if result.IsError != wantError || !strings.Contains(contentText(t, result), contains) {
		t.Fatalf("isError=%v content=%q; want error=%v containing %q", result.IsError, contentText(t, result), wantError, contains)
	}
}

func TestCapabilityRouteLeavesNextCallOnSessionHop(t *testing.T) {
	session, hits, log := capabilitySession(t, []ProviderSpec{typesafeSpec, providers["openrouter"]}, []int{200, 200})
	large := evaluateIn{State: budgetText(100_000), Questions: simpleIn().Questions, Model: "caller-model"}
	capabilityCall(t, session, large, false, `"noul":0.42`)
	capabilityCall(t, session, simpleIn(), false, `"noul":0.42`)
	if fmt.Sprint(hits) != "[1 1]" || log.Len() != 0 {
		t.Fatalf("hits=%v log=%q; want [1 1] and no session move", hits, log.String())
	}
}

func TestCapabilityRouteComposesWithFailures(t *testing.T) {
	third := typesafeSpec
	third.Name, third.DefaultModel = "third", "third-default"
	third.BillingAccount = third.Name
	for _, tc := range []struct {
		name                      string
		limited                   int
		statuses                  []int
		firstHits, nextHits, move string
	}{
		{"routed failure leaves session", 0, []int{200, 401, 200}, "[0 1 1]", "[1 1 1]", ""},
		{"failure moves before routing", 1, []int{401, 200, 200}, "[1 0 1]", "[1 1 1]", "using the openrouter fallback"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			specs := []ProviderSpec{typesafeSpec, providers["openrouter"], third}
			specs[tc.limited].Limits.Questions = 1
			session, hits, log := capabilitySession(t, specs, tc.statuses)
			in := simpleIn()
			in.Questions = map[string]question{"a": {Type: typeNoul, Instructions: "judge"}, "b": {Type: typeNoul, Instructions: "judge"}}
			capabilityCall(t, session, in, false, `"noul":0.42`)
			if fmt.Sprint(hits) != tc.firstHits {
				t.Fatalf("hits=%v; want %s", hits, tc.firstHits)
			}
			capabilityCall(t, session, simpleIn(), false, `"noul":0.42`)
			if fmt.Sprint(hits) != tc.nextHits || (tc.move == "" && log.Len() != 0) || (tc.move != "" && strings.Count(log.String(), tc.move) != 1) {
				t.Fatalf("hits=%v log=%q; want %s, move=%q", hits, log.String(), tc.nextHits, tc.move)
			}
		})
	}
}

func TestCapabilityRoutesRespectEveryHopsImageOptIn(t *testing.T) {
	for _, route := range []bool{false, true} {
		t.Run(fmt.Sprintf("route=%v", route), func(t *testing.T) {
			first := withImages(typesafeSpec)
			status := 401
			wantHits := "[1 0]"
			if route {
				first.Limits.Images = 1
				status, wantHits = 200, "[0 0]"
			}
			session, hits, _ := capabilitySession(t, []ProviderSpec{first, providers["openrouter"]}, []int{status, 200})
			in := imageRequest(mustPNG(t, 280, 280), "png")
			if route {
				in.Images["second"] = in.Images["door"]
				in.State = []any{"door", "second"}
			}
			wantReason := "images and box questions are disabled"
			if route {
				wantReason = "images has 2 entries, over the 1 the backend accepts"
			}
			capabilityCall(t, session, in, true, wantReason)
			if fmt.Sprint(hits) != wantHits {
				t.Fatalf("hits=%v; want %s; a hop without opt-in must receive no images", hits, wantHits)
			}
		})
	}
}

func TestCapabilityRouteRejectsUniversalShapeBeforeHopLimits(t *testing.T) {
	in := simpleIn()
	in.Questions = map[string]question{
		"a": {Type: typeScore, Instructions: "judge", Criteria: []any{"one"}},
		"b": {Type: typeNoul},
	}
	session, hits, log := capabilitySession(t, []ProviderSpec{typesafeSpec, providers["openrouter"]}, []int{200, 200})
	capabilityCall(t, session, in, true, "questions.b.instructions is required")
	if fmt.Sprint(hits) != "[0 0]" || log.Len() != 0 {
		t.Fatalf("hits=%v log=%q; want no calls or move", hits, log.String())
	}
}

type capabilityCallCase struct {
	name                 string
	tokens, status, code int
	hits                 string
	reasons              []string
}

func TestCapabilityRouteCallExitCodes(t *testing.T) {
	for _, tc := range []capabilityCallCase{
		{"no able hop is local", 300_000, 200, 2, "0/0", []string{"over the 64000"}},
		{"route answers", 100_000, 200, 0, "0/1", nil},
		{"moved session retains failure", 100_000, 503, 5, "1/0", []string{"HTTP 503", "fallback cannot take this request", "JEV_LONG_CONTEXT", "using the typesafe fallback"}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", "typesafe,openrouter")
			if tc.status == 503 {
				t.Setenv("JEV_CHAIN", "openrouter,typesafe")
			}
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv("JEV_LONG_CONTEXT", "false")
			p, f := newCountingBackend(t, tc.status, validAnswer), newCountingBackend(t, 200, validAnswer)
			input, err := json.Marshal(evaluateIn{State: budgetText(tc.tokens), Questions: simpleIn().Questions})
			if err != nil {
				t.Fatal(err)
			}
			got := runCallForTest(t, callOptions{retarget: retargetTo(p, f)}, string(input))
			if got.code != tc.code || fmt.Sprintf("%d/%d", p.hits.Load(), f.hits.Load()) != tc.hits {
				t.Fatalf("call=%+v hits=%d/%d; want exit %d, hits %s", got, p.hits.Load(), f.hits.Load(), tc.code, tc.hits)
			}
			checkCapabilityCallOutput(t, tc, got)
		})
	}
}

func checkCapabilityCallOutput(t *testing.T, tc capabilityCallCase, got callResult) {
	t.Helper()
	if tc.code == 0 && strings.TrimSpace(got.stdout) != validAnswer || tc.code != 0 && got.stdout != "" {
		t.Fatalf("unexpected stdout: %q", got.stdout)
	}
	for _, reason := range tc.reasons {
		if !strings.Contains(got.stderr, reason) {
			t.Errorf("stderr=%q; want %q", got.stderr, reason)
		}
	}
}

func TestCapabilityRouteInternalPreparationFailureKeepsProviderExit(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	p, f := newCountingBackend(t, 401, "{}"), newCountingBackend(t, 200, validAnswer)
	got := runCallForTest(t, callOptions{retarget: func(cfg *Config) {
		retargetTo(p, f)(cfg)
		cfg.Fallback.Provider.RequestTokens = 0
	}}, validRequest)
	if got.code != 5 || got.stdout != "" || p.hits.Load() != 1 || f.hits.Load() != 0 || !strings.Contains(got.stderr, "HTTP 401") || !strings.Contains(got.stderr, "internal: openrouter has no context budget") {
		t.Fatalf("call=%+v hits=%d/%d; want provider failure with internal preparation reason", got, p.hits.Load(), f.hits.Load())
	}
}
