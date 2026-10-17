package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"hash/crc32"
	"image"
	"image/jpeg"
	"image/png"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
)

func mustPNG(t *testing.T, w, h int) []byte {
	t.Helper()
	img := image.NewNRGBA(image.Rect(0, 0, w, h))
	img.Pix[0], img.Pix[1], img.Pix[2], img.Pix[3] = 10, 20, 30, 255
	var buf bytes.Buffer
	if err := png.Encode(&buf, img); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func mustJPEG(t *testing.T, w, h int) []byte {
	t.Helper()
	img := image.NewRGBA(image.Rect(0, 0, w, h))
	img.Pix[0], img.Pix[1], img.Pix[2], img.Pix[3] = 10, 20, 30, 255
	var buf bytes.Buffer
	if err := jpeg.Encode(&buf, img, &jpeg.Options{Quality: 80}); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

func b64(data []byte) string { return base64.StdEncoding.EncodeToString(data) }

func withImages(spec ProviderSpec) ProviderSpec {
	spec.AllowImages = true
	return spec
}

func imageRequest(data []byte, format string) evaluateIn {
	return evaluateIn{
		State: map[string]any{"photo": map[string]any{"image": "door"}},
		Images: map[string]imageSource{
			"door": {DataBase64: b64(data), Format: format},
		},
		Questions: map[string]question{
			"present": {Type: typeNoul, Instructions: "Is there a person in the photo?"},
		},
	}
}

const noulOK = `{"model":"m","usage":{"input_tokens":12,"output_tokens":5},"answers":{"present":{"type":"noul","noul":0.5}}}`

func TestImageWireFormatPerBackend(t *testing.T) {
	pngBytes := mustPNG(t, 280, 280)
	for _, provider := range []string{"typesafe", "openrouter"} {
		t.Run(provider, func(t *testing.T) {
			var body map[string]any
			var header http.Header
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				header = r.Header.Clone()
				if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
					t.Error(err)
				}
				w.Write([]byte(noulOK))
			}))
			defer srv.Close()

			spec := withImages(providerAt(provider, srv.URL))
			c := testClient(spec, srv)
			if _, err := runEvaluate(context.Background(), c, imageRequest(pngBytes, "png")); err != nil {
				t.Fatal(err)
			}

			if _, ok := body["images"]; ok {
				t.Fatalf("%s body still has the neutral images map", provider)
			}
			if _, ok := body["assets"]; ok != (provider == "typesafe") {
				t.Fatalf("%s assets present=%v", provider, ok)
			}
			photo := body["state"].(map[string]any)["photo"]
			switch provider {
			case "typesafe":
				ref, ok := photo.(string)
				if !ok || !strings.HasPrefix(ref, "jevimg-") {
					t.Fatalf("typesafe reference = %#v", photo)
				}
				assets := body["assets"].(map[string]any)
				asset := assets[ref].(map[string]any)
				if asset["type"] != "image" || asset["format"] != "png" {
					t.Fatalf("asset = %#v", asset)
				}
				if asset["data_base64"] != b64(pngBytes) {
					t.Fatal("asset bytes do not match the file")
				}
				if header.Get(headerDangerImages) != "true" {
					t.Fatalf("images header = %q", header.Get(headerDangerImages))
				}
				if header.Get(headerDangerLong) != "" {
					t.Fatal("long-context header sent without the opt-in")
				}
			case "openrouter":
				part := photo.(map[string]any)
				if part["type"] != "image_url" {
					t.Fatalf("part = %#v", part)
				}
				url := part["image_url"].(map[string]any)["url"].(string)
				prefix := "data:image/png;base64,"
				if !strings.HasPrefix(url, prefix) || url[len(prefix):] != b64(pngBytes) {
					t.Fatal("openrouter data URL is not the PNG")
				}
				if header.Get(headerDangerImages) != "" || header.Get(headerDangerLong) != "" {
					t.Fatalf("openrouter received TypeSafe headers: %v", header)
				}
			}
		})
	}
}

func TestJPEGUsesJpegMediaType(t *testing.T) {
	jpg := mustJPEG(t, 280, 280)
	var body map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewDecoder(r.Body).Decode(&body)
		w.Write([]byte(noulOK))
	}))
	defer srv.Close()

	c := testClient(withImages(providerAt("openrouter", srv.URL)), srv)
	in := imageRequest(jpg, "jpeg")
	if _, err := runEvaluate(context.Background(), c, in); err != nil {
		t.Fatal(err)
	}
	photo := body["state"].(map[string]any)["photo"].(map[string]any)
	url := photo["image_url"].(map[string]any)["url"].(string)
	if !strings.HasPrefix(url, "data:image/jpeg;base64,") {
		t.Fatalf("url prefix = %q", url[:min(32, len(url))])
	}

	var ts map[string]any
	srv2 := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewDecoder(r.Body).Decode(&ts)
		w.Write([]byte(noulOK))
	}))
	defer srv2.Close()
	c = testClient(withImages(providerAt("typesafe", srv2.URL)), srv2)
	if _, err := runEvaluate(context.Background(), c, in); err != nil {
		t.Fatal(err)
	}
	ref := ts["state"].(map[string]any)["photo"].(string)
	format := ts["assets"].(map[string]any)[ref].(map[string]any)["format"]
	if format != "jpg" {
		t.Fatalf("typesafe format = %#v", format)
	}
}

func TestLongContextHeaderIsTypeSafeOnly(t *testing.T) {
	for _, provider := range []string{"typesafe", "openrouter"} {
		t.Run(provider, func(t *testing.T) {
			var header http.Header
			srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				header = r.Header.Clone()
				w.Write([]byte(noulOK))
			}))
			defer srv.Close()
			spec := providerAt(provider, srv.URL)
			spec = applyOperator(spec, false, true)
			c := testClient(spec, srv)
			in := evaluateIn{State: "x", Questions: map[string]question{"present": {Type: typeNoul, Instructions: "i"}}}
			if _, err := runEvaluate(context.Background(), c, in); err != nil {
				t.Fatal(err)
			}
			got := header.Get(headerDangerLong)
			if provider == "typesafe" && got != "true" {
				t.Fatalf("typesafe long-context header = %q", got)
			}
			if provider == "openrouter" && got != "" {
				t.Fatalf("openrouter long-context header = %q", got)
			}
		})
	}
}

func TestImagesDisabledMakesNoRequest(t *testing.T) {
	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Write([]byte(noulOK))
	}))
	defer srv.Close()
	c := testClient(providerAt("openrouter", srv.URL), srv) // AllowImages left false
	sentinel := "SENTINEL-image-bytes-must-not-leak"
	in := imageRequest(mustPNG(t, 280, 280), "")
	in.Images["door"] = imageSource{DataBase64: sentinel}
	_, err := runEvaluate(context.Background(), c, in)
	if err == nil {
		t.Fatal("images were sent without JEV_IMAGES")
	}
	if calls.Load() != 0 {
		t.Fatalf("made %d requests", calls.Load())
	}
	if strings.Contains(err.Error(), sentinel) {
		t.Fatalf("error quoted the image: %v", err)
	}
	if !strings.Contains(err.Error(), "JEV_IMAGES") {
		t.Fatalf("error = %v", err)
	}
}

func TestImageErrorsHideBytesAndPaths(t *testing.T) {
	spec := withImages(openrouterSpec)
	sentinel := "SENTINEL-b64-value"
	in := imageRequest(nil, "")
	in.Images = map[string]imageSource{"door": {DataBase64: sentinel}}
	in.State = map[string]any{"photo": map[string]any{"image": "door"}}
	err := validateRequest(spec, in)
	if err == nil {
		// Shape is valid; the decode failure is in the encoder, still local.
		c := testClient(spec, httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
			t.Fatal("a bad image was posted")
		})))
		_, err = c.Evaluate(context.Background(), in)
	}
	if err == nil {
		t.Fatal("accepted a non-image")
	}
	if strings.Contains(err.Error(), sentinel) {
		t.Fatalf("error quoted image data: %v", err)
	}

	path := filepath.Join(t.TempDir(), "SENTINEL-path-name.png")
	in.Images = map[string]imageSource{"door": {Path: path}}
	err = validateRequest(spec, in)
	if err != nil && strings.Contains(err.Error(), "not referenced") {
		t.Fatal(err)
	}
	c := testClient(spec, httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {})))
	_, err = c.Evaluate(context.Background(), in)
	if err == nil || strings.Contains(err.Error(), "SENTINEL-path-name") || strings.Contains(err.Error(), path) {
		t.Fatalf("path leaked or request was sent: %v", err)
	}
}

func TestUnreferencedImageIsNotOpened(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "secret.png")
	if err := os.WriteFile(path, mustPNG(t, 280, 280), 0o600); err != nil {
		t.Fatal(err)
	}
	spec := withImages(typesafeSpec)
	in := evaluateIn{
		State:  "no picture here",
		Images: map[string]imageSource{"door": {Path: path}},
		Questions: map[string]question{
			"q": {Type: typeNoul, Instructions: "anything?"},
		},
	}
	err := validateRequest(spec, in)
	if err == nil || !strings.Contains(err.Error(), "not referenced") {
		t.Fatalf("error = %v", err)
	}
	if strings.Contains(err.Error(), path) {
		t.Fatalf("error quoted the path: %v", err)
	}
}

func TestImageReferenceFormsAndLimits(t *testing.T) {
	pngBytes := mustPNG(t, 280, 280)
	spec := withImages(typesafeSpec)

	t.Run("whole string", func(t *testing.T) {
		var body map[string]any
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			json.NewDecoder(r.Body).Decode(&body)
			w.Write([]byte(noulOK))
		}))
		defer srv.Close()
		c := testClient(withImages(providerAt("typesafe", srv.URL)), srv)
		in := evaluateIn{
			State:  "door",
			Images: map[string]imageSource{"door": {DataBase64: b64(pngBytes)}},
			Questions: map[string]question{
				"present": {Type: typeNoul, Instructions: "Is there a person at the door?"},
			},
		}
		if _, err := runEvaluate(context.Background(), c, in); err != nil {
			t.Fatal(err)
		}
		if _, ok := body["state"].(string); !ok {
			t.Fatalf("state = %#v", body["state"])
		}
		// The word inside the instruction is not a reference.
		ins := body["questions"].(map[string]any)["present"].(map[string]any)["instructions"]
		if ins != "Is there a person at the door?" {
			t.Fatalf("instruction was rewritten: %#v", ins)
		}
	})

	t.Run("substring is not a reference", func(t *testing.T) {
		in := evaluateIn{
			State:  "doorknob",
			Images: map[string]imageSource{"door": {DataBase64: b64(pngBytes)}},
			Questions: map[string]question{
				"q": {Type: typeNoul, Instructions: "x"},
			},
		}
		err := validateRequest(spec, in)
		if err == nil || !strings.Contains(err.Error(), "not referenced") {
			t.Fatalf("error = %v", err)
		}
	})

	t.Run("criteria and instructions", func(t *testing.T) {
		var body map[string]any
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			json.NewDecoder(r.Body).Decode(&body)
			w.Write([]byte(`{"model":"m","usage":{"input_tokens":1,"output_tokens":1},"answers":{"owner":{"type":"choice","choice":"a"}}}`))
		}))
		defer srv.Close()
		c := testClient(withImages(providerAt("openrouter", srv.URL)), srv)
		in := evaluateIn{
			State:  "text only",
			Images: map[string]imageSource{"badge": {DataBase64: b64(pngBytes)}},
			Questions: map[string]question{
				"owner": {
					Type:         typeChoice,
					Instructions: []any{"who is this", map[string]any{"image": "badge"}},
					Criteria:     map[string]any{"a": "the badge", "b": map[string]any{"image": "badge"}},
				},
			},
		}
		if _, err := runEvaluate(context.Background(), c, in); err != nil {
			t.Fatal(err)
		}
		q := body["questions"].(map[string]any)["owner"].(map[string]any)
		ins := q["instructions"].([]any)
		if ins[1].(map[string]any)["type"] != "image_url" {
			t.Fatalf("instructions = %#v", ins)
		}
		crit := q["criteria"].(map[string]any)
		if crit["b"].(map[string]any)["type"] != "image_url" {
			t.Fatalf("criteria = %#v", crit)
		}
		if _, ok := body["assets"]; ok {
			t.Fatal("openrouter body has assets")
		}
	})

	t.Run("raw image_url is rejected", func(t *testing.T) {
		in := evaluateIn{
			State: []any{map[string]any{"type": "image_url", "image_url": map[string]any{"url": "data:image/png;base64,aaaa"}}},
			Images: map[string]imageSource{
				"door": {DataBase64: b64(pngBytes)},
			},
			Questions: map[string]question{"q": {Type: typeNoul, Instructions: "door"}},
		}
		err := validateRequest(spec, in)
		if err == nil || !strings.Contains(err.Error(), "image_url") {
			t.Fatalf("error = %v", err)
		}
	})

	t.Run("unknown marker", func(t *testing.T) {
		in := imageRequest(pngBytes, "")
		in.State = map[string]any{"photo": map[string]any{"image": "missing"}}
		err := validateRequest(spec, in)
		if err == nil || !strings.Contains(err.Error(), "missing") {
			t.Fatalf("error = %v", err)
		}
	})
}

func TestImageDimensionsArePerBackend(t *testing.T) {
	// 256x307 meets OpenRouter's 256 side minimum and the shared pixel floor
	// (78592), and misses TypeSafe's 280 side minimum.
	narrow := mustPNG(t, 256, 307)
	wide := mustPNG(t, 100, 100)

	assertLocal := func(t *testing.T, spec ProviderSpec, data []byte) {
		t.Helper()
		var calls atomic.Int64
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
			calls.Add(1)
		}))
		defer srv.Close()
		c := testClient(withImages(providerAt(spec.Name, srv.URL)), srv)
		_, err := runEvaluate(context.Background(), c, imageRequest(data, ""))
		if err == nil {
			t.Fatal("accepted an image outside the backend limits")
		}
		if calls.Load() != 0 {
			t.Fatalf("billed a request the limits reject: %d", calls.Load())
		}
	}

	assertLocal(t, typesafeSpec, narrow)
	assertLocal(t, typesafeSpec, wide)
	assertLocal(t, openrouterSpec, wide)

	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Write([]byte(noulOK))
	}))
	defer srv.Close()
	c := testClient(withImages(providerAt("openrouter", srv.URL)), srv)
	if _, err := runEvaluate(context.Background(), c, imageRequest(narrow, "")); err != nil {
		t.Fatal(err)
	}
	if calls.Load() != 1 {
		t.Fatalf("calls = %d", calls.Load())
	}
}

func TestAnimatedPNGAndFormatMismatchAreLocal(t *testing.T) {
	spec := withImages(openrouterSpec)
	pngBytes := mustPNG(t, 280, 280)
	animated := insertPNGChunk(t, pngBytes, "acTL", []byte{0, 0, 0, 1, 0, 0, 0, 0})
	in := imageRequest(animated, "")
	c := testClient(spec, httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		t.Error("animated png was posted")
	})))
	if _, err := c.Evaluate(context.Background(), in); err == nil || !strings.Contains(err.Error(), "animated") {
		t.Fatalf("error = %v", err)
	}

	in = imageRequest(mustJPEG(t, 280, 280), "png")
	if _, err := c.Evaluate(context.Background(), in); err == nil || !strings.Contains(err.Error(), "format") {
		t.Fatalf("error = %v", err)
	}
}

func TestImageFilePath(t *testing.T) {
	path := filepath.Join(t.TempDir(), "door.png")
	data := mustPNG(t, 280, 280)
	if err := os.WriteFile(path, data, 0o600); err != nil {
		t.Fatal(err)
	}
	var body map[string]any
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		json.NewDecoder(r.Body).Decode(&body)
		w.Write([]byte(noulOK))
	}))
	defer srv.Close()
	c := testClient(withImages(providerAt("typesafe", srv.URL)), srv)
	in := evaluateIn{
		State:  map[string]any{"photo": "door"},
		Images: map[string]imageSource{"door": {Path: path}},
		Questions: map[string]question{
			"present": {Type: typeNoul, Instructions: "Is there a person in the photo?"},
		},
	}
	if _, err := runEvaluate(context.Background(), c, in); err != nil {
		t.Fatal(err)
	}
	ref := body["state"].(map[string]any)["photo"].(string)
	got := body["assets"].(map[string]any)[ref].(map[string]any)["data_base64"].(string)
	if got != b64(data) {
		t.Fatal("file bytes were not the asset")
	}

	in.Images = map[string]imageSource{"door": {Path: "door.png"}}
	if err := validateRequest(withImages(typesafeSpec), in); err == nil || !strings.Contains(err.Error(), "absolute") {
		t.Fatalf("error = %v", err)
	}
}

func TestOversizedImageIsLocal(t *testing.T) {
	spec := withImages(openrouterSpec)
	in := imageRequest(nil, "")
	in.Images = map[string]imageSource{"door": {DataBase64: strings.Repeat("A", base64.StdEncoding.EncodedLen(maxImageBytes)+4)}}
	in.State = map[string]any{"photo": "door"}
	c := testClient(spec, httptest.NewServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		t.Error("oversized image was posted")
	})))
	_, err := c.Evaluate(context.Background(), in)
	if err == nil || !strings.Contains(err.Error(), "byte limit") {
		t.Fatalf("error = %v", err)
	}
	if strings.Contains(err.Error(), "AAAA") {
		t.Fatal("error quoted the payload")
	}
}

func TestImageBytesDoNotCountAsTextTokens(t *testing.T) {
	spec := withImages(typesafeSpec)
	// Two megabytes of base64 would be about half a million tokens if it were
	// counted. The text is a few dozen bytes and must pass the 32k budget.
	in := evaluateIn{
		State: map[string]any{"photo": "door"},
		Images: map[string]imageSource{
			"door": {DataBase64: strings.Repeat("A", 2<<20)},
		},
		Questions: map[string]question{"q": {Type: typeNoul, Instructions: "short"}},
	}
	if err := validateRequest(spec, in); err != nil {
		t.Fatal(err)
	}
}

func TestBoxModelGate(t *testing.T) {
	pngBytes := mustPNG(t, 280, 280)
	box := func(model string) evaluateIn {
		in := imageRequest(pngBytes, "")
		in.Model = model
		in.Questions = map[string]question{"mug": {Type: typeBox, Instructions: "the mug in the photo"}}
		return in
	}

	var calls atomic.Int64
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, _ *http.Request) {
		calls.Add(1)
		w.Write([]byte(noulOK))
	}))
	defer srv.Close()

	for _, model := range []string{"jev-latest", "jev-1.13.0", "jev-1.13"} {
		c := testClient(withImages(providerAt("typesafe", srv.URL)), srv)
		c.Model = "jev-preview" // must not override an explicit 1.13
		in := box(model)
		_, err := runEvaluate(context.Background(), c, in)
		if err == nil || !strings.Contains(err.Error(), "1.13") || !strings.Contains(err.Error(), model) {
			t.Fatalf("%s: %v", model, err)
		}
	}
	if calls.Load() != 0 {
		t.Fatalf("known 1.13 models were billed: %d", calls.Load())
	}

	// The TypeSafe default is jev-latest. An omitted model must still fail
	// locally, because runOn fills that default before the check.
	c := testClient(withImages(providerAt("typesafe", srv.URL)), srv)
	in := box("")
	if _, err := runEvaluate(context.Background(), c, in); err == nil || !strings.Contains(err.Error(), "jev-latest") {
		t.Fatalf("default model: %v", err)
	}

	for _, model := range []string{"typesafe/jev-1.13", "~typesafe/jev-1.13"} {
		err := validateRequest(withImages(openrouterSpec), box(model))
		if err == nil || !strings.Contains(err.Error(), "1.13") {
			t.Fatalf("%s: %v", model, err)
		}
	}

	for _, tc := range []struct {
		provider string
		model    string
	}{
		{"typesafe", "jev-preview"},
		{"typesafe", "jev-1.14.0"},
		{"openrouter", "typesafe/jev-1.14"},
		{"openrouter", "~typesafe/jev-latest"},
		{"openrouter", "some-other/model"},
	} {
		err := validateRequest(withImages(providers[tc.provider]), box(tc.model))
		if err != nil {
			t.Errorf("%s %s: %v", tc.provider, tc.model, err)
		}
	}
}

func TestBoxWireAndResponse(t *testing.T) {
	pngBytes := mustPNG(t, 280, 280)
	const reply = `{"model":"typesafe/jev-1.14","usage":{"input_tokens":20,"output_tokens":8},"answers":{"mug":{"type":"box","box":{"top":0.1,"bottom":0.4,"left":0.2,"right":0.8},"confidence":0.9}}}`
	var body map[string]any
	var header http.Header
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		header = r.Header.Clone()
		json.NewDecoder(r.Body).Decode(&body)
		w.Write([]byte(reply))
	}))
	defer srv.Close()
	c := testClient(withImages(providerAt("typesafe", srv.URL)), srv)
	in := imageRequest(pngBytes, "")
	in.Model = "jev-1.14.0"
	in.Questions = map[string]question{"mug": {Type: typeBox, Instructions: "the mug in the photo"}}
	got, err := runEvaluate(context.Background(), c, in)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(got), `"top":0.1`) {
		t.Fatalf("response = %s", got)
	}
	if header.Get(headerDangerImages) != "true" {
		t.Fatalf("header = %q", header.Get(headerDangerImages))
	}
	q := body["questions"].(map[string]any)["mug"].(map[string]any)
	if q["type"] != "box" {
		t.Fatalf("question = %#v", q)
	}
	if _, ok := q["criteria"]; ok {
		t.Fatal("box question was sent with criteria")
	}

	base := in
	base.Questions = map[string]question{"mug": {Type: typeBox, Instructions: "the mug", Criteria: "nope"}}
	if err := validateRequest(withImages(typesafeSpec), base); err == nil {
		t.Fatal("box accepted criteria")
	}

	edges := `{"model":"m","usage":{"input_tokens":1,"output_tokens":1},"answers":{"mug":{"type":"box","box":{"top":0.2,"bottom":0.2,"left":0.1,"right":0.4}}}}`
	if err := validateResponse(openrouterSpec, in, []byte(edges)); err == nil {
		t.Fatal("accepted a zero-height box")
	}
	// Confidence is optional on OpenRouter's DecisionsBoxAnswer.
	bare := `{"model":"m","usage":{"input_tokens":1,"output_tokens":1},"answers":{"mug":{"type":"box","box":{"top":0.1,"bottom":0.2,"left":0.1,"right":0.4}}}}`
	if err := validateResponse(openrouterSpec, in, []byte(bare)); err != nil {
		t.Fatal(err)
	}
	over := `{"model":"m","usage":{"input_tokens":1,"output_tokens":1},"answers":{"mug":{"type":"box","box":{"top":0.1,"bottom":1.2,"left":0.1,"right":0.4}}}}`
	if err := validateResponse(openrouterSpec, in, []byte(over)); err == nil {
		t.Fatal("accepted an edge above 1")
	}
}

func TestScoreLevelCap(t *testing.T) {
	levels := func(n int) []any {
		out := make([]any, n)
		for i := range out {
			out[i] = "level"
		}
		return out
	}
	in := func(n int) evaluateIn {
		return evaluateIn{
			State: "x",
			Questions: map[string]question{
				"q": {Type: typeScore, Instructions: "rate it", Criteria: levels(n)},
			},
		}
	}
	for _, spec := range []ProviderSpec{typesafeSpec, openrouterSpec} {
		if err := validateRequest(spec, in(maxScoreLevels)); err != nil {
			t.Errorf("%s rejected %d levels: %v", spec.Name, maxScoreLevels, err)
		}
		err := validateRequest(spec, in(maxScoreLevels+1))
		if err == nil || !strings.Contains(err.Error(), "11") || !strings.Contains(err.Error(), "10") {
			t.Errorf("%s: %v", spec.Name, err)
		}
	}
}

func TestFallbackRebuildsTheOtherWireFormat(t *testing.T) {
	pngBytes := mustPNG(t, 280, 280)
	var primary, fallback map[string]any
	var primaryHeader, fallbackHeader http.Header
	primarySrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		primaryHeader = r.Header.Clone()
		json.NewDecoder(r.Body).Decode(&primary)
		w.WriteHeader(http.StatusUnauthorized)
		w.Write([]byte(`{"error":{"message":"no"}}`))
	}))
	defer primarySrv.Close()
	fallbackSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		fallbackHeader = r.Header.Clone()
		json.NewDecoder(r.Body).Decode(&fallback)
		w.Write([]byte(noulOK))
	}))
	defer fallbackSrv.Close()

	primaryClient := testClient(withImages(providerAt("typesafe", primarySrv.URL)), primarySrv)
	primaryClient.MaxRetries = 0
	primaryClient.Fallback = testClient(withImages(providerAt("openrouter", fallbackSrv.URL)), fallbackSrv)
	primaryClient.Log = &bytes.Buffer{}

	if _, err := runEvaluate(context.Background(), primaryClient, imageRequest(pngBytes, "")); err != nil {
		t.Fatal(err)
	}
	if _, ok := primary["assets"]; !ok {
		t.Fatal("typesafe primary had no assets")
	}
	if primaryHeader.Get(headerDangerImages) != "true" {
		t.Fatal("typesafe primary omitted the images header")
	}
	if _, ok := fallback["assets"]; ok {
		t.Fatal("openrouter fallback was sent assets")
	}
	if _, ok := fallback["images"]; ok {
		t.Fatal("openrouter fallback was sent images")
	}
	photo := fallback["state"].(map[string]any)["photo"].(map[string]any)
	if photo["type"] != "image_url" {
		t.Fatalf("fallback photo = %#v", photo)
	}
	if fallbackHeader.Get(headerDangerImages) != "" {
		t.Fatal("openrouter fallback was sent the TypeSafe images header")
	}
}

func TestCallRejectsAssetsAndAcceptsImages(t *testing.T) {
	_, err := readCallRequest(strings.NewReader(`{"state":"s","questions":{"q":{"type":"noul","instructions":"i"}},"assets":{"a":{"type":"image"}}}`))
	if err == nil {
		t.Fatal("stdin assets were accepted")
	}
	in, err := readCallRequest(strings.NewReader(`{"state":"door","questions":{"q":{"type":"noul","instructions":"i"}},"images":{"door":{"data_base64":"aaaa","format":"png"}}}`))
	if err != nil {
		t.Fatal(err)
	}
	if in.Images["door"].Format != "png" || in.Images["door"].DataBase64 != "aaaa" {
		t.Fatalf("decoded = %#v", in.Images)
	}
}

func TestOperatorFlags(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_IMAGES":       "true",
		"JEV_LONG_CONTEXT": "1",
	}))
	if err != nil {
		t.Fatal(err)
	}
	if !cfg.AllowImages || !cfg.LongContext {
		t.Fatalf("flags = images %v long %v", cfg.AllowImages, cfg.LongContext)
	}
	spec := applyOperator(cfg.Provider, cfg.AllowImages, cfg.LongContext)
	if !spec.LongContext || spec.RequestTokens != longContextTokens || spec.QuestionTokens != longContextTokens {
		t.Fatalf("typesafe spec = %+v", spec)
	}

	cfg.Provider = providers["openrouter"]
	cfg.Fallback = &FallbackConfig{Provider: providers["typesafe"]}
	fb := cfg.fallbackConfig()
	if !fb.AllowImages || !fb.LongContext {
		t.Fatal("fallback dropped the operator flags")
	}
	fbSpec := applyOperator(fb.Provider, fb.AllowImages, fb.LongContext)
	if !fbSpec.LongContext || fbSpec.Name != "typesafe" {
		t.Fatalf("fallback spec = %+v", fbSpec)
	}
	or := applyOperator(providers["openrouter"], true, true)
	if or.LongContext {
		t.Fatal("openrouter took the TypeSafe long-context flag")
	}
	if or.RequestTokens != longContextTokens {
		t.Fatalf("openrouter budget = %d", or.RequestTokens)
	}

	if _, err := resolveConfig(envLookup(map[string]string{"JEV_IMAGES": "maybe"})); err == nil {
		t.Fatal("an unknown JEV_IMAGES value was accepted")
	}

	t.Setenv("TYPESAFE_API_KEY", "test-key")
	client, err := newClient(Config{
		Provider:    providers["typesafe"],
		Model:       "jev-latest",
		Timeout:     defaultTimeout,
		AllowImages: true,
		LongContext: true,
	})
	if err != nil {
		t.Fatal(err)
	}
	if !client.Provider.AllowImages || !client.Provider.LongContext || client.Provider.RequestTokens != longContextTokens {
		t.Fatalf("client spec = %+v", client.Provider)
	}
}

func TestSchemaAdvertisesImagesAndBox(t *testing.T) {
	srv := mockBackend(t, noulOK)
	cfg, c := backendFor(t, "openrouter", srv)
	session := connect(t, cfg, c)
	res, err := session.ListTools(context.Background(), nil)
	if err != nil {
		t.Fatal(err)
	}
	schema, err := json.Marshal(res.Tools[0].InputSchema)
	if err != nil {
		t.Fatal(err)
	}
	for _, want := range []string{`"images"`, `"data_base64"`, `"path"`, "box"} {
		if !strings.Contains(string(schema), want) {
			t.Errorf("schema missing %s: %s", want, schema)
		}
	}
	if strings.Contains(string(schema), `"assets"`) {
		t.Fatalf("schema advertises assets: %s", schema)
	}
}

func insertPNGChunk(t *testing.T, pngBytes []byte, ctype string, data []byte) []byte {
	t.Helper()
	idx := bytes.Index(pngBytes, []byte("IDAT"))
	if idx < 4 {
		t.Fatal("png has no IDAT")
	}
	chunk := pngChunk(ctype, data)
	out := make([]byte, 0, len(pngBytes)+len(chunk))
	out = append(out, pngBytes[:idx-4]...)
	out = append(out, chunk...)
	out = append(out, pngBytes[idx-4:]...)
	return out
}

func pngChunk(ctype string, data []byte) []byte {
	var buf bytes.Buffer
	var length [4]byte
	binary.BigEndian.PutUint32(length[:], uint32(len(data)))
	buf.Write(length[:])
	buf.WriteString(ctype)
	buf.Write(data)
	sum := crc32.ChecksumIEEE(buf.Bytes()[4:])
	var crc [4]byte
	binary.BigEndian.PutUint32(crc[:], sum)
	buf.Write(crc[:])
	return buf.Bytes()
}
