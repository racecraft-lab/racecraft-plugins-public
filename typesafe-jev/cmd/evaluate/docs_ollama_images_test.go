package main

import "testing"

// #1439: the provider-contracts doc covers Ollama's image wire format and caps.
func TestProviderContractsCoverOllamaImages(t *testing.T) {
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md", "For Ollama, whole-name string references and `{\"image\":\"name\"}` markers in")
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md", "Ollama allows at most 4 images, 4 MiB each, 8 MiB in total")
}
