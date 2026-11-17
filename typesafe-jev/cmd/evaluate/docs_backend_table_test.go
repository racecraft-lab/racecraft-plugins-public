package main

import (
	"fmt"
	"strconv"
	"testing"
)

// The judgment skill's "Backends differ" table states each backend row's
// limits to the agent. Its numbers come from the rows, so a change to a row
// turns this test red until the table says the same.
func TestJudgmentSkillTableMatchesBackendRows(t *testing.T) {
	ts, or, ol := providers["typesafe"], providers["openrouter"], providers["ollama"]
	requireDocText(t, "typesafe-jev/plugin/shared-skills/typed-judgments/SKILL.md",
		fmt.Sprintf("| Questions per call | no local cap | no local cap | %d |", ol.Limits.Questions),
		fmt.Sprintf("| up to %d ASCII letters, digits,", ol.Limits.QuestionIDLength),
		fmt.Sprintf("| Choice options | %d to %d | %d to %d | %d to %d |",
			ts.Limits.ChoiceMin, ts.Limits.ChoiceMax, or.Limits.ChoiceMin, or.Limits.ChoiceMax,
			ol.Limits.ChoiceMin, ol.Limits.ChoiceMax),
		fmt.Sprintf("| %s per request, %s for state plus the longest question; %s with `JEV_LONG_CONTEXT=true` | %s | %s |",
			thousands(ts.RequestTokens), thousands(ts.QuestionTokens), thousands(ts.LongContextTokens),
			thousands(or.RequestTokens), thousands(ol.RequestTokens)),
		fmt.Sprintf("at most %d images, %d MiB each, %d MiB in all |",
			ol.Limits.Images, ol.Limits.ImageBytes>>20, ol.Limits.TotalImageBytes>>20),
		fmt.Sprintf("more than %d questions", ol.Limits.Questions),
		fmt.Sprintf("a state over %s tokens skips the Ollama backends", thousands(ol.RequestTokens)))
}

// thousands writes n with comma separators, as the skill's prose does.
func thousands(n int) string {
	s := strconv.Itoa(n)
	for i := len(s) - 3; i > 0; i -= 3 {
		s = s[:i] + "," + s[i:]
	}
	return s
}
