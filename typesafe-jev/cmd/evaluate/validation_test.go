package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
)

var (
	typesafeSpec   = providers["typesafe"]
	openrouterSpec = providers["openrouter"]
)

// jsonValue round-trips through JSON so a test case has the same dynamic types
// the MCP SDK hands the handler: map[string]any, []any, string.
func jsonValue(t *testing.T, literal string) any {
	t.Helper()
	var v any
	if err := json.Unmarshal([]byte(literal), &v); err != nil {
		t.Fatal(err)
	}
	return v
}

// threePrimitives is the synthetic batch from examples/openrouter-request.json:
// one noul, one choice, one score over the same state.
func threePrimitives(t *testing.T) evaluateIn {
	t.Helper()
	return evaluateIn{
		State: "A production checkout service is unavailable and customers cannot complete purchases.",
		Questions: map[string]question{
			"customer_impact": {
				Type:         "noul",
				Instructions: "Does the incident describe a customer-impacting service failure?",
				Criteria: jsonValue(t, `{
					"true": "Customers are unable to complete a normal operation.",
					"false": "No customer-facing operation is impaired."
				}`),
			},
			"owner": {
				Type:         "choice",
				Instructions: "Which team should initially investigate this incident?",
				Criteria: jsonValue(t, `{
					"billing": "An invoice, charge, or refund dispute without a service outage.",
					"engineering": "A technical service failure that prevents a normal operation.",
					"sales": "A question about purchasing, pricing, or a contract.",
					"unknown": "The incident does not provide enough evidence to select a team."
				}`),
			},
			"disruption": {
				Type:         "score",
				Instructions: "Rate the operational disruption described by the incident.",
				Criteria: jsonValue(t, `[
					"Minor disruption: the operation remains available.",
					"Major disruption: the operation is degraded or intermittently fails.",
					"Service unavailable: customers cannot complete the operation."
				]`),
			},
		},
		Model: "~typesafe/jev-latest",
	}
}

// REQ-01: the documented three-primitive batch is accepted by both backends.
func TestValidateRequestAcceptsThreePrimitives(t *testing.T) {
	in := threePrimitives(t)
	for _, spec := range []ProviderSpec{typesafeSpec, openrouterSpec} {
		if err := validateRequest(spec, in); err != nil {
			t.Errorf("%s: %v", spec.Name, err)
		}
	}
}

// REQ-02, REQ-03: both backends document structured instructions. TypeSafe
// always has; OpenRouter's Decisions schemas typed them as plain strings until
// it republished them as anyOf string, object, or array. Neither backend may
// reject the structured form, and neither may stringify it to force it through.
func TestStructuredInstructionsAcceptedOnBothBackends(t *testing.T) {
	for _, literal := range []string{
		`{"field":{"name":"amount_due","type":"number"},"question":"How large is it?"}`,
		`["compare sender name","compare sender domain"]`,
	} {
		in := evaluateIn{
			State:     "x",
			Questions: map[string]question{"q": {Type: "noul", Instructions: jsonValue(t, literal)}},
		}
		for _, spec := range []ProviderSpec{typesafeSpec, openrouterSpec} {
			if err := validateRequest(spec, in); err != nil {
				t.Errorf("%s rejected documented structure %s: %v", spec.Name, literal, err)
			}
		}
	}
}

// A backend that types these fields as plain strings must still be narrowed.
// The capability drives the rule, so this is what re-narrowing would cost.
func TestStructuredInstructionsRejectedWhenBackendLacksSupport(t *testing.T) {
	narrow := openrouterSpec
	narrow.StructuredEntries = false

	in := evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: jsonValue(t, `{"question":"structured"}`)}},
	}
	err := validateRequest(narrow, in)
	if err == nil {
		t.Fatal("a string-only backend accepted structured instructions")
	}
	if !strings.Contains(err.Error(), "questions.q.instructions") {
		t.Errorf("error should name the field path: %v", err)
	}
}

// REQ-04, REQ-05: a null choice description means "the option name says it".
// Both backends document it: TypeSafe for every entry field, OpenRouter for
// choice option descriptions, which is the only optional entry this server has.
func TestNullChoiceDescriptionAcceptedOnBothBackends(t *testing.T) {
	in := evaluateIn{
		State: "x",
		Questions: map[string]question{
			"customer_name": {
				Type:         "choice",
				Instructions: "Which option is the value in the source text?",
				Criteria:     jsonValue(t, `{"Beaver Dam Logistics": null, "Dam Logistics": null}`),
			},
		},
	}
	for _, spec := range []ProviderSpec{typesafeSpec, openrouterSpec} {
		if err := validateRequest(spec, in); err != nil {
			t.Errorf("%s rejected a documented null description: %v", spec.Name, err)
		}
	}
}

// REQ-03, REQ-05: a locally rejected request costs nothing, so the provider
// must never be contacted.
func TestLocalRejectionMakesNoRequest(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Write([]byte(`{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{}}`))
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	// Structure is accepted on both backends now, so the trigger is a rule
	// that is still local: a blank instruction string.
	_, err := runEvaluate(context.Background(), c, evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "   "}},
	})
	if err == nil {
		t.Fatal("want a validation error")
	}
	if calls.Load() != 0 {
		t.Fatalf("made %d HTTP requests for a locally invalid call", calls.Load())
	}
}

// REQ-06: every malformed shape is refused with a field path, and the error
// never quotes the value, which may be the private state being judged.
func TestValidateRequestRejectsMalformedShapes(t *testing.T) {
	const sentinel = "confidential-incident-detail"
	for name, in := range map[string]evaluateIn{
		"no state":          {Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}}},
		"numeric state":     {State: jsonValue(t, `42`), Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}}},
		"boolean state":     {State: jsonValue(t, `true`), Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}}},
		"no questions":      {State: sentinel},
		"unknown type":      {State: sentinel, Questions: map[string]question{"q": {Type: "ranking", Instructions: "i"}}},
		"missing type":      {State: sentinel, Questions: map[string]question{"q": {Instructions: "i"}}},
		"no instructions":   {State: sentinel, Questions: map[string]question{"q": {Type: "noul"}}},
		"blank instruction": {State: sentinel, Questions: map[string]question{"q": {Type: "noul", Instructions: "   "}}},
		"choice no criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "choice", Instructions: "i"}}},
		"choice empty criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "choice", Instructions: "i", Criteria: jsonValue(t, `{}`)}}},
		"choice array criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "choice", Instructions: "i", Criteria: jsonValue(t, `["a","b"]`)}}},
		"score no criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "score", Instructions: "i"}}},
		"score one level": {State: sentinel, Questions: map[string]question{
			"q": {Type: "score", Instructions: "i", Criteria: jsonValue(t, `["only"]`)}}},
		"score map criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "score", Instructions: "i", Criteria: jsonValue(t, `{"a":"b"}`)}}},
		"noul half criteria": {State: sentinel, Questions: map[string]question{
			"q": {Type: "noul", Instructions: "i", Criteria: jsonValue(t, `{"true":"yes"}`)}}},
		"noul stray key": {State: sentinel, Questions: map[string]question{
			"q": {Type: "noul", Instructions: "i", Criteria: jsonValue(t, `{"true":"y","false":"n","maybe":"m"}`)}}},
		"whitespace model": {State: sentinel, Model: "   ", Questions: map[string]question{
			"q": {Type: "noul", Instructions: "i"}}},
	} {
		t.Run(name, func(t *testing.T) {
			err := validateRequest(typesafeSpec, in)
			if err == nil {
				t.Fatal("want an error")
			}
			if strings.Contains(err.Error(), sentinel) {
				t.Fatalf("error echoed the state: %v", err)
			}
		})
	}
}

// REQ-07: a score level's number is its position, so order is the meaning and
// must survive serialization exactly.
func TestScoreCriteriaOrderIsPreserved(t *testing.T) {
	var sent evaluateIn
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if err := json.NewDecoder(r.Body).Decode(&sent); err != nil {
			t.Error(err)
		}
		w.Write([]byte(`{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"disruption":{"type":"score","score":1.3}}}`))
	}))
	defer srv.Close()

	levels := []any{"Minor disruption", "Major disruption", "Service unavailable"}
	c := testClient(providerAt("openrouter", srv.URL), srv)
	if _, err := runEvaluate(context.Background(), c, evaluateIn{
		State: "x",
		Questions: map[string]question{
			"disruption": {Type: "score", Instructions: "Rate it.", Criteria: levels},
		},
	}); err != nil {
		t.Fatal(err)
	}

	got, _ := sent.Questions["disruption"].Criteria.([]any)
	if len(got) != len(levels) {
		t.Fatalf("levels = %v", got)
	}
	for i := range levels {
		if got[i] != levels[i] {
			t.Fatalf("level %d = %v, want %v", i, got[i], levels[i])
		}
	}
}

// REQ-08, HTTP-01, HTTP-02: the request is a Decisions request, not a chat
// completion, and carries only the selected backend's credential.
func TestRequestIsDecisionsNotChat(t *testing.T) {
	t.Setenv("TYPESAFE_API_KEY", "typesafe-secret")
	var body map[string]any
	var gotPath, gotAuth, gotReferer string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath, gotAuth = r.URL.Path, r.Header.Get("Authorization")
		gotReferer = r.Header.Get("HTTP-Referer")
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			t.Error(err)
		}
		w.Write([]byte(`{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":0.9}}}`))
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL+"/api/alpha/decisions"), srv)
	c.APIKey = "openrouter-secret"
	if _, err := runEvaluate(context.Background(), c, evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "urgent?"}},
	}); err != nil {
		t.Fatal(err)
	}

	if gotPath != "/api/alpha/decisions" {
		t.Errorf("path = %q; a Decisions call must never go to a chat endpoint", gotPath)
	}
	if gotAuth != "Bearer openrouter-secret" {
		t.Errorf("authorization = %q", gotAuth)
	}
	if strings.Contains(gotAuth, "typesafe-secret") {
		t.Error("sent the other backend's credential")
	}
	if gotReferer != attributionURL {
		t.Errorf("HTTP-Referer = %q, want %q", gotReferer, attributionURL)
	}
	for _, chatField := range []string{"messages", "max_tokens", "stream", "temperature"} {
		if _, present := body[chatField]; present {
			t.Errorf("request carried the chat-completion field %q", chatField)
		}
	}
	for _, required := range []string{"model", "state", "questions"} {
		if _, present := body[required]; !present {
			t.Errorf("request is missing %q", required)
		}
	}
}

// The TypeSafe backend sends no OpenRouter attribution headers.
func TestAttributionIsOpenRouterOnly(t *testing.T) {
	var referer, title string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		referer, title = r.Header.Get("HTTP-Referer"), r.Header.Get("X-OpenRouter-Title")
		w.Write([]byte(`{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":0.5}}}`))
	}))
	defer srv.Close()

	c := testClient(providerAt("typesafe", srv.URL), srv)
	if _, err := runEvaluate(context.Background(), c, evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}},
	}); err != nil {
		t.Fatal(err)
	}
	if referer != "" || title != "" {
		t.Errorf("typesafe sent attribution headers: %q %q", referer, title)
	}
}

// RES-01: a 200 that is not a judgment is never presented as one.
func TestResponseRejectsNonJudgments(t *testing.T) {
	in := evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}},
	}
	for name, body := range map[string]string{
		"empty":         ``,
		"html":          `<!doctype html><html><body>502 Bad Gateway</body></html>`,
		"invalid json":  `{"answers":`,
		"error object":  `{"error":{"code":402,"message":"Insufficient credits"}}`,
		"no answers":    `{"model":"m","usage":{"input_tokens":1,"output_tokens":1}}`,
		"null answers":  `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":null}`,
		"missing id":    `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"other":{"type":"noul","noul":0.5}}}`,
		"wrong type":    `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"choice","choice":"a"}}}`,
		"no value":      `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul"}}}`,
		"noul over one": `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"q":{"type":"noul","noul":1.4}}}`,
	} {
		t.Run(name, func(t *testing.T) {
			if err := validateResponse(openrouterSpec, in, []byte(body)); err == nil {
				t.Fatalf("accepted %s as a judgment", name)
			}
		})
	}
}

// RES-02: unknown fields and provider metadata reach the caller untouched. A
// narrower output struct would silently drop cost, usage, and ids.
func TestResponseMetadataIsPreserved(t *testing.T) {
	const reply = `{"id":"gen-123","model":"typesafe/jev-2026-01-01","provider":"TypeSafe",` +
		`"usage":{"input_tokens":120,"output_tokens":8,"cost":0.00042},` +
		`"answers":{"q":{"type":"noul","noul":0.97}},"future_field":{"kept":true}}`
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		w.Write([]byte(reply))
	}))
	defer srv.Close()

	c := testClient(providerAt("openrouter", srv.URL), srv)
	got, err := runEvaluate(context.Background(), c, evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}},
	})
	if err != nil {
		t.Fatal(err)
	}
	for _, keep := range []string{`"gen-123"`, `"cost":0.00042`, `"future_field"`, `"typesafe/jev-2026-01-01"`} {
		if !strings.Contains(string(got), keep) {
			t.Errorf("response dropped %s: %s", keep, got)
		}
	}
}

// RES-03: OpenRouter may omit confidence and probabilities where TypeSafe
// always sends them. Absent means absent; nothing is invented to fill the gap.
func TestOptionalConfidenceMayBeAbsent(t *testing.T) {
	in := evaluateIn{
		State: "x",
		Questions: map[string]question{
			"owner":      {Type: "choice", Instructions: "i", Criteria: map[string]any{"engineering": "e", "billing": "b"}},
			"disruption": {Type: "score", Instructions: "i", Criteria: []any{"low", "mid", "high"}},
		},
	}
	// No confidence, no probabilities, no legend anywhere.
	bare := `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{
		"owner":{"type":"choice","choice":"engineering"},
		"disruption":{"type":"score","score":1.7}}}`
	if err := validateResponse(openrouterSpec, in, []byte(bare)); err != nil {
		t.Fatalf("rejected a valid response with optional fields absent: %v", err)
	}
	if strings.Contains(bare, "confidence") {
		t.Fatal("fixture should not contain confidence")
	}
}

// RES-05: a zero probability is a real answer, and a score is a position on the
// level number line rather than a probability.
func TestZeroValuesAndScoreRangeSurvive(t *testing.T) {
	in := evaluateIn{
		State: "x",
		Questions: map[string]question{
			"owner":      {Type: "choice", Instructions: "i", Criteria: map[string]any{"engineering": "e", "billing": "b"}},
			"disruption": {Type: "score", Instructions: "i", Criteria: []any{"low", "mid", "high"}},
		},
	}
	// score 2.0 is the top level of a three-level scale, well outside 0-1.
	valid := `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{
		"owner":{"type":"choice","choice":"engineering","confidence":0,"probabilities":{"engineering":1,"billing":0}},
		"disruption":{"type":"score","score":2,"confidence":0.9}}}`
	if err := validateResponse(openrouterSpec, in, []byte(valid)); err != nil {
		t.Fatalf("rejected valid zero/top-of-range values: %v", err)
	}

	// Above the top level number is out of range for this scale.
	tooHigh := `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{
		"owner":{"type":"choice","choice":"engineering"},
		"disruption":{"type":"score","score":3.1}}}`
	if err := validateResponse(openrouterSpec, in, []byte(tooHigh)); err == nil {
		t.Error("accepted a score above the top level")
	}
}

// RES-04: an answer that chose an option nobody offered is an error, not a
// partial success the agent has to notice on its own.
func TestChoiceOutsideCriteriaIsRejected(t *testing.T) {
	in := evaluateIn{
		State: "x",
		Questions: map[string]question{
			"owner": {Type: "choice", Instructions: "i", Criteria: map[string]any{"engineering": "e", "billing": "b"}},
		},
	}
	body := `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"owner":{"type":"choice","choice":"legal"}}}`
	if err := validateResponse(openrouterSpec, in, []byte(body)); err == nil {
		t.Error("accepted an option that was never offered")
	}
}

// Both backends document model and usage as required. Their absence means this
// is not a judgment envelope, which a truncated reply or an unrelated JSON
// document can otherwise impersonate.
func TestResponseRequiresModelAndUsage(t *testing.T) {
	in := evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: "i"}},
	}
	const answer = `"answers":{"q":{"type":"noul","noul":0.5}}`

	for name, body := range map[string]string{
		"no model":    `{` + answer + `,"usage":{"input_tokens":1,"output_tokens":1}}`,
		"empty model": `{"model":"",` + answer + `,"usage":{"input_tokens":1,"output_tokens":1}}`,
		"no usage":    `{"model":"m",` + answer + `}`,
		"null usage":  `{"model":"m","usage":null,` + answer + `}`,
	} {
		t.Run(name, func(t *testing.T) {
			if err := validateResponse(openrouterSpec, in, []byte(body)); err == nil {
				t.Errorf("accepted a response with %s", name)
			}
		})
	}

	// The shapes are not narrowed, only their presence checked: usage gained an
	// optional cost field once already and will gain more.
	full := `{"model":"m","usage":{"input_tokens":1,"output_tokens":1,"cost":0.1,"future":true},` + answer + `}`
	if err := validateResponse(openrouterSpec, in, []byte(full)); err != nil {
		t.Errorf("rejected a valid response with an extended usage block: %v", err)
	}
}

// The answer space is capped, and the cap is enforced here rather than by the
// provider. Probed against the OpenRouter backend on 2026-09-18: 255 options
// answered correctly, 256 returned an HTTP 400 that named no field. Without
// this check the operator pays for a round trip and gets back "the provider
// rejected the request shape", which is exactly the outcome every other
// constraint in this file exists to prevent.
func TestChoiceOptionCap(t *testing.T) {
	options := func(n int) map[string]any {
		m := make(map[string]any, n)
		for i := range n {
			m[fmt.Sprintf("opt%d", i)] = "a description"
		}
		return m
	}

	for _, spec := range []ProviderSpec{providers["openrouter"], providers["typesafe"]} {
		t.Run(spec.Name, func(t *testing.T) {
			if err := validateChoiceCriteria(spec, "q", options(maxChoiceOptions)); err != nil {
				t.Errorf("%d options should be accepted: %v", maxChoiceOptions, err)
			}

			err := validateChoiceCriteria(spec, "q", options(maxChoiceOptions+1))
			if err == nil {
				t.Fatalf("%d options should be refused before the call is billed", maxChoiceOptions+1)
			}
			// The message has to name the field and both numbers, or the
			// caller cannot tell which question to trim.
			for _, want := range []string{"q.criteria", "256", "255"} {
				if !strings.Contains(err.Error(), want) {
					t.Errorf("error %q does not mention %q", err, want)
				}
			}
		})
	}
}

// Jev's context budgets are documented but were not checked, so an oversized
// state was serialised, sent, billed, and returned as a bare HTTP 400 whose
// text blames the question types. Found by smoke-testing the released plugin
// with a 45,000-token state: exactly the failure the option cap fix was about.
func TestContextBudget(t *testing.T) {
	// Roughly n tokens of text, at the estimator's own ratio.
	text := func(tokens int) string { return strings.Repeat("a", tokens*bytesPerToken) }
	noul := func(instructions string) question {
		return question{Type: typeNoul, Instructions: instructions}
	}

	t.Run("a state within both budgets passes", func(t *testing.T) {
		err := validateBudget(text(1_000), map[string]question{"q": noul("short")})
		if err != nil {
			t.Errorf("a small request should pass: %v", err)
		}
	})

	t.Run("a state over the state budget is refused", func(t *testing.T) {
		err := validateBudget(text(maxStateTokens+5_000), map[string]question{"q": noul("short")})
		if err == nil {
			t.Fatal("an oversized state should be refused before the call is billed")
		}
		// The message must name the budget that was blown and the question
		// that contributed, or the caller cannot tell what to shorten.
		for _, want := range []string{"questions.q", "state"} {
			if !strings.Contains(err.Error(), want) {
				t.Errorf("error %q does not mention %q", err, want)
			}
		}
	})

	t.Run("many questions can exceed the total while each stays small", func(t *testing.T) {
		questions := map[string]question{}
		for i := range 40 {
			questions[fmt.Sprintf("q%d", i)] = noul(text(2_000))
		}
		err := validateBudget(text(1_000), questions)
		if err == nil {
			t.Fatal("the total budget should be enforced, not only the state one")
		}
		if !strings.Contains(err.Error(), "fewer questions") {
			t.Errorf("the total-budget error should suggest fewer questions: %v", err)
		}
	})

	// The budget has to be reached through validateRequest, which is what the
	// tool actually calls. Testing validateBudget alone passes even when the
	// check is never wired in, which is how this was first written.
	t.Run("validateRequest enforces it", func(t *testing.T) {
		in := evaluateIn{
			State: text(maxStateTokens + 5_000),
			Questions: map[string]question{
				"q": {Type: typeNoul, Instructions: "short"},
			},
		}
		err := validateRequest(providers["openrouter"], in)
		if err == nil {
			t.Fatal("validateRequest let an oversized request through")
		}
		if !strings.Contains(err.Error(), "tokens") {
			t.Errorf("error is not the budget one: %v", err)
		}
	})

	// The estimate under-counts dense input rather than over-counting it, so a
	// borderline request reaches the provider instead of being refused here on
	// a guess. Being permissive at the edge is the point.
	t.Run("the estimate does not over-count", func(t *testing.T) {
		if got := estimateTokens(strings.Repeat("a", 4_000)); got > 1_100 {
			t.Errorf("estimate %d is far above the ~1000 tokens 4000 ascii bytes cost", got)
		}
	})
}
