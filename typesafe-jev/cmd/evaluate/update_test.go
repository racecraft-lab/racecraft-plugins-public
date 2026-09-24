package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"strconv"
	"strings"
	"testing"
)

// REL-01: every release path points at the fork. An updater that falls back to
// upstream would replace this binary with one that has none of its changes:
// no explicit backend selection, no credential rules, no validation.
func TestReleaseSourceIsTheFork(t *testing.T) {
	if githubRepo != "racecraft-lab/racecraft-plugins-public" {
		t.Fatalf("githubRepo = %q", githubRepo)
	}
	if strings.Contains(githubRepo, "itsmostafa") {
		t.Fatal("the updater points at upstream")
	}
	if !strings.Contains(attributionURL, "racecraft-lab") {
		t.Errorf("attribution URL = %q", attributionURL)
	}
}

// REL-02: an older or equal release never replaces the running build, and a
// development build refuses to self-update at all.
func TestVersionComparison(t *testing.T) {
	for _, tc := range []struct {
		latest, current string
		wantNewer       bool
	}{
		{"v0.5.0", "v0.4.0", true},
		{"v0.4.1", "v0.4.0", true},
		{"v1.0.0", "v0.99.99", true},
		// The case upstream got wrong: unequal strings meant "update", so an
		// older release replaced a newer local build.
		{"v0.4.0", "v0.5.0", false},
		{"v0.4.0", "v0.4.0", false},
		{"v0.4.0", "v0.4.1", false},
		// A pre-release leads to its version, so it sorts before it.
		{"v0.5.0", "v0.5.0-rc.1", true},
		{"v0.5.0-rc.1", "v0.5.0", false},
		{"v0.5.0-rc.2", "v0.5.0-rc.1", true},
	} {
		latest, err := parseVersion(tc.latest)
		if err != nil {
			t.Fatalf("%s: %v", tc.latest, err)
		}
		current, err := parseVersion(tc.current)
		if err != nil {
			t.Fatalf("%s: %v", tc.current, err)
		}
		if got := latest.newerThan(current); got != tc.wantNewer {
			t.Errorf("%s newerThan %s = %v, want %v", tc.latest, tc.current, got, tc.wantNewer)
		}
	}
}

// A build that is not a release has nothing to compare, so parsing must fail
// and runUpdate must refuse rather than guess.
func TestDevelopmentBuildsHaveNoVersion(t *testing.T) {
	for _, v := range []string{"dev", "", "(devel)", "v0.4.0+dirty", "main", "0.4"} {
		if _, err := parseVersion(v); err == nil {
			t.Errorf("parseVersion(%q) should fail; a non-release must not self-update", v)
		}
	}
	// Release tags in both common spellings do parse.
	for _, v := range []string{"v0.4.0", "0.4.0", "v1.2.3-rc.1"} {
		if _, err := parseVersion(v); err != nil {
			t.Errorf("parseVersion(%q): %v", v, err)
		}
	}
}

// A pre-release is compared by SemVer's rules, not as a string. Plain string
// comparison puts "rc.10" before "rc.2", because "1" sorts before "2", which
// would refuse a real upgrade.
func TestPreReleaseOrdering(t *testing.T) {
	for _, tc := range []struct {
		later, earlier string
	}{
		{"v1.0.0-rc.10", "v1.0.0-rc.2"},
		{"v1.0.0-rc.2", "v1.0.0-rc.1"},
		{"v1.0.0-beta.11", "v1.0.0-beta.2"},
		// Numeric identifiers sort below alphanumeric ones.
		{"v1.0.0-alpha.beta", "v1.0.0-alpha.1"},
		// A longer identifier set wins when the shared prefix is equal.
		{"v1.0.0-alpha.1", "v1.0.0-alpha"},
		// The SemVer specification's own example chain.
		{"v1.0.0-alpha.beta", "v1.0.0-alpha.1"},
		{"v1.0.0-beta", "v1.0.0-alpha.beta"},
		{"v1.0.0-beta.2", "v1.0.0-beta"},
		{"v1.0.0-rc.1", "v1.0.0-beta.11"},
		{"v1.0.0", "v1.0.0-rc.1"},
	} {
		later, err := parseVersion(tc.later)
		if err != nil {
			t.Fatalf("%s: %v", tc.later, err)
		}
		earlier, err := parseVersion(tc.earlier)
		if err != nil {
			t.Fatalf("%s: %v", tc.earlier, err)
		}
		if !later.newerThan(earlier) {
			t.Errorf("%s should be newer than %s", tc.later, tc.earlier)
		}
		if earlier.newerThan(later) {
			t.Errorf("%s should not be newer than %s", tc.earlier, tc.later)
		}
	}
}

// fakeReleasesAPI serves releases, newest first, releasesPerPage at a time, the
// way GitHub's list endpoint does. A request for /releases/latest fails the
// test: in a repository that releases several components, "latest" can be
// another component's release.
func fakeReleasesAPI(t *testing.T, releases []githubRelease) *httptest.Server {
	t.Helper()
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.HasSuffix(r.URL.Path, "/releases/latest") {
			t.Errorf("the updater asked for %s", r.URL.Path)
			http.NotFound(w, r)
			return
		}
		if r.URL.Path != "/repos/"+githubRepo+"/releases" {
			http.NotFound(w, r)
			return
		}
		page, _ := strconv.Atoi(r.URL.Query().Get("page"))
		perPage, _ := strconv.Atoi(r.URL.Query().Get("per_page"))
		start := (page - 1) * perPage
		end := min(start+perPage, len(releases))
		if start < 0 || start > len(releases) {
			start, end = 0, 0
		}
		json.NewEncoder(w).Encode(releases[start:end])
	}))
	t.Cleanup(srv.Close)
	return srv
}

func withReleasesAPI(t *testing.T, srv *httptest.Server, perPage int) {
	t.Helper()
	oldAPI, oldPerPage := githubAPI, releasesPerPage
	githubAPI, releasesPerPage = srv.URL, perPage
	t.Cleanup(func() { githubAPI, releasesPerPage = oldAPI, oldPerPage })
}

// REL-03: the updater picks the highest published typesafe-jev-v* release,
// however the listing interleaves it with speckit-pro-v* releases, and
// wherever the page boundary falls.
func TestLatestReleaseIsThisComponents(t *testing.T) {
	releases := []githubRelease{
		{TagName: "speckit-pro-v2.40.0"},
		{TagName: "speckit-pro-v2.39.1"},
		{TagName: "typesafe-jev-v0.11.0", Draft: true},
		{TagName: "speckit-pro-v2.39.0"},
		{TagName: "typesafe-jev-v0.10.0-rc.1", Prerelease: true},
		{TagName: "typesafe-jev-v0.9.0"},
		{TagName: "speckit-pro-v2.38.0"},
		{TagName: "typesafe-jev-v0.10.0"},
		{TagName: "typesafe-jev-vnext"},
		{TagName: "v9.9.9"},
		{TagName: "typesafe-jev-v0.8.0"},
	}
	for _, perPage := range []int{2, 3, 100} {
		t.Run(fmt.Sprintf("%d per page", perPage), func(t *testing.T) {
			withReleasesAPI(t, fakeReleasesAPI(t, releases), perPage)
			got, v, err := fetchLatestRelease(context.Background())
			if err != nil {
				t.Fatal(err)
			}
			if got.TagName != "typesafe-jev-v0.10.0" {
				t.Errorf("picked %s, want typesafe-jev-v0.10.0", got.TagName)
			}
			if want, _ := parseVersion("v0.10.0"); v != want {
				t.Errorf("version = %+v", v)
			}
		})
	}
}

// REL-04: a repository with no published typesafe-jev release is an error, not
// a reason to take another component's release.
func TestNoComponentReleaseIsAnError(t *testing.T) {
	withReleasesAPI(t, fakeReleasesAPI(t, []githubRelease{
		{TagName: "speckit-pro-v2.40.0"},
		{TagName: "typesafe-jev-v0.9.0", Draft: true},
	}), 100)
	if got, _, err := fetchLatestRelease(context.Background()); err == nil {
		t.Fatalf("picked %s from a list with no published typesafe-jev release", got.TagName)
	}
}

// A listing still full at the page cap is an error naming the cap, not a pick
// from the pages read: a newer release may sit past the last page fetched.
func TestTruncatedReleaseListingIsAnError(t *testing.T) {
	var releases []githubRelease
	for i := range maxReleasePages + 1 {
		releases = append(releases, githubRelease{TagName: fmt.Sprintf("typesafe-jev-v0.%d.0", i)})
	}
	withReleasesAPI(t, fakeReleasesAPI(t, releases), 1)
	got, _, err := fetchLatestRelease(context.Background())
	if err == nil {
		t.Fatalf("picked %s from a listing truncated at the page cap", got.TagName)
	}
	if want := fmt.Sprintf("all %d pages", maxReleasePages); !strings.Contains(err.Error(), want) {
		t.Errorf("error %q does not name the %d-page cap", err, maxReleasePages)
	}

	// A listing that ends on a short page inside the cap succeeds.
	withReleasesAPI(t, fakeReleasesAPI(t, releases[:maxReleasePages-1]), 1)
	if _, _, err := fetchLatestRelease(context.Background()); err != nil {
		t.Errorf("a listing that ends inside the cap failed: %v", err)
	}
}

func TestComponentVersion(t *testing.T) {
	for tag, want := range map[string]bool{
		"typesafe-jev-v0.9.0":       true,
		"typesafe-jev-v1.0.0-rc.1":  true,
		"typesafe-jev-0.9.0":        false,
		"speckit-pro-v0.9.0":        false,
		"v0.9.0":                    false,
		"typesafe-jev-v0.9.0+dirty": false,
		"typesafe-jev-v0.9":         false,
	} {
		if _, ok := componentVersion(tag); ok != want {
			t.Errorf("componentVersion(%q) ok = %v, want %v", tag, ok, want)
		}
	}
}
