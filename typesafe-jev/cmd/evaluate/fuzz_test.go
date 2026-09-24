package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"strings"
	"testing"
)

// keyRejections are the only errors parseKey may return.
var keyRejections = []error{errKeyEmpty, errKeyWhitespace, errKeyControlChar, errKeyPlaceholder}

// partOfRejectionText reports whether s appears inside a rejection reason's
// fixed text, as " " does inside "has leading or trailing whitespace". Such an
// input shows up in the error by coincidence, not because it was quoted.
func partOfRejectionText(s string) bool {
	for _, r := range keyRejections {
		if strings.Contains(r.Error(), s) {
			return true
		}
	}
	return false
}

// FuzzParseKey: parseKey never panics, rejects only with one of its fixed
// reasons, never quotes the candidate in an error, and accepts only a value it
// passes through unchanged.
func FuzzParseKey(f *testing.F) {
	for _, seed := range []string{
		"sk-sentinel-fuzz-seed",
		"",
		" sk-sentinel-fuzz-seed",
		"sk-sentinel-fuzz-seed\n",
		"sk-sentinel\r\nX-Injected: 1",
		"sk-sentinel\x00",
		"${TYPESAFE_API_KEY}",
		"sk-sentinel-ünicode-☃",
		"\x7f",
	} {
		f.Add(seed)
	}
	f.Fuzz(func(t *testing.T, s string) {
		key, err := parseKey(s)
		if err != nil {
			if s != "" && strings.Contains(err.Error(), s) && !partOfRejectionText(s) {
				t.Fatalf("error quotes the candidate: %q", err)
			}
			for _, r := range keyRejections {
				if err == r {
					if key != "" {
						t.Fatal("a rejected candidate also returned a credential")
					}
					return
				}
			}
			t.Fatalf("parseKey returned %q, which is not one of its fixed rejection reasons", err)
		}
		if key.reveal() != s {
			t.Fatal("an accepted key was changed on the way through")
		}
		if s == "" || s != strings.TrimSpace(s) || strings.ContainsFunc(s, func(r rune) bool { return r < 0x20 || r == 0x7f }) {
			t.Fatalf("accepted a candidate parseKey should reject: %q", s)
		}
		if got := fmt.Sprint(key); got != "[redacted]" {
			t.Fatalf("a credential printed as %q", got)
		}
	})
}

// callRequestErrors is every error readCallRequest may return. Each is fixed
// text: a decoder's own message can quote the input, which may be the private
// state being judged.
var callRequestErrors = map[string]bool{
	"reading the request from stdin failed":                                                       true,
	fmt.Sprintf("the request on stdin is over the %d byte limit", maxRequestBody):                 true,
	`stdin is not one JSON object of the form {"state": ..., "questions": {...}, "model": "..."}`: true,
	"stdin holds more than one JSON value; send exactly one request":                              true,
}

// FuzzCallRequestDecode: the `evaluate call` stdin decoder never panics,
// fails only with fixed text, and rejects unknown fields and oversize input.
func FuzzCallRequestDecode(f *testing.F) {
	// The size limit is checked once here rather than per input: a 16 MiB
	// read on every iteration would leave the fuzzer almost no time to search.
	atLimit := validRequest + strings.Repeat(" ", maxRequestBody-len(validRequest))
	if _, err := readCallRequest(strings.NewReader(atLimit)); err != nil {
		f.Fatalf("a request of exactly %d bytes was rejected: %v", maxRequestBody, err)
	}
	if _, err := readCallRequest(strings.NewReader(atLimit + " ")); err == nil {
		f.Fatalf("a request of %d bytes was accepted", maxRequestBody+1)
	}

	for _, seed := range []string{
		validRequest,
		`{"state":{"ticket":{"id":7,"text":"db timeouts"}},"questions":{"team":{"type":"choice","instructions":"Which team owns this?","criteria":{"database":"db errors","none":null}}},"model":"jev-latest"}`,
		`{"state":"s","questions":{"sev":{"type":"score","instructions":"How severe?","criteria":["minor","major"]}}}`,
		`{"state":"s","questions":{"q":{"type":"noul","instructions":"i"}},"apiKey":"x"}`,
		`{"state":"s","questions":{"q":{"type":"noul","instructions":"i","extra":1}}}`,
		validRequest + validRequest,
		`{"state": "unterminated`,
		`null`,
		`[]`,
		``,
		`[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[`,
	} {
		f.Add([]byte(seed))
	}
	f.Fuzz(func(t *testing.T, data []byte) {
		_, err := readCallRequest(bytes.NewReader(data))
		if err != nil {
			if !callRequestErrors[err.Error()] {
				t.Fatalf("error is not one of the fixed messages: %q", err)
			}
			return
		}
		// Accepted: one JSON value, so it must also unmarshal on its own.
		var fields map[string]json.RawMessage
		if err := json.Unmarshal(data, &fields); err != nil {
			t.Fatalf("accepted input is not a single JSON object: %v", err)
		}
		if fields == nil {
			return // a bare null, which decodes to the zero request
		}
		// The same request with one field it does not define must be refused.
		fields["zzUnknownField"] = json.RawMessage("1")
		withUnknown, err := json.Marshal(fields)
		if err != nil {
			t.Fatal(err)
		}
		if _, err := readCallRequest(bytes.NewReader(withUnknown)); err == nil {
			t.Fatalf("accepted a request with an unknown field: %s", withUnknown)
		}
	})
}
