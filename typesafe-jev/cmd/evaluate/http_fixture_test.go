package main

import (
	"io"
	"net/http"
	"strings"
)

// fixtureHTTPResponse is the offline response boundary shared by wire tests.
func fixtureHTTPResponse(status int, body string) *http.Response {
	return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(body))}
}
