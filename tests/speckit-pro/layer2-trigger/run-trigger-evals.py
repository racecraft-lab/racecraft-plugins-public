#!/usr/bin/env python3
"""Run Claude Layer 2 trigger evals via skill-creator."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import shutil
import subprocess
import sys
import tempfile


SCRIPT_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = (SCRIPT_DIR / "../../../speckit-pro").resolve()
DEFAULT_MODEL = "sonnet"
RUNS_PER_QUERY = 3
TRIGGER_THRESHOLD = 0.5


def load_eval_corpus(path: Path) -> tuple[list[dict[str, object]] | None, str]:
    """Load and validate the complete corpus before any provider subprocess."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return None, f"could not read eval file: {exc}"
    if not isinstance(value, list):
        return None, "eval file must contain a JSON list"
    seen_queries: set[str] = set()
    for index, entry in enumerate(value, start=1):
        if not isinstance(entry, dict):
            return None, f"eval case {index} must be an object"
        query = entry.get("query")
        should_trigger = entry.get("should_trigger")
        if not isinstance(query, str) or not query.strip() or not isinstance(should_trigger, bool):
            return None, f"eval case {index} requires a non-empty query and boolean should_trigger"
        if query in seen_queries:
            return None, f"eval case {index} duplicates query {query!r}"
        seen_queries.add(query)
    return value, "valid eval corpus"


class TerminationRequested(Exception):
    """Raised by termination handlers so the restoration ``finally`` runs."""

    def __init__(self, signum: int) -> None:
        super().__init__(f"termination requested by signal {signum}")
        self.signum = signum


def handle_termination(signum: int, _frame: object) -> None:
    raise TerminationRequested(signum)


def install_termination_handlers() -> dict[int, object]:
    previous: dict[int, object] = {}
    for name in ("SIGHUP", "SIGTERM"):
        signum = getattr(signal, name, None)
        if not isinstance(signum, int):
            continue
        try:
            previous[signum] = signal.getsignal(signum)
            signal.signal(signum, handle_termination)
        except (OSError, ValueError):
            previous.pop(signum, None)
    return previous


def restore_termination_handlers(previous: dict[int, object]) -> None:
    for signum, handler in previous.items():
        try:
            signal.signal(signum, handler)
        except (OSError, ValueError):
            pass


def eprint(message: str = "") -> None:
    print(message, file=sys.stderr)


def available_evals(eval_dir: Path) -> list[str]:
    return [path.name.removesuffix("-trigger.json") for path in sorted(eval_dir.glob("*-trigger.json"))]


def detect_installed_marketplace(home: Path) -> str:
    settings_path = home / ".claude/settings.json"
    if not settings_path.is_file():
        return ""
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ""
    enabled = settings.get("enabledPlugins") or {}
    if not isinstance(enabled, dict):
        return ""
    for key, value in enabled.items():
        if isinstance(key, str) and key.startswith("speckit-pro@") and value is True:
            return key.removeprefix("speckit-pro@")
    return ""


def append_csv(base: str, item: str) -> str:
    return f"{base},{item}" if base else item


def write_settings_file(disable_plugins: str) -> Path:
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        prefix="eval-disable-plugins-",
        suffix=".json",
        delete=False,
    )
    with handle:
        disabled = {plugin.strip(): False for plugin in disable_plugins.split(",") if plugin.strip()}
        handle.write(json.dumps({"enabledPlugins": disabled}))
        handle.write("\n")
    return Path(handle.name)


def find_executable_excluding(name: str, excluded_dir: Path, env: dict[str, str]) -> str:
    path_entries = [
        entry
        for entry in env.get("PATH", os.defpath).split(os.pathsep)
        if entry and Path(entry).resolve() != excluded_dir.resolve()
    ]
    return shutil.which(name, path=os.pathsep.join(path_entries)) or ""


def write_claude_wrapper(wrapper_dir: Path, settings_file: Path | None, bare: bool, env: dict[str, str]) -> None:
    real_claude = find_executable_excluding("claude", wrapper_dir, env)
    prefix_args: list[str] = []
    if settings_file is not None:
        prefix_args.extend(["--settings", str(settings_file)])
    suffix_args = ["--bare"] if bare else []

    wrapper_script = wrapper_dir / "claude-wrapper.py"
    wrapper_script.write_text(
        "\n".join(
            [
                "import subprocess",
                "import sys",
                f"real_claude = {real_claude!r}",
                f"prefix_args = {prefix_args!r}",
                f"suffix_args = {suffix_args!r}",
                "if not real_claude:",
                "    sys.stderr.write('ERROR: claude CLI not found on PATH.\\n')",
                "    raise SystemExit(127)",
                "completed = subprocess.run(",
                "    [real_claude, *prefix_args, *sys.argv[1:], *suffix_args],",
                "    shell=False,",
                ")",
                "raise SystemExit(completed.returncode)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    wrapper = wrapper_dir / "claude"
    wrapper.write_text(
        f"#!{sys.executable}\nimport runpy\nrunpy.run_path({str(wrapper_script)!r}, run_name='__main__')\n",
        encoding="utf-8",
    )
    wrapper.chmod(0o755)
    windows_command = subprocess.list2cmdline([sys.executable, str(wrapper_script)])
    (wrapper_dir / "claude.cmd").write_text(
        f"@echo off\r\n{windows_command} %*\r\nexit /b %ERRORLEVEL%\r\n",
        encoding="utf-8",
    )


def move_aside(path: Path, target: Path, success_message: str, warning_message: str) -> bool:
    if target.exists():
        eprint(warning_message)
        return False
    try:
        shutil.move(str(path), str(target))
    except OSError:
        eprint(warning_message)
        return False
    eprint(success_message)
    return True


def restore_moves(moves: list[tuple[Path, Path]]) -> list[tuple[Path, Path]]:
    failures: list[tuple[Path, Path]] = []
    for original, disabled in reversed(moves):
        if disabled.exists():
            if original.exists():
                eprint(f"ERROR: cannot restore {original}; backup preserved at {disabled}")
                failures.append((original, disabled))
                continue
            try:
                shutil.move(str(disabled), str(original))
            except OSError as exc:
                eprint(f"ERROR: could not restore {original}; backup preserved at {disabled}: {exc}")
                failures.append((original, disabled))
    return failures


def wrapper_mode_message(skill: str, settings_enabled: bool, bare_enabled: bool) -> str:
    if settings_enabled and bare_enabled:
        return f"Using Claude wrapper with --settings and --bare for '{skill}'"
    if settings_enabled:
        return f"Using Claude wrapper with --settings only for '{skill}'"
    if bare_enabled:
        return f"Using Claude wrapper with --bare only for '{skill}'"
    return f"Running Claude directly (no wrapper, no --settings, no --bare) for '{skill}'"


def validate_eval_result(
    output: str,
    expected_cases: list[dict[str, object]],
    runs_per_query: int,
    trigger_threshold: float,
) -> tuple[bool, str]:
    """Fail closed unless the upstream evaluator reports every expected trial passing."""
    try:
        report = json.loads(output)
    except json.JSONDecodeError as exc:
        return False, f"upstream evaluator did not emit valid JSON: {exc}"
    if not isinstance(report, dict) or not isinstance(report.get("summary"), dict):
        return False, "upstream evaluator result is missing summary"
    summary = report["summary"]
    results = report.get("results")
    if not isinstance(results, list):
        return False, "upstream evaluator result is missing per-case results"
    expected_total = len(expected_cases)
    expected_summary = {
        "total": expected_total,
        "passed": expected_total,
        "failed": 0,
    }
    if any(summary.get(key) != value for key, value in expected_summary.items()):
        return False, f"upstream evaluator summary did not pass all {expected_total} cases"
    if len(results) != expected_total:
        return False, f"upstream evaluator returned {len(results)} of {expected_total} case results"
    expected_roster = {str(entry["query"]): bool(entry["should_trigger"]) for entry in expected_cases}
    actual_roster: dict[str, bool] = {}
    for index, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            return False, f"upstream evaluator case {index} is not an object"
        if not isinstance(result.get("query"), str) or not isinstance(result.get("should_trigger"), bool):
            return False, f"upstream evaluator case {index} has an invalid query or polarity"
        query = str(result["query"])
        if query in actual_roster:
            return False, f"upstream evaluator duplicates query {query!r}"
        actual_roster[query] = bool(result["should_trigger"])
        triggers = result.get("triggers")
        trigger_rate = result.get("trigger_rate")
        if (
            result.get("runs") != runs_per_query
            or not isinstance(triggers, int)
            or isinstance(triggers, bool)
            or not 0 <= triggers <= runs_per_query
            or not isinstance(trigger_rate, (int, float))
            or isinstance(trigger_rate, bool)
        ):
            return False, f"upstream evaluator case {index} has invalid trial accounting"
        computed_rate = triggers / runs_per_query
        if abs(float(trigger_rate) - computed_rate) > 0.0005:
            return False, f"upstream evaluator case {index} has inconsistent trigger rate"
        expected_pass = (computed_rate >= trigger_threshold) == result.get("should_trigger")
        if result.get("pass") is not expected_pass or result.get("pass") is not True:
            return False, f"upstream evaluator case {index} has inconsistent or failed polarity"
    if actual_roster != expected_roster:
        return False, "upstream evaluator query/polarity roster does not exactly match the eval corpus"
    return True, "all cases and trials passed"


def retain_upstream_evidence(
    evidence_dir: Path,
    stdout: str,
    stderr: str,
    requested_model: str,
) -> dict[str, object]:
    """Retain exact upstream output; the upstream report is the direct trial evidence available here."""
    stdout_path = evidence_dir / "upstream-result.json"
    stderr_path = evidence_dir / "upstream-stderr.log"
    stdout_path.write_text(stdout, encoding="utf-8", newline="")
    stderr_path.write_text(stderr, encoding="utf-8", newline="")
    resolved_model: str | None = None
    try:
        report = json.loads(stdout)
        summary = report.get("summary") if isinstance(report, dict) else None
        candidate = summary.get("model") if isinstance(summary, dict) else None
        resolved_model = candidate if isinstance(candidate, str) and candidate else None
    except json.JSONDecodeError:
        pass
    evidence = {
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "stdout_path": str(stdout_path.resolve()),
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8")).hexdigest(),
        "stderr_path": str(stderr_path.resolve()),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8")).hexdigest(),
    }
    (evidence_dir / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    return evidence


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", nargs="?", default="speckit-coach")
    parser.add_argument("--model", default=os.environ.get("EVAL_MODEL", DEFAULT_MODEL))
    parser.add_argument("--evidence-dir", help="Directory for exact upstream stdout/stderr evidence")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    home = Path(os.environ.get("HOME", str(Path.home())))
    skill_creator = Path(
        os.environ.get(
            "SKILL_CREATOR_ROOT",
            str(home / ".claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator"),
        )
    )
    skill = args.skill

    eval_dir = PLUGIN_ROOT / "../tests/speckit-pro/layer2-trigger/evals"
    eval_file = eval_dir / f"{skill}-trigger.json"
    if (PLUGIN_ROOT / f"skills/{skill}").is_dir():
        skill_path = PLUGIN_ROOT / f"skills/{skill}"
    elif (PLUGIN_ROOT / f"codex-skills/{skill}").is_dir():
        skill_path = PLUGIN_ROOT / f"codex-skills/{skill}"
    else:
        skill_path = None

    if not eval_file.is_file():
        eprint(f"ERROR: Eval file not found: {eval_file}")
        eprint("Available evals:")
        for name in available_evals(eval_dir):
            eprint(name)
        return 1
    if skill_path is None or not skill_path.is_dir():
        eprint(f"ERROR: Skill not found for requested skill '{skill}'.")
        eprint("Searched locations:")
        eprint(f"  - {PLUGIN_ROOT / f'skills/{skill}'}")
        eprint(f"  - {PLUGIN_ROOT / f'codex-skills/{skill}'}")
        return 1
    if not skill_creator.is_dir():
        eprint(f"ERROR: skill-creator not found at: {skill_creator}")
        eprint("Set SKILL_CREATOR_ROOT to the skill-creator skill directory.")
        return 1
    eval_data, corpus_reason = load_eval_corpus(eval_file)
    if eval_data is None:
        eprint(f"ERROR: {corpus_reason}")
        return 1
    if args.evidence_dir:
        evidence_dir = Path(args.evidence_dir).resolve()
        try:
            evidence_dir.mkdir(parents=True, exist_ok=False)
        except OSError as exc:
            eprint(f"ERROR: could not create evidence directory {evidence_dir}: {exc}")
            return 1
    else:
        evidence_dir = Path(tempfile.mkdtemp(prefix=f"claude-eval-evidence-{skill}-"))

    previous_handlers = install_termination_handlers()

    installed_marketplace = detect_installed_marketplace(home)

    disable_default = ""
    if skill == "grill-me":
        disable_default = "superpowers@claude-plugins-official"
    if installed_marketplace:
        disable_default = append_csv(disable_default, f"speckit-pro@{installed_marketplace}")
    disable_plugins = os.environ.get("EVAL_DISABLE_PLUGINS") or disable_default
    need_bare = os.environ.get("EVAL_FORCE_BARE", "")

    wrapper_dir_ctx = tempfile.TemporaryDirectory()
    wrapper_dir = Path(wrapper_dir_ctx.name)
    settings_file: Path | None = None
    moved_paths: list[tuple[Path, Path]] = []
    local_disabled_dir: Path | None = None
    result = 0
    restore_failures: list[tuple[Path, Path]] = []
    termination_signal: int | None = None

    try:
        if installed_marketplace:
            production_skill_dir = (
                home / f".claude/plugins/marketplaces/{installed_marketplace}/speckit-pro/skills/{skill}"
            )
            if production_skill_dir.is_dir():
                disabled = production_skill_dir.with_name(f"{production_skill_dir.name}.eval-disabled-{os.getpid()}")
                if move_aside(
                    production_skill_dir,
                    disabled,
                    f"Renamed production skill out of the way: {production_skill_dir} \u2192 {disabled}",
                    f"WARNING: could not rename production skill at {production_skill_dir} \u2014 collision may suppress results",
                ):
                    moved_paths.append((production_skill_dir, disabled))

        local_competitors: list[str] = []
        if skill == "speckit-resolve-pr":
            local_competitors = ["pr-triple-review", "gitnexus-pr-review"]

        if local_competitors:
            local_disabled_dir = Path(tempfile.mkdtemp(prefix="eval-disabled-local-"))
            for competitor in local_competitors:
                competitor_dir = home / f".claude/skills/{competitor}"
                if competitor_dir.is_dir():
                    disabled = local_disabled_dir / competitor
                    if move_aside(
                        competitor_dir,
                        disabled,
                        f"Moved local competitor skill out of ~/.claude/skills/: {competitor_dir} \u2192 {disabled}",
                        f"WARNING: could not move local competitor at {competitor_dir}",
                    ):
                        moved_paths.append((competitor_dir, disabled))

        env = os.environ.copy()
        if disable_plugins:
            settings_file = write_settings_file(disable_plugins)
            eprint(f"Disabling competing plugins for eval: {disable_plugins}")

        if need_bare == "1" or settings_file is not None:
            bare = need_bare == "1"
            eprint(wrapper_mode_message(skill, settings_file is not None, bare))
            write_claude_wrapper(wrapper_dir, settings_file, bare, env)
            env["PATH"] = f"{wrapper_dir}{os.pathsep}{env.get('PATH', '')}"
        else:
            eprint(wrapper_mode_message(skill, False, False))

        eprint(f"Running trigger evals for: {skill}")
        eprint(f"Eval file: {eval_file}")
        eprint(f"Skill path: {skill_path}")
        eprint(f"Model: {args.model}")
        eprint()

        cmd = [
            sys.executable,
            "-m",
            "scripts.run_eval",
            "--eval-set",
            str(eval_file),
            "--skill-path",
            str(skill_path),
            "--runs-per-query",
            str(RUNS_PER_QUERY),
            "--trigger-threshold",
            str(TRIGGER_THRESHOLD),
            "--model",
            args.model,
            "--verbose",
        ]
        if disable_plugins:
            eprint("Forcing --num-workers 1 (parallelism + --settings is racy)")
            cmd.extend(["--num-workers", "1"])

        completed = subprocess.run(
            cmd,
            cwd=skill_creator,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=False,
        )
        evidence = retain_upstream_evidence(evidence_dir, completed.stdout, completed.stderr, args.model)
        eprint(f"Evidence: {evidence_dir}")
        eprint(
            "Requested model: "
            f"{evidence['requested_model']}; resolved model: {evidence['resolved_model'] or 'unknown'}"
        )
        sys.stdout.write(completed.stdout)
        sys.stderr.write(completed.stderr)
        if completed.returncode != 0:
            result = completed.returncode
        else:
            valid, reason = validate_eval_result(
                completed.stdout,
                expected_cases=eval_data,
                runs_per_query=RUNS_PER_QUERY,
                trigger_threshold=TRIGGER_THRESHOLD,
            )
            if not valid:
                eprint(f"ERROR: {reason}")
                result = 1
            else:
                result = 0
    except TerminationRequested as exc:
        termination_signal = exc.signum
        eprint(f"Termination requested by signal {exc.signum}; restoring moved paths before exit.")
    finally:
        restore_failures = restore_moves(moved_paths)
        if local_disabled_dir is not None:
            preserved_local = [disabled for _original, disabled in restore_failures if local_disabled_dir in disabled.parents]
            if preserved_local:
                eprint(f"ERROR: local skill backups preserved under {local_disabled_dir}")
            else:
                try:
                    shutil.rmtree(local_disabled_dir)
                except OSError as exc:
                    eprint(f"ERROR: could not remove temporary local-skill directory: {exc}")
                    result = 2
                if local_disabled_dir.exists():
                    eprint(f"ERROR: temporary local-skill directory residue remains at {local_disabled_dir}")
                    result = 2
        if settings_file is not None:
            try:
                settings_file.unlink()
            except OSError as exc:
                eprint(f"ERROR: could not remove temporary settings file {settings_file}: {exc}")
                result = 2
        try:
            wrapper_dir_ctx.cleanup()
        except OSError as exc:
            eprint(f"ERROR: could not remove temporary wrapper directory {wrapper_dir}: {exc}")
            result = 2
        if wrapper_dir.exists():
            eprint(f"ERROR: temporary wrapper directory residue remains at {wrapper_dir}")
            result = 2
        restore_termination_handlers(previous_handlers)

    if termination_signal is not None:
        return 128 + termination_signal
    return 2 if restore_failures else result


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
