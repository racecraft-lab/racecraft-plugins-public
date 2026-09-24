#!/usr/bin/env python3
"""Behavior tests for the shipped workflow guard hook.

Drives the script with the documented PreToolUse and Stop payloads against
scratch git repositories, so every deny and block path is exercised
without a live Claude Code or Codex session.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SHARED_LIB = REPO_ROOT / "tests" / "speckit-pro" / "lib"
PLUGIN_ROOT = REPO_ROOT / "speckit-pro"
for _root in (SHARED_LIB, PLUGIN_ROOT):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from speckit_pro_runner.gates import active_path_guard  # noqa: E402
from test_result import run_counted  # noqa: E402

HOOK = REPO_ROOT / "speckit-pro" / "scripts" / "workflow-guard-hook.py"
VERSION = "workflow-guard-v1"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": "/nonexistent",
       "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "support@openai.com",
       "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "support@openai.com",
       "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1"}


def run_hook(mode: str, data: dict, version: str = VERSION) -> tuple[int, dict, str]:
    result = subprocess.run(
        [sys.executable, str(HOOK), mode, version], input=json.dumps(data),
        capture_output=True, text=True, env=ENV, check=False,
    )
    out = json.loads(result.stdout) if result.stdout.strip() else {}
    return result.returncode, out, result.stderr


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True, env=ENV, check=True).stdout


def shell(cwd: Path, command: str) -> dict:
    return {"hook_event_name": "PreToolUse", "tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(cwd)}


class WorkflowGuardHookTests(unittest.TestCase):
    def test_lockfile_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            git(root, "init", "-q")
            (root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
            with self.subTest(msg="npm under a pnpm lockfile is denied with the documented shape"):
                code, out, _ = run_hook("lockfile", shell(root, "npm install left-pad"))
                self.assertEqual(0, code)
                self.assertEqual("deny", out["hookSpecificOutput"]["permissionDecision"])
                self.assertEqual("PreToolUse", out["hookSpecificOutput"]["hookEventName"])
                self.assertIn("pnpm", out["hookSpecificOutput"]["permissionDecisionReason"])
            with self.subTest(msg="npx is npm"):
                self.assertEqual("deny", run_hook("lockfile", shell(root, "npx vitest run"))[1]["hookSpecificOutput"]["permissionDecision"])
            with self.subTest(msg="the lockfile's own manager passes"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "pnpm install && pnpm test"))[1])
            with self.subTest(msg="a subdirectory inherits the repository lockfile"):
                (root / "packages" / "a").mkdir(parents=True)
                self.assertEqual("deny", run_hook("lockfile", shell(root / "packages" / "a", "yarn add x"))[1]["hookSpecificOutput"]["permissionDecision"])
            with self.subTest(msg="commands without a package manager are not a decision"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "git status && ls node_modules/.bin/npm-run-all"))[1])
            with self.subTest(msg="a path segment containing a manager name is not an invocation"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "cat docs/npm-notes.md"))[1])
            for command in ('echo "npm"', "grep npm README.md", "rg 'npm:' pnpm-lock.yaml", "git log --grep yarn"):
                with self.subTest(msg=f"a manager name as an argument is not an invocation: {command}"):
                    self.assertEqual({}, run_hook("lockfile", shell(root, command))[1])
            for command in ("CI=1 npm test", "sudo npm install -g x", "ls && npm ci", "echo $(npm bin)", "./node_modules/.bin/npm run x"):
                with self.subTest(msg=f"a manager in executable position is an invocation: {command}"):
                    self.assertEqual("deny", run_hook("lockfile", shell(root, command))[1]["hookSpecificOutput"]["permissionDecision"])
            for command in ('grep -rn "a\\|yarn build\\|b" src', "grep -E 'npm run|yarn build' notes.md", 'echo "ok && npm install"'):
                with self.subTest(msg=f"an operator inside quotes does not start a segment: {command}"):
                    self.assertEqual({}, run_hook("lockfile", shell(root, command))[1])
            with self.subTest(msg="command substitution inside double quotes is still an invocation"):
                self.assertEqual("deny", run_hook("lockfile", shell(root, 'echo "$(npm bin)"'))[1]["hookSpecificOutput"]["permissionDecision"])
            heredoc_data = {
                "a quoted heredoc body is data": "cat > notes.md <<'EOF'\n- [ ] `npm install` first\nnpm test\nEOF",
                "a double-quoted delimiter": 'cat > notes.md <<"EOF"\n`npm install`\nEOF',
                "a backslash-quoted delimiter": "cat > notes.md <<\\EOF\n`npm install`\nEOF",
                "an unquoted heredoc line is data, not a command": "cat > notes.md <<EOF\nnpm install left-pad\nEOF",
                "a tab-stripped heredoc ends at its indented delimiter": "cat <<-'EOF' > notes.md\n\t`npm ci`\n\tEOF\npnpm test",
            }
            for label, command in heredoc_data.items():
                with self.subTest(msg=label):
                    self.assertEqual({}, run_hook("lockfile", shell(root, command))[1])
            heredoc_runs = {
                "substitution in an unquoted heredoc body runs": "cat > notes.md <<EOF\nbin: $(npm bin)\nEOF",
                "a backtick in an unquoted heredoc body runs": "cat > notes.md <<EOF\n`npm bin`\nEOF",
                "a command after the delimiter runs": "cat > notes.md <<'EOF'\ntext\nEOF\nnpm install",
            }
            for label, command in heredoc_runs.items():
                with self.subTest(msg=label):
                    self.assertEqual("deny", run_hook("lockfile", shell(root, command))[1]["hookSpecificOutput"]["permissionDecision"])
            with self.subTest(msg="tools without a command string are ignored"):
                self.assertEqual({}, run_hook("lockfile", {"hook_event_name": "PreToolUse", "tool_name": "Edit", "tool_input": {"file_path": "npm.md"}, "cwd": str(root)})[1])
            (root / "yarn.lock").write_text("", encoding="utf-8")
            with self.subTest(msg="two lockfile kinds are ambiguous, so no decision"):
                self.assertEqual({}, run_hook("lockfile", shell(root, "npm install"))[1])
        with tempfile.TemporaryDirectory() as tmp:
            # A Bun session whose command targets a sibling pnpm project.
            base = Path(tmp).resolve()
            bun_repo = base / "bun-repo"
            pnpm_repo = base / "pnpm-repo"
            for repo, lockfile in ((bun_repo, "bun.lock"), (pnpm_repo, "pnpm-lock.yaml")):
                (repo / ".git").mkdir(parents=True)
                (repo / lockfile).write_text("", encoding="utf-8")
            (pnpm_repo / "docs-site").mkdir()
            (bun_repo / "sub").mkdir()
            allowed = {
                "a leading cd moves the lookup to the target project": f"cd {pnpm_repo} && pnpm install",
                "a relative cd resolves from the session directory": "cd ../pnpm-repo && pnpm test",
                "pnpm --dir reads the target directory's lockfile": f"pnpm --dir {pnpm_repo}/docs-site install --frozen-lockfile",
                "pnpm --dir= form": f"pnpm --dir={pnpm_repo}/docs-site install",
                "pnpm -C form": f"pnpm -C {pnpm_repo} test",
                "npm --prefix into a directory without a lockfile is not a decision": f"npm audit --prefix {base} --audit-level=high",
                "a quoted cd path": f'cd "{pnpm_repo}" && pnpm test',
            }
            for label, command in allowed.items():
                with self.subTest(msg=label):
                    self.assertEqual({}, run_hook("lockfile", shell(bun_repo, command))[1])
            denied = {
                "npm at a Bun root is still denied": "npm install",
                "a directory flag pointing at a Bun project is denied": f"pnpm --dir {bun_repo}/sub install",
                "cd into a Bun subdirectory keeps the Bun lockfile": "cd sub && npm install",
                "a flag of another manager does not move the lookup": f"npm --dir {pnpm_repo} install",
                "cd with extra arguments falls back to the session directory": f"cd {pnpm_repo} extra && pnpm install",
            }
            for label, command in denied.items():
                with self.subTest(msg=label):
                    self.assertEqual("deny", run_hook("lockfile", shell(bun_repo, command))[1]["hookSpecificOutput"]["permissionDecision"])
        with tempfile.TemporaryDirectory() as tmp:
            with self.subTest(msg="no lockfile means no decision"):
                self.assertEqual({}, run_hook("lockfile", shell(Path(tmp), "npm install"))[1])
        with self.subTest(msg="malformed input fails open with a stderr note"):
            result = subprocess.run([sys.executable, str(HOOK), "lockfile", VERSION], input="[1,2", capture_output=True, text=True, env=ENV, check=False)
            self.assertEqual((0, ""), (result.returncode, result.stdout))
            self.assertIn("no decision", result.stderr)
        with self.subTest(msg="version mismatch exits 2"):
            self.assertEqual(2, run_hook("lockfile", {}, version="workflow-guard-v0")[0])
        with self.subTest(msg="an interpreter below 3.11 fails open with one warning, even on a deny-worthy payload"):
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                (root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
                shim = (
                    "import sys, runpy; sys.version_info = (3, 10, 0, 'final', 0); "
                    f"sys.argv = [{str(HOOK)!r}, 'lockfile', {VERSION!r}]; runpy.run_path({str(HOOK)!r}, run_name='__main__')"
                )
                result = subprocess.run([sys.executable, "-c", shim], input=json.dumps(shell(root, "npm install")),
                                        capture_output=True, text=True, env=ENV, check=False)
                self.assertEqual((0, ""), (result.returncode, result.stdout))
                self.assertIn("fail-open", result.stderr)
                self.assertEqual(1, result.stderr.count("\n"))

    def test_unpushed_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp).resolve()
            remote = base / "remote.git"
            git(base, "init", "-q", "--bare", str(remote))
            root = base / "work"
            root.mkdir()
            git(root, "init", "-q", "-b", "main")
            (root / "README.md").write_text("x\n", encoding="utf-8")
            git(root, "add", "README.md")
            git(root, "commit", "-q", "-m", "init")
            stop = {"hook_event_name": "Stop", "stop_hook_active": False, "cwd": str(root)}
            state = root / "docs" / "ai" / "specs" / ".process" / "autopilot-state.json"
            state.parent.mkdir(parents=True)
            with self.subTest(msg="no autopilot state means no decision even with unpushed commits"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            state.write_text(json.dumps({"status": "in_progress"}), encoding="utf-8")
            with self.subTest(msg="active state with no upstream blocks and names the commit count"):
                out = run_hook("unpushed", stop)[1]
                self.assertEqual("block", out["decision"])
                self.assertIn("1 commit", out["reason"])
            git(root, "remote", "add", "origin", str(remote))
            git(root, "push", "-q", "-u", "origin", "main")
            with self.subTest(msg="pushed branch passes"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            (root / "a.txt").write_text("a\n", encoding="utf-8")
            git(root, "add", "a.txt")
            git(root, "commit", "-q", "-m", "more")
            with self.subTest(msg="a commit ahead of upstream blocks"):
                self.assertEqual("block", run_hook("unpushed", stop)[1]["decision"])
            with self.subTest(msg="stop_hook_active yields so a blocked turn cannot loop"):
                self.assertEqual({}, run_hook("unpushed", {**stop, "stop_hook_active": True})[1])
            state.write_text(json.dumps({"status": "completed_pr_open"}), encoding="utf-8")
            with self.subTest(msg="a finished state is not active"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])
            state.write_text("{not json", encoding="utf-8")
            with self.subTest(msg="an unreadable state fails open"):
                self.assertEqual({}, run_hook("unpushed", stop)[1])


class HookMatcherExemptionTests(unittest.TestCase):
    """The installed-runtime guard exempts exactly the matcher field of the two hook manifests."""

    def test_matcher_exemption_is_narrow(self) -> None:
        shell = "B" + "ash"  # the shell tool's name, kept out of this file's own scan surface
        cases = {
            "hooks.json matcher line is exempt": ("speckit-pro/hooks/hooks.json", f'        "matcher": "{shell}",', True),
            "codex-hooks.json matcher line is exempt": ("speckit-pro/codex-hooks.json", f'  "matcher": "{shell}"', True),
            "a command field in hooks.json is not exempt": ("speckit-pro/hooks/hooks.json", f'        "command": "{shell} -c true",', False),
            "a matcher-shaped line in a script is not exempt": ("speckit-pro/scripts/x.py", f'"matcher": "{shell}"', False),
            "a matcher-shaped line in prose is not exempt": ("speckit-pro/skills/a/SKILL.md", f'"matcher": "{shell}"', False),
        }
        for label, (path, line, exempt) in cases.items():
            with self.subTest(msg=label):
                self.assertIs(exempt, active_path_guard.is_hook_matcher_line(path, line))
        with self.subTest(msg="scan_installed_runtime_sources drops the matcher finding and keeps the command finding"):
            content = '{"hooks": {"PreToolUse": [{"matcher": "%s", "hooks": [{"type": "command", "command": "%s -c true"}]}]}}' % (shell, shell)
            pretty = content.replace('"matcher"', '\n"matcher"').replace(', "hooks"', ',\n"hooks"')
            source = active_path_guard.SourceFile(path="speckit-pro/hooks/hooks.json", content=pretty, source_kind="repo")
            findings = active_path_guard.scan_installed_runtime_sources([source], REPO_ROOT)
            lines = sorted(f.line for f in findings if f.category == "bash")
            self.assertEqual([3], lines, findings)


def build_suite() -> unittest.TestSuite:
    suite = unittest.TestSuite()
    for case in (WorkflowGuardHookTests, HookMatcherExemptionTests):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    return suite


def main() -> int:
    return run_counted(build_suite(), label="test-workflow-guard-hook")


if __name__ == "__main__":
    raise SystemExit(main())
