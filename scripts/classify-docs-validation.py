#!/usr/bin/env python3
"""Classify changed files for the PR Checks docs-validation job."""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class DocsValidationError(RuntimeError):
    """Raised when changed-file classification cannot be completed."""


@dataclass(frozen=True)
class DocsClassification:
    rendered_docs: bool
    generated_reference: bool
    docs_contract: bool

    @property
    def should_validate_docs(self) -> bool:
        return self.validation_mode != "skip"

    @property
    def validation_mode(self) -> str:
        if self.rendered_docs or self.docs_contract:
            return "full"
        if self.generated_reference:
            return "reference"
        return "skip"

    def output_fields(self) -> dict[str, str]:
        return {
            "should_validate_docs": _boolean_output(self.should_validate_docs),
            "validation_mode": self.validation_mode,
            "rendered_docs": _boolean_output(self.rendered_docs),
            "generated_reference": _boolean_output(self.generated_reference),
            "docs_contract": _boolean_output(self.docs_contract),
        }


def _boolean_output(value: bool) -> str:
    return "true" if value else "false"


def path_is_under(file_path: str, directory: str) -> bool:
    return file_path.startswith(f"{directory}/")


def classify_changed_files(changed_files: Iterable[str]) -> DocsClassification:
    rendered_docs = False
    generated_reference = False
    docs_contract = False

    for file_path in changed_files:
        if not file_path:
            continue

        if path_is_under(file_path, "docs-site"):
            rendered_docs = True

        if (
            file_path.endswith("/.claude-plugin/plugin.json")
            or file_path.endswith("/.codex-plugin/plugin.json")
            or file_path in {
                ".claude-plugin/marketplace.json",
                ".agents/plugins/marketplace.json",
                "speckit-pro/codex-hooks.json",
                "README.md",
                "docs/prd-interactive-documentation.md",
                "docs/roadmap-interactive-documentation.md",
                "release-please-config.json",
                ".release-please-manifest.json",
            }
            or (file_path.endswith("/README.md") and file_path != "README.md")
            or path_is_under(file_path, ".specify/integrations")
        ):
            generated_reference = True

        if any(
            path_is_under(file_path, directory)
            for directory in (
                "speckit-pro/skills",
                "speckit-pro/codex-skills",
                "speckit-pro/agents",
                "speckit-pro/codex-agents",
                "speckit-pro/hooks",
                "speckit-pro/scripts",
                "scripts",
                "tests/speckit-pro",
                "dist/claude",
                "dist/codex",
            )
        ):
            generated_reference = True

        if (
            path_is_under(file_path, "docs-site/scripts")
            or file_path
            in {
                "docs-site/src/data/safe-install-aids.ts",
                "docs-site/package.json",
                "docs-site/playwright.config.mjs",
                "docs-site/tests/docs-smoke.spec.mjs",
                ".github/workflows/pr-checks.yml",
                ".github/workflows/deploy-docs.yml",
                ".github/workflows/release.yml",
            }
        ):
            docs_contract = True

    return DocsClassification(
        rendered_docs=rendered_docs,
        generated_reference=generated_reference,
        docs_contract=docs_contract,
    )


def changed_files_for_base(
    base_ref: str,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[str, ...]:
    if not base_ref:
        raise DocsValidationError("BASE_REF is not set")
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", f"origin/{base_ref}...HEAD"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=True,
            shell=False,
        )
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or "").strip()
        suffix = f": {detail}" if detail else ""
        raise DocsValidationError(
            f"git changed-file detection failed with exit code {error.returncode}{suffix}"
        ) from error
    except OSError as error:
        raise DocsValidationError(f"unable to run git changed-file detection: {error}") from error
    return tuple(completed.stdout.splitlines())


def append_github_output(output_path: Path, fields: Mapping[str, str]) -> None:
    for key, value in fields.items():
        if not key.replace("_", "").isalnum() or "\n" in value or "\r" in value:
            raise DocsValidationError(f"unsafe GitHub output field: {key!r}")
    try:
        with output_path.open("a", encoding="utf-8", newline="\n") as output:
            for key, value in fields.items():
                output.write(f"{key}={value}\n")
    except OSError as error:
        raise DocsValidationError(f"unable to append GITHUB_OUTPUT: {error}") from error


def _print_summary(classification: DocsClassification) -> None:
    fields = classification.output_fields()
    print(f"Rendered docs-site changed: {fields['rendered_docs']}")
    print(f"Generated-reference source changed: {fields['generated_reference']}")
    print(f"Docs-validation contract changed: {fields['docs_contract']}")
    print(f"Docs validation mode: {fields['validation_mode']}")
    if not classification.should_validate_docs:
        print("No DOC-010 docs validation surfaces changed; validate-docs skipped successfully.")


def main(argv: Sequence[str] | None = None) -> int:
    try:
        if argv:
            raise DocsValidationError("classify-docs-validation.py does not accept arguments")
        changed_files = changed_files_for_base(os.environ.get("BASE_REF", ""))
        classification = classify_changed_files(changed_files)
        output_value = os.environ.get("GITHUB_OUTPUT", "")
        if not output_value:
            raise DocsValidationError("GITHUB_OUTPUT is not set")
        _print_summary(classification)
        append_github_output(Path(output_value), classification.output_fields())
    except DocsValidationError as error:
        print(f"::error::Docs validation classification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
