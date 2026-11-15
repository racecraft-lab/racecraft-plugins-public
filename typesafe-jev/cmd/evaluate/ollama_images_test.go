package main

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestOllamaImagesGoldenRequest(t *testing.T) {
	png, jpeg := mustPNG(t, 280, 280), mustJPEG(t, 280, 280)
	in := evaluateIn{
		Model: "clef",
		State: map[string]any{"second": "zeta", "first": map[string]any{"image": "alpha"}},
		Images: map[string]imageSource{
			"zeta":  {DataBase64: b64(jpeg), Format: "jpeg"},
			"alpha": {DataBase64: b64(png), Format: "png"},
		},
		Questions: map[string]question{"q": {
			Type: typeNoul, Instructions: []any{"zeta", map[string]any{"image": "alpha"}},
			Criteria: map[string]any{"true": "alpha", "false": "zeta"},
		}},
	}
	body, headers, err := encodeRequest(withImages(providers["ollama"]), in)
	if err != nil {
		t.Fatal(err)
	}
	want := fmt.Sprintf(`{"images":["%s","%s"],"model":"clef","questions":{"q":{"criteria":{"false":"image 2","true":"image 1"},"instructions":["image 2","image 1"],"type":"noul"}},"state":{"first":"image 1","second":"image 2"}}`, b64(png), b64(jpeg))
	if string(body) != want || len(headers) != 0 {
		t.Fatalf("wire request differs from golden (body=%d bytes, headers=%v)", len(body), headers)
	}
}

func ollamaImageResponse() *http.Response {
	return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulOK))}
}

func TestOllamaImagesCaps(t *testing.T) {
	for _, tc := range []struct {
		name     string
		sizes    []int
		provider string
	}{
		{"four images", []int{0, 0, 0, 0}, "ollama"},
		{"fifth image", []int{0, 0, 0, 0, 0}, "openrouter"},
		{"per image and total at cap", []int{4 << 20, 4 << 20}, "ollama"},
		{"per image over cap", []int{(4 << 20) + 1}, "openrouter"},
		{"total over cap", []int{4 << 20, 4 << 20, 0}, "openrouter"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			in := ollamaSizedImages(t, tc.sizes...)
			ollamaCloudEnv(t)
			t.Setenv("JEV_CHAIN", "ollama,openrouter")
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv("JEV_IMAGES", "true")
			calls := 0
			fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
				calls++
				if req.URL.String() != providers[tc.provider].EndpointURL {
					t.Errorf("request went to %s, want %s", req.URL, tc.provider)
				}
				if tc.provider == "ollama" {
					checkOllamaImageBody(t, req, in)
				}
				return ollamaImageResponse(), nil
			})
			got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
			if got.code != 0 || strings.TrimSpace(got.stdout) != noulOK || calls != 1 {
				t.Fatalf("exit=%d calls=%d stderr=%s", got.code, calls, got.stderr)
			}
		})
	}
}

func ollamaSizedImages(t *testing.T, sizes ...int) evaluateIn {
	t.Helper()
	in := imageRequest(nil, "png")
	in.Images = make(map[string]imageSource)
	names := make([]any, len(sizes))
	for i, size := range sizes {
		name := fmt.Sprintf("photo%d", i)
		data := mustPNG(t, 280, 280)
		data = append(data, make([]byte, max(0, size-len(data)))...)
		in.Images[name] = imageSource{DataBase64: b64(data), Format: "png"}
		names[i] = name
	}
	in.State = names
	return in
}

func marshalOllamaImages(t *testing.T, in evaluateIn) string {
	t.Helper()
	var body strings.Builder
	if err := json.NewEncoder(&body).Encode(in); err != nil {
		t.Fatalf("encode image input: %v", err)
	}
	return body.String()
}

func checkOllamaImageBody(t *testing.T, req *http.Request, in evaluateIn) {
	t.Helper()
	var got map[string]any
	if err := json.NewDecoder(req.Body).Decode(&got); err != nil {
		t.Fatal(err)
	}
	images, ok := got["images"].([]any)
	if !ok || len(images) != len(in.Images) || got["assets"] != nil {
		t.Fatalf("wire images type=%T count=%d", got["images"], len(images))
	}
	for i, name := range sortedKeys(in.Images) {
		if images[i] != in.Images[name].DataBase64 {
			t.Errorf("wire image %d differs from input", i+1)
		}
	}
}

func TestOllamaImagesRequireOperatorOptIn(t *testing.T) {
	for _, optIn := range []string{"", "false"} {
		t.Run("JEV_IMAGES="+optIn, func(t *testing.T) {
			ollamaCloudEnv(t)
			t.Setenv("JEV_IMAGES", optIn)
			blockOllamaHTTP(t)
			in := imageRequest(nil, "png")
			in.Images["door"] = imageSource{Path: filepath.Join(t.TempDir(), "unread.png")}
			got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
			if got.code != 2 || !strings.Contains(got.stderr, "set JEV_IMAGES=true") {
				t.Fatalf("exit=%d stderr=%s; opt-in must precede file access", got.code, got.stderr)
			}
		})
	}
}

func TestOllamaImagesOptInIsPerHop(t *testing.T) {
	session, hits, log := capabilitySession(t, []ProviderSpec{providers["ollama"], withImages(providers["openrouter"])}, []int{200, 200})
	capabilityCall(t, session, imageRequest(mustPNG(t, 280, 280), "png"), false, `"noul":0.42`)
	if hits[0] != 0 {
		t.Fatalf("non-opted-in Ollama received %d requests", hits[0])
	}
	if hits[1] != 1 {
		t.Fatalf("opted-in OpenRouter received %d requests", hits[1])
	}
	if log.Len() > 0 {
		t.Fatalf("capability route moved the session: %s", log.String())
	}
}

func TestOllamaImagesReadOnceAcrossHops(t *testing.T) {
	ollamaCloudEnv(t)
	t.Setenv("JEV_CHAIN", "ollama,openrouter")
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	t.Setenv("JEV_IMAGES", "true")
	data := mustPNG(t, 280, 280)
	path := filepath.Join(t.TempDir(), "photo.png")
	writeImageFixture(t, path, data)
	in := imageRequest(nil, "png")
	in.Images["door"] = imageSource{Path: path}
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		response := ollamaImageResponse()
		if calls == 1 {
			if err := os.Remove(path); err != nil {
				return nil, err
			}
			checkOllamaImageBody(t, req, imageRequest(data, "png"))
			response.StatusCode = 401
		} else {
			var body map[string]any
			if err := json.NewDecoder(req.Body).Decode(&body); err != nil {
				return nil, err
			}
			checkOriginalImage(t, "openrouter", body, data)
		}
		return response, nil
	})
	got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
	if got.code != 0 || strings.TrimSpace(got.stdout) != noulOK || calls != 2 {
		t.Fatalf("exit=%d calls=%d stderr=%s", got.code, calls, got.stderr)
	}
}

func TestOllamaImagesRepeatedReferencesSendOneCopy(t *testing.T) {
	in := ollamaSizedImages(t, 4<<20)
	in.State = []any{"photo0", "photo0", "photo0", "photo0"}
	ollamaCloudEnv(t)
	t.Setenv("JEV_IMAGES", "true")
	calls := 0
	fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
		calls++
		checkOllamaImageBody(t, req, in)
		return ollamaImageResponse(), nil
	})
	got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
	if got.code != 0 || calls != 1 {
		t.Fatalf("exit=%d calls=%d stderr=%s", got.code, calls, got.stderr)
	}
}

func TestOllamaImagesBodyCapIncludesText(t *testing.T) {
	in := ollamaSizedImages(t, 4<<20, 4<<20)
	// The model is not part of the text-token estimate. Together with the
	// 8 MiB of base64-expanded files, it exceeds the 13 MiB body cap.
	in.Model = strings.Repeat("m", 3<<20)
	checkOllamaRoute(t, in, false, false)
	checkOllamaRoute(t, in, true, false)
}
