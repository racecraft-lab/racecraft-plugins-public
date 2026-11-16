package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"image"
	_ "image/jpeg" // registers the decoder DecodeConfig uses
	_ "image/png"
	"io"
	"maps"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"syscall"
)

// The two backends do not share an image wire format, and mixing them is a
// billed no-op: a TypeSafe `assets` map posted to OpenRouter comes back HTTP
// 200 with answers that never saw the picture. This file is the only place
// that chooses a format. Callers name an image and point at it; the encoder
// builds `assets` plus the images header for TypeSafe, or image_url data-URL
// parts for OpenRouter, and refuses to put `assets` on an OpenRouter body.
//
// Multipart is TypeSafe's preferred upload and is rejected by OpenRouter, so
// both backends get base64 JSON. One encoder, and no path that can only be
// correct for one of them.

const (
	headerDangerImages = "TypeSafe-Danger-Zone-Images"
	headerDangerLong   = "TypeSafe-Danger-Zone-Long-Context"

	// maxImageName bounds a name that an error is willing to repeat. A longer
	// name could be the picture itself, stuffed into the key to be echoed back.
	maxImageName = 128
)

// preparedImage is one file after local checks, plus the reference token the
// TypeSafe body will use. The token is minted here so a short caller name
// such as "cat" cannot match inside "category" once it becomes an asset key.
type preparedImage struct {
	format        string // "png" or "jpg"
	data          []byte
	ref           string
	width, height int
	sizeError     *imageSizeError
	readError     error
}

// encodeRequest builds the body and the extra headers for one backend. It
// trusts a request validateRequest has passed. Image reads and decoding are
// cached lazily, after the ordered request checks and each earlier image's
// hop limits pass; a refused prefix never opens a later source.
// A request with no images is marshalled as it always was, so the bytes on
// the wire do not change for existing callers. Headers are still applied:
// long context is a property of the process, not of the payload.
func encodeRequest(spec ProviderSpec, in evaluateIn) ([]byte, map[string]string, error) {
	images := shapedImages{read: readOneImage}
	if err := images.prepare(spec, in); err != nil {
		return nil, nil, err
	}
	return encodeLoadedRequest(spec, in, images.loaded)
}

// encodeLoadedRequest never opens an image source. Each hop builds its own
// wire representation from the shared snapshot, without rereading sources.
func encodeLoadedRequest(spec ProviderSpec, in evaluateIn, loaded map[string]preparedImage) ([]byte, map[string]string, error) {
	switch spec.WireFormat {
	case wireTypeSafeAssets, wireOpenRouterParts:
	default:
		return nil, nil, fmt.Errorf("internal: %s has no supported image wire format", spec.Name)
	}
	headers := dangerHeaders(spec, in)
	if len(in.Images) == 0 {
		// evaluateIn has no assets field and omits an empty images map, so
		// this body cannot carry either.
		body, err := json.Marshal(in)
		if err != nil {
			return nil, nil, err
		}
		return body, headers, nil
	}

	state, questions, err := imageTrees(in)
	if err != nil {
		return nil, nil, err
	}
	replace := replacementFor(spec, loaded)
	state, questions, err = rewriteImageSites(state, questions, func(_ string, v any) (any, bool, error) {
		return replaceVisit(v, in.Images, replace)
	})
	if err != nil {
		return nil, nil, err
	}

	payload := map[string]any{
		"state":     state,
		"questions": questions,
	}
	if in.Model != "" {
		payload["model"] = in.Model
	}
	if spec.WireFormat == wireTypeSafeAssets {
		assets := make(map[string]any, len(loaded))
		for _, name := range sortedKeys(loaded) {
			img := loaded[name]
			assets[img.ref] = map[string]any{
				"type":        "image",
				"format":      img.format,
				"data_base64": base64.StdEncoding.EncodeToString(img.data),
			}
		}
		payload["assets"] = assets
	}
	if err := rejectForeignImageFields(spec, payload); err != nil {
		return nil, nil, err
	}

	body, err := json.Marshal(payload)
	if err != nil {
		return nil, nil, err
	}
	return body, headers, nil
}

// dangerHeaders returns the TypeSafe opt-in headers this request needs.
// OpenRouter documents none of them, and sending one there would be a header
// the operator did not agree to share with that host.
func dangerHeaders(spec ProviderSpec, in evaluateIn) map[string]string {
	if spec.ImageHeader == "" && spec.LongContextHeader == "" {
		return nil
	}
	headers := map[string]string{}
	if spec.LongContext && spec.LongContextHeader != "" {
		headers[spec.LongContextHeader] = "true"
	}
	if spec.ImageHeader != "" && (len(in.Images) > 0 || requestHasBox(in)) {
		headers[spec.ImageHeader] = "true"
	}
	if len(headers) == 0 {
		return nil
	}
	return headers
}

// rejectForeignImageFields fails closed on an image payload that would ship
// the wrong top-level image field. OpenRouter ignores a top-level assets map
// and still bills the call, which is the failure this check exists to make
// impossible. It reads the payload map the body is marshalled from, so the
// body is never parsed back.
func rejectForeignImageFields(spec ProviderSpec, payload map[string]any) error {
	if _, ok := payload["images"]; ok {
		return errors.New("internal: the wire request still carries the images map")
	}
	_, assets := payload["assets"]
	if spec.WireFormat == wireOpenRouterParts && assets {
		return errors.New("internal: refused to put an assets map on an openrouter request")
	}
	if spec.WireFormat == wireTypeSafeAssets && !assets {
		return errors.New("internal: a typesafe image request has no assets map")
	}
	return nil
}

func requestHasBox(in evaluateIn) bool {
	for _, id := range sortedKeys(in.Questions) {
		if in.Questions[id].Type == typeBox {
			return true
		}
	}
	return false
}

// imageUseChecks preserves the parent's order: media guard, opt-in, count,
// entries, box model, box image requirement, then references. None opens paths.
func imageUseChecks(in evaluateIn, allowImages bool) requestCheckList {
	var checks requestCheckList
	sites, err := scanImageSites(in)
	checks.shape(err)
	hasBox := requestHasBox(in)
	if len(in.Images) == 0 && !hasBox {
		return checks
	}
	checks.shape(requireImageOptIn(allowImages))
	checks.hop(func(spec ProviderSpec, _ evaluateIn) error {
		if err := requireImageOptIn(spec.ImageTrust == imageTrustOperatorOptIn); err != nil {
			return err
		}
		if overLimit(len(in.Images), spec.Limits.Images) {
			return fmt.Errorf("images has %d entries, over the %d the backend accepts", len(in.Images), spec.Limits.Images)
		}
		return nil
	})
	checks.shape(validateImageEntries(in.Images))
	if hasBox {
		checks.hop(func(spec ProviderSpec, resolved evaluateIn) error { return validateBoxModel(spec, resolved.Model) })
		if len(in.Images) == 0 {
			checks.shape(errors.New("a box question needs an image in the request"))
		}
	}
	if len(in.Images) > 0 {
		checks.shape(sites.check(in.Images))
	}
	return checks
}

func requireImageOptIn(allowed bool) error {
	if !allowed {
		return errors.New("images and box questions are disabled; set JEV_IMAGES=true to send them")
	}
	return nil
}

func validateImageEntries(images map[string]imageSource) error {
	for _, name := range sortedKeys(images) {
		if !imageNameOK(name) {
			return errors.New("images has a blank or oversized name")
		}
		src := images[name]
		label := imageLabel(name)
		switch {
		case src.Path != "" && src.DataBase64 != "":
			return fmt.Errorf("%s: set path or data_base64, not both", label)
		case src.Path == "" && src.DataBase64 == "":
			return fmt.Errorf("%s: set path or data_base64", label)
		case src.Path != "" && !filepath.IsAbs(src.Path):
			return fmt.Errorf("%s: path must be absolute", label)
		}
		if src.Format != "" {
			if _, ok := canonicalFormat(src.Format); !ok {
				return fmt.Errorf("%s: format must be png, jpg, or jpeg", label)
			}
		}
	}
	return nil
}

// validateBoxModel rejects a model this process knows is Jev 1.13. Anything
// else is sent through: an unlisted id is the operator's, and rewriting it
// would hide the 404 they asked to see. The resolved model is what counts;
// prepare fills the backend default before this runs. Both defaults are Jev
// 1.14: TypeSafe's jev-latest moved to jev-1.14.0 on 2026-10-14
// (https://docs.typesafe.ai/models.md, read 2026-11-14).
func validateBoxModel(spec ProviderSpec, model string) error {
	if !spec.rejectsBoxModel(model) {
		return nil
	}
	return fmt.Errorf("model %s is Jev 1.13, which rejects box questions; use jev-latest or jev-1.14.0 on TypeSafe, or typesafe/jev-1.14 or ~typesafe/jev-latest on OpenRouter", model)
}

// imageSites is what one walk of a request's value positions found.
type imageSites struct {
	// uses counts the references to each provided image.
	uses map[string]int
	// unknown is the path of the first {"image": ...} marker that names no
	// provided image, or "".
	unknown string
}

// scanImageSites walks state, instructions, and criteria once. It refuses a
// media part the caller wrote by hand, on every request: only the encoder
// builds one, from a file the local checks have passed. When the request
// names images, the same walk counts their references.
func scanImageSites(in evaluateIn) (imageSites, error) {
	sites := imageSites{uses: map[string]int{}}
	state, questions, err := imageTrees(in)
	if err != nil {
		return sites, err
	}
	_, _, err = rewriteImageSites(state, questions, func(path string, v any) (any, bool, error) {
		if m, ok := v.(map[string]any); ok && mediaPart(m) {
			return nil, false, fmt.Errorf("%s is a provider media part (image_url, input_audio, video_url, or file); name a PNG or JPEG in images and reference it from state, instructions, or criteria", path)
		}
		name, hit, unknown := imageUse(v, in.Images)
		if unknown && sites.unknown == "" {
			sites.unknown = path
		}
		if hit {
			sites.uses[name]++
		}
		// A hit is a leaf. Descending would also count the marker's own string.
		return nil, hit, nil
	})
	return sites, err
}

// check refuses an image nothing references. A marker-shaped object that
// names no provided image is ordinary data, such as {"image": "hero.jpg"} in
// a product record, and is sent as written. A mistyped marker still fails
// here, because it leaves its image unreferenced, and the error names that
// object's path so the typo can be found.
func (s imageSites) check(images map[string]imageSource) error {
	for _, name := range sortedKeys(images) {
		if s.uses[name] > 0 {
			continue
		}
		if s.unknown != "" {
			// The path only: the marker's value is state content.
			return fmt.Errorf("%s is not referenced from state, instructions, or criteria; %s is an {\"image\": ...} object that names no provided image, and is sent as data",
				imageLabel(name), s.unknown)
		}
		return fmt.Errorf("%s is not referenced from state, instructions, or criteria", imageLabel(name))
	}
	return nil
}

// mediaPartTypes are the content-part types a provider may read as media.
// OpenRouter's multimodal Decisions guide (2026-10-17) documents image_url for
// every image model, and input_audio and video_url for cloudflare/clef-omni;
// the caller's model passes through, so all three are reachable. input_image,
// file, and input_file are the Responses and Chat Completions shapes. The
// guide says input_image is not read today; it is refused so a provider that
// starts reading it does not become a way around JEV_IMAGES.
var mediaPartTypes = map[string]bool{
	"image_url": true, "input_audio": true, "video_url": true,
	"input_image": true, "file": true, "input_file": true,
}

// mediaPayloadKeys are the fields that carry, or point at, a part's bytes.
var mediaPayloadKeys = map[string]bool{
	"image_url": true, "input_audio": true, "video_url": true,
	"file": true, "file_data": true, "file_url": true, "file_id": true,
	"image": true, "audio": true,
}

// mediaPart reports whether m has a media part's shape. Every key and the type
// value are compared trimmed and case-folded, in case a parser folds them. It
// is a part when:
//   - its type names a part, whatever its payload field is called;
//   - a payload field holds a data: URL, or an object holding one, whatever
//     the type says; or
//   - it has no type (no non-empty string under a type key) and a payload
//     field holds an object.
//
// A typed object that names no part and carries no data: URL, or a plain
// string such as an image link, is ordinary state.
func mediaPart(m map[string]any) bool {
	typed, isPart := partType(m)
	if isPart {
		return true
	}
	for key, v := range m {
		if !mediaPayloadKeys[foldKey(key)] {
			continue
		}
		// An object holding a data: URL in one of its own fields, such as
		// {"url": "data:image/png;base64,..."}, carries the bytes too.
		obj, isObject := v.(map[string]any)
		if dataURL(v) || (isObject && (!typed || slices.ContainsFunc(slices.Collect(maps.Values(obj)), dataURL))) {
			return true
		}
	}
	return false
}

// partType reports whether m has a type, meaning a non-empty string under any
// spelling of the type key, and whether any such type names a media part.
func partType(m map[string]any) (typed, isPart bool) {
	for key, v := range m {
		s, ok := v.(string)
		if foldKey(key) != "type" || !ok || strings.TrimSpace(s) == "" {
			continue
		}
		typed = true
		if mediaPartTypes[foldKey(s)] {
			return true, true
		}
	}
	return typed, false
}

func foldKey(s string) string { return strings.ToLower(strings.TrimSpace(s)) }

// dataURL reports a string that starts with "data:", ignoring case and leading
// whitespace. Only the prefix is examined, so a large payload is not copied.
func dataURL(v any) bool {
	s, ok := v.(string)
	if !ok {
		return false
	}
	s = strings.TrimLeft(s, " \t\r\n")
	return len(s) >= 5 && strings.EqualFold(s[:5], "data:")
}

func imageTrees(in evaluateIn) (any, map[string]any, error) {
	state, err := toTree(in.State)
	if err != nil {
		return nil, nil, err
	}
	rawQuestions, err := toTree(in.Questions)
	if err != nil {
		return nil, nil, err
	}
	if rawQuestions == nil {
		// A nil map marshals as null. validateRequest refuses it; here it
		// simply has no sites to walk.
		return state, map[string]any{}, nil
	}
	questions, ok := rawQuestions.(map[string]any)
	if !ok {
		return nil, nil, errors.New("questions are malformed")
	}
	return state, questions, nil
}

func toTree(v any) (any, error) {
	b, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	var out any
	if err := json.Unmarshal(b, &out); err != nil {
		return nil, err
	}
	return out, nil
}

// shapedImages caches each read, including errors, across hop preparations.
// Reads stay incremental: only an allowed image prefix may open the next path.
type shapedImages struct {
	read     func(string, imageSource, int, string) (preparedImage, error)
	loaded   map[string]preparedImage
	uses     map[string]int
	haystack string
}

func (images *shapedImages) prepare(spec ProviderSpec, in evaluateIn) error {
	if len(in.Images) == 0 {
		return nil
	}
	if spec.ImageLimits.MaxSide <= 0 {
		return fmt.Errorf("internal: %s has no image limits", spec.Name)
	}
	if err := images.initialize(in); err != nil {
		return &requestShapeError{err}
	}
	var budget imageBudget
	fileLimit, _ := imageReadLimits()
	for _, name := range sortedKeys(in.Images) {
		img, ok := images.loaded[name]
		if !ok {
			var err error
			img, err = images.read(name, in.Images[name], fileLimit, images.haystack)
			img.readError = err
			images.loaded[name] = img
		}
		if err := img.validateForHop(spec, name, in.Images[name]); err != nil {
			return err
		}
		n := max(images.uses[name], 1)
		inBody := n
		if spec.WireFormat == wireTypeSafeAssets {
			inBody = 1
		}
		if err := budget.add(spec.Limits, len(img.data), inBody, n); err != nil {
			return &hopRefusalError{err}
		}
	}
	return nil
}

// initialize records reference sites before opening the first image.
func (images *shapedImages) initialize(in evaluateIn) error {
	if images.loaded != nil {
		return nil
	}
	state, questions, err := imageTrees(in)
	if err != nil {
		return err
	}
	images.haystack, err = referenceHaystack(state, questions)
	if err != nil {
		return err
	}
	images.uses, err = countImageUses(state, questions, in.Images)
	if err != nil {
		return err
	}
	images.loaded = make(map[string]preparedImage, len(in.Images))
	return nil
}

// validateForHop preserves size, read, then dimension diagnostic precedence.
func (img preparedImage) validateForHop(spec ProviderSpec, name string, source imageSource) error {
	if img.sizeError != nil {
		return &hopRefusalError{img.sizeError.forLimit(spec.Limits.ImageBytes)}
	}
	if overLimit(len(img.data), spec.Limits.ImageBytes) {
		size := int64(-1)
		if source.Path != "" {
			size = int64(len(img.data))
		}
		return &hopRefusalError{(&imageSizeError{imageLabel(name), size, spec.Limits.ImageBytes}).forLimit(spec.Limits.ImageBytes)}
	}
	if img.readError != nil {
		return &requestShapeError{img.readError}
	}
	if err := checkImageDimensions(imageLabel(name), img.width, img.height, spec.ImageLimits); err != nil {
		return &hopRefusalError{err}
	}
	return nil
}

// imageBudget tracks wire-body, expanded-request, and decoded-file totals.
type imageBudget struct{ body, expanded, total int }

// add counts one image of size bytes that appears inBody times in the wire
// body and is used uses times. Caps come from the backend row. Divided rather
// than multiplied, so a huge use count cannot overflow before the check.
func (b *imageBudget) add(limits backendLimits, size, inBody, uses int) error {
	if limits.BodyBytes != noLimit && size > (base64.StdEncoding.DecodedLen(limits.BodyBytes)-b.body)/inBody {
		return fmt.Errorf("images together are over the %d byte request limit once base64-encoded; send fewer or smaller images, or reference each one fewer times", limits.BodyBytes)
	}
	if limits.ExpandedBytes != noLimit && size > (limits.ExpandedBytes-b.expanded)/uses {
		return fmt.Errorf("images together are over the %d byte expanded request limit, which adds an image again for each use; send fewer or smaller images, or reference each one fewer times", limits.ExpandedBytes)
	}
	if limits.TotalImageBytes != noLimit && size > limits.TotalImageBytes-b.total {
		return fmt.Errorf("images together are over the %d byte decoded image limit; send fewer or smaller images", limits.TotalImageBytes)
	}
	b.total += size
	b.body += inBody * size
	b.expanded += uses * size
	return nil
}

func referenceHaystack(state any, questions map[string]any) (string, error) {
	b, err := json.Marshal(struct {
		State     any            `json:"state"`
		Questions map[string]any `json:"questions"`
	}{state, questions})
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func readOneImage(name string, src imageSource, limit int, haystack string) (preparedImage, error) {
	label := imageLabel(name)
	data, err := imageBytes(label, src, limit)
	if err != nil {
		var size *imageSizeError
		if errors.As(err, &size) {
			// No hop can take this file; retain its size refusal without
			// allocating the bytes or treating a hop limit as a shape error.
			return preparedImage{sizeError: size}, nil
		}
		return preparedImage{}, err
	}
	if animatedPNG(data) {
		return preparedImage{data: data}, fmt.Errorf("%s: animated PNGs are rejected", label)
	}
	cfg, detected, err := image.DecodeConfig(bytes.NewReader(data))
	if err != nil {
		return preparedImage{data: data}, fmt.Errorf("%s: not a PNG or JPEG", label)
	}
	format, ok := canonicalFormat(detected)
	if !ok {
		return preparedImage{data: data}, fmt.Errorf("%s: not a PNG or JPEG", label)
	}
	if src.Format != "" {
		want, _ := canonicalFormat(src.Format)
		if want != format {
			return preparedImage{data: data}, fmt.Errorf("%s: format does not match the file", label)
		}
	}
	return preparedImage{format: format, data: data, ref: referenceToken(name, haystack), width: cfg.Width, height: cfg.Height}, nil
}

// imageSizeError preserves the old file/base64 diagnostics while deferring a
// read ceiling to hop preparation. Exact file sizes never include the path.
type imageSizeError struct {
	label string
	size  int64
	limit int
}

func (e *imageSizeError) Error() string { return e.forLimit(e.limit).Error() }

func (e *imageSizeError) forLimit(limit int) error {
	if e.size >= 0 {
		return fmt.Errorf("%s: the file is %d bytes, over the %d byte limit", e.label, e.size, limit)
	}
	return fmt.Errorf("%s: the file is over the %d byte limit", e.label, limit)
}

// imageBytes reads one image from its single source. validateImageEntries is
// the one home for the source rules: exactly one of path and data_base64, and
// an absolute path.
func imageBytes(label string, src imageSource, limit int) ([]byte, error) {
	if src.Path == "" {
		return decodeImageBase64(label, src.DataBase64, limit)
	}
	return readImageFile(label, src.Path, limit)
}

func readImageFile(label, path string, limit int) ([]byte, error) {
	// O_NONBLOCK: os.Open on a named pipe waits for a writer before any check
	// below can refuse it, and would hang the server with no message.
	f, err := os.OpenFile(path, os.O_RDONLY|syscall.O_NONBLOCK, 0)
	if err != nil {
		return nil, fmt.Errorf("%s: the image file cannot be read", label)
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() == 0 {
		return nil, fmt.Errorf("%s: the image file cannot be read", label)
	}
	if limit != noLimit && info.Size() > int64(limit) {
		return nil, &imageSizeError{label, info.Size(), limit}
	}
	var reader io.Reader = f
	if limit != noLimit {
		reader = io.LimitReader(f, int64(limit)+1)
	}
	b, err := io.ReadAll(reader)
	if err != nil || overLimit(len(b), limit) {
		if err == nil {
			return nil, &imageSizeError{label, -1, limit}
		}
		return nil, fmt.Errorf("%s: the image file cannot be read", label)
	}
	return b, nil
}

func decodeImageBase64(label, s string, limit int) ([]byte, error) {
	if strings.HasPrefix(s, "data:") || strings.ContainsAny(s, " \t\r\n") {
		return nil, fmt.Errorf("%s: data_base64 must be standard base64 with no whitespace and no data: prefix", label)
	}
	if limit != noLimit && len(s) > base64.StdEncoding.EncodedLen(limit) {
		return nil, &imageSizeError{label, -1, limit}
	}
	b, err := base64.StdEncoding.Strict().DecodeString(s)
	if err != nil {
		return nil, fmt.Errorf("%s: data_base64 is not standard base64", label)
	}
	if len(b) == 0 || overLimit(len(b), limit) {
		return nil, &imageSizeError{label, -1, limit}
	}
	return b, nil
}

func checkImageDimensions(label string, w, h int, limits imageBounds) error {
	if w < limits.MinSide || h < limits.MinSide || w > limits.MaxSide || h > limits.MaxSide {
		return fmt.Errorf("%s: sides are %d by %d pixels, outside the %d-%d range this backend accepts",
			label, w, h, limits.MinSide, limits.MaxSide)
	}
	// Sides are already inside MaxSide, so the product cannot overflow int.
	pixels := w * h
	if pixels < limits.MinPixels || pixels > limits.MaxPixels {
		return fmt.Errorf("%s: the image is %d pixels, outside the %d-%d range this backend accepts",
			label, pixels, limits.MinPixels, limits.MaxPixels)
	}
	return nil
}

func canonicalFormat(s string) (string, bool) {
	switch strings.ToLower(strings.TrimSpace(s)) {
	case "png":
		return "png", true
	case "jpg", "jpeg":
		return "jpg", true
	default:
		return "", false
	}
}

// referenceToken is the asset key written into a TypeSafe body. It is hashed
// from the caller's name so tests and retries are stable, and it is re-hashed
// once when that token already occurs in the text, which would make TypeSafe
// replace a string the caller did not mean as a reference.
func referenceToken(name, haystack string) string {
	sum := sha256.Sum256([]byte("jev-image-ref\x00" + name))
	token := "jevimg-" + hex.EncodeToString(sum[:16])
	if strings.Contains(haystack, token) {
		sum = sha256.Sum256(sum[:])
		token = "jevimg-" + hex.EncodeToString(sum[:16])
	}
	return token
}

var pngSignature = []byte{0x89, 'P', 'N', 'G', '\r', '\n', 0x1a, '\n'}

// animatedPNG reports an APNG acTL chunk ahead of the first IDAT. TypeSafe
// and OpenRouter both reject animated PNGs. The scan stops at IDAT, which is
// where the animation control chunk has to sit.
func animatedPNG(data []byte) bool {
	if len(data) < len(pngSignature) || !bytes.Equal(data[:len(pngSignature)], pngSignature) {
		return false
	}
	i := len(pngSignature)
	for i+8 <= len(data) {
		// Chunk length is a uint32. Adding it in uint64 keeps a huge length
		// from wrapping the cursor on a 32-bit int.
		n := uint64(binary.BigEndian.Uint32(data[i : i+4]))
		ctype := data[i+4 : i+8]
		switch {
		case bytes.Equal(ctype, []byte("acTL")):
			return true
		case bytes.Equal(ctype, []byte("IDAT")), bytes.Equal(ctype, []byte("IEND")):
			return false
		}
		next := uint64(i) + 12 + n
		if next > uint64(len(data)) {
			return false
		}
		i = int(next)
	}
	return false
}

func countImageUses(state any, questions map[string]any, sources map[string]imageSource) (map[string]int, error) {
	used := map[string]int{}
	_, _, err := rewriteImageSites(state, questions, func(_ string, v any) (any, bool, error) {
		name, hit, _ := imageUse(v, sources)
		if hit {
			used[name]++
		}
		// A hit is a leaf. Descending would also count the marker's own string.
		return nil, hit, nil
	})
	return used, err
}

func replacementFor(spec ProviderSpec, loaded map[string]preparedImage) func(string) any {
	if spec.WireFormat == wireTypeSafeAssets {
		return func(name string) any { return loaded[name].ref }
	}
	// Encoded once per image, not once per reference. Every part that names
	// the image shares the one string.
	urls := make(map[string]string, len(loaded))
	for name, img := range loaded {
		media := "image/jpeg"
		if img.format == "png" {
			media = "image/png"
		}
		urls[name] = "data:" + media + ";base64," + base64.StdEncoding.EncodeToString(img.data)
	}
	return func(name string) any {
		return map[string]any{
			"type":      "image_url",
			"image_url": map[string]any{"url": urls[name]},
		}
	}
}

// replaceVisit swaps a reference for its wire form. Anything else, including a
// marker-shaped object that names no provided image, is left as written.
func replaceVisit(v any, sources map[string]imageSource, replace func(string) any) (any, bool, error) {
	name, hit, _ := imageUse(v, sources)
	if !hit {
		return nil, false, nil
	}
	return replace(name), true, nil
}

// imageUse reports the image name a value references. A reference is either a
// string equal to a name, or an object whose only field is {"image": name}.
// Substring matches are intentionally not references: TypeSafe would expand
// them inside ordinary words, and OpenRouter would not see them as parts.
// unknown reports a marker-shaped object whose name is not in sources.
// Hand-written media parts are refused earlier, by scanImageSites.
func imageUse(v any, sources map[string]imageSource) (name string, hit, unknown bool) {
	switch val := v.(type) {
	case map[string]any:
		marker, ok := markerName(val)
		if !ok {
			return "", false, false
		}
		_, exists := sources[marker]
		return marker, exists, !exists
	case string:
		_, exists := sources[val]
		return val, exists, false
	default:
		return "", false, false
	}
}

func markerName(m map[string]any) (string, bool) {
	if len(m) != 1 {
		return "", false
	}
	raw, ok := m["image"]
	if !ok {
		return "", false
	}
	name, ok := raw.(string)
	return name, ok && imageNameOK(name)
}

// rewriteImageSites walks state and the instruction and criteria values.
// Question types and object keys are not values, so an image named "noul" or
// "box" cannot rewrite the question's own type field. It returns new trees and
// never writes to its arguments, so a counting pass can share them with the
// encoder.
func rewriteImageSites(state any, questions map[string]any, visit func(string, any) (any, bool, error)) (any, map[string]any, error) {
	state, err := rewriteValue(state, visit, "state")
	if err != nil {
		return nil, nil, err
	}
	out := make(map[string]any, len(questions))
	for _, id := range sortedKeys(questions) {
		q, ok := questions[id].(map[string]any)
		if !ok {
			return nil, nil, fmt.Errorf("questions.%s is malformed", id)
		}
		q = maps.Clone(q)
		if ins, ok := q["instructions"]; ok {
			q["instructions"], err = rewriteValue(ins, visit, "questions."+id+".instructions")
			if err != nil {
				return nil, nil, err
			}
		}
		if crit, ok := q["criteria"]; ok && crit != nil {
			// The criteria object itself is never visited: its keys are
			// option names or true and false, so a one-option choice named
			// "image" is an option, not an image marker. Its entries are.
			root := "questions." + id + ".criteria"
			q["criteria"], err = rewriteValue(crit, skipRoot(root, visit), root)
			if err != nil {
				return nil, nil, err
			}
		}
		out[id] = q
	}
	return state, out, nil
}

// skipRoot wraps visit so the value at root is descended into but is never
// itself a hit. Child paths are always longer than root.
func skipRoot(root string, visit func(string, any) (any, bool, error)) func(string, any) (any, bool, error) {
	return func(path string, v any) (any, bool, error) {
		if path == root {
			return nil, false, nil
		}
		return visit(path, v)
	}
}

// rewriteValue returns the replacement when visit reports one, and otherwise
// descends into objects and arrays. Keys are copied unchanged.
func rewriteValue(v any, visit func(string, any) (any, bool, error), path string) (any, error) {
	repl, ok, err := visit(path, v)
	if err != nil {
		return nil, err
	}
	if ok {
		return repl, nil
	}
	switch val := v.(type) {
	case map[string]any:
		out := make(map[string]any, len(val))
		for _, k := range sortedKeys(val) {
			child := k
			if path != "" {
				child = path + "." + k
			}
			nv, err := rewriteValue(val[k], visit, child)
			if err != nil {
				return nil, err
			}
			out[k] = nv
		}
		return out, nil
	case []any:
		out := make([]any, len(val))
		for i, el := range val {
			nv, err := rewriteValue(el, visit, fmt.Sprintf("%s[%d]", path, i))
			if err != nil {
				return nil, err
			}
			out[i] = nv
		}
		return out, nil
	default:
		return v, nil
	}
}

func imageNameOK(name string) bool {
	return name != "" && name == strings.TrimSpace(name) && len(name) <= maxImageName && !strings.ContainsAny(name, "\r\n")
}

func imageLabel(name string) string {
	if !imageNameOK(name) {
		return "images"
	}
	return "images." + name
}
