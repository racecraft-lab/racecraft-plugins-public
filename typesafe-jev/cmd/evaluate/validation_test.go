package main

import (
	"context"
	"encoding/json"
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

// REQ-02, REQ-03: TypeSafe documents structured instructions; OpenRouter types
// them as strings. The strictness applies to OpenRouter only, and never
// stringifies the structure to force it through.
func TestStructuredInstructionsAreBackendSpecific(t *testing.T) {
	for _, literal := range []string{
		`{"field":{"name":"amount_due","type":"number"},"question":"How large is it?"}`,
		`["compare sender name","compare sender domain"]`,
	} {
		in := evaluateIn{
			State:     "x",
			Questions: map[string]question{"q": {Type: "noul", Instructions: jsonValue(t, literal)}},
		}
		if err := validateRequest(typesafeSpec, in); err != nil {
			t.Errorf("typesafe rejected documented structure %s: %v", literal, err)
		}
		err := validateRequest(openrouterSpec, in)
		if err == nil {
			t.Errorf("openrouter accepted structure it cannot parse: %s", literal)
			continue
		}
		if !strings.Contains(err.Error(), "questions.q.instructions") {
			t.Errorf("error should name the field path: %v", err)
		}
	}
}

// REQ-04, REQ-05: a null choice description means "the option name says it" on
// TypeSafe. OpenRouter types the description as a string.
func TestNullChoiceDescriptionIsBackendSpecific(t *testing.T) {
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
	if err := validateRequest(typesafeSpec, in); err != nil {
		t.Errorf("typesafe rejected a documented null description: %v", err)
	}
	if err := validateRequest(openrouterSpec, in); err == nil {
		t.Error("openrouter accepted a null description")
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
	_, err := runEvaluate(context.Background(), c, evaluateIn{
		State:     "x",
		Questions: map[string]question{"q": {Type: "noul", Instructions: jsonValue(t, `{"question":"structured"}`)}},
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
