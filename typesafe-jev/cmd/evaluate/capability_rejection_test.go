package main

import (
	"strings"
	"testing"
)

func TestCapabilityRejectionMessages(t *testing.T) {
	reasons := map[string]string{
		"ollama-local": "questions.q.type is not supported by ollama-local",
		"ollama":       "questions.q.type is not supported by ollama",
		"typesafe":     "images.door: sides are 96 by 96 pixels, outside the 280-1568 range this backend accepts",
		"openrouter":   "images.door: sides are 96 by 96 pixels, outside the 256-1568 range this backend accepts",
	}
	for _, chain := range []string{
		"ollama-local", "ollama", "typesafe", "openrouter",
		"ollama-local,ollama,typesafe", "typesafe,ollama,ollama-local",
		"ollama-local,ollama,typesafe,openrouter",
	} {
		t.Run(chain, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", chain)
			t.Setenv("OLLAMA_API_KEY", fixtureKey)
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv("JEV_IMAGES", "true")
			blockOllamaHTTP(t)
			in := imageRequest(mustPNG(t, 96, 96), "png")
			in.Questions = map[string]question{"q": {Type: typeBox, Instructions: "Find the door in door"}}
			got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
			names := strings.Split(chain, ",")
			want := reasons[names[0]]
			if len(names) > 1 {
				var labelled []string
				for _, name := range names {
					labelled = append(labelled, name+": "+reasons[name])
				}
				want = "no backend can take this request: " + strings.Join(labelled, "; ")
			}
			want = "evaluate: " + want + "\n"
			if got.code != 2 || got.stdout != "" || got.stderr != want {
				t.Fatalf("call=%+v; want exit 2, empty stdout, stderr %q", got, want)
			}
		})
	}
}
