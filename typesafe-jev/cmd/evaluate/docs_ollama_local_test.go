package main

import "testing"

// #1440: the provider-contracts doc has an ollama-local column beside Ollama.
func TestProviderContractsHaveOllamaLocalColumn(t *testing.T) {
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md",
		"| Per-hop limit | TypeSafe | OpenRouter | Ollama | `ollama-local` |",
		"| Field | TypeSafe accepts | OpenRouter accepts | Ollama accepts | `ollama-local` |")
}
