package main

import (
	"io"
	"net/http"
	"os"
	"strings"
	"testing"
	"time"
)

var invalidHopTimeoutCases = callRejectionCases{
	setting: "JEV_HOP_TIMEOUT", values: []string{"soon", "0", "-1s", "46s", " "},
}

func TestCallRejectsInvalidHopTimeout(t *testing.T) {
	invalidHopTimeoutCases.run(t)
}

func TestWholeDeadlineReturnsTimeoutWithoutMove(t *testing.T) {
	for _, status := range []int{429, 200} {
		t.Run(http.StatusText(status), func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", "typesafe,openrouter")
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv("JEV_REQUEST_TIMEOUT", "20ms")
			t.Setenv("JEV_HOP_TIMEOUT", "20ms")
			hits := 0
			original := http.DefaultTransport
			http.DefaultTransport = backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				hits++
				<-req.Context().Done()
				// A status arriving at the deadline must not hide the whole-call timeout.
				return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
			})
			t.Cleanup(func() { http.DefaultTransport = original })
			result := runCallForTest(t, callOptions{}, validRequest)
			if result.code != 5 || result.stdout != "" || !strings.Contains(result.stderr, "context deadline exceeded") || strings.Contains(result.stderr, "rest of this session") || hits != 1 {
				t.Fatalf("call=%+v hits=%d; want exit 5 timeout, one request and no session move", result, hits)
			}
		})
	}
}

func TestLastReachableHopGetsRequestDeadline(t *testing.T) {
	for _, laterRefuses := range []bool{false, true} {
		name := "one hop"
		if laterRefuses {
			name = "later hop refuses"
		}
		t.Run(name, func(t *testing.T) {
			log := new(strings.Builder)
			first := &Client{Provider: typesafeSpec, Model: typesafeSpec.DefaultModel,
				Timeout: time.Second, HopTimeout: 20 * time.Millisecond}
			first.HTTP = &http.Client{Transport: backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
				deadline, ok := req.Context().Deadline()
				if !ok || time.Until(deadline) < 500*time.Millisecond {
					t.Errorf("last reachable hop has %v left; want the full one-second request budget", time.Until(deadline))
				}
				return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
			})}
			chain := &chainRunner{hops: []*Client{first}, log: log}
			if laterRefuses {
				spec := providers["openrouter"]
				spec.QuestionTypes = []string{typeChoice}
				chain.hops = append(chain.hops, &Client{Provider: spec, Model: spec.DefaultModel,
					Timeout: time.Second, HTTP: &http.Client{Transport: backendFixtureTransport(func(*http.Request) (*http.Response, error) {
						t.Fatal("a hop that refuses the question must not receive an HTTP request")
						return nil, nil
					})}})
			}
			capabilityCall(t, connect(t, Config{Provider: first.Provider}, chain), simpleIn(), false, `"noul":0.9`)
			if log.Len() != 0 {
				t.Fatalf("unexpected session move: %s", log)
			}
		})
	}
}

func TestHopTimeoutRoutesCallAndKeepsSession(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("JEV_CHAIN", "typesafe,openrouter")
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("OPENROUTER_API_KEY", fixtureKey)
	t.Setenv("JEV_REQUEST_TIMEOUT", "1s")
	t.Setenv("JEV_HOP_TIMEOUT", "20ms")
	resolved, err := resolveHops(os.LookupEnv, false)
	if err != nil {
		t.Fatal(err)
	}
	log := new(strings.Builder)
	chain, cfg, err := startChain(resolved, log, io.Discard)
	if err != nil {
		t.Fatal(err)
	}
	hits := [2]int{}
	for i, hop := range chain.hops {
		hop.HTTP.Transport = backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
			hits[i]++
			if i == 0 && hits[i] == 1 {
				<-req.Context().Done()
				return nil, req.Context().Err()
			}
			if i == 1 {
				deadline, ok := req.Context().Deadline()
				if !ok || time.Until(deadline) < 500*time.Millisecond {
					t.Errorf("final hop must get the remaining request time, got %v", time.Until(deadline))
				}
			}
			return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
		})
	}
	session := connect(t, cfg, chain)
	capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
	capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
	if hits != [2]int{2, 1} || log.Len() != 0 {
		t.Fatalf("hits=%v log=%q; want [2 1] and no session move", hits, log.String())
	}
}

func TestHopRetryDeadlineRetainsStatus(t *testing.T) {
	for _, mode := range []string{"wait cannot fit", "status at deadline", "retry hangs"} {
		t.Run(mode, func(t *testing.T) {
			hits := [2]int{}
			log := new(strings.Builder)
			chain := hopDeadlineChain(log, 3, []ProviderSpec{typesafeSpec, providers["openrouter"]}, func(i int) http.RoundTripper {
				return backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
					hits[i]++
					if i == 0 {
						return hopRetryDeadlineResponse(req, mode, hits[i])
					}
					return &http.Response{StatusCode: 200, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
				})
			})
			session := connect(t, Config{Provider: typesafeSpec}, chain)
			capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
			capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
			want := [2]int{1, 2}
			if mode == "retry hangs" {
				want[0] = 2
			}
			if hits != want || strings.Count(log.String(), "rest of this session") != 1 || !strings.Contains(log.String(), "HTTP 429") {
				t.Fatalf("hits=%v log=%q; want %v and one HTTP 429 session move", hits, log.String(), want)
			}
		})
	}
}

// hopRetryDeadlineResponse models the three status/retry deadline boundaries.
func hopRetryDeadlineResponse(req *http.Request, mode string, hit int) (*http.Response, error) {
	if mode == "retry hangs" && hit == 2 {
		<-req.Context().Done()
		return nil, req.Context().Err()
	}
	if mode == "status at deadline" {
		<-req.Context().Done()
	}
	header := http.Header{"Retry-After": {"600"}}
	if mode == "retry hangs" {
		header = http.Header{}
	}
	return &http.Response{StatusCode: 429, Header: header, Body: io.NopCloser(strings.NewReader("{}"))}, nil
}

func TestSetupCarriesHopTimeout(t *testing.T) {
	cfg, err := resolveConfig(envLookup(map[string]string{
		"JEV_PROVIDER": "typesafe", "JEV_HOP_TIMEOUT": "3s",
	}))
	if err != nil {
		t.Fatal(err)
	}
	got := generate(t, cfg, "/opt/racecraft/evaluate", setupOptions{clients: []string{"claude-code", "codex"}})
	if !strings.Contains(got, "'JEV_HOP_TIMEOUT=3s'") || !strings.Contains(got, `JEV_HOP_TIMEOUT = "3s"`) {
		t.Fatalf("setup must preserve the configured hop timeout for both clients: %s", got)
	}
}

func TestCallHopTimeoutDefaultsAndOverrides(t *testing.T) {
	for _, tc := range []struct {
		raw  string
		want time.Duration
	}{{"", 10 * time.Second}, {"1s", time.Second}, {"45s", 45 * time.Second}, {" 2s ", 2 * time.Second}} {
		t.Run(tc.raw, func(t *testing.T) {
			isolateCallEnv(t)
			t.Setenv("JEV_CHAIN", "typesafe,openrouter")
			t.Setenv("TYPESAFE_API_KEY", fixtureKey)
			t.Setenv("OPENROUTER_API_KEY", fixtureKey)
			t.Setenv("JEV_HOP_TIMEOUT", tc.raw)
			result := runCallForTest(t, callOptions{check: true, retarget: func(cfg *Config) {
				if cfg.HopTimeout != tc.want || cfg.fallbackConfig().HopTimeout != tc.want {
					t.Fatalf("hop timeout = %v/%v; want %v on both hops", cfg.HopTimeout, cfg.fallbackConfig().HopTimeout, tc.want)
				}
			}}, "")
			if result.code != 0 || result.stderr != "" {
				t.Fatalf("valid hop timeout %q: %+v", tc.raw, result)
			}
		})
	}
}

func TestShortRequestTimeoutKeepsImplicitHopDefaultUsable(t *testing.T) {
	isolateCallEnv(t)
	t.Setenv("TYPESAFE_API_KEY", fixtureKey)
	t.Setenv("JEV_REQUEST_TIMEOUT", "1s")
	result := runCallForTest(t, callOptions{check: true, retarget: func(cfg *Config) {
		if cfg.Timeout != time.Second || cfg.HopTimeout != time.Second {
			t.Fatalf("request/hop budgets = %v/%v; want 1s/1s", cfg.Timeout, cfg.HopTimeout)
		}
	}}, "")
	if result.code != 0 || result.stderr != "" {
		t.Fatalf("short request budget with implicit hop default must remain usable: %+v", result)
	}
}

func TestFailureAfterHopTimeoutKeepsOriginalSession(t *testing.T) {
	hits := [3]int{}
	log := new(strings.Builder)
	chain := hopDeadlineChain(log, 0, []ProviderSpec{typesafeSpec, providers["openrouter"], typesafeSpec}, func(i int) http.RoundTripper {
		return backendFixtureTransport(func(req *http.Request) (*http.Response, error) {
			hits[i]++
			if i == 0 && hits[i] == 1 {
				<-req.Context().Done()
				return nil, req.Context().Err()
			}
			status := 200
			if i == 1 {
				status = 401
			}
			return &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(noulReply))}, nil
		})
	})
	session := connect(t, Config{Provider: typesafeSpec}, chain)
	capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
	capabilityCall(t, session, simpleIn(), false, `"noul":0.9`)
	if hits != [3]int{2, 1, 1} || log.Len() != 0 {
		t.Fatalf("hits=%v log=%q; want [2 1 1] and no session move", hits, log.String())
	}
}

// hopDeadlineChain owns the common client budgets for deadline routing fixtures.
func hopDeadlineChain(log io.Writer, retries int, specs []ProviderSpec, transport func(int) http.RoundTripper) *chainRunner {
	chain := &chainRunner{log: log}
	for i, spec := range specs {
		chain.hops = append(chain.hops, &Client{Provider: spec, Model: spec.DefaultModel,
			Timeout: time.Second, HopTimeout: 20 * time.Millisecond, MaxRetries: retries,
			HTTP: &http.Client{Transport: transport(i)},
		})
	}
	return chain
}
