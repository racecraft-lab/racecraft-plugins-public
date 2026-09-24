package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"
	"time"
)

// githubRepo is the only release source. There is no upstream fallback: a fork
// that quietly installed the original project's binary when its own release
// was missing would undo every change in this repository, including the
// explicit backend selection and the credential rules.
const githubRepo = "racecraft-lab/racecraft-plugins-public"

// releaseTagPrefix marks this component's releases. The repository releases
// more than one component, so its "latest" release may belong to another one:
// the updater lists releases and picks the highest typesafe-jev-v* tag, and
// never asks GitHub for "latest".
const releaseTagPrefix = "typesafe-jev-"

// githubAPI is the API root. Tests point it at a local server.
var githubAPI = "https://api.github.com"

// releasesPerPage and maxReleasePages bound the release listing: 1,000
// releases across every component, far more than this repository will carry.
var releasesPerPage = 100

const maxReleasePages = 10

const (
	// One deadline covers connect, headers and body: a stalled mirror must not
	// hang `evaluate update` forever.
	updateTimeout = 5 * time.Minute
	// Release JSON and SHA256SUMS.txt are a few KB; the archive is one
	// compressed binary. Both caps are generous by orders of magnitude.
	maxMetadataBytes = 1 << 20
	maxArchiveBytes  = 100 << 20
	// A page of 100 releases carries each one's notes and asset list.
	maxReleaseListBytes = 16 << 20
)

var updateClient = &http.Client{Timeout: updateTimeout}

// httpGet fetches url with the command's context and a bounded client, and
// rejects non-200 responses so no caller parses an error page as data.
func httpGet(ctx context.Context, url string) (*http.Response, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, err
	}
	resp, err := updateClient.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode != http.StatusOK {
		resp.Body.Close()
		return nil, fmt.Errorf("%s returned %s", url, resp.Status)
	}
	return resp, nil
}

// download reads url into memory, failing if the body exceeds limit bytes.
func download(ctx context.Context, url string, limit int64) ([]byte, error) {
	resp, err := httpGet(ctx, url)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	b, err := io.ReadAll(io.LimitReader(resp.Body, limit+1))
	if err == nil && int64(len(b)) > limit {
		err = fmt.Errorf("%s exceeds %d bytes", url, limit)
	}
	return b, err
}

// runUpdate replaces the running binary with the newest typesafe-jev release.
func runUpdate(ctx context.Context) error {
	exe, err := os.Executable()
	if err == nil {
		// Depending on the OS, exe can be the symlink the binary was started
		// through; renaming over it would replace the link, not the binary.
		exe, err = filepath.EvalSymlinks(exe)
	}
	if err != nil {
		return fmt.Errorf("finding current executable: %w", err)
	}

	// Stage beside exe so the final rename never crosses filesystems, and an
	// unwritable install dir fails before anything is downloaded. CreateTemp's
	// exclusive random name can't be redirected by a planted symlink.
	staged, err := os.CreateTemp(filepath.Dir(exe), ".evaluate-update-*")
	if err != nil {
		if errors.Is(err, os.ErrPermission) {
			return fmt.Errorf("%s is not writable, re-run with: sudo evaluate update", filepath.Dir(exe))
		}
		return fmt.Errorf("staging update: %w", err)
	}
	defer os.Remove(staged.Name()) // no-op after a successful rename
	defer staged.Close()

	// A source or development build has no release to compare against, and
	// replacing it would silently discard whatever it was built from.
	current, err := parseVersion(version)
	if err != nil {
		return fmt.Errorf("this is a %s build, not a release; rebuild from %s instead of updating in place", version, githubRepo)
	}

	release, latest, err := fetchLatestRelease(ctx)
	if err != nil {
		// Not a reason to look anywhere else. The operator fixes the
		// repository's releases, or rebuilds from source.
		return fmt.Errorf("finding the latest typesafe-jev release of %s: %w", githubRepo, err)
	}
	// Compared, not merely differenced: upstream replaced a newer local build
	// with an older release whenever the two strings happened to differ.
	if !latest.newerThan(current) {
		fmt.Printf("Already up to date (%s; latest release is %s).\n", version, release.TagName)
		return nil
	}
	fmt.Printf("Updating %s → %s from %s\n", version, release.TagName, githubRepo)

	archiveName := fmt.Sprintf("evaluate-%s-%s.tar.gz", runtime.GOOS, runtime.GOARCH)
	archiveURL, err := findAssetURL(release.Assets, archiveName)
	if err != nil {
		return err
	}
	sumsURL, err := findAssetURL(release.Assets, "SHA256SUMS.txt")
	if err != nil {
		return err
	}
	expectedHash, err := fetchExpectedChecksum(ctx, sumsURL, archiveName)
	if err != nil {
		return fmt.Errorf("fetching checksums: %w", err)
	}

	archive, err := download(ctx, archiveURL, maxArchiveBytes)
	if err != nil {
		return fmt.Errorf("downloading archive: %w", err)
	}
	sum := sha256.Sum256(archive)
	if got := hex.EncodeToString(sum[:]); got != expectedHash {
		return fmt.Errorf("checksum mismatch: got %s, want %s", got, expectedHash)
	}

	if err := extractBinaryFromTar(archive, "evaluate", staged); err != nil {
		return fmt.Errorf("extracting binary: %w", err)
	}
	if err := staged.Close(); err != nil {
		return err
	}
	if err := os.Chmod(staged.Name(), 0755); err != nil {
		return err
	}
	if err := os.Rename(staged.Name(), exe); err != nil {
		return fmt.Errorf("replacing executable: %w", err)
	}

	fmt.Printf("Updated to %s. Run `evaluate version` to confirm.\n", release.TagName)
	return nil
}

type githubRelease struct {
	TagName    string        `json:"tag_name"`
	Draft      bool          `json:"draft"`
	Prerelease bool          `json:"prerelease"`
	Assets     []githubAsset `json:"assets"`
}

type githubAsset struct {
	Name               string `json:"name"`
	BrowserDownloadURL string `json:"browser_download_url"`
}

// fetchLatestRelease lists the repository's releases and returns the highest
// published typesafe-jev-v* release, with its version. Drafts and pre-releases
// are skipped, and so is every other component's release, wherever it falls in
// the listing.
//
// A listing whose last page at the maxReleasePages cap is still full may hold
// a newer release past the cap, so it is an error rather than a quiet pick
// from the pages read.
func fetchLatestRelease(ctx context.Context) (*githubRelease, semver, error) {
	var best *githubRelease
	var bestVersion semver
	truncated := true
	for page := 1; page <= maxReleasePages; page++ {
		url := fmt.Sprintf("%s/repos/%s/releases?per_page=%d&page=%d", githubAPI, githubRepo, releasesPerPage, page)
		body, err := download(ctx, url, maxReleaseListBytes)
		if err != nil {
			return nil, semver{}, err
		}
		var releases []githubRelease
		if err := json.Unmarshal(body, &releases); err != nil {
			return nil, semver{}, fmt.Errorf("%s is not a release list: %w", url, err)
		}
		for i := range releases {
			r := &releases[i]
			if r.Draft || r.Prerelease {
				continue
			}
			v, ok := componentVersion(r.TagName)
			if !ok {
				continue
			}
			if best == nil || v.newerThan(bestVersion) {
				best, bestVersion = r, v
			}
		}
		if len(releases) < releasesPerPage {
			truncated = false
			break
		}
	}
	if truncated {
		return nil, semver{}, fmt.Errorf("the release listing fills all %d pages of %d releases, the updater's cap; a newer typesafe-jev release may be past it",
			maxReleasePages, releasesPerPage)
	}
	if best == nil {
		return nil, semver{}, errors.New("no published release has a typesafe-jev-v tag")
	}
	return best, bestVersion, nil
}

// componentVersion returns the version in a typesafe-jev-vX.Y.Z tag, and false
// for any other tag.
func componentVersion(tag string) (semver, bool) {
	rest, ok := strings.CutPrefix(tag, releaseTagPrefix)
	if !ok || !strings.HasPrefix(rest, "v") {
		return semver{}, false
	}
	v, err := parseVersion(rest)
	return v, err == nil
}

func findAssetURL(assets []githubAsset, name string) (string, error) {
	for _, a := range assets {
		if a.Name == name {
			return a.BrowserDownloadURL, nil
		}
	}
	return "", fmt.Errorf("asset %q not found in release", name)
}

func fetchExpectedChecksum(ctx context.Context, sumsURL, assetName string) (string, error) {
	body, err := download(ctx, sumsURL, maxMetadataBytes)
	if err != nil {
		return "", err
	}
	for line := range strings.Lines(string(body)) {
		fields := strings.Fields(line)
		if len(fields) == 2 && fields[1] == assetName {
			return fields[0], nil
		}
	}
	return "", fmt.Errorf("no checksum found for %q", assetName)
}

// extractBinaryFromTar copies the regular file binaryName from a .tar.gz
// archive into dst.
func extractBinaryFromTar(archive []byte, binaryName string, dst io.Writer) error {
	gr, err := gzip.NewReader(bytes.NewReader(archive))
	if err != nil {
		return err
	}
	defer gr.Close()
	tr := tar.NewReader(gr)
	for {
		hdr, err := tr.Next()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}
		if hdr.Name != binaryName {
			continue
		}
		if hdr.Typeflag != tar.TypeReg {
			return fmt.Errorf("archive member %q is not a regular file", hdr.Name)
		}
		// tar.Reader stops at hdr.Size, so this bounds the copy too.
		if hdr.Size > maxArchiveBytes {
			return fmt.Errorf("archive member %q declares %d bytes, over the %d byte limit", hdr.Name, hdr.Size, int64(maxArchiveBytes))
		}
		_, err = io.Copy(dst, tr)
		return err
	}
	return fmt.Errorf("binary %q not found in archive", binaryName)
}

// semver is the subset of semantic versioning a release tag uses here:
// major.minor.patch, optionally prefixed with "v" and suffixed with a
// pre-release identifier.
//
// A hand-rolled comparison rather than a new dependency: three integers and a
// pre-release flag is the whole contract, and the rule that matters is simply
// that an older release must never replace a newer build.
type semver struct {
	major, minor, patch int
	pre                 string
}

// Build metadata is deliberately not accepted. A release tag never carries a
// "+" suffix, but Go stamps one onto a build made from a modified working tree
// ("v0.4.0+dirty"). Treating that as the release it was built near would
// replace someone's local changes with the published binary.
var semverPattern = regexp.MustCompile(`^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?$`)

func parseVersion(s string) (semver, error) {
	m := semverPattern.FindStringSubmatch(strings.TrimSpace(s))
	if m == nil {
		return semver{}, fmt.Errorf("%q is not a semantic version", s)
	}
	var v semver
	var err error
	if v.major, err = strconv.Atoi(m[1]); err != nil {
		return semver{}, err
	}
	if v.minor, err = strconv.Atoi(m[2]); err != nil {
		return semver{}, err
	}
	if v.patch, err = strconv.Atoi(m[3]); err != nil {
		return semver{}, err
	}
	v.pre = m[4]
	return v, nil
}

// newerThan reports whether v is a later version than other. A pre-release
// sorts before the release it leads to, so 1.2.0-rc.1 is older than 1.2.0.
func (v semver) newerThan(other semver) bool {
	for _, pair := range [][2]int{
		{v.major, other.major},
		{v.minor, other.minor},
		{v.patch, other.patch},
	} {
		if pair[0] != pair[1] {
			return pair[0] > pair[1]
		}
	}
	switch {
	case v.pre == other.pre:
		return false
	case v.pre == "":
		return true
	case other.pre == "":
		return false
	default:
		return comparePre(v.pre, other.pre) > 0
	}
}

// comparePre orders two pre-release strings by the SemVer rules, returning a
// negative number, zero, or a positive number.
//
// A plain string comparison is wrong here: it puts "rc.10" before "rc.2",
// because "1" sorts before "2". SemVer compares dot-separated identifiers, and
// a numeric identifier is compared as a number. It also sorts a numeric
// identifier below an alphanumeric one, and treats a longer set of identifiers
// as greater when every earlier one is equal.
func comparePre(a, b string) int {
	ai := strings.Split(a, ".")
	bi := strings.Split(b, ".")
	for i := 0; i < len(ai) && i < len(bi); i++ {
		if c := comparePreIdentifier(ai[i], bi[i]); c != 0 {
			return c
		}
	}
	return len(ai) - len(bi)
}

func comparePreIdentifier(a, b string) int {
	an, aNum := preNumber(a)
	bn, bNum := preNumber(b)
	switch {
	case aNum && bNum:
		return an - bn
	case aNum:
		// Numeric identifiers always have lower precedence.
		return -1
	case bNum:
		return 1
	default:
		return strings.Compare(a, b)
	}
}

// preNumber reports whether s is a numeric identifier, and its value. Leading
// zeros are not valid in a numeric identifier, so "01" is compared as text.
func preNumber(s string) (int, bool) {
	if s == "" || (len(s) > 1 && s[0] == '0') {
		return 0, false
	}
	n, err := strconv.Atoi(s)
	if err != nil || n < 0 {
		return 0, false
	}
	return n, true
}
