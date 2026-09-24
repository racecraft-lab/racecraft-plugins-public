package main

import (
	"archive/tar"
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
)

// installerPath is the shipped installer, relative to the repository root.
const installerPath = "plugin/scripts/install_evaluate.py"

// releaseArchive builds evaluate-<os>-<arch>.tar.gz holding one file named
// evaluate with the given contents, as a release does.
func releaseArchive(t *testing.T, contents string) []byte {
	t.Helper()
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	if err := tw.WriteHeader(&tar.Header{Name: "evaluate", Mode: 0o755, Size: int64(len(contents)), Typeflag: tar.TypeReg}); err != nil {
		t.Fatal(err)
	}
	if _, err := tw.Write([]byte(contents)); err != nil {
		t.Fatal(err)
	}
	if err := tw.Close(); err != nil {
		t.Fatal(err)
	}
	if err := gz.Close(); err != nil {
		t.Fatal(err)
	}
	return buf.Bytes()
}

// fakeReleaseDownloads serves one tag's assets the way a release download URL
// does: /<tag>/<asset>. It records every path requested.
type fakeReleaseDownloads struct {
	*httptest.Server
	requests atomic.Int32
	mu       sync.Mutex
	paths    []string
}

func (f *fakeReleaseDownloads) requested() []string {
	f.mu.Lock()
	defer f.mu.Unlock()
	return append([]string(nil), f.paths...)
}

func newFakeReleaseDownloads(t *testing.T, tag string, assets map[string][]byte) *fakeReleaseDownloads {
	t.Helper()
	f := &fakeReleaseDownloads{}
	f.Server = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		f.requests.Add(1)
		f.mu.Lock()
		f.paths = append(f.paths, r.URL.Path)
		f.mu.Unlock()
		name, ok := strings.CutPrefix(r.URL.Path, "/"+tag+"/")
		body, found := assets[name]
		if !ok || !found {
			http.NotFound(w, r)
			return
		}
		w.Write(body)
	}))
	t.Cleanup(f.Close)
	return f
}

func assetName() string {
	return "evaluate-" + runtime.GOOS + "-" + runtime.GOARCH + ".tar.gz"
}

func sumsFor(name string, archive []byte) []byte {
	sum := sha256.Sum256(archive)
	return []byte(hex.EncodeToString(sum[:]) + "  " + name + "\n" +
		strings.Repeat("0", 64) + "  evaluate-other-os.tar.gz\n")
}

func runInstaller(t *testing.T, args ...string) (string, string, error) {
	t.Helper()
	return runInstallerIn(t, t.TempDir(), nil, args...)
}

// runInstallerIn runs the installer with HOME set to home and env added to an
// environment built from scratch.
func runInstallerIn(t *testing.T, home string, env []string, args ...string) (string, string, error) {
	t.Helper()
	if runtime.GOOS != "darwin" && runtime.GOOS != "linux" {
		t.Skipf("no release build for %s", runtime.GOOS)
	}
	cmd := exec.Command(pythonPath(t), append([]string{filepath.Join(repoRoot(t), filepath.FromSlash(installerPath))}, args...)...)
	cmd.Env = append([]string{"PATH=" + os.Getenv("PATH"), "HOME=" + home}, env...)
	var stdout, stderr strings.Builder
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	return stdout.String(), stderr.String(), err
}

// INS-01: the installer downloads the named tag's archive, checks it against
// that release's SHA256SUMS.txt, and installs the binary it holds. It asks for
// the tag by name, never for "latest".
func TestInstallerInstallsAVerifiedRelease(t *testing.T) {
	archive := releaseArchive(t, "release binary")
	srv := newFakeReleaseDownloads(t, "typesafe-jev-v0.9.0", map[string][]byte{
		assetName():      archive,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	dest := filepath.Join(t.TempDir(), "libexec", "evaluate")

	stdout, stderr, err := runInstaller(t, "--version", "0.9.0", "--dest", dest, "--base-url", srv.URL)
	if err != nil {
		t.Fatalf("%v\nstdout: %s\nstderr: %s", err, stdout, stderr)
	}
	got, err := os.ReadFile(dest)
	if err != nil {
		t.Fatal(err)
	}
	if string(got) != "release binary" {
		t.Errorf("installed %q", got)
	}
	if info, _ := os.Stat(dest); info.Mode().Perm()&0o111 == 0 {
		t.Errorf("installed binary is not executable: %v", info.Mode())
	}
	for _, p := range srv.requested() {
		if strings.Contains(p, "latest") {
			t.Errorf("the installer asked for %s", p)
		}
	}
	assertNoStagedFiles(t, filepath.Dir(dest))
}

// INS-02: an archive whose checksum does not match is refused, and nothing is
// installed or left behind.
func TestInstallerRefusesAChecksumMismatch(t *testing.T) {
	archive := releaseArchive(t, "release binary")
	tampered := releaseArchive(t, "something else")
	srv := newFakeReleaseDownloads(t, "typesafe-jev-v0.9.0", map[string][]byte{
		assetName():      tampered,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	dir := t.TempDir()
	dest := filepath.Join(dir, "evaluate")

	_, stderr, err := runInstaller(t, "--version", "0.9.0", "--dest", dest, "--base-url", srv.URL)
	if err == nil {
		t.Fatal("want a failure on a checksum mismatch")
	}
	if !strings.Contains(stderr, "checksum mismatch") {
		t.Errorf("stderr = %q", stderr)
	}
	if _, err := os.Stat(dest); !os.IsNotExist(err) {
		t.Errorf("a binary was installed: %v", err)
	}
	assertNoStagedFiles(t, dir)
}

// INS-03: an existing binary is replaced only with --force, and a refusal
// happens before anything is downloaded.
func TestInstallerReplacesOnlyWithForce(t *testing.T) {
	archive := releaseArchive(t, "new binary")
	srv := newFakeReleaseDownloads(t, "typesafe-jev-v0.9.0", map[string][]byte{
		assetName():      archive,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	dir := t.TempDir()
	dest := filepath.Join(dir, "evaluate")
	if err := os.WriteFile(dest, []byte("old binary"), 0o755); err != nil {
		t.Fatal(err)
	}

	_, stderr, err := runInstaller(t, "--version", "0.9.0", "--dest", dest, "--base-url", srv.URL)
	if err == nil || !strings.Contains(stderr, "--force") {
		t.Fatalf("want a refusal naming --force; err=%v stderr=%q", err, stderr)
	}
	if n := srv.requests.Load(); n != 0 {
		t.Errorf("the refusal came after %d downloads", n)
	}
	if got, _ := os.ReadFile(dest); string(got) != "old binary" {
		t.Errorf("the existing binary changed: %q", got)
	}

	if _, stderr, err := runInstaller(t, "--version", "0.9.0", "--dest", dest, "--base-url", srv.URL, "--force"); err != nil {
		t.Fatalf("--force: %v; stderr: %s", err, stderr)
	}
	if got, _ := os.ReadFile(dest); string(got) != "new binary" {
		t.Errorf("--force installed %q", got)
	}
	assertNoStagedFiles(t, dir)
}

// A leading ~ in EVALUATE_BIN is the home directory, as it is for the
// launcher, so the installer writes the file the launcher will look for.
func TestInstallerExpandsTildeInEvaluateBin(t *testing.T) {
	archive := releaseArchive(t, "release binary")
	srv := newFakeReleaseDownloads(t, "typesafe-jev-v0.9.0", map[string][]byte{
		assetName():      archive,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	home := t.TempDir()

	_, stderr, err := runInstallerIn(t, home, []string{"EVALUATE_BIN=~/bin/evaluate"}, "--version", "0.9.0", "--base-url", srv.URL)
	if err != nil {
		t.Fatalf("%v; stderr: %s", err, stderr)
	}
	if got, err := os.ReadFile(filepath.Join(home, "bin", "evaluate")); err != nil || string(got) != "release binary" {
		t.Errorf("installed at ~/bin/evaluate: %q, %v", got, err)
	}
}

// INS-04: by default the installer takes the plugin's own version, so the
// binary matches the launcher that runs it.
func TestInstallerDefaultsToThePluginVersion(t *testing.T) {
	version, _ := readJSON(t, filepath.Join(repoRoot(t), "plugin/.claude-plugin/plugin.json"))["version"].(string)
	tag := "typesafe-jev-v" + version
	archive := releaseArchive(t, "plugin version")
	srv := newFakeReleaseDownloads(t, tag, map[string][]byte{
		assetName():      archive,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	dest := filepath.Join(t.TempDir(), "evaluate")

	if _, stderr, err := runInstaller(t, "--dest", dest, "--base-url", srv.URL); err != nil {
		t.Fatalf("%v; stderr: %s; requested %v", err, stderr, srv.requested())
	}
	for _, p := range srv.requested() {
		if !strings.HasPrefix(p, "/"+tag+"/") {
			t.Errorf("requested %s, outside %s", p, tag)
		}
	}
}

// INS-05: an archive whose evaluate member is not a regular file is refused.
func TestInstallerRefusesANonRegularMember(t *testing.T) {
	var buf bytes.Buffer
	gz := gzip.NewWriter(&buf)
	tw := tar.NewWriter(gz)
	tw.WriteHeader(&tar.Header{Name: "evaluate", Typeflag: tar.TypeSymlink, Linkname: "/etc/passwd"})
	tw.Close()
	gz.Close()
	archive := buf.Bytes()
	srv := newFakeReleaseDownloads(t, "typesafe-jev-v0.9.0", map[string][]byte{
		assetName():      archive,
		"SHA256SUMS.txt": sumsFor(assetName(), archive),
	})
	dir := t.TempDir()
	dest := filepath.Join(dir, "evaluate")
	_, stderr, err := runInstaller(t, "--version", "0.9.0", "--dest", dest, "--base-url", srv.URL)
	if err == nil || !strings.Contains(stderr, "not a regular file") {
		t.Fatalf("err=%v stderr=%q", err, stderr)
	}
	if _, err := os.Lstat(dest); !os.IsNotExist(err) {
		t.Errorf("something was installed: %v", err)
	}
}

func assertNoStagedFiles(t *testing.T, dir string) {
	t.Helper()
	entries, _ := os.ReadDir(dir)
	for _, e := range entries {
		if strings.HasPrefix(e.Name(), ".evaluate-install-") {
			t.Errorf("a staged file was left behind: %s", e.Name())
		}
	}
}
