package main

import (
	"net/url"
	"testing"
)

// SECURITY.md: remote providers are reached over HTTPS; only ollama-local
// uses plain HTTP, and only to the loopback daemon.
func TestProviderEndpointsAreHTTPSOrLoopbackDaemon(t *testing.T) {
	for name, spec := range providers {
		u, err := url.Parse(spec.EndpointURL)
		if err != nil {
			t.Fatalf("%s endpoint %q: %v", name, spec.EndpointURL, err)
		}
		switch {
		case u.Scheme == "https":
		case u.Scheme == "http" && spec.Daemon && u.Hostname() == "localhost":
		default:
			t.Errorf("%s endpoint %q must be HTTPS, or HTTP to localhost for a daemon row", name, spec.EndpointURL)
		}
	}
}
