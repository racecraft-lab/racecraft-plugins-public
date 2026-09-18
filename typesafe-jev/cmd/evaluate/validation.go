package main

import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
)

// The two backends take the same request shape but do not accept the same
// values inside it. TypeSafe documents that instructions, choice option
// descriptions, score level descriptions, and noul true/false descriptions all
// accept a string, an object, an array, or null. OpenRouter's Decisions
// schemas type every one of those as a plain string.
//
// So the strictness is per backend, never global: narrowing TypeSafe to match
// OpenRouter would drop input shapes TypeSafe publishes and existing callers
// use. See docs/provider-contracts.md for the field-by-field source.

const (
	// Question types, shared by both backends.
	typeNoul   = "noul"
	typeChoice = "choice"
	typeScore  = "score"
	// minScoreLevels is this fork's policy, not a published constraint.
	// OpenRouter's schema sets no minItems, but a one-level scale gives the
	// model nothing to place a value between.
	minScoreLevels = 2
	// maxChoiceOptions is a published limit, not this fork's policy: the tool
	// description states at most 255 options. Probed 2026-09-18 against the
	// OpenRouter backend, 255 options answered correctly and 256 came back as
	// an HTTP 400 naming no field.
	maxChoiceOptions = 255
	// Jev's documented context budgets (https://docs.typesafe.ai/models.md):
	// 64k tokens for the whole request, and 32k for the state plus the single
	// longest question. Exceeding either is a billed round trip that comes
	// back as a bare HTTP 400, whose text blames the question types.
	maxRequestTokens = 64_000
	maxStateTokens   = 32_000
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
		if err := validateQuestion(spec, id, in.Questions[id]); err != nil {
			return err
		}
	}
	return validateBudget(in.State, in.Questions)
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
func validateBudget[Q any](state any, questions map[string]Q) error {
	stateTokens := estimateTokens(state)

	total, longest, longestID := stateTokens, 0, ""
	for _, id := range sortedKeys(questions) {
		n := estimateTokens(questions[id])
		total += n
		if n > longest {
			longest, longestID = n, id
		}
	}

	if total > maxRequestTokens {
		return fmt.Errorf("the request is about %d tokens, over the %d the model accepts; send less state or fewer questions",
			total, maxRequestTokens)
	}
	if stateTokens+longest > maxStateTokens {
		return fmt.Errorf("state plus the longest question (questions.%s) is about %d tokens, over the %d the model accepts for the two together; send less state",
			longestID, stateTokens+longest, maxStateTokens)
	}
	return nil
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

	switch q.Type {
	case typeNoul, typeChoice, typeScore:
	case "":
		return fmt.Errorf("%s.type is required; use noul, choice, or score", path)
	default:
		return fmt.Errorf("%s.type must be noul, choice, or score", path)
	}

	if err := validateEntry(spec, path+".instructions", q.Instructions, entryRequired); err != nil {
		return err
	}

	switch q.Type {
	case typeNoul:
		return validateNoulCriteria(spec, path, q.Criteria)
	case typeChoice:
		return validateChoiceCriteria(spec, path, q.Criteria)
	default:
		return validateScoreCriteria(spec, path, q.Criteria)
	}
}

// entryRequired marks a field that must be present. Optional fields skip the
// nil check but still have their type checked when they are supplied.
type entryMode int

const (
	entryRequired entryMode = iota
	entryOptional
)

// validateEntry checks one of TypeSafe's EntryType fields: instructions, an
// option description, or a level description.
func validateEntry(spec ProviderSpec, path string, v any, mode entryMode) error {
	if v == nil {
		if mode == entryRequired {
			return fmt.Errorf("%s is required", path)
		}
		// TypeSafe documents null as a valid description, meaning "the option
		// name says it". OpenRouter types the field as a string.
		if spec.Name == "openrouter" {
			return fmt.Errorf("%s must be a string for the openrouter backend; it may be null only on typesafe", path)
		}
		return nil
	}

	switch val := v.(type) {
	case string:
		if strings.TrimSpace(val) == "" {
			return fmt.Errorf("%s must not be blank", path)
		}
		return nil
	case map[string]any, []any:
		if spec.Name == "openrouter" {
			// Not stringified silently: JSON-encoding an object into the
			// instructions would send the model something nobody wrote.
			return fmt.Errorf("%s must be a string for the openrouter backend; structured %s are supported on typesafe only",
				path, describeKind(v))
		}
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
	m, ok := criteria.(map[string]any)
	if !ok {
		return fmt.Errorf("%s.criteria must be an object with true and false descriptions", path)
	}
	for _, key := range []string{"true", "false"} {
		v, present := m[key]
		if !present {
			return fmt.Errorf("%s.criteria.%s is required when criteria is given", path, key)
		}
		if err := validateEntry(spec, path+".criteria."+key, v, entryRequired); err != nil {
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

// validateChoiceCriteria requires a non-empty option map. Option names are the
// answer space, so they are preserved exactly.
func validateChoiceCriteria(spec ProviderSpec, path string, criteria any) error {
	if criteria == nil {
		return fmt.Errorf("%s.criteria is required for a choice question", path)
	}
	m, ok := criteria.(map[string]any)
	if !ok {
		return fmt.Errorf("%s.criteria must be an object mapping each option to its description", path)
	}
	if len(m) == 0 {
		return fmt.Errorf("%s.criteria must name at least one option", path)
	}
	// The answer space is enumerated in the request, and both backends cap it.
	// Without this check the call is billed and comes back as a generic HTTP
	// 400 naming no field, which is the one failure mode every other
	// constraint here exists to avoid.
	if len(m) > maxChoiceOptions {
		return fmt.Errorf("%s.criteria names %d options, over the %d the backend accepts", path, len(m), maxChoiceOptions)
	}
	for _, option := range sortedKeys(m) {
		if strings.TrimSpace(option) == "" {
			return fmt.Errorf("%s.criteria has a blank option name", path)
		}
		// Optional: a null description is meaningful on TypeSafe, and
		// validateEntry rejects it for OpenRouter.
		if err := validateEntry(spec, path+".criteria."+option, m[option], entryOptional); err != nil {
			return err
		}
	}
	return nil
}

// validateScoreCriteria requires an ordered list of levels. Order is the
// meaning: a level's number is its position, so the slice is never sorted or
// deduplicated.
func validateScoreCriteria(spec ProviderSpec, path string, criteria any) error {
	if criteria == nil {
		return fmt.Errorf("%s.criteria is required for a score question", path)
	}
	levels, ok := criteria.([]any)
	if !ok {
		return fmt.Errorf("%s.criteria must be an ordered array of level descriptions", path)
	}
	if len(levels) < minScoreLevels {
		return fmt.Errorf("%s.criteria needs at least %d ordered levels", path, minScoreLevels)
	}
	for i, level := range levels {
		if err := validateEntry(spec, fmt.Sprintf("%s.criteria[%d]", path, i), level, entryRequired); err != nil {
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

	for _, id := range sortedKeys(in.Questions) {
		raw, ok := env.Answers[id]
		if !ok {
			return fmt.Errorf("%s: no answer for question %q", spec.Name, id)
		}
		if err := validateAnswer(spec, id, in.Questions[id], raw); err != nil {
			return err
		}
	}
	return nil
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
