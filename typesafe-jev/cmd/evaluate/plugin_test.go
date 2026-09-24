package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"testing"
)

// repoRoot returns the repository root from the package directory.
func repoRoot(t *testing.T) string {
	t.Helper()
	root, err := filepath.Abs(filepath.Join("..", ".."))
	if err != nil {
		t.Fatal(err)
	}
	return root
}

// pythonPath resolves python3 from PATH, the same way the plugin's MCP entries
// do, and skips the test where none exists, so these run on more than one
// layout.
func pythonPath(t *testing.T) string {
	t.Helper()
	python, err := exec.LookPath("python3")
	if err != nil {
		t.Skipf("no python3 on PATH: %v", err)
	}
	return python
}

// launcherPath is the shipped launcher, relative to the repository root.
const launcherPath = "plugin/scripts/evaluate_launch.py"

// pluginRoot is the payload directory. Paths inside a plugin manifest resolve
// against it, not against the repository, which is why it is separate from
// repoRoot: the two were the same until the payload moved out of the root so a
// client would stop caching the Go source and the eval suite.
func pluginRoot(t *testing.T) string {
	t.Helper()
	return filepath.Join(repoRoot(t), "plugin")
}

func readJSON(t *testing.T, path string) map[string]any {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("%s: %v", path, err)
	}
	var doc map[string]any
	if err := json.Unmarshal(b, &doc); err != nil {
		t.Fatalf("%s is not valid JSON: %v", path, err)
	}
	return doc
}

// Every manifest must parse and every path it points at must exist. A plugin
// that names a missing file fails at install time, in someone else's client,
// with an error that does not say which manifest was wrong.
func TestPluginManifestsResolve(t *testing.T) {
	root := repoRoot(t)

	for _, manifest := range []string{
		"plugin/.claude-plugin/plugin.json",
		"plugin/.codex-plugin/plugin.json",
		"plugin/mcp/claude.json",
		"plugin/.mcp.json",
	} {
		doc := readJSON(t, filepath.Join(root, manifest))
		if len(doc) == 0 {
			t.Errorf("%s is empty", manifest)
		}
	}

	for _, client := range []string{"plugin/.claude-plugin/plugin.json", "plugin/.codex-plugin/plugin.json"} {
		doc := readJSON(t, filepath.Join(root, client))

		skills, _ := doc["skills"].([]any)
		if len(skills) == 0 {
			t.Errorf("%s declares no skills", client)
		}
		for i, entry := range skills {
			// Checked, not asserted: a non-string entry should name the file
			// and index that is wrong, rather than panicking somewhere in the
			// middle of the run.
			path, ok := entry.(string)
			if !ok {
				t.Errorf("%s: skills[%d] is %T, want a string", client, i, entry)
				continue
			}
			dir := filepath.Join(pluginRoot(t), filepath.Clean(path))
			if info, err := os.Stat(dir); err != nil || !info.IsDir() {
				t.Errorf("%s: skills path %q does not resolve to a directory", client, path)
			}
		}

		servers, _ := doc["mcpServers"].(string)
		if servers == "" {
			t.Errorf("%s declares no mcpServers file", client)
			continue
		}
		if _, err := os.Stat(filepath.Join(pluginRoot(t), filepath.Clean(servers))); err != nil {
			t.Errorf("%s: mcpServers path %q does not exist", client, servers)
		}
	}

	// Both clients must agree on the plugin name and version, or an operator
	// ends up with two differently-versioned installs of the same thing.
	claude := readJSON(t, filepath.Join(root, "plugin/.claude-plugin/plugin.json"))
	codex := readJSON(t, filepath.Join(root, "plugin/.codex-plugin/plugin.json"))
	for _, key := range []string{"name", "version", "repository"} {
		if claude[key] != codex[key] {
			t.Errorf("%s differs: claude=%v codex=%v", key, claude[key], codex[key])
		}
	}
}

// The MCP entries must launch the shipped launcher, name the backend
// explicitly, and carry no credential. A key in a committed manifest is a key
// in everyone's checkout.
func TestPluginMCPEntries(t *testing.T) {
	root := repoRoot(t)

	for _, tc := range []struct{ file, wantScript string }{
		{"plugin/mcp/claude.json", "${CLAUDE_PLUGIN_ROOT}/scripts/evaluate_launch.py"},
		{"plugin/.mcp.json", "scripts/evaluate_launch.py"},
	} {
		doc := readJSON(t, filepath.Join(root, tc.file))
		servers, _ := doc["mcpServers"].(map[string]any)
		if len(servers) != 1 {
			t.Errorf("%s: want exactly one server, got %d", tc.file, len(servers))
			continue
		}
		entry, _ := servers["jev"].(map[string]any)
		if entry == nil {
			t.Errorf("%s: no server named jev", tc.file)
			continue
		}
		if got, _ := entry["command"].(string); got != "python3" {
			t.Errorf("%s: command = %q, want %q", tc.file, got, "python3")
		}
		if args, _ := entry["args"].([]any); len(args) != 1 || args[0] != tc.wantScript {
			t.Errorf("%s: args = %v, want [%q]", tc.file, entry["args"], tc.wantScript)
		}

		env, _ := entry["env"].(map[string]any)
		// TypeSafe first, with OpenRouter as the operator's explicit fallback,
		// each with its own model id: the ids differ per backend.
		for key, want := range map[string]string{
			"JEV_PROVIDER":          "typesafe",
			"JEV_MODEL":             "jev-latest",
			"JEV_FALLBACK_PROVIDER": "openrouter",
		} {
			if got, _ := env[key].(string); got != want {
				t.Errorf("%s: %s = %q, want %q", tc.file, key, got, want)
			}
		}
		// The binary's own default stays typesafe; the plugin opts in rather
		// than the server guessing from which keys are set.
		if providers["typesafe"].Name != "typesafe" {
			t.Fatal("provider table changed")
		}
		for key := range env {
			if strings.Contains(key, "API_KEY") && !strings.HasSuffix(key, "_FILE") {
				t.Errorf("%s: env carries a credential variable %q", tc.file, key)
			}
		}
		raw, err := os.ReadFile(filepath.Join(root, tc.file))
		if err != nil {
			t.Fatal(err)
		}
		for _, secretish := range []string{"sk-", "sk-or-", "Bearer "} {
			if strings.Contains(string(raw), secretish) {
				t.Errorf("%s looks like it contains a credential", tc.file)
			}
		}
	}
}

// The vendored skill must keep its upstream licence and provenance, and must
// carry the two Racecraft additions that make it agree with this server.
func TestVendoredSkillKeepsProvenance(t *testing.T) {
	root := filepath.Join(repoRoot(t), "plugin", "shared-skills", "typesafe-ai")

	license, err := os.ReadFile(filepath.Join(root, "LICENSE"))
	if err != nil {
		t.Fatalf("vendored skill has no LICENSE: %v", err)
	}
	if !strings.Contains(string(license), "TypeSafe AI") {
		t.Error("LICENSE does not credit TypeSafe AI")
	}

	b, err := os.ReadFile(filepath.Join(root, "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	skill := string(b)

	for _, want := range []string{
		"typesafe-ai/skills",    // where it came from
		"version 0.5.7",         // which version
		"Make the judgment now", // the addition that routes to the tool
		"`evaluate`",            // names the tool
		// The backend note. It used to warn that OpenRouter took only
		// strings; that backend now accepts the structured form, so what
		// is left to say is which fields its answers may omit.
		"`openrouter` backend",
		"confidence",
		"Install this plugin", // the collision warning
	} {
		if !strings.Contains(skill, want) {
			t.Errorf("vendored SKILL.md is missing %q", want)
		}
	}

	// Upstream's own guidance must survive the adaptation.
	for _, want := range []string{
		"System One",
		"docs.typesafe.ai/llms.txt",
		"no separate confidence",
	} {
		if !strings.Contains(skill, want) {
			t.Errorf("vendored SKILL.md lost upstream guidance %q", want)
		}
	}
}

// The launcher is the plugin's only moving part, so its two paths are checked
// against a fake binary rather than a real install.
func TestLauncherResolvesTheBinary(t *testing.T) {
	launcher := filepath.Join(repoRoot(t), filepath.FromSlash(launcherPath))
	if info, err := os.Stat(launcher); err != nil || !info.Mode().IsRegular() {
		t.Fatalf("launcher missing: %v", err)
	}

	t.Run("missing binary reports on stderr and fails", func(t *testing.T) {
		cmd := exec.Command(pythonPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+filepath.Join(t.TempDir(), "absent"))
		var stdout, stderr strings.Builder
		cmd.Stdout, cmd.Stderr = &stdout, &stderr

		err := cmd.Run()
		if err == nil {
			t.Fatal("want a non-zero exit when the binary is missing")
		}
		// Stdout carries the MCP protocol. A human-readable line there is a
		// frame the client cannot parse.
		if stdout.String() != "" {
			t.Errorf("launcher wrote to stdout: %q", stdout.String())
		}
		if !strings.Contains(stderr.String(), "go build") {
			t.Errorf("stderr should say how to install: %q", stderr.String())
		}
	})

	t.Run("present binary is exec'd with the key-file default", func(t *testing.T) {
		dir := t.TempDir()
		fake := filepath.Join(dir, "evaluate")
		script := "#!/bin/sh\necho \"args=$*\"\necho \"keyfile=$JEV_API_KEY_FILE\"\n"
		if err := os.WriteFile(fake, []byte(script), 0o755); err != nil {
			t.Fatal(err)
		}

		cmd := exec.Command(pythonPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+fake, "HOME="+dir)
		out, err := cmd.Output()
		if err != nil {
			t.Fatalf("%v", err)
		}
		got := string(out)
		if !strings.Contains(got, "args=mcp") {
			t.Errorf("launcher did not pass `mcp`: %q", got)
		}
		if !strings.Contains(got, filepath.Join(dir, ".config", "racecraft-jev", "typesafe.key")) {
			t.Errorf("key-file default not applied: %q", got)
		}
	})

	t.Run("each backend gets its own key-file default, and a fallback gets one only when configured", func(t *testing.T) {
		dir := t.TempDir()
		fake := filepath.Join(dir, "evaluate")
		script := "#!/bin/sh\necho \"keyfile=$JEV_API_KEY_FILE\"\necho \"fallbackfile=${JEV_FALLBACK_API_KEY_FILE:-none}\"\n"
		if err := os.WriteFile(fake, []byte(script), 0o755); err != nil {
			t.Fatal(err)
		}
		keys := filepath.Join(dir, ".config", "racecraft-jev")
		for _, tc := range []struct {
			env           []string
			key, fallback string
		}{
			{nil, filepath.Join(keys, "typesafe.key"), "none"},
			{[]string{"JEV_PROVIDER=openrouter"}, filepath.Join(keys, "openrouter.key"), "none"},
			{[]string{"JEV_PROVIDER=typesafe", "JEV_FALLBACK_PROVIDER=openrouter"}, filepath.Join(keys, "typesafe.key"), filepath.Join(keys, "openrouter.key")},
			{[]string{"JEV_FALLBACK_PROVIDER=openrouter", "JEV_FALLBACK_API_KEY_FILE=/else/or.key"}, filepath.Join(keys, "typesafe.key"), "/else/or.key"},
		} {
			cmd := exec.Command(pythonPath(t), launcher)
			cmd.Env = append(append(os.Environ(), "EVALUATE_BIN="+fake, "HOME="+dir), tc.env...)
			out, err := cmd.Output()
			if err != nil {
				t.Fatal(err)
			}
			if !strings.Contains(string(out), "keyfile="+tc.key+"\n") || !strings.Contains(string(out), "fallbackfile="+tc.fallback+"\n") {
				t.Errorf("%v: got %q, want key %s and fallback %s", tc.env, out, tc.key, tc.fallback)
			}
		}
	})

	t.Run("an explicit key file is not overridden", func(t *testing.T) {
		dir := t.TempDir()
		fake := filepath.Join(dir, "evaluate")
		if err := os.WriteFile(fake, []byte("#!/bin/sh\necho \"keyfile=$JEV_API_KEY_FILE\"\n"), 0o755); err != nil {
			t.Fatal(err)
		}
		cmd := exec.Command(pythonPath(t), launcher)
		cmd.Env = append(os.Environ(), "EVALUATE_BIN="+fake, "HOME="+dir,
			"JEV_API_KEY_FILE=/somewhere/else.key")
		out, err := cmd.Output()
		if err != nil {
			t.Fatal(err)
		}
		if !strings.Contains(string(out), "keyfile=/somewhere/else.key") {
			t.Errorf("launcher overrode an explicit key file: %q", out)
		}
	})
}

// skillFrontmatter returns a skill's YAML frontmatter as raw lines.
func skillFrontmatter(t *testing.T, path string) map[string]string {
	t.Helper()
	b, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("%s: %v", path, err)
	}
	body := string(b)
	if !strings.HasPrefix(body, "---\n") {
		t.Fatalf("%s does not open with YAML frontmatter", path)
	}
	end := strings.Index(body[4:], "\n---\n")
	if end < 0 {
		t.Fatalf("%s has no closing frontmatter delimiter", path)
	}
	// A minimal reader rather than a YAML dependency: these files hold scalars
	// and one folded block, and the fields under test are known.
	fields := map[string]string{}
	key := ""
	for i, line := range strings.Split(body[4:4+end], "\n") {
		if strings.HasPrefix(line, " ") || strings.HasPrefix(line, "\t") {
			// A continuation before any key means the frontmatter is
			// malformed. Folding it into fields[""] would accept the file and
			// then fail somewhere less obvious, such as a description that
			// measures zero characters.
			if key == "" {
				t.Fatalf("%s: line %d is indented but continues no key: %q", path, i+2, line)
			}
			if fields[key] != "" {
				fields[key] += " "
			}
			fields[key] += strings.TrimSpace(line)
			continue
		}
		name, value, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		key = strings.TrimSpace(name)
		fields[key] = strings.TrimSpace(strings.TrimSuffix(strings.TrimSpace(value), ">"))
	}
	return fields
}

// Every shipped skill meets the published requirements for a skill folder:
// a kebab-case name matching the directory, a description that says what it
// does and when to use it within the length limit, and no angle brackets,
// which are refused because frontmatter reaches the system prompt.
//
// A skill that violates these does not fail loudly. It silently never loads,
// which is indistinguishable from the model choosing not to use the tool.
func TestSkillsMeetTheAuthoringRules(t *testing.T) {
	root := filepath.Join(pluginRoot(t), "shared-skills")
	entries, err := os.ReadDir(root)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) == 0 {
		t.Fatal("no skills are shipped")
	}

	kebab := regexp.MustCompile(`^[a-z0-9]+(-[a-z0-9]+)*$`)
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		t.Run(entry.Name(), func(t *testing.T) {
			dir := filepath.Join(root, entry.Name())
			// Exactly SKILL.md: the loader is case-sensitive and a variant
			// spelling is simply not found.
			path := filepath.Join(dir, "SKILL.md")
			if _, err := os.Stat(path); err != nil {
				t.Fatalf("no SKILL.md: %v", err)
			}
			if _, err := os.Stat(filepath.Join(dir, "README.md")); err == nil {
				t.Error("a skill folder must not contain README.md")
			}

			fields := skillFrontmatter(t, path)
			name := fields["name"]
			if !kebab.MatchString(name) {
				t.Errorf("name %q is not kebab-case", name)
			}
			if name != entry.Name() {
				t.Errorf("name %q does not match the directory %q", name, entry.Name())
			}
			if strings.HasPrefix(name, "claude") || strings.HasPrefix(name, "anthropic") {
				t.Errorf("name %q uses a reserved prefix", name)
			}

			desc := fields["description"]
			if desc == "" {
				t.Fatal("no description")
			}
			if len(desc) > 1024 {
				t.Errorf("description is %d characters, over the 1024 limit", len(desc))
			}
			if strings.ContainsAny(desc, "<>") {
				t.Error("description contains an angle bracket, which is refused in frontmatter")
			}
			// "When to use it" is what decides whether the skill ever loads.
			if !strings.Contains(strings.ToLower(desc), "use ") {
				t.Error("description does not say when to use the skill")
			}
		})
	}
}

// The judgment skill is the one that has to fire without being asked, so it
// carries the two things a description needs beyond the shared rules: the
// moments that should trigger it, and the negative triggers that keep it from
// firing on everything else.
func TestJudgmentSkillNamesItsTriggers(t *testing.T) {
	path := filepath.Join(repoRoot(t), "plugin", "shared-skills", "typed-judgments", "SKILL.md")
	fields := skillFrontmatter(t, path)
	desc := strings.ToLower(fields["description"])

	for _, trigger := range []string{"merge", "sever", "flaky", "constraint", "classif"} {
		if !strings.Contains(desc, trigger) {
			t.Errorf("description names no %q moment; it will under-trigger", trigger)
		}
	}
	if !strings.Contains(desc, "do not use") {
		t.Error("description has no negative trigger; it will over-trigger")
	}
	if !strings.Contains(desc, "evaluate") {
		t.Error("description does not name the tool it routes to")
	}

	body, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	// The three rules that decide whether an answer is worth having. Each was
	// established against the live backend, not inferred.
	for _, rule := range []string{
		"no-match",       // a choice without one hides a bad fit
		"0.5",            // uncertain, not medium intensity
		"parallel",       // batched questions cannot see each other
		"probability-we", // score is weighted, not an index
	} {
		if !strings.Contains(string(body), rule) {
			t.Errorf("SKILL.md omits the %q rule", rule)
		}
	}
}

// The skills install without the plugin, through skills.sh, which carries
// skill files and no MCP server. That path is real (upstream distributes the
// same way and it resolves this repository's plugin/shared-skills/ directory), so the
// README has to name it, and the judgment skill has to say what to do when the
// tool it routes to does not exist. A skill that keeps recommending a tool
// nobody has is worse than one that admits it.
func TestSkillsSurviveInstallWithoutTheServer(t *testing.T) {
	root := repoRoot(t)

	readme, err := os.ReadFile(filepath.Join(root, "README.md"))
	if err != nil {
		t.Fatal(err)
	}
	for _, want := range []string{
		"skills add racecraft-lab/typesafe-mcp", // the command
		"no MCP server",                         // and its one real limitation
	} {
		if !strings.Contains(string(readme), want) {
			t.Errorf("README does not document %q", want)
		}
	}

	skill, err := os.ReadFile(filepath.Join(root, "plugin", "shared-skills", "typed-judgments", "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	for _, want := range []string{
		"No `evaluate` tool exists at all", // the case is named
		"skills add",                       // and attributed to the right cause
		"make the judgment yourself",       // with an instruction that works
	} {
		if !strings.Contains(string(skill), want) {
			t.Errorf("typed-judgments does not handle the no-server install: missing %q", want)
		}
	}

	// Both skills name the tool, so both have to survive its absence. The
	// vendored one said "this plugin ships an MCP server" and "call evaluate"
	// with no condition, which under skills add routes an agent to a tool that
	// is not there. Only the Racecraft-added section may change, which is
	// where the condition belongs.
	vendored, err := os.ReadFile(filepath.Join(root, "plugin", "shared-skills", "typesafe-ai", "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	for _, want := range []string{
		"skills add",          // the install that has no server
		"when it is there",    // the call is conditional
		"no such tool exists", // and the absent case is handled
		"in the ordinary way", // with an instruction that works
	} {
		if !strings.Contains(string(vendored), want) {
			t.Errorf("typesafe-ai routes to evaluate unconditionally: missing %q", want)
		}
	}
	// The unconditional instruction must be gone, not merely qualified later.
	if strings.Contains(string(vendored), "**Call `evaluate`.**") {
		t.Error("typesafe-ai still says to call evaluate unconditionally")
	}
}

// The skill's own metadata states a version, so it has to move with the
// plugin's. The x-release-please-version annotation beside the value is how a
// release reaches a Markdown file.
func TestSkillVersionMatchesThePlugin(t *testing.T) {
	root := repoRoot(t)
	const skillPath = "plugin/shared-skills/typed-judgments/SKILL.md"

	b, err := os.ReadFile(filepath.Join(root, skillPath))
	if err != nil {
		t.Fatal(err)
	}
	version, _ := readJSON(t, filepath.Join(root, "plugin/.claude-plugin/plugin.json"))["version"].(string)
	if version == "" {
		t.Fatal("the plugin manifest states no version")
	}
	want := "version: " + version + " # x-release-please-version"
	if !strings.Contains(string(b), want) {
		t.Errorf("SKILL.md metadata does not carry %q", want)
	}
}

// Upstream's skill carries no bundled scripts or references; it routes the
// agent to live documentation, which is what keeps it current as the model
// changes. The judgment skill has to do the same for the pages that bear on
// designing a question, or an agent using the tool has only what fits in one
// file. Every link is checked for the .md suffix Mintlify needs, because a
// link to the extensionless page returns HTML an agent cannot read well.
func TestJudgmentSkillRoutesToLiveDocs(t *testing.T) {
	b, err := os.ReadFile(filepath.Join(pluginRoot(t), "shared-skills", "typed-judgments", "SKILL.md"))
	if err != nil {
		t.Fatal(err)
	}
	skill := string(b)

	// The pages that matter for asking a question, as opposed to writing an
	// integration, which is the other skill's job.
	for _, page := range []string{
		"https://docs.typesafe.ai/llms.txt",
		"https://docs.typesafe.ai/primitives.md",
		"https://docs.typesafe.ai/primitives/choice.md",
		"https://docs.typesafe.ai/primitives/score.md",
		"https://docs.typesafe.ai/primitives/noul.md",
		"https://docs.typesafe.ai/concepts/state.md",
		"https://docs.typesafe.ai/confidence.md",
	} {
		if !strings.Contains(skill, page) {
			t.Errorf("SKILL.md does not route to %s", page)
		}
	}

	// Every docs link except the index must end in .md, or Mintlify serves the
	// HTML page instead of the Markdown one.
	links := regexp.MustCompile(`https://docs\.typesafe\.ai/[^\s)\]]+`).FindAllString(skill, -1)
	if len(links) < 7 {
		t.Fatalf("found only %d docs links", len(links))
	}
	for _, l := range links {
		if l == "https://docs.typesafe.ai/llms.txt" {
			continue
		}
		if !strings.HasSuffix(l, ".md") {
			t.Errorf("docs link %q does not end in .md, so it serves HTML", l)
		}
	}

	// And the failure mode is named, so an agent without network access says
	// so rather than inventing a version-dependent detail.
	if !strings.Contains(skill, "If the docs cannot be fetched") {
		t.Error("SKILL.md does not say what to do when the docs are unreachable")
	}
}
