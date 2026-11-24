package main

import (
	"encoding/binary"
	"net/http"
	"strings"
	"testing"
)

// A complete lossless 1x1 image, kept inline rather than as a binary fixture.
func stillWebP(t *testing.T) []byte {
	t.Helper()
	return []byte{
		0x52, 0x49, 0x46, 0x46, 0x1e, 0, 0, 0, 0x57, 0x45, 0x42, 0x50,
		0x56, 0x50, 0x38, 0x4c, 0x11, 0, 0, 0, 0x2f, 0, 0, 0, 0,
		0x07, 0xd0, 0xff, 0xfe, 0xf7, 0xbf, 0xff, 0x81, 0x88, 0xe8, 0x7f, 0, 0,
	}
}
func webPChunk(kind string, payload []byte) []byte {
	chunk := make([]byte, 8)
	copy(chunk, kind)
	binary.LittleEndian.PutUint32(chunk[4:], uint32(len(payload)))
	chunk = append(chunk, payload...)
	if len(payload)%2 != 0 {
		chunk = append(chunk, 0)
	}
	return chunk
}
func webPFile(chunks ...[]byte) []byte {
	data := []byte("RIFF\x00\x00\x00\x00WEBP")
	for _, chunk := range chunks {
		data = append(data, chunk...)
	}
	binary.LittleEndian.PutUint32(data[4:], uint32(len(data)-8))
	return data
}

// Header-only fixtures test dimensions without allocating pixel buffers.
func dimensionWebP(kind string, width, height int) []byte {
	var header []byte
	switch kind {
	case "VP8 ":
		header = []byte{0x10, 0, 0, 0x9d, 1, 0x2a, 0, 0, 0, 0}
		binary.LittleEndian.PutUint16(header[6:], uint16(width))
		binary.LittleEndian.PutUint16(header[8:], uint16(height))
	case "VP8L":
		header = make([]byte, 5)
		header[0] = 0x2f
		binary.LittleEndian.PutUint32(header[1:], uint32(width-1)|uint32(height-1)<<14)
	case "VP8X":
		header = make([]byte, 10)
		binary.LittleEndian.PutUint32(header[4:], uint32(width-1))
		header[7], header[8], header[9] = byte(height-1), byte((height-1)>>8), byte((height-1)>>16)
	}
	return webPFile(webPChunk(kind, header))
}
func animatedWebP(t *testing.T) []byte {
	t.Helper()
	extended := dimensionWebP("VP8X", 1, 1)[12:]
	extended[8] = 2
	frame := append(make([]byte, 16), stillWebP(t)[12:]...)
	frame[12] = 1
	return webPFile(extended, webPChunk("ANIM", make([]byte, 6)), webPChunk("ANMF", frame), webPChunk("ANMF", frame))
}
func TestWebPDimensions(t *testing.T) {
	for _, kind := range []string{"VP8 ", "VP8L", "VP8X"} {
		t.Run(kind, func(t *testing.T) {
			img, err := readOneImage("door", imageSource{DataBase64: b64(dimensionWebP(kind, 321, 654))}, maxImageBytes, "")
			if err != nil || img.format != "webp" || img.width != 321 || img.height != 654 {
				t.Fatalf("format=%s dimensions=%dx%d err=%v", img.format, img.width, img.height, err)
			}
		})
	}
}
func TestWebPVP8XIgnoresReservedFields(t *testing.T) {
	for name, reserved := range map[string][]byte{
		"high flag bits": {0xc0, 0, 0, 0},
		"low flag bit":   {0x01, 0, 0, 0},
		"reserved bytes": {0, 0xff, 0xff, 0xff},
		"all reserved":   {0xc1, 0xff, 0xff, 0xff},
	} {
		t.Run(name, func(t *testing.T) {
			data := dimensionWebP("VP8X", 321, 654)
			copy(data[20:24], reserved)
			img, err := readOneImage("door", imageSource{DataBase64: b64(data)}, maxImageBytes, "")
			if err != nil || img.format != "webp" || img.width != 321 || img.height != 654 {
				t.Fatalf("format=%s dimensions=%dx%d err=%v", img.format, img.width, img.height, err)
			}
		})
	}
}

func TestWebPOllamaWireAndJevRouting(t *testing.T) {
	for _, backend := range []string{"ollama", "ollama-local"} {
		for _, animated := range []bool{false, true} {
			t.Run(backend+map[bool]string{false: "/still", true: "/animated"}[animated], func(t *testing.T) {
				ollamaCloudEnv(t)
				t.Setenv("TYPESAFE_API_KEY", fixtureKey)
				t.Setenv("OPENROUTER_API_KEY", fixtureKey)
				t.Setenv("JEV_CHAIN", "typesafe,openrouter,"+backend)
				t.Setenv("JEV_IMAGES", "true")
				data := stillWebP(t)
				if animated {
					data = animatedWebP(t)
				}
				in := imageRequest(data, "") // Byte detection, without a format hint.
				calls := 0
				fakeOllamaTransport(t, func(req *http.Request) (*http.Response, error) {
					calls++
					if req.URL.String() != providers[backend].EndpointURL {
						t.Errorf("WebP sent to %s", req.URL)
					}
					checkOllamaImageBody(t, req, in)
					return ollamaImageResponse(), nil
				})
				got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, in))
				if got.code != 0 || calls != 1 {
					t.Fatalf("exit=%d calls=%d stderr=%s", got.code, calls, got.stderr)
				}
			})
		}
	}
}
func TestWebPJevOnlyChainReasons(t *testing.T) {
	ollamaCloudEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	t.Setenv("JEV_IMAGES", "true")
	blockOllamaHTTP(t)
	got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, imageRequest(stillWebP(t), "webp")))
	if got.code != 2 {
		t.Fatalf("exit=%d stderr=%s", got.code, got.stderr)
	}
	for _, backend := range []string{"typesafe", "openrouter"} {
		if !strings.Contains(got.stderr, backend+": images.door: webp is not supported by this backend") {
			t.Errorf("missing %s refusal: %s", backend, got.stderr)
		}
	}
}
func TestWebPLocalValidation(t *testing.T) {
	badSize := stillWebP(t)
	badSize[4]++
	badSignature := dimensionWebP("VP8L", 1, 1)
	badSignature[20] = 0
	for name, tc := range map[string]struct {
		data         []byte
		format, want string
	}{
		"riff size":       {badSize, "", "malformed or truncated WebP"},
		"truncated chunk": {webPFile([]byte("VP8L\xff\xff\xff\xff")), "", "malformed or truncated WebP"},
		"short header":    {webPFile(webPChunk("VP8X", []byte{0})), "", "malformed or truncated WebP"},
		"bad signature":   {badSignature, "", "malformed or truncated WebP"},
		"unknown header":  {webPFile(webPChunk("ABCD", make([]byte, 10))), "", "malformed or truncated WebP"},
		"empty container": {webPFile(), "", "malformed or truncated WebP"},
		"mismatched hint": {stillWebP(t), "png", "format does not match the file"},
		"over pixel cap":  {dimensionWebP("VP8X", 4000, 4001), "webp", "over the 16000000 pixel limit"},
	} {
		t.Run(name, func(t *testing.T) {
			ollamaCloudEnv(t)
			t.Setenv("JEV_IMAGES", "true")
			blockOllamaHTTP(t)
			got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, imageRequest(tc.data, tc.format)))
			if got.code != 2 || !strings.Contains(got.stderr, tc.want) {
				t.Fatalf("exit=%d stderr=%s; want %s", got.code, got.stderr, tc.want)
			}
		})
	}
}
func TestWebPPixelBoundaryAndFormatHint(t *testing.T) {
	spec := withImages(providers["ollama"])
	if _, err := prepare(&Client{Provider: spec, Model: spec.DefaultModel}, imageRequest(dimensionWebP("VP8X", 4000, 4000), "webp")); err != nil {
		t.Fatal(err)
	}
}
func TestWebPRequiresOperatorOptIn(t *testing.T) {
	ollamaCloudEnv(t)
	blockOllamaHTTP(t)
	got := runCallForTest(t, callOptions{}, marshalOllamaImages(t, imageRequest(stillWebP(t), "webp")))
	if got.code != 2 || !strings.Contains(got.stderr, "set JEV_IMAGES=true") {
		t.Fatalf("exit=%d stderr=%s", got.code, got.stderr)
	}
}

func TestWebPFormatCapabilityComesFromBackendRow(t *testing.T) {
	spec := withImages(providers["ollama"])
	spec.ImageFormats = []string{"png", "jpg"}
	_, err := prepare(&Client{Provider: spec, Model: spec.DefaultModel}, imageRequest(stillWebP(t), "webp"))
	if err == nil || !strings.Contains(err.Error(), "webp is not supported") {
		t.Fatalf("format capability ignored: %v", err)
	}
}
