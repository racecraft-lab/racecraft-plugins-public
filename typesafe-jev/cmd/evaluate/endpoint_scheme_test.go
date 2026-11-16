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
		if spec.Daemon {
			if u.Scheme != "http" || u.Hostname() != "localhost" {
				t.Errorf("%s is a daemon row, so its endpoint %q must be HTTP to localhost", name, spec.EndpointURL)
			}
		} else if u.Scheme != "https" {
			t.Errorf("%s endpoint %q must be HTTPS", name, spec.EndpointURL)
		}
	}
}
