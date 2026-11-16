package main

import "testing"

// #1438: the provider-contracts doc has an Ollama column beside OpenRouter.
func TestProviderContractsHaveOllamaColumn(t *testing.T) {
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md", "| Per-hop limit | TypeSafe | OpenRouter | Ollama |")
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md", "| Field | TypeSafe accepts | OpenRouter accepts | Ollama accepts |")
}
