package main

import (
	"encoding/json"
	"fmt"
	"slices"
	"sort"
	"strings"
)

// Universal shape checks are independent of a backend. Hop preparation checks
// its capabilities and limits (ADR 0028); it does not narrow the shared shape.
// The two existing backends accept the same values
// inside it. TypeSafe documents that instructions, choice option descriptions,
// score level descriptions, and noul true/false descriptions all accept a
// string, an object, an array, or null. OpenRouter's Decisions schemas typed
// every one of those as a plain string until it republished them; they are now
// anyOf string, object, or array, with null additionally allowed for choice
// option descriptions.
//
// So structure is no longer narrowed for OpenRouter. What remains of the
// divergence is null in the three positions this server requires a value
// anyway (instructions, noul true/false, score levels), which is why no
// per-backend null rule survives here either. The capability still lives on
// ProviderSpec rather than being assumed, so a backend that re-narrows is one
// field to flip. See docs/provider-contracts.md for the field-by-field source.

const (
	// Question types, shared by both backends.
	typeNoul   = "noul"
	typeChoice = "choice"
	typeScore  = "score"
	typeBox    = "box"
	// answerRefusal is an answer type, not a question type: OpenRouter sends
	// it when a provider declines one question.
	answerRefusal = "refusal"
	// Tokens are estimated from serialised bytes because no tokenizer ships
	// here and adding one for a guardrail would be a poor trade. Four bytes
	// per token is the usual figure for English text; it UNDER-counts denser
	// input such as CJK or code, so the estimate errs toward letting a
	// borderline request through and leaving the provider to judge it. That
	// is the safe direction: this check exists to turn an opaque 400 into a
	// useful message, not to second-guess the backend.
	bytesPerToken = 4
)

// validateRequest checks a call before it costs anything. The MCP schema
// already rejects some of this, but a client-side schema is a convenience, not
// a boundary: the handler validates again.
//
// Errors name the field path and never the value. A rejection message reaches
// the agent's transcript, and the value may be the private state being judged.
func validateRequest(spec ProviderSpec, in evaluateIn) error {
	if err := validateRequestShape(in, spec.AllowImages); err != nil {
		return &requestShapeError{err}
	}
	if err := validateHopRequest(spec, in); err != nil {
		return &hopRefusalError{err}
	}
	return nil
}

// These types describe which phase refused a call. The compatibility boundary
// still wraps both as requestInvalidError until capability routes land.
type requestShapeError struct{ err error }

func (e *requestShapeError) Error() string { return e.err.Error() }
func (e *requestShapeError) Unwrap() error { return e.err }

type hopRefusalError struct{ err error }

func (e *hopRefusalError) Error() string { return e.err.Error() }
func (e *hopRefusalError) Unwrap() error { return e.err }

func validateRequestShape(in evaluateIn, allowImages bool) error {
	if err := validateState(in.State); err != nil {
		return err
	}
	if len(in.Questions) == 0 {
		return fmt.Errorf("questions must not be empty")
	}
	if in.Model != "" && strings.TrimSpace(in.Model) == "" {
		return fmt.Errorf("model is whitespace only; omit it to use the configured default")
	}

	// Sorted so a request with several problems reports the same one every
	// time; map iteration order would make the message change run to run.
	for _, id := range sortedKeys(in.Questions) {
		if err := validateQuestionShape(id, in.Questions[id]); err != nil {
			return err
		}
	}
	return validateImageShape(in, allowImages)
}

func validateHopRequest(spec ProviderSpec, in evaluateIn) error {
	if overLimit(len(in.Questions), spec.Limits.Questions) {
		return fmt.Errorf("questions has %d entries, over the %d the backend accepts", len(in.Questions), spec.Limits.Questions)
	}
	for _, id := range sortedKeys(in.Questions) {
		if err := validateQuestion(spec, id, in.Questions[id]); err != nil {
			return err
		}
	}
	if err := validateImageHop(spec, in); err != nil {
		return err
	}
	return validateBudget(spec, in.State, in.Questions)
}

// shapedCall holds backend-neutral input and image bytes, shared across hops.
type shapedCall struct {
	in     evaluateIn
	images map[string]preparedImage
	uses   map[string]int
}

func shapeRequest(in evaluateIn, allowImages bool) (shapedCall, error) {
	if err := validateRequestShape(in, allowImages); err != nil {
		return shapedCall{}, &requestShapeError{err}
	}
	images, uses, err := shapeImages(in)
	if err != nil {
		return shapedCall{}, &requestShapeError{err}
	}
	return shapedCall{in: in, images: images, uses: uses}, nil
}

func prepareForHop(c *Client, shaped shapedCall) (preparedCall, error) {
	in := shaped.in
	// Precedence: the tool call's model, then JEV_MODEL, then the backend
	// default. c.Model already holds the resolved second and third of those.
	//
	// An explicit model passes through exactly as given. A "~typesafe/" prefix
	// is neither added nor stripped: a mismatched id becomes a 404 the agent
	// can read, which beats a silent rewrite to a model nobody asked for.
	if in.Model == "" {
		in.Model = c.Model
	}
	if err := validateHopRequest(c.Provider, in); err != nil {
		return preparedCall{}, &requestInvalidError{&hopRefusalError{err}}
	}
	if err := validateLoadedImages(c.Provider, in.Images, shaped.images, shaped.uses); err != nil {
		return preparedCall{}, &requestInvalidError{&hopRefusalError{err}}
	}
	body, headers, err := encodeLoadedRequest(c.Provider, in, shaped.images)
	if err != nil {
		return preparedCall{}, &requestInvalidError{&hopRefusalError{err}}
	}
	if err := checkBodySize(c.Provider, body); err != nil {
		return preparedCall{}, &requestInvalidError{&hopRefusalError{err}}
	}
	return preparedCall{in: in, body: body, headers: headers}, nil
}

func checkBodySize(spec ProviderSpec, body []byte) error {
	if overLimit(len(body), spec.Limits.BodyBytes) {
		return fmt.Errorf("%s: request is %d bytes, over the %d byte limit; send less state, fewer questions, or fewer or smaller images",
			spec.Name, len(body), spec.Limits.BodyBytes)
	}
	return nil
}

// estimateTokens approximates the tokens a value costs once serialised.
func estimateTokens(v any) int {
	b, err := json.Marshal(v)
	if err != nil {
		// Unmarshalable input fails elsewhere with a better message; charging
		// it nothing here keeps this from being the error the caller sees.
		return 0
	}
	return len(b) / bytesPerToken
}

// validateBudget refuses a request that cannot fit Jev's context window.
//
// Both budgets are checked because they fail differently: the total covers the
// state plus every question, while the second covers the state plus only the
// longest single question, so a large state with many small questions can pass
// one and fail the other.
func validateBudget[Q any](spec ProviderSpec, state any, questions map[string]Q) error {
	if spec.RequestTokens <= 0 || spec.QuestionTokens <= 0 {
		return fmt.Errorf("internal: %s has no context budget", spec.Name)
	}
	stateTokens := estimateTokens(state)

	total, longest, longestID := stateTokens, 0, ""
	for _, id := range sortedKeys(questions) {
		n := estimateTokens(questions[id])
		total += n
		if n > longest {
			longest, longestID = n, id
		}
	}

	if overLimit(total, spec.RequestTokens) {
		return budgetTooLarge(spec, total, fmt.Sprintf("the request is about %d tokens, over the %d the model accepts; send less state or fewer questions",
			total, spec.RequestTokens))
	}
	if statePlus := stateTokens + longest; overLimit(statePlus, spec.QuestionTokens) {
		return budgetTooLarge(spec, statePlus, fmt.Sprintf("state plus the longest question (questions.%s) is about %d tokens, over the %d the model accepts for the two together; send less state",
			longestID, statePlus, spec.QuestionTokens))
	}
	return nil
}

// budgetTooLarge adds the long-context hint only when that flag would actually
// let this request through. A request past 262k tokens is over both windows.
func budgetTooLarge(spec ProviderSpec, tokens int, msg string) error {
	if spec.LongContextHeader != "" && !spec.LongContext && tokens <= spec.LongContextTokens {
		return fmt.Errorf("%s; set JEV_LONG_CONTEXT=true to raise both budgets to %d", msg, spec.LongContextTokens)
	}
	return fmt.Errorf("%s", msg)
}

// validateState accepts what both backends document: a string, a JSON object,
// or a JSON array. A bare number or boolean is rejected, because it carries no
// context a judgment could use.
func validateState(state any) error {
	switch state.(type) {
	case nil:
		return fmt.Errorf("state is required")
	case string, map[string]any, []any:
		return nil
	default:
		return fmt.Errorf("state must be a string, object, or array")
	}
}

func validateQuestion(spec ProviderSpec, id string, q question) error {
	path := "questions." + id
	if !slices.Contains(spec.QuestionTypes, q.Type) {
		return fmt.Errorf("%s.type is not supported by %s", path, spec.Name)
	}
	if err := validateEntryCapability(spec, path+".instructions", q.Instructions); err != nil {
		return err
	}
	switch q.Type {
	case typeNoul:
		return validateNoulCriteria(spec, path, q.Criteria)
	case typeChoice:
		return validateChoiceCriteria(spec, path, q.Criteria)
	case typeScore:
		return validateScoreCriteria(spec, path, q.Criteria)
	}
	return nil
}

func validateQuestionShape(id string, q question) error {
	path := "questions." + id

	switch q.Type {
	case typeNoul, typeChoice, typeScore, typeBox:
	case "":
		return fmt.Errorf("%s.type is required; use noul, choice, score, or box", path)
	default:
		return fmt.Errorf("%s.type must be noul, choice, score, or box", path)
	}

	if err := validateEntryShape(path+".instructions", q.Instructions, entryRequired); err != nil {
		return err
	}

	switch q.Type {
	case typeNoul:
		return validateNoulShape(path, q.Criteria)
	case typeChoice:
		m, err := criteriaOf[map[string]any](choiceRule, path, q.Criteria)
		if err != nil {
			return err
		}
		for _, option := range sortedKeys(m) {
			if strings.TrimSpace(option) == "" {
				return fmt.Errorf("%s.criteria has a blank option name", path)
			}
			if err := validateEntryShape(path+".criteria."+option, m[option], entryOptional); err != nil {
				return err
			}
		}
		return nil
	case typeBox:
		// Box takes instructions and an image, nothing else. Dropping a
		// criteria the caller sent would judge a different question than the
		// one they wrote.
		if q.Criteria != nil {
			return fmt.Errorf("%s.criteria is not accepted on a box question", path)
		}
		return nil
	default:
		levels, err := criteriaOf[[]any](scoreRule, path, q.Criteria)
		if err != nil {
			return err
		}
		for i, level := range levels {
			if err := validateEntryShape(fmt.Sprintf("%s.criteria[%d]", path, i), level, entryRequired); err != nil {
				return err
			}
		}
		return nil
	}
}

// entryRequired marks a field that must be present. Optional fields skip the
// nil check but still have their type checked when they are supplied.
type entryMode int

const (
	entryRequired entryMode = iota
	entryOptional
)

// validateEntryCapability checks a hop's support for structured entries.
func validateEntryCapability(spec ProviderSpec, path string, v any) error {
	switch v.(type) {
	case map[string]any, []any:
		if !spec.StructuredEntries {
			return fmt.Errorf("%s must be a string for the %s backend; structured %s are not accepted there",
				path, spec.Name, describeKind(v))
		}
	}
	return nil
}

func validateEntryShape(path string, v any, mode entryMode) error {
	if v == nil {
		if mode == entryRequired {
			return fmt.Errorf("%s is required", path)
		}
		// A null choice description means "the option name says it".
		return nil
	}

	switch val := v.(type) {
	case string:
		if strings.TrimSpace(val) == "" {
			return fmt.Errorf("%s must not be blank", path)
		}
		return nil
	case map[string]any, []any:
		return nil
	default:
		return fmt.Errorf("%s must be a string, object, or array", path)
	}
}

func describeKind(v any) string {
	if _, ok := v.([]any); ok {
		return "arrays"
	}
	return "objects"
}

// validateNoulCriteria allows criteria to be omitted on both backends. When it
// is present, both true and false descriptions are required: OpenRouter's
// schema requires the pair, and a half-described noul is ambiguous anyway.
func validateNoulCriteria(spec ProviderSpec, path string, criteria any) error {
	if criteria == nil {
		return nil
	}
	m := criteria.(map[string]any) // shaping checked the map and required keys
	for _, key := range []string{"true", "false"} {
		if err := validateEntryCapability(spec, path+".criteria."+key, m[key]); err != nil {
			return err
		}
	}
	return nil
}

func validateNoulShape(path string, criteria any) error {
	if criteria == nil {
		return nil
	}
	m, ok := criteria.(map[string]any)
	if !ok {
		return fmt.Errorf("%s.criteria must be an object with true and false descriptions", path)
	}
	for _, key := range []string{"true", "false"} {
		v, present := m[key]
		if !present {
			return fmt.Errorf("%s.criteria.%s is required when criteria is given", path, key)
		}
		if err := validateEntryShape(path+".criteria."+key, v, entryRequired); err != nil {
			return err
		}
	}
	for key := range m {
		if key != "true" && key != "false" {
			return fmt.Errorf("%s.criteria has an unexpected key %q; a noul takes only true and false", path, key)
		}
	}
	return nil
}

// criteriaRule is one question type's contract for its criteria: present, the
// right shape, and a bounded answer space. The answer space is enumerated in
// the request, and both backends cap it. Without the bound the call is billed
// and comes back as a generic HTTP 400 naming no field, which is the one
// failure mode every other constraint here exists to avoid.
type criteriaRule struct {
	qtype       string // the question type, for the missing-criteria error
	shape       string // what the criteria must be, for the wrong-shape error
	least, most int    // the entry count bounds, inclusive
	few         string // the error text under least
	verb, unit  string // how the error over most counts the entries
}

var (
	choiceRule = criteriaRule{
		qtype: typeChoice, shape: "an object mapping each option to its description",
		least: 0, most: noLimit,
		few: "must name at least one option", verb: "names", unit: "options",
	}
	scoreRule = criteriaRule{
		qtype: typeScore, shape: "an ordered array of level descriptions",
		least: 0, most: noLimit,
		verb: "has", unit: "levels",
	}
)

// withBounds combines a question shape with this backend's numeric limits.
func (rule criteriaRule) withBounds(least, most int) criteriaRule {
	rule.least, rule.most = least, most
	if rule.qtype == typeScore {
		rule.few = fmt.Sprintf("needs at least %d ordered levels", least)
	} else if least != 1 {
		rule.few = fmt.Sprintf("must name at least %d options", least)
	}
	return rule
}

// criteriaOf returns a question's criteria as T once rule holds for it.
func criteriaOf[T map[string]any | []any](rule criteriaRule, path string, criteria any) (T, error) {
	var zero T
	if criteria == nil {
		return zero, fmt.Errorf("%s.criteria is required for a %s question", path, rule.qtype)
	}
	v, ok := criteria.(T)
	switch {
	case !ok:
		return zero, fmt.Errorf("%s.criteria must be %s", path, rule.shape)
	case len(v) < rule.least:
		return zero, fmt.Errorf("%s.criteria %s", path, rule.few)
	case overLimit(len(v), rule.most):
		return zero, fmt.Errorf("%s.criteria %s %d %s, over the %d the backend accepts", path, rule.verb, len(v), rule.unit, rule.most)
	}
	return v, nil
}

// validateChoiceCriteria requires a non-empty option map. Option names are the
// answer space, so they are preserved exactly.
func validateChoiceCriteria(spec ProviderSpec, path string, criteria any) error {
	rule := choiceRule.withBounds(spec.Limits.ChoiceMin, spec.Limits.ChoiceMax)
	m, err := criteriaOf[map[string]any](rule, path, criteria)
	if err != nil {
		return err
	}
	for _, option := range sortedKeys(m) {
		if err := validateEntryCapability(spec, path+".criteria."+option, m[option]); err != nil {
			return err
		}
	}
	return nil
}

// validateScoreCriteria requires an ordered list of levels. Order is the
// meaning: a level's number is its position, so the slice is never sorted or
// deduplicated.
func validateScoreCriteria(spec ProviderSpec, path string, criteria any) error {
	rule := scoreRule.withBounds(spec.Limits.ScoreMin, spec.Limits.ScoreMax)
	levels, err := criteriaOf[[]any](rule, path, criteria)
	if err != nil {
		return err
	}
	for i, level := range levels {
		if err := validateEntryCapability(spec, fmt.Sprintf("%s.criteria[%d]", path, i), level); err != nil {
			return err
		}
	}
	return nil
}

// validateResponse checks that what came back answers what was asked, without
// narrowing it. The raw bytes are what the caller receives; this only refuses
// to present a malformed reply as a judgment.
//
// Optional fields stay optional. OpenRouter may omit confidence and
// probabilities where TypeSafe always sends them, and an absent field is
// reported as absent rather than filled in with a plausible number.
func validateResponse(spec ProviderSpec, in evaluateIn, body []byte) error {
	if len(body) == 0 {
		return fmt.Errorf("%s: empty response body", spec.Name)
	}

	var env struct {
		Answers map[string]json.RawMessage `json:"answers"`
		Error   json.RawMessage            `json:"error"`
		Model   *string                    `json:"model"`
		Usage   json.RawMessage            `json:"usage"`
	}
	if err := json.Unmarshal(body, &env); err != nil {
		// HTML from a proxy, or a truncated body, lands here. A 200 that is
		// not valid JSON is a failure, not an answer.
		return fmt.Errorf("%s: response is not valid JSON", spec.Name)
	}
	// Some gateways return 200 with an error object inside.
	if len(env.Error) > 0 && string(env.Error) != "null" {
		return fmt.Errorf("%s: response carried an error object instead of answers", spec.Name)
	}
	if env.Answers == nil {
		return fmt.Errorf("%s: response has no answers object", spec.Name)
	}
	// Both backends document model and usage as required. Their absence means
	// this is not a judgment envelope at all, which a truncated reply or an
	// unrelated JSON document can otherwise impersonate. The shapes are not
	// narrowed here, only their presence checked: usage gained an optional
	// cost field once already, and will gain more.
	if env.Model == nil || *env.Model == "" {
		return fmt.Errorf("%s: response names no model", spec.Name)
	}
	if len(env.Usage) == 0 || string(env.Usage) == "null" {
		return fmt.Errorf("%s: response reports no usage", spec.Name)
	}

	return validateAnswers(spec, in, env.Answers)
}

// validateAnswers checks that every question asked has an answer: a refusal,
// or a value of the type asked.
func validateAnswers(spec ProviderSpec, in evaluateIn, answers map[string]json.RawMessage) error {
	for _, id := range sortedKeys(in.Questions) {
		raw, ok := answers[id]
		if !ok {
			return fmt.Errorf("%s: no answer for question %q", spec.Name, id)
		}
		refused, err := checkRefusal(spec, id, raw)
		if err != nil {
			return err
		}
		if refused {
			continue
		}
		if err := validateAnswer(spec, id, in.Questions[id], raw); err != nil {
			return err
		}
	}
	return nil
}

// refusalValueFields are the answer fields a refusal must not carry.
var refusalValueFields = []string{"noul", "choice", "score", "box", "confidence", "probabilities"}

// checkRefusal reports whether raw is OpenRouter's {"type":"refusal"}, sent
// when a provider declines one question. A refusal is that question's whole
// answer and is passed through with no value; one that also carries a value
// is malformed.
func checkRefusal(spec ProviderSpec, id string, raw json.RawMessage) (bool, error) {
	var fields map[string]json.RawMessage
	var typ string
	if json.Unmarshal(raw, &fields) != nil || json.Unmarshal(fields["type"], &typ) != nil || typ != answerRefusal {
		return false, nil
	}
	for _, f := range refusalValueFields {
		if _, ok := fields[f]; ok {
			return false, fmt.Errorf("%s: answer %q is a refusal that carries a value", spec.Name, id)
		}
	}
	return true, nil
}

func validateAnswer(spec ProviderSpec, id string, q question, raw json.RawMessage) error {
	var a struct {
		Type          *string            `json:"type"`
		Noul          *float64           `json:"noul"`
		Choice        *string            `json:"choice"`
		Score         *float64           `json:"score"`
		Confidence    *float64           `json:"confidence"`
		Probabilities map[string]float64 `json:"probabilities"`
		Legend        map[string]any     `json:"legend"`
		Box           *boxEdges          `json:"box"`
	}
	if err := json.Unmarshal(raw, &a); err != nil {
		return fmt.Errorf("%s: answer %q is malformed", spec.Name, id)
	}
	// TypeSafe's schema defaults type rather than requiring it, so an absent
	// type is accepted; a present one must match what was asked.
	if a.Type != nil && *a.Type != q.Type {
		return fmt.Errorf("%s: answer %q is a %s but %s was asked", spec.Name, id, *a.Type, q.Type)
	}

	switch q.Type {
	case typeNoul:
		if a.Noul == nil {
			return fmt.Errorf("%s: answer %q has no noul value", spec.Name, id)
		}
		if err := inUnitRange(spec, id, "noul", *a.Noul); err != nil {
			return err
		}
	case typeChoice:
		if a.Choice == nil {
			return fmt.Errorf("%s: answer %q has no choice value", spec.Name, id)
		}
		if m, ok := q.Criteria.(map[string]any); ok {
			if _, offered := m[*a.Choice]; !offered {
				return fmt.Errorf("%s: answer %q chose an option that was not offered", spec.Name, id)
			}
		}
	case typeBox:
		if err := validateBoxAnswer(spec, id, a.Box); err != nil {
			return err
		}
	case typeScore:
		if a.Score == nil {
			return fmt.Errorf("%s: answer %q has no score value", spec.Name, id)
		}
		// A score is a position on the level number line, not a probability:
		// a three-level scale returns 0 to 2. Clamping it to 0-1 would reject
		// almost every valid answer.
		levels, _ := q.Criteria.([]any)
		if top := float64(len(levels) - 1); len(levels) > 0 && (*a.Score < 0 || *a.Score > top) {
			return fmt.Errorf("%s: answer %q has a score outside the 0-%g level range", spec.Name, id, top)
		}
	}

	// Optional on OpenRouter, always sent by TypeSafe. Checked only for shape
	// when present, and never defaulted when absent.
	if a.Confidence != nil {
		if err := inUnitRange(spec, id, "confidence", *a.Confidence); err != nil {
			return err
		}
	}
	for option, p := range a.Probabilities {
		if err := inUnitRange(spec, id, "probabilities."+option, p); err != nil {
			return err
		}
	}
	return nil
}

// boxEdges are fractions of the image, measured from the top-left. Pointers
// so a missing edge is absent rather than a real zero.
type boxEdges struct {
	Top    *float64 `json:"top"`
	Bottom *float64 `json:"bottom"`
	Left   *float64 `json:"left"`
	Right  *float64 `json:"right"`
}

// validateBoxAnswer requires all four edges, each in 0-1, in order.
func validateBoxAnswer(spec ProviderSpec, id string, box *boxEdges) error {
	if box == nil || box.Top == nil || box.Bottom == nil || box.Left == nil || box.Right == nil {
		return fmt.Errorf("%s: answer %q has no box", spec.Name, id)
	}
	for _, edge := range []struct {
		name string
		v    float64
	}{
		{"box.top", *box.Top},
		{"box.bottom", *box.Bottom},
		{"box.left", *box.Left},
		{"box.right", *box.Right},
	} {
		if err := inUnitRange(spec, id, edge.name, edge.v); err != nil {
			return err
		}
	}
	// TypeSafe documents left < right and top < bottom. An inverted box is
	// not a region anyone can crop.
	if *box.Left >= *box.Right || *box.Top >= *box.Bottom {
		return fmt.Errorf("%s: answer %q has a box whose edges are out of order", spec.Name, id)
	}
	return nil
}

func inUnitRange(spec ProviderSpec, id, field string, v float64) error {
	// Zero is a real value and must survive: a probability of 0 means the
	// model ruled that option out, which is information.
	if v < 0 || v > 1 {
		return fmt.Errorf("%s: answer %q has %s outside 0-1", spec.Name, id, field)
	}
	return nil
}

func sortedKeys[V any](m map[string]V) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
