package main

import (
	"reflect"
	"testing"
)

// Each row's structured-entry cells match docs/provider-contracts.md, and the
// rows hold independent tables.
func TestStructuredEntryCellsPerRow(t *testing.T) {
	all := entryObject | entryArray
	want := map[string]map[entryPosition]entryKinds{
		"typesafe":   {entryInstructions: all, entryChoiceValue: all, entryScoreLevel: all, entryNoulDescription: all},
		"openrouter": {entryInstructions: all, entryChoiceValue: all, entryScoreLevel: all, entryNoulDescription: all},
		"ollama":     {entryChoiceValue: entryObject, entryScoreLevel: entryObject},
	}
	for name, cells := range want {
		got := providers[name].StructuredEntries
		for _, position := range []entryPosition{entryInstructions, entryChoiceValue, entryScoreLevel, entryNoulDescription} {
			if got[position] != cells[position] {
				t.Errorf("%s %v = %b, want %b", name, position, got[position], cells[position])
			}
		}
	}
	typesafe := reflect.ValueOf(providers["typesafe"].StructuredEntries).Pointer()
	if typesafe == reflect.ValueOf(providers["openrouter"].StructuredEntries).Pointer() {
		t.Error("typesafe and openrouter share one structured-entry table")
	}
}
