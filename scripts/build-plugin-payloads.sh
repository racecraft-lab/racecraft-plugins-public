#!/usr/bin/env bash
# build-plugin-payloads.sh -- Build platform-specific install payloads.
#
# speckit-pro/ is the authoring tree. It intentionally carries Claude and Codex
# variants side by side, which is not safe as an installed payload because Codex
# can see duplicate skill names. This script emits isolated marketplace roots:
#   - dist/claude/speckit-pro
#   - dist/codex/speckit-pro
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

python3 - "$REPO_ROOT" <<'PY'
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

repo = Path(sys.argv[1]).resolve()
source = repo / "speckit-pro"
dist = repo / "dist"
claude = dist / "claude" / "speckit-pro"
codex = dist / "codex" / "speckit-pro"

if not source.is_dir():
    raise SystemExit(f"source plugin directory not found: {source}")


def reset_dir(path: Path) -> None:
    real_repo = repo.resolve()
    real_path = path.resolve() if path.exists() else path
    if real_repo not in [real_path, *real_path.parents]:
        raise SystemExit(f"refusing to reset path outside repo: {path}")
    if not str(path).startswith(str(dist)):
        raise SystemExit(f"refusing to reset non-dist path: {path}")
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def copy_path(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    elif src.is_file():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def copy_required(src_name: str, dst_root: Path, dst_name: Optional[str] = None) -> None:
    src = source / src_name
    if not src.exists():
        raise SystemExit(f"required source path missing: {src}")
    copy_path(src, dst_root / (dst_name or src_name))


def copy_optional(src_name: str, dst_root: Path, dst_name: Optional[str] = None) -> None:
    src = source / src_name
    if src.exists():
        copy_path(src, dst_root / (dst_name or src_name))


def copy_repo_optional(src_name: str, dst_root: Path, dst_name: Optional[str] = None) -> None:
    src = repo / src_name
    if src.exists():
        copy_path(src, dst_root / (dst_name or src_name))


def strip_codex_guard(skill_file: Path) -> None:
    text = skill_file.read_text()
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].rstrip("\n") == "## Codex Skill-Selection Guard":
            i += 1
            while i < len(lines):
                line = lines[i]
                i += 1
                if "fallback guard was triggered." in line:
                    break
            while i < len(lines) and lines[i].strip() == "":
                i += 1
            if i < len(lines) and lines[i].startswith("The Codex variant must"):
                while i < len(lines) and lines[i].strip() != "":
                    i += 1
                while i < len(lines) and lines[i].strip() == "":
                    i += 1
            continue
        out.append(lines[i])
        i += 1
    skill_file.write_text("".join(out))


def rewrite_codex_manifest() -> None:
    manifest = codex / ".codex-plugin" / "plugin.json"
    data = json.loads(manifest.read_text())
    data["skills"] = "./skills/"
    manifest.write_text(json.dumps(data, indent=2) + "\n")


REL_SKILL_PATH = re.compile(r"(?P<prefix>(?:\.\./)+(?:skills|codex-skills)/)(?P<rest>[^\s`)\"']+)")


def rewrite_payload_skill_paths(path: Path) -> None:
    try:
        text = path.read_text()
    except UnicodeDecodeError:
        return

    current_dir = path.parent

    def replace(match: re.Match[str]) -> str:
        rest = match.group("rest")
        suffix = ""
        while rest and rest[-1] in ".,;:":
            suffix = rest[-1] + suffix
            rest = rest[:-1]
        anchor = ""
        if "#" in rest:
            rest, anchor = rest.split("#", 1)
            anchor = "#" + anchor
        trailing_slash = rest.endswith("/")
        target = codex / "skills" / rest
        rel = os.path.relpath(target, current_dir).replace(os.sep, "/")
        if trailing_slash and not rel.endswith("/"):
            rel += "/"
        return rel + anchor + suffix

    new_text = REL_SKILL_PATH.sub(replace, text)
    if new_text != text:
        path.write_text(new_text)


def build_claude_payload() -> None:
    reset_dir(claude)
    for name in [
        ".claude-plugin",
        "agents",
        "commands",
        "hooks",
        "skills",
        "scripts",
        "README.md",
        "CHANGELOG.md",
    ]:
        copy_optional(name, claude)
    copy_repo_optional("LICENSE", claude)
    for skill_file in claude.glob("skills/*/SKILL.md"):
        strip_codex_guard(skill_file)


def build_codex_payload() -> None:
    reset_dir(codex)
    for name in [
        ".codex-plugin",
        "codex-agents",
        "codex-hooks.json",
        "scripts",
        "README.md",
        "CHANGELOG.md",
    ]:
        copy_optional(name, codex)
    copy_repo_optional("LICENSE", codex)
    copy_required("skills", codex)
    copy_required("codex-skills", codex, "skills")
    rewrite_codex_manifest()
    for text_file in codex.rglob("*"):
        if text_file.is_file():
            rewrite_payload_skill_paths(text_file)


build_claude_payload()
build_codex_payload()
print(f"Built {claude.relative_to(repo)}")
print(f"Built {codex.relative_to(repo)}")
PY
