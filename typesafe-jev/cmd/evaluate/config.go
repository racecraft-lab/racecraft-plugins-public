package main

import (
	"fmt"
	"path/filepath"
	"slices"
	"sort"
	"strconv"
	"strings"
	"time"
)

// ProviderSpec is the non-secret description of an evaluation backend. The
// credential itself never lives here: see credentials.go.
type ProviderSpec struct {
	// Name is the JEV_PROVIDER value that selects this backend.
	Name string
	// EndpointURL is the complete URL to POST to, not a base to append to.
	EndpointURL string
	// APIKeyEnv is the only environment variable this backend reads a key
	// from. A backend never falls back to another backend's variable.
	APIKeyEnv string
	// DefaultModel applies when neither the tool call nor JEV_MODEL names one.
	DefaultModel         string
	AuthKind             authKind
	BillingAccount       string
	WireFormat           imageWireFormat
	QuestionTypes        []string
	UnsupportedBoxModels []string
	ImageTrust           imageTrust
	// Headers and notes are backend capabilities, independent of wire format.
	ImageHeader       string
	LongContextHeader string
	AnswerNote        string
	LongContextNote   string
	// Attribution is sent as fixed HTTP-Referer / X-OpenRouter-Title headers
	// when set. It is a constant, never derived from local paths or content.
	Attribution bool
	// StructuredEntries reports whether the backend accepts a JSON object or
	// array where an instruction or a description is expected, rather than a
	// plain string.
	//
	// Both backends do. OpenRouter's Decisions schemas typed these fields as
	// plain strings until it republished them; as of the 2026-09-20 fetch
	// recorded in docs/provider-contracts.md they are anyOf string, object, or
	// array, matching what TypeSafe documents. It stays a capability rather
	// than an assumption so a re-narrowing is one field to flip, not a hunt
	// through the validator.
	StructuredEntries bool
	// RetryStatuses are the HTTP statuses worth a second attempt on this
	// backend. See docs/provider-contracts.md: this is fork policy, not a
	// provider guarantee.
	RetryStatuses []int
	// Limits are the backend's request and image caps. LongContextTokens is
	// the enlarged context budget when LongContextHeader is supported.
	Limits            backendLimits
	LongContextTokens int
	// RequestTokens is the per-request context budget: state plus every
	// question. QuestionTokens is state plus the single longest question.
	// Image bytes are not part of either estimate.
	RequestTokens  int
	QuestionTokens int
	// ImageLimits are the publisher's pixel bounds for one image. They differ
	// by backend; a file that fails them is rejected before it is billed.
	ImageLimits imageBounds
	// AllowImages is the operator opt-in JEV_IMAGES, copied onto the spec the
	// process actually uses. It is not a property of the backend.
	AllowImages bool
	// LongContext is set only for TypeSafe, and only when the operator set
	// JEV_LONG_CONTEXT. OpenRouter's budget is already the long window and
	// takes no header, so the flag must not leak onto that spec.
	LongContext bool
}

// backendLimits holds backend-specific caps. -1 explicitly means no limit;
// zero is always an incomplete row, never an implicit unlimited value.
type backendLimits struct {
	Questions       int
	ChoiceMin       int
	ChoiceMax       int
	ScoreMin        int
	ScoreMax        int
	BodyBytes       int
	Images          int
	ImageBytes      int
	TotalImageBytes int
	ExpandedBytes   int
}

const (
	noLimit = -1
	// Both publishers document 32 MiB bodies and 16 MiB decoded images
	// (docs/provider-contracts.md, fetched 2026-10-17). Expanded size adds
	// the image again per reference; locally counted file bytes are a floor
	// because TypeSafe may enlarge an image during processing.
	maxRequestBody     = 32 << 20
	maxImageBytes      = 16 << 20
	maxExpandedRequest = 32 << 20
	// minScoreLevels is this fork's policy, stricter than either publisher.
	// OpenRouter's schema sets minItems: 1, but a one-level scale gives the
	// model nothing to place a value between.
	minScoreLevels = 2
	// maxScoreLevels is TypeSafe's published cap ("the API accepts up to 10",
	// https://docs.typesafe.ai/api.md, 2026-10-17). OpenRouter's Decisions
	// schema sets no maxItems. Both rows retain the historical cap in this
	// behavior-preserving layer; ADR 0028 allows per-hop limits later.
	maxScoreLevels = 10
	// maxChoiceOptions is a published limit, not this fork's policy: the tool
	// description states at most 255 options. Probed 2026-09-18 against the
	// OpenRouter backend, 255 options answered correctly and 256 came back as
	// an HTTP 400 naming no field.
	maxChoiceOptions = 255
	// TypeSafe's default context budgets (https://docs.typesafe.ai/models.md,
	// 2026-10-17): 64k tokens for the whole request, and 32k for the state
	// plus the single longest question. Exceeding either without the
	// long-context header is a billed round trip that comes back as a bare
	// HTTP 400, whose text blames the question types. With
	// TypeSafe-Danger-Zone-Long-Context: true, both budgets are
	// longContextTokens. OpenRouter's window is longContextTokens with no header.
	typesafeRequestTokens  = 64_000
	typesafeQuestionTokens = 32_000
	longContextTokens      = 262_144
	// Pixel bounds. Sides and totals are inclusive. TypeSafe's minimum side
	// is 280; OpenRouter's is 256. The total-pixel range is the same on both
	// (https://docs.typesafe.ai/images.md and OpenRouter's multimodal guide,
	// both 2026-10-17).
	imageSideMax      = 1568
	imagePixelsMin    = 78_400
	imagePixelsMax    = 2_458_624
	typesafeSideMin   = 280
	openrouterSideMin = 256
)

func overLimit(value, limit int) bool {
	return limit != noLimit && value > limit
}

// imageBounds is one backend's inclusive pixel limits for a single image.
type imageBounds struct {
	MinSide   int
	MaxSide   int
	MinPixels int
	MaxPixels int
}

type authKind string

const authBearer authKind = "bearer"

// Only images.go selects an encoding from this enum. The third format is
// reserved for the Ollama layer; no Ollama backend is registered here.
type imageWireFormat int

const (
	wireTypeSafeAssets imageWireFormat = iota + 1
	wireOpenRouterParts
	wireOllamaImages
)

type imageTrust int

// Both current backends require the operator's explicit image opt-in.
const imageTrustOperatorOptIn imageTrust = 1

// providers is the closed set of backends. Adding a URL here is the only way
// to change where a request goes; there is deliberately no environment
// variable that points the server at an arbitrary host.
var providers = map[string]ProviderSpec{
	"typesafe": {
		Name:        "typesafe",
		EndpointURL: "https://api.typesafe.ai/v1/systemone",
		APIKeyEnv:   "TYPESAFE_API_KEY",
		// jev-1.14.0 since 2026-10-14 (https://docs.typesafe.ai/models.md).
		DefaultModel:         "jev-latest",
		AuthKind:             authBearer,
		BillingAccount:       "typesafe",
		WireFormat:           wireTypeSafeAssets,
		QuestionTypes:        []string{typeNoul, typeChoice, typeScore, typeBox},
		UnsupportedBoxModels: []string{"jev-1.13.0", "jev-1.13"},
		ImageTrust:           imageTrustOperatorOptIn,
		ImageHeader:          headerDangerImages,
		LongContextHeader:    headerDangerLong,
		LongContextNote:      "\nLong context is enabled for the TypeSafe backend: its budgets are 262144 tokens and each TypeSafe request sends the long-context header.",
		// TypeSafe documents string, object, array, or null for every
		// instruction and description field.
		StructuredEntries: true,
		Limits:            backendRequestLimits(),
		LongContextTokens: longContextTokens,
		// 529 is TypeSafe's overload status, which upstream already retried.
		RetryStatuses: []int{429, 529},
		// Defaults from https://docs.typesafe.ai/models.md (2026-10-17).
		// JEV_LONG_CONTEXT raises both to longContextTokens and sends the header.
		RequestTokens:  typesafeRequestTokens,
		QuestionTokens: typesafeQuestionTokens,
		// https://docs.typesafe.ai/images.md (2026-10-17).
		ImageLimits: backendImageLimits(typesafeSideMin),
	},
	"openrouter": {
		Name:        "openrouter",
		EndpointURL: "https://openrouter.ai/api/alpha/decisions",
		APIKeyEnv:   "OPENROUTER_API_KEY",
		// Jev 1.14 (https://openrouter.ai/docs/guides/community/jev, 2026-10-17).
		DefaultModel:         "~typesafe/jev-latest",
		AuthKind:             authBearer,
		BillingAccount:       "openrouter",
		WireFormat:           wireOpenRouterParts,
		QuestionTypes:        []string{typeNoul, typeChoice, typeScore, typeBox},
		UnsupportedBoxModels: []string{"typesafe/jev-1.13", "~typesafe/jev-1.13", "typesafe/jev-1.13.0", "~typesafe/jev-1.13.0"},
		ImageTrust:           imageTrustOperatorOptIn,
		AnswerNote: "\nThis backend may omit confidence and probabilities from a choice or score" +
			" answer, which the TypeSafe backend always sends. Treat an absent field as" +
			" absent: do not substitute a default before branching on it." +
			" A question it declines comes back as {\"type\":\"refusal\"} with no value, while the" +
			" other questions still answer; treat a refusal as no judgment, never as a no.",
		Attribution: true,
		// Matches TypeSafe since OpenRouter republished the Decisions schemas.
		StructuredEntries: true,
		Limits:            backendRequestLimits(),
		LongContextTokens: longContextTokens,
		// All four are documented on the Decisions path and transient in
		// kind: 429 rate limited, 503 unavailable, 524 an upstream timeout,
		// and 529 overloaded. 524 and 529 were absent from the documented
		// list at the 2026-09-18 fetch and present at the 2026-09-20 one.
		// 500 and 502 are documented too but are not retried: neither is
		// transient by nature, and a replayed inference call bills again.
		RetryStatuses: []int{429, 503, 524, 529},
		// https://openrouter.ai/docs/guides/community/jev (2026-10-17): 262,144
		// tokens, with no danger-zone header. Image requests already run in
		// TypeSafe's long-context mode on the far side of OpenRouter.
		RequestTokens:  longContextTokens,
		QuestionTokens: longContextTokens,
		// Side minimum is 256, not TypeSafe's 280. Total pixels match TypeSafe.
		// https://openrouter.ai/docs/guides/community/multimodal-decisions (2026-10-17).
		ImageLimits: backendImageLimits(openrouterSideMin),
	},
}

// Both current rows share these caps; each gets its own value to keep copies
// independently configurable by the operator and tests.
func backendRequestLimits() backendLimits {
	return backendLimits{
		Questions: noLimit, ChoiceMin: 1, ChoiceMax: maxChoiceOptions,
		ScoreMin: minScoreLevels, ScoreMax: maxScoreLevels,
		BodyBytes: maxRequestBody, Images: noLimit, ImageBytes: maxImageBytes,
		TotalImageBytes: noLimit, ExpandedBytes: maxExpandedRequest,
	}
}

func backendImageLimits(minSide int) imageBounds {
	return imageBounds{
		MinSide: minSide, MaxSide: imageSideMax,
		MinPixels: imagePixelsMin, MaxPixels: imagePixelsMax,
	}
}

const (
	defaultTimeout    = 45 * time.Second
	maxTimeout        = 5 * time.Minute
	defaultMaxRetries = 3
	maxMaxRetries     = 5
)

// Config is everything needed to serve, except the credential. It holds no
// secret, so it is safe to print in a diagnostic.
type Config struct {
	Provider   ProviderSpec
	Model      string
	Timeout    time.Duration
	MaxRetries int
	// KeyFile is an absolute path, or "" to use the provider's environment
	// variable. The path is not a secret; the file's contents are.
	KeyFile string
	// KeyFileDefaulted reports that KeyFile came from --plugin-defaults rather
	// than from the operator, so a diagnostic can say which.
	KeyFileDefaulted bool
	// keyFileVar names the variable KeyFile came from, for diagnostics. It is
	// empty for the primary, which reads JEV_API_KEY_FILE; fallbackConfig sets
	// it to JEV_FALLBACK_API_KEY_FILE.
	keyFileVar string
	// Fallback is the backend a call moves to when Provider refuses its
	// credential or is unavailable, or nil. It is set only by the operator
	// (JEV_FALLBACK_PROVIDER): which keys happen to exist never creates one.
	Fallback *FallbackConfig
	// AllowImages is JEV_IMAGES. Box questions use the same opt-in: TypeSafe
	// requires the images danger-zone header for either, and a box needs an image.
	AllowImages bool
	// LongContext is JEV_LONG_CONTEXT. It changes TypeSafe's budgets and
	// header only. OpenRouter ignores it.
	LongContext bool
}

// FallbackConfig names the second backend and where its key comes from, by
// the same rules as the primary's.
type FallbackConfig struct {
	Provider ProviderSpec
	// KeyFile is an absolute path, or "" to use the fallback provider's own
	// environment variable.
	KeyFile string
	// KeyFileDefaulted is KeyFileDefaulted for the fallback's key file.
	KeyFileDefaulted bool
}

// fallbackConfig is the Config a client for the fallback backend is built
// from: its own provider, model default and key, and the primary's limits.
func (c Config) fallbackConfig() Config {
	return Config{
		Provider:   c.Fallback.Provider,
		Model:      c.Fallback.Provider.DefaultModel,
		Timeout:    c.Timeout,
		MaxRetries: c.MaxRetries,
		KeyFile:    c.Fallback.KeyFile,

		KeyFileDefaulted: c.Fallback.KeyFileDefaulted,
		keyFileVar:       pluginFallbackFileEnv,
		AllowImages:      c.AllowImages,
		LongContext:      c.LongContext,
	}
}

// applyOperator copies the process-wide image and long-context flags onto a
// backend spec. The long-context header and the raised budgets are TypeSafe's;
// applying them to OpenRouter would send a header that backend does not use
// and would not change a budget it already sets to the long window.
func applyOperator(spec ProviderSpec, allowImages, longContext bool) ProviderSpec {
	spec.AllowImages = allowImages
	if spec.LongContextHeader != "" && longContext {
		spec.LongContext = true
		spec.RequestTokens = spec.LongContextTokens
		spec.QuestionTokens = spec.LongContextTokens
	}
	return spec
}

// Kept for the live model probe; the model exclusions have one home in the row.
func knownBoxReject(provider, model string) bool {
	return providers[provider].rejectsBoxModel(model)
}

func (spec ProviderSpec) rejectsBoxModel(model string) bool {
	return slices.Contains(spec.UnsupportedBoxModels, model)
}

// keyFileEnv names the variable that sets this Config's key file.
func (c Config) keyFileEnv() string {
	if c.keyFileVar != "" {
		return c.keyFileVar
	}
	return pluginKeyFileEnv
}

// lookupFunc reports a variable's value and whether it was set at all. The
// distinction matters: an unset JEV_PROVIDER selects the default, while one
// explicitly set to blank is a mistake worth reporting.
type lookupFunc func(string) (string, bool)

// resolveOptIn reads a feature flag. Unset leaves it off. An explicit false is
// off, an explicit true is on, and any other value is a configuration error:
// guessing would send image bytes, or a long-context header, that the operator
// did not ask for.
func resolveOptIn(look lookupFunc, name string) (bool, error) {
	raw, set := look(name)
	if !set || raw == "" {
		return false, nil
	}
	switch strings.ToLower(strings.TrimSpace(raw)) {
	case "1", "true":
		return true, nil
	case "0", "false":
		return false, nil
	case "":
		return false, fmt.Errorf("%s is whitespace only; unset it to leave the feature off", name)
	default:
		return false, fmt.Errorf("%s=%q must be true or false", name, raw)
	}
}

// resolveProvider selects the backend. Selection is explicit: which API keys
// happen to be set in the environment never decides where a request goes, or
// which account it bills.
func resolveProvider(look lookupFunc) (ProviderSpec, error) {
	raw, set := look("JEV_PROVIDER")
	if !set {
		return providers["typesafe"], nil
	}
	name := strings.TrimSpace(raw)
	if name == "" {
		return ProviderSpec{}, fmt.Errorf("JEV_PROVIDER is set but blank; unset it for the default (typesafe) or name one of %s", providerNames())
	}
	spec, ok := providers[name]
	if !ok {
		// Deliberately not a fuzzy match: silently correcting a misspelling
		// could send state and billing to a backend nobody chose.
		return ProviderSpec{}, fmt.Errorf("JEV_PROVIDER=%q is not a known backend; use one of %s", name, providerNames())
	}
	return spec, nil
}

func providerNames() string {
	names := make([]string, 0, len(providers))
	for n := range providers {
		names = append(names, n)
	}
	sort.Strings(names)
	return strings.Join(names, ", ")
}

// resolveModel applies JEV_MODEL. A tool call's own model argument outranks
// this and is applied later, per request.
func resolveModel(look lookupFunc, spec ProviderSpec) (string, error) {
	raw, set := look("JEV_MODEL")
	if !set || raw == "" {
		return spec.DefaultModel, nil
	}
	if strings.TrimSpace(raw) == "" {
		return "", fmt.Errorf("JEV_MODEL is whitespace only; unset it for the backend default (%s)", spec.DefaultModel)
	}
	// Returned exactly as given. A "~typesafe/" prefix is neither added nor
	// stripped: guessing at model ids turns a clear 404 into a mystery.
	return raw, nil
}

func resolveTimeout(look lookupFunc) (time.Duration, error) {
	raw, set := look("JEV_REQUEST_TIMEOUT")
	if !set || raw == "" {
		return defaultTimeout, nil
	}
	d, err := time.ParseDuration(strings.TrimSpace(raw))
	if err != nil {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q is not a duration such as 45s or 2m", raw)
	}
	if d <= 0 {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q must be positive", raw)
	}
	if d > maxTimeout {
		return 0, fmt.Errorf("JEV_REQUEST_TIMEOUT=%q is above the %s ceiling", raw, maxTimeout)
	}
	return d, nil
}

func resolveMaxRetries(look lookupFunc) (int, error) {
	raw, set := look("JEV_MAX_RETRIES")
	if !set || raw == "" {
		return defaultMaxRetries, nil
	}
	n, err := strconv.Atoi(strings.TrimSpace(raw))
	if err != nil {
		return 0, fmt.Errorf("JEV_MAX_RETRIES=%q is not a whole number", raw)
	}
	if n < 0 || n > maxMaxRetries {
		return 0, fmt.Errorf("JEV_MAX_RETRIES=%q is outside the accepted range 0-%d", raw, maxMaxRetries)
	}
	return n, nil
}

func resolveKeyFileVar(look lookupFunc, name string) (string, error) {
	raw, set := look(name)
	if !set || raw == "" {
		return "", nil
	}
	path := strings.TrimSpace(raw)
	if path == "" {
		return "", fmt.Errorf("%s is whitespace only; unset it to use the provider's environment variable", name)
	}
	// Absolute only. A client launches this server with an unpredictable
	// working directory, so a relative path would resolve somewhere nobody
	// intended, or nowhere at all.
	if !filepath.IsAbs(path) {
		return "", fmt.Errorf("%s=%q must be an absolute path", name, path)
	}
	return path, nil
}

// resolveFallback reads the opt-in second backend. Unset means none, which is
// exactly the behaviour before fallback existed. A fallback key file with no
// fallback provider is a mistake worth reporting, not a hint to guess one.
func resolveFallback(look lookupFunc, primary ProviderSpec, home string) (*FallbackConfig, error) {
	raw, set := look("JEV_FALLBACK_PROVIDER")
	if !set || raw == "" {
		if file, _ := look("JEV_FALLBACK_API_KEY_FILE"); file != "" {
			return nil, fmt.Errorf("JEV_FALLBACK_API_KEY_FILE is set without JEV_FALLBACK_PROVIDER; name the fallback backend, one of %s", providerNames())
		}
		return nil, nil
	}
	name := strings.TrimSpace(raw)
	spec, ok := providers[name]
	if !ok {
		return nil, fmt.Errorf("JEV_FALLBACK_PROVIDER=%q is not a known backend; use one of %s", name, providerNames())
	}
	if spec.Name == primary.Name {
		return nil, fmt.Errorf("JEV_FALLBACK_PROVIDER=%q is the primary backend; a fallback must be the other one", name)
	}
	keyFile, defaulted, err := resolveHopKeyFile(look, pluginFallbackFileEnv, spec.Name, home)
	if err != nil {
		return nil, err
	}
	return &FallbackConfig{Provider: spec, KeyFile: keyFile, KeyFileDefaulted: defaulted}, nil
}

// credentialSource names where the key will be read from, for a diagnostic
// that must not print the key itself.
func (c Config) credentialSource() string {
	if c.KeyFile != "" {
		return "file " + c.KeyFile
	}
	return "environment " + c.Provider.APIKeyEnv
}
