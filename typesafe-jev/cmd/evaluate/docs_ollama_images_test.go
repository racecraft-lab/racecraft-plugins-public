package main

import "testing"

// #1439: the provider-contracts doc covers Ollama's image wire format and caps.
func TestProviderContractsCoverOllamaImages(t *testing.T) {
	requireDocText(t, "typesafe-jev/docs/provider-contracts.md",
		"For Ollama, whole-name string references and `{\"image\":\"name\"}` markers in",
		"Ollama allows at most 4 images, 4 MiB each, 8 MiB in total")
}

func TestDocsCoverWebPFormatsAndRouting(t *testing.T) {
	for _, path := range []string{
		"typesafe-jev/README.md",
		"typesafe-jev/docs/provider-contracts.md",
		"typesafe-jev/plugin/shared-skills/typed-judgments/SKILL.md",
		"typesafe-jev/plugin/shared-skills/typesafe-ai/SKILL.md",
	} {
		requireDocText(t, path, "PNG, JPEG, or WebP", "animated WebP", "WebP skips", "JEV_IMAGES=true")
	}
}
