#!/usr/bin/env python3
"""Live probe: each curated install command runs in a fresh project at the pinned Spec Kit.

This is an operator-run, networked check and is not part of any suite layer. It needs the pinned
`specify` CLI first on PATH and reaches github.com. It fails, never skips, when the CLI
is missing or is not the pinned version.

For every entry in `speckit-pro/scripts/curated-set.json` it runs the argv the install and upgrade
skills give the operator, `<kind> add <id> --from <archive_url>`, in a fresh `specify init` project:

- A preset installs without a prompt. The probe requires exit 0 and its directory, but reports
  completion unproven: those observations do not establish registration or manifest identity.
- An extension URL install stops at Spec Kit's own trust prompt, which only the operator answers.
  The check closes stdin, so the default is deny. It requires a normal nonzero exit after the
  prompt (the discovery-only refusal is gone), a verifiably empty registry, and an archive whose
  `extension.yml` declares the entry's id. That proves the refusal is gone, not that an install
  succeeds, so each extension is reported "unproven: needs operator confirmation" and the run exits 2.
- The legacy `--trust-pinned-archives` option fails closed: this check cannot certify a completed
  extension install and never bypasses the trust prompt. Live acceptance belongs to the operator.

Exit codes: 1 a failure, 2 no failure but every entry is unproven. No entry can pass, so the check
never exits 0: completed installs need owner-run acceptance.

`--owner-acceptance` is that owner-run acceptance. The owner runs it in their own terminal:
`python3 tests/speckit-pro/run-curated-install-check.py --owner-acceptance`. It refuses to start
without an interactive terminal. Each `<kind> add <id> --from <archive_url>` inherits the terminal,
so the owner reads and answers Spec Kit's own trust prompt; nothing here pipes, scripts or bypasses
it. YAML evidence is read with the standard library (`read_yaml`), which refuses what it cannot read exactly.

Every install runs first. An entry is then `installed` only when its `specify` exited 0 and every
piece of Spec Kit v1.1.0's on-disk evidence holds in the tree the last install left, checked for all
entries in one pass; otherwise it is `failed`, or `not-run` when nothing was attempted:

- bound to this run: reads are descriptor-relative and no-follow from the project directory this
  run created, `.specify` and `.claude` must be the directories its `specify init` made, nothing
  the install writes may exist before it, every file read is a singly linked regular file, and
  every node read is re-checked unchanged after the last read;
- manifest and payload identity: the installed manifest and every file it declares are
  byte-identical to the pinned archive's;
- registration: `.specify/<kind>s/.registry` has the id with that manifest's hash and declared
  version, `source: local`, `enabled: true`, the default priority 10, and an `installed_at` inside
  this install's window;
- registered artifacts: every declared command and alias is registered, and the frontmatter
  `metadata.source` of its `.claude/skills/<skill>/SKILL.md` is exactly one Spec Kit writes for it
  (the body is never read);
- active configuration (extensions): `.specify/extensions.yml`, read with duplicate keys refused,
  lists the id under `installed:` and carries exactly the hooks the manifest declares;
- events: an entry whose manifest declares `events:` is never certified, because its native hooks
  and dispatcher are outside this evidence. No curated entry declares events.

It exits 0 only when every curated entry is `installed`, and 1 otherwise.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from contextlib import ExitStack
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "speckit-pro"))
from isolated_child import minimal_env  # noqa: E402
from speckit_pro_runner import spec_kit_pin  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
CURATED_SET = REPO_ROOT / "speckit-pro" / "scripts" / "curated-set.json"
COMMAND_TIMEOUT_SECONDS = 180
DISCOVERY_ONLY = "discovery-only"
TRUST_PROMPT = "Continue with installation?"
MANIFEST_NAMES = {"extension": "extension.yml", "preset": "preset.yml"}
REGISTRY_DIRS = {"extension": ".specify/extensions", "preset": ".specify/presets"}
REGISTRY_KEYS = {"extension": "extensions", "preset": "presets"}
EXTENSION_CONFIG = ".specify/extensions.yml"
# The operator's terminal settings, so Spec Kit can draw its prompt; none of them answers it.
TERMINAL_KEYS = ("TERM", "COLUMNS", "LINES")
# Only what pinned Spec Kit v1.1.0 reads to reach github.com: GITHUB_TOKEN/GH_TOKEN
# (authentication/github_http.py), and, through its urllib.request.build_opener openers
# (authentication/http.py), urllib's <scheme>_proxy/no_proxy variables and OpenSSL's default CA paths.
NETWORK_KEYS = ("GH_TOKEN", "GITHUB_TOKEN", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy",
                "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR")


def install_args(entry: dict[str, str]) -> list[str]:
    """The arguments after `specify` that the install and upgrade skills hand the operator."""
    return [entry["kind"], "add", entry["id"], "--from", entry["archive_url"]]


def specify(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the `specify` found on PATH, with stdin closed so a trust prompt defaults to deny."""
    return subprocess.run(
        ["specify", *args], cwd=cwd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
        env=minimal_env({"NO_COLOR": "1"}, keys=NETWORK_KEYS), timeout=COMMAND_TIMEOUT_SECONDS,
        shell=False, check=False,
    )


def check_cli_version(cwd: Path) -> list[str]:
    try:
        result = specify(["version"], cwd)
    except FileNotFoundError:
        installed_version, cli_found = None, False
    else:
        installed_version = spec_kit_pin.parse_cli_version(result.stdout) if result.returncode == 0 else None
        cli_found = True
    status = spec_kit_pin.version_status(installed_version, cli_found=cli_found)
    if status != "match":
        return [f"specify is {status} against the pinned {spec_kit_pin.PINNED_VERSION}"]
    return []


def archive_manifest(url: str, kind: str) -> bytes | None:
    """The manifest at the top of the pinned archive, the bytes Spec Kit copies on install."""
    with urllib.request.urlopen(url, timeout=COMMAND_TIMEOUT_SECONDS) as response:  # noqa: S310 (https URL from the curated set)
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    for name in archive.namelist():
        parts = name.split("/")
        if len(parts) == 2 and parts[1] == MANIFEST_NAMES[kind]:
            return archive.read(name)
    return None


def declares_id(manifest: bytes, entry_id: str) -> bool:
    pattern = re.compile(rf"^\s*id:\s*[\"']?{re.escape(entry_id)}[\"']?\s*$", re.MULTILINE)
    return bool(pattern.search(manifest.decode("utf-8", errors="replace")))


def archive_declares_id(url: str, kind: str, entry_id: str) -> bool:
    manifest = archive_manifest(url, kind)
    return manifest is not None and declares_id(manifest, entry_id)


def directory_state(info: os.stat_result) -> tuple[int, ...]:
    """Bind an inspection to both directory identity and its content-change timestamps."""
    return info.st_dev, info.st_ino, info.st_mode, info.st_mtime_ns, info.st_ctime_ns


def registry_entries(project: Path, kind: str, entry_id: str | None = None) -> list[str] | None:
    """List the whole registry without following links; unknown evidence is not absence."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        with ExitStack() as descriptors:
            parent = os.open(project / ".specify", flags)
            descriptors.callback(os.close, parent)
            bindings = [(project / ".specify", None, directory_state(os.fstat(parent)))]
            name = Path(REGISTRY_DIRS[kind]).name
            try:
                registry = os.open(name, flags, dir_fd=parent)
            except FileNotFoundError:
                registry = None
            entries = []
            if registry is not None:
                descriptors.callback(os.close, registry)
                bindings.append((Path(name), parent, directory_state(os.fstat(registry))))
                if entry_id is not None:
                    target = os.open(entry_id, flags, dir_fd=registry)
                    descriptors.callback(os.close, target)
                    bindings.append((Path(entry_id), registry, directory_state(os.fstat(target))))
                entries = os.listdir(registry)
            if not all(directory_state(os.stat(path, dir_fd=base, follow_symlinks=False)) == before
                       for path, base, before in reversed(bindings)):
                return None
            if registry is None:
                try:
                    os.stat(name, dir_fd=parent, follow_symlinks=False)
                except FileNotFoundError:
                    return [] if entry_id is None else None
                return None
            return entries
    except OSError:
        return None


def check_entry(entry: dict[str, str], project: Path) -> list[str]:
    label = f"{entry['kind']} {entry['id']}"
    if "archive_url" not in entry:
        return [f"{label}: no archive_url, and Spec Kit refuses a bare add on its default catalogs"]
    result = specify(install_args(entry), project)
    output = result.stdout + result.stderr
    failures = []
    if DISCOVERY_ONLY in output:
        failures.append(f"{label}: refused as discovery-only")
    if entry["kind"] == "preset":
        directory_observed = registry_entries(project, "preset", entry["id"]) is not None
        if result.returncode != 0 or not directory_observed:
            failures.append(f"{label}: exit {result.returncode}, directory_observed={directory_observed}")
        return failures
    if TRUST_PROMPT not in output:
        failures.append(f"{label}: did not reach the trust prompt")
    if result.returncode <= 0:
        failures.append(f"{label}: expected a normal nonzero abort, got exit {result.returncode}")
    if registry_entries(project, entry["kind"]) != []:
        failures.append(f"{label}: registry is not verifiably empty after the unanswered trust prompt")
    if not archive_declares_id(entry["archive_url"], entry["kind"], entry["id"]):
        failures.append(f"{label}: archive has no {MANIFEST_NAMES[entry['kind']]} declaring this id")
    return failures


def init_project(project: Path) -> list[str]:
    """Initialize a Spec Kit project in `project`, or say why that failed."""
    if subprocess.run(["git", "init", "-q", "."], cwd=project, env=minimal_env(), capture_output=True,
                      shell=False, check=False).returncode:
        return ["setup failed: git init"]
    created = specify(["init", "--here", "--integration", "claude", "--force", "--script", "py"], project)
    return [f"setup failed: specify init exit {created.returncode}"] if created.returncode else []


def fresh_project(project: Path) -> list[str]:
    """Initialize a Spec Kit project at the pinned version, or say why that is not possible."""
    return check_cli_version(project) or init_project(project)


def check_completed_install(entry: dict[str, str]) -> list[str]:
    """Fail closed until the operator supplies completed-install acceptance outside this check."""
    label = f"{entry['kind']} {entry['id']}"
    # Directory presence and init's exit status are not registration or manifest evidence.
    # Do not manufacture that evidence by pre-authorizing third-party extension execution.
    return [f"{label}: completed install is unproven; owner-run acceptance is required"]


def entry_result(entry: dict[str, str], project: Path, trust_archives: bool) -> tuple[str, list[str]]:
    """Fail with its failures, or unproven: this check never certifies a completed install."""
    failures = check_entry(entry, project)
    if not failures and entry["kind"] == "extension" and trust_archives:
        failures = check_completed_install(entry)
    if failures:
        return "fail", failures
    return "unproven", []


O_DIR = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
O_FILE = os.O_RDONLY | os.O_NOFOLLOW
# Spec Kit v1.1.0 facts the evidence is checked against (src/specify_cli at the v1.1.0 tag).
DEFAULT_PRIORITY = 10  # `add --priority` default: extensions/command_add.py L26, presets/command_add.py L144-147
SKILLS_DIR = (".claude", "skills")  # `init --integration claude`: integrations/claude/__init__.py L47-53
CLOCK_SLACK = timedelta(seconds=2)


class EvidenceError(Exception):
    """One piece of completed-install evidence is missing, foreign or inconsistent."""


# PyYAML 1.1 implicit types (yaml/resolver.py): words it constructs as null or bool, and the other
# int, float, timestamp, merge and value forms, which this reader refuses rather than misread.
YAML_WORDS = {spelling: value for word, value in (("null", None), ("true", True), ("yes", True), ("on", True),
                                                  ("false", False), ("no", False), ("off", False))
              for spelling in (word, word.title(), word.upper())} | {"~": None}
YAML_INT = re.compile(r"[-+]?(?:0|[1-9][0-9]*)")
YAML_OTHER = re.compile(r"[-+]?(?:0b[01_]+|0[0-7_]+|0x[0-9a-fA-F_]+|[0-9][0-9_]*(?::[0-5]?[0-9])+(?:\.[0-9_]*)?"
                        r"|[1-9][0-9_]*|[0-9][0-9_]*\.[0-9_]*(?:[eE][-+][0-9]+)?|\.[0-9_]+(?:[eE][-+][0-9]+)?"
                        r"|\.(?:inf|Inf|INF|nan|NaN|NAN))|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}(?:[Tt ].*)?|<<|=")
YAML_KEY = re.compile(r"([A-Za-z_][\w.-]*):(?: +(.*))?")
YAML_ESCAPES = {"\\": "\\", '"': '"', "/": "/", "n": "\n", "t": "\t", "r": "\r", "0": "\0"}
YAML_FLOW_ITEM = re.compile(r" *('(?:[^']|'')*'|\"(?:[^\"\\]|\\.)*\"|[^,\[\]{}#'\" ?:][^,\[\]{}#:]*?) *([,\]])")


def quoted(text: str, start: int) -> tuple[str, int] | None:
    """The quoted scalar opening at `start` and the index after it, or None when it does not close."""
    quote, out, index = text[start], [], start + 1
    while index < len(text):
        char, after = text[index], text[index + 1:index + 2]
        if char == quote and not (quote == "'" and after == "'"):
            return "".join(out), index + 1
        if char == quote or (quote == '"' and char == "\\"):  # `''` or a backslash escape
            require(char == "'" or after in YAML_ESCAPES, "unsupported YAML escape")
            out.append("'" if char == "'" else YAML_ESCAPES[after])
            index += 2
        else:
            out.append(char)
            index += 1
    return None


def plain(text: str) -> object:
    require(text != "" and text[0] not in "[]{}#&*!|>%@`,'\"?:" and text != "-"
            and not text.startswith("- ") and ": " not in text and not text.endswith(":"),
            "unsupported YAML plain scalar")
    if text in YAML_WORDS:
        return YAML_WORDS[text]
    if YAML_INT.fullmatch(text):
        return int(text)
    require(YAML_OTHER.fullmatch(text) is None, "unsupported implicit YAML type")
    return text


def flow(text: str) -> tuple[list | dict, str]:
    """`{}`, `[]`, or a one-line sequence of scalars, and the text after it."""
    if text.startswith(("{}", "[]")):
        return ({} if text[0] == "{" else []), text[2:]
    require(text[0] == "[", "unsupported YAML flow collection")
    items, index, end = [], 1, ","
    while end == ",":
        match = YAML_FLOW_ITEM.match(text, index)
        require(match is not None, "unsupported YAML flow sequence")
        assert match is not None
        item, end = match.groups()
        found = quoted(item, 0) if item[0] in "'\"" else None
        items.append(found[0] if found else plain(item))
        index = match.end()
    return items, text[index:]


def continues(rows: list[list], index: int, indent: int) -> bool:
    """Whether row `index` continues the scalar above it: deeper, with no blank or comment line between."""
    return index < len(rows) and rows[index][1] > indent and rows[index][0] == rows[index - 1][0] + 1


def scalar(rows: list[list], index: int, text: str, indent: int) -> tuple[object, int]:
    """A value that starts on row `index`, folding PyYAML's wrapped plain and single-quoted lines."""
    index += 1
    if text[0] in "[{":
        value, rest = flow(text)
    elif text[0] in "'\"":
        while (found := quoted(text, 0)) is None and text[0] == "'" and continues(rows, index, indent):
            text, index = text.rstrip(" ") + " " + rows[index][2].strip(" "), index + 1
        require(found is not None, "unclosed or multi-line double-quoted YAML scalar")
        assert found is not None
        value, rest = found[0], text[found[1]:]
    else:
        lines = [text.split(" #", 1)]
        while len(lines[-1]) == 1 and continues(rows, index, indent):
            lines.append(rows[index][2].split(" #", 1))
            index += 1
        return plain(" ".join(line[0].strip(" ") for line in lines)), index
    require(rest.strip(" ") == "" or re.match(r" +#", rest) is not None, "unexpected text after a YAML value")
    return value, index


def nested(rows: list[list], index: int, indent: int, same_indent_sequence: bool) -> tuple[object, int]:
    """The block under an empty `key:` or `-`, or null when there is none."""
    if index < len(rows) and (rows[index][1] > indent or (same_indent_sequence and rows[index][1] == indent
                                                          and re.match(r"-( |$)", rows[index][2]))):
        return block(rows, index, rows[index][1])
    return None, index


def block(rows: list[list], index: int, indent: int) -> tuple[object, int]:
    """The block mapping or sequence whose rows sit at `indent`, starting at row `index`."""
    if re.match(r"-( |$)", rows[index][2]):
        return block_sequence(rows, index, indent)
    return block_mapping(rows, index, indent)


def block_mapping(rows: list[list], index: int, indent: int) -> tuple[dict, int]:
    result: dict[str, object] = {}
    while index < len(rows) and rows[index][1] == indent:
        match = YAML_KEY.fullmatch(rows[index][2])
        require(match is not None, "unsupported YAML line")
        assert match is not None
        key, text = match.group(1), (match.group(2) or "").rstrip(" ")
        require(key not in YAML_WORDS, "unsupported non-string YAML key")
        require(key not in result, "duplicate YAML key")
        if text == "" or text.startswith("#"):
            result[key], index = nested(rows, index + 1, indent, True)
        else:
            result[key], index = scalar(rows, index, text, indent)
    return result, index


def block_sequence(rows: list[list], index: int, indent: int) -> tuple[list, int]:
    items = []
    while index < len(rows) and rows[index][1] == indent and re.match(r"-( |$)", rows[index][2]):
        number, _indent, body = rows[index]
        text = body[1:].lstrip(" ").rstrip(" ")
        if text == "" or text.startswith("#"):
            value, index = nested(rows, index + 1, indent, False)
        elif YAML_KEY.fullmatch(text) or re.match(r"-( |$)", text):
            rows[index] = [number, indent + len(body) - len(body[1:].lstrip(" ")), text]
            value, index = block(rows, index, rows[index][1])
        else:
            value, index = scalar(rows, index, text, indent)
        items.append(value)
    return items, index


def read_yaml(data: bytes) -> object:
    """Read YAML with the standard library: the block subset Spec Kit v1.1.0's pinned manifests,
    `extensions.yml` (yaml.dump) and SKILL.md frontmatter (yaml.dump/safe_dump) use, giving what
    PyYAML's safe loader gives. Anything else is refused, never guessed: anchors, aliases, tags,
    block scalars, multi-line double quotes, blank lines inside a value, other implicit types and
    any duplicate key."""
    text = data.decode("utf-8")
    # Only `\n` breaks lines and no tab or character PyYAML rejects appears (yaml/reader.py NON_PRINTABLE).
    require(re.search("[^\n\x20-\x7e\xa0-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]|[\u2028\u2029]", text) is None,
            "unsupported YAML character")
    rows = []
    for number, line in enumerate(text.split("\n")):
        body = line.lstrip(" ")
        if body and not body.startswith("#"):
            require(body.rstrip(" ") not in ("---", "...") and body[0] != "%", "unsupported YAML line")
            rows.append([number, len(line) - len(body), body])
    if not rows:
        return None
    value, index = block(rows, 0, rows[0][1])
    require(index == len(rows), "unsupported YAML indentation")
    return value


def pinned_archive(url: str) -> dict[str, bytes]:
    """Every file under the pinned archive's top directory, keyed by its path below it."""
    with urllib.request.urlopen(url, timeout=COMMAND_TIMEOUT_SECONDS) as response:  # noqa: S310 (https URL from the curated set)
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
    return {name.split("/", 1)[1]: archive.read(name) for name in archive.namelist()
            if "/" in name and not name.endswith("/")}


def node_state(info: os.stat_result) -> tuple[int, ...]:
    return info.st_dev, info.st_ino, info.st_mode, info.st_nlink, info.st_size, info.st_mtime_ns, info.st_ctime_ns


class BoundTree:
    """Descriptor-relative, no-follow reads under the project this run created.

    Every directory and file read is bound to the state it was read in; `verify_unchanged`
    re-checks all of them after the last read, so evidence comes from one consistent tree.
    """

    def __init__(self, stack: ExitStack, root: int, identities: dict[str, tuple[int, int]]):
        self.stack, self.root, self.identities = stack, root, identities
        self.bindings: list[tuple[int, str, tuple[int, ...]]] = []

    def directory(self, parts: tuple[str, ...]) -> int:
        fd = self.root
        for depth, name in enumerate(parts):
            child = os.open(name, O_DIR, dir_fd=fd)
            self.stack.callback(os.close, child)
            info = os.fstat(child)
            if depth == 0 and name in self.identities and (info.st_dev, info.st_ino) != self.identities[name]:
                raise EvidenceError(f"{name} is not the directory `specify init` created for this run")
            self.bindings.append((fd, name, node_state(info)))
            fd = child
        return fd

    def read(self, parts: tuple[str, ...]) -> bytes:
        parent = self.directory(parts[:-1])
        with os.fdopen(os.open(parts[-1], O_FILE, dir_fd=parent), "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise EvidenceError(f"{'/'.join(parts)} is not a regular, singly linked file")
            data = handle.read()
            if node_state(os.fstat(handle.fileno())) != node_state(info):
                raise EvidenceError(f"{'/'.join(parts)} changed while it was read")
        self.bindings.append((parent, parts[-1], node_state(info)))
        return data

    def exists(self, parts: tuple[str, ...]) -> bool:
        try:
            parent = self.directory(parts[:-1])
            os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True

    def verify_unchanged(self) -> None:
        for parent, name, state in self.bindings:
            try:
                current = node_state(os.stat(name, dir_fd=parent, follow_symlinks=False))
            except OSError as error:
                raise EvidenceError(f"{name} changed after it was read") from error
            if current != state:
                raise EvidenceError(f"{name} changed after it was read")


def skill_name(command: str) -> str:
    """The skill directory Spec Kit writes for a command (agents.py L579-594, extensions L1427-1432)."""
    short = command[len("speckit."):] if command.startswith("speckit.") else command
    return "speckit-" + short.replace(".", "-")


def declared(doc: dict, kind: str) -> tuple[list[str], dict[str, str]]:
    """The payload files the pinned manifest declares, and each command name (aliases too) with its file."""
    provides = doc.get("provides") or {}
    if kind == "preset":
        templates = provides.get("templates") or []
        return ([item["file"] for item in templates],
                {item["name"]: item["file"] for item in templates if item.get("type") == "command"})
    commands = provides.get("commands") or []
    files = [item["file"] for item in commands] + [item["file"] for item in provides.get("scripts") or []]
    files += [item["template"] for item in provides.get("config") or [] if item.get("template")]
    return files, {name: item["file"] for item in commands for name in [item["name"], *(item.get("aliases") or [])]}


def hook_entry(item: object, entry_id: str) -> dict | None:
    """One extensions.yml hook as register_hooks writes it (extensions/__init__.py L5885-5896)."""
    command = item.get("command") if isinstance(item, dict) else None
    if not isinstance(item, dict) or not command:
        return None
    parts = str(command).split(".")  # alias-form refs are lifted to canonical names (L523-549)
    command = f"speckit.{entry_id}.{parts[1]}" if len(parts) == 2 and parts[0] == entry_id else command
    priority = item.get("priority")  # normalize_priority (L195-214)
    valid = isinstance(priority, int) and not isinstance(priority, bool) and priority >= 1
    return {"extension": entry_id, "command": command, "enabled": True, "optional": item.get("optional", True),
            "priority": priority if valid else DEFAULT_PRIORITY, "prompt": item.get("prompt", f"Execute {command}?"),
            "description": item.get("description", ""), "condition": item.get("condition")}


def expected_hooks(doc: dict, entry_id: str) -> dict[str, list[dict]]:
    """The extensions.yml hooks register_hooks writes for this manifest (L5817-5905), last duplicate wins."""
    hooks = {}
    for event, config in (doc.get("hooks") or {}).items():
        entries: dict[str, dict] = {}
        for item in config if isinstance(config, list) else [config]:
            hook = hook_entry(item, entry_id)
            if hook is not None:
                entries.pop(hook["command"], None)
                entries[hook["command"]] = hook
        if entries:
            hooks[event] = list(entries.values())
    return hooks


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise EvidenceError(reason)


def strict_json(data: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict:
        require(len({key for key, _value in items}) == len(items), "duplicate JSON key")
        return dict(items)
    return json.loads(data, object_pairs_hook=pairs)


def check_registration(tree: BoundTree, entry: dict[str, str], doc: dict, manifest: bytes,
                       window: tuple[datetime, datetime]) -> dict:
    kind, entry_id = entry["kind"], entry["id"]
    registry = strict_json(tree.read((".specify", f"{kind}s", ".registry")))
    records = registry.get(REGISTRY_KEYS[kind]) if isinstance(registry, dict) else None
    record = records.get(entry_id) if isinstance(records, dict) else None
    require(isinstance(record, dict), f"not registered in {REGISTRY_DIRS[kind]}/.registry")
    assert isinstance(record, dict)
    require(record.get("manifest_hash") == "sha256:" + hashlib.sha256(manifest).hexdigest(),
            "registry manifest_hash does not match the installed manifest")
    require(record.get("version") == (doc.get(kind) or {}).get("version"), "registry version is not the manifest's")
    require(record.get("source") == "local", "registry source is not the local archive a --from install records")
    require(record.get("enabled") is True, "registry entry is not enabled")
    require(record.get("priority") == DEFAULT_PRIORITY and not isinstance(record.get("priority"), bool),
            f"registry priority is not the default {DEFAULT_PRIORITY} the command used")
    try:
        installed_at = datetime.fromisoformat(str(record.get("installed_at")))
    except ValueError:
        installed_at = None
    require(installed_at is not None and installed_at.tzinfo is not None
            and window[0] - CLOCK_SLACK <= installed_at <= window[1] + CLOCK_SLACK,
            "registry entry was not written by this run's install")
    return record


def owns_skill(skill: bytes, entry: dict[str, str], file: str) -> bool:
    """Whether a SKILL.md's frontmatter `metadata.source` is exactly one Spec Kit writes for this
    entry's command: `<id>:<file>` (agents.py L461-466), `extension:<id>` (extensions/__init__.py
    L1736-1741) or `preset:<id>` (presets/_manager_skills.py L800-805). The frontmatter ends at the
    first `---` line (agents.py L130-149); the body is never read, so its text cannot claim ownership."""
    lines = skill.decode("utf-8").split("\n")
    require(lines[0] == "---" and "---" in lines[1:], "SKILL.md has no closed frontmatter")
    front = read_yaml("\n".join(lines[1:lines.index("---", 1)]).encode())
    metadata = front.get("metadata") if isinstance(front, dict) else None
    source = metadata.get("source") if isinstance(metadata, dict) else None
    return isinstance(source, str) and source in (f"{entry['id']}:{file}", f"{entry['kind']}:{entry['id']}")


def check_artifacts(tree: BoundTree, entry: dict[str, str], record: dict, names: dict[str, str]) -> None:
    """Each declared command is registered and its skill is on disk, bound to this entry."""
    commands = record.get("registered_commands")
    skills = record.get("registered_skills")
    registered = {name for values in (commands or {}).values() if isinstance(values, list) for name in values}
    registered |= set(skills) if isinstance(skills, list) else set()
    for name, file in names.items():
        require(name in registered or skill_name(name) in registered, f"command {name} is not registered")
        require(owns_skill(tree.read((*SKILLS_DIR, skill_name(name), "SKILL.md")), entry, file),
                f"skill for {name} does not come from this {entry['kind']}")


def check_configuration(tree: BoundTree, entry_id: str, doc: dict) -> None:
    """The active extensions.yml lists the id and carries exactly the manifest's hooks."""
    config = read_yaml(tree.read((".specify", "extensions.yml")))
    require(isinstance(config, dict), "extensions.yml is not a mapping")
    assert isinstance(config, dict)
    installed = config.get("installed")
    require(isinstance(installed, list) and entry_id in installed, "not listed under installed: in extensions.yml")
    hooks = config.get("hooks") or {}
    require(isinstance(hooks, dict), "extensions.yml hooks is not a mapping")
    actual = {event: [hook for hook in items if isinstance(hook, dict) and hook.get("extension") == entry_id]
              for event, items in hooks.items() if isinstance(items, list)}
    actual = {event: items for event, items in actual.items() if items}
    require(actual == expected_hooks(doc, entry_id), "hook registrations differ from the manifest's")


Install = tuple[dict[str, bytes], tuple[datetime, datetime]]  # the pinned archive's files, the install window


def completion_evidence(tree: BoundTree, entry: dict[str, str], files: dict[str, bytes],
                        window: tuple[datetime, datetime]) -> tuple[str, list[str]]:
    """`installed` with its evidence, or `failed` naming the first evidence that does not hold."""
    kind, entry_id = entry["kind"], entry["id"]
    label = f"{kind} {entry_id}"
    try:
        pinned = files[MANIFEST_NAMES[kind]]
        doc = read_yaml(pinned)
        require(isinstance(doc, dict) and (doc.get(kind) or {}).get("id") == entry_id,
                "pinned manifest does not declare this id")
        assert isinstance(doc, dict)
        # Manifest events become native hooks and a dispatcher outside this evidence
        # (events/__init__.py L1071-1100, L1350-1392), so such an entry is never certified here.
        require("events" not in doc, "the manifest declares Spec Kit events, which this check does not verify")
        home = (".specify", f"{kind}s", entry_id)
        manifest = tree.read((*home, MANIFEST_NAMES[kind]))
        require(manifest == pinned, "installed manifest differs from the pinned archive's")
        payload, names = declared(doc, kind)
        for path in payload:
            require(path in files and tree.read((*home, *path.split("/"))) == files[path],
                    f"declared file {path} is missing or differs from the pinned archive's")
        record = check_registration(tree, entry, doc, manifest, window)
        check_artifacts(tree, entry, record, names)
        if kind == "extension":
            check_configuration(tree, entry_id, doc)
    except Exception as error:  # noqa: BLE001 (unreadable evidence is missing evidence, not a crash)
        return "failed", [f"{label}: {error if isinstance(error, EvidenceError) else repr(error)}"]
    return "installed", [f"{label}: version {doc[kind]['version']}, {len(payload)} declared files and "
                         f"{len(names)} commands match the pinned archive and are registered"]


def registered_before(tree: BoundTree, entry: dict[str, str]) -> bool:
    kind = entry["kind"]
    if tree.exists((".specify", f"{kind}s", entry["id"])):
        return True
    if not tree.exists((".specify", f"{kind}s", ".registry")):
        return False
    registry = strict_json(tree.read((".specify", f"{kind}s", ".registry")))
    records = registry.get(REGISTRY_KEYS[kind]) if isinstance(registry, dict) else None
    return not isinstance(records, dict) or entry["id"] in records


def configured_before(tree: BoundTree, entry_id: str) -> bool:
    if not tree.exists((".specify", "extensions.yml")):
        return False
    config = read_yaml(tree.read((".specify", "extensions.yml")))
    require(isinstance(config, dict), "extensions.yml is not a mapping")
    assert isinstance(config, dict)
    hooks = [hook for items in (config.get("hooks") or {}).values() for hook in items or []]
    return entry_id in (config.get("installed") or []) or any(
        isinstance(hook, dict) and hook.get("extension") == entry_id for hook in hooks)


def prior_evidence(project: int, identities: dict[str, tuple[int, int]], entry: dict[str, str],
                   files: dict[str, bytes]) -> bool:
    """Whether anything this entry's install would write is already there (fails closed)."""
    try:
        with ExitStack() as stack:
            tree = BoundTree(stack, project, identities)
            doc = read_yaml(files[MANIFEST_NAMES[entry["kind"]]])
            names = declared(doc, entry["kind"])[1] if isinstance(doc, dict) else {}
            # A preset's skills replace core ones `specify init` wrote, so only an owned skill is prior.
            skills = {(*SKILLS_DIR, skill_name(name), "SKILL.md"): file for name, file in names.items()}
            found = (registered_before(tree, entry)
                     or any(tree.exists(skill) and owns_skill(tree.read(skill), entry, file)
                            for skill, file in skills.items())
                     or (entry["kind"] == "extension" and configured_before(tree, entry["id"])))
            tree.verify_unchanged()
            return found
    except Exception:  # noqa: BLE001 (unknown prior state is not absence)
        return True


def operator_specify(args: list[str], cwd: Path) -> int:
    """Run `specify` on the operator's terminal: stdin, stdout and stderr are inherited, so only
    the operator answers any prompt. No flag or variable that skips a prompt is added."""
    env = minimal_env(keys=(*NETWORK_KEYS, *TERMINAL_KEYS))
    return subprocess.run(["specify", *args], cwd=cwd, env=env, shell=False, check=False).returncode


def accept_entry(entry: dict[str, str], project: Path, root: int, identities: dict[str, tuple[int, int]],
                 installs: dict[str, Install]) -> tuple[str, list[str]]:
    """Install one entry on the operator's terminal. A clean exit is only `pending`: its evidence is
    judged after the last install, so a later install cannot leave stale evidence certified."""
    label = f"{entry['kind']} {entry['id']}"
    if "archive_url" not in entry:
        return "not-run", [f"{label}: no archive_url"]
    try:
        files = pinned_archive(entry["archive_url"])
    except (OSError, zipfile.BadZipFile) as error:
        return "not-run", [f"{label}: pinned archive unavailable ({type(error).__name__})"]
    if MANIFEST_NAMES[entry["kind"]] not in files:
        return "not-run", [f"{label}: pinned archive has no {MANIFEST_NAMES[entry['kind']]}"]
    if prior_evidence(root, identities, entry, files):
        return "failed", [f"{label}: install evidence existed before this run's install"]
    args = install_args(entry)
    print(f"\n== {label}: specify {' '.join(args)}", flush=True)
    print("   Review the prompt and answer it yourself.", flush=True)
    started = datetime.now(timezone.utc)
    try:
        code = operator_specify(args, project)
    except OSError as error:
        return "not-run", [f"{label}: specify did not start ({type(error).__name__})"]
    if code != 0:
        how = f"was terminated by signal {-code}" if code < 0 else f"exited {code}"
        return "failed", [f"{label}: specify {how}"]
    installs[label] = (files, (started, datetime.now(timezone.utc)))
    return "pending", []


def final_evidence(root: int, identities: dict[str, tuple[int, int]], entries: list[dict[str, str]],
                   results: list[tuple[str, list[str]]], installs: dict[str, Install]) -> list[tuple[str, list[str]]]:
    """Judge every pending entry against the tree as the last install left it, in one bound pass:
    a node that changes before the pass ends fails every entry that pass would certify."""
    with ExitStack() as stack:
        tree = BoundTree(stack, root, identities)
        labels = [f"{entry['kind']} {entry['id']}" for entry in entries]
        results = [completion_evidence(tree, entry, *installs[label]) if status == "pending" else (status, details)
                   for entry, label, (status, details) in zip(entries, labels, results, strict=True)]
        try:
            tree.verify_unchanged()
        except EvidenceError as error:
            results = [("failed", [f"{label}: {error}"]) if status == "installed" else (status, details)
                       for label, (status, details) in zip(labels, results, strict=True)]
    return results


def interactive() -> bool:
    """Whether a person is at this terminal to read and answer Spec Kit's prompts."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def bind_project(root: int) -> dict[str, tuple[int, int]]:
    """The identity of each directory `specify init` created, for every later read to match."""
    identities = {}
    for name in (".specify", SKILLS_DIR[0]):
        info = os.stat(name, dir_fd=root, follow_symlinks=False)
        if not stat.S_ISDIR(info.st_mode):
            raise EvidenceError(f"{name} is not a directory after init")
        identities[name] = (info.st_dev, info.st_ino)
    return identities


def run_acceptance(entries: list[dict[str, str]]) -> list[tuple[str, list[str]]]:
    with tempfile.TemporaryDirectory(prefix="curated-acceptance-") as raw, ExitStack() as stack:
        project = Path(raw).resolve()
        root = os.open(project, O_DIR)
        stack.callback(os.close, root)
        setup_failures = fresh_project(project)
        if not setup_failures:
            try:
                identities = bind_project(root)
            except (OSError, EvidenceError) as error:
                setup_failures = [f"setup failed: {error}"]
        if setup_failures:
            return [("not-run", setup_failures)] * len(entries)
        installs: dict[str, Install] = {}
        results = [accept_entry(entry, project, root, identities, installs) for entry in entries]
        return final_evidence(root, identities, entries, results, installs)


def owner_acceptance(entries: list[dict[str, str]]) -> int:
    """Install every curated entry with the operator at the terminal; 0 only when all are installed."""
    if not interactive():
        results = [("not-run", ["owner acceptance needs an interactive terminal; run it yourself"])] * len(entries)
    else:
        results = run_acceptance(entries)
    for entry, (status, details) in zip(entries, results, strict=True):
        print(f"{status.upper()} {entry['kind']} {entry['id']}: " + "; ".join(details))
    installed = [status for status, _details in results].count("installed")
    print(f"run-curated-install-check --owner-acceptance: {installed}/{len(entries)} installed")
    return 0 if installed == len(entries) else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--curated-set", type=Path, default=CURATED_SET)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--trust-pinned-archives", action="store_true",
        help="legacy option: fails closed; completed installs need owner-run acceptance",
    )
    mode.add_argument(
        "--owner-acceptance", action="store_true",
        help="owner-run: install each entry on your terminal, answer Spec Kit's prompts yourself, verify",
    )
    args = parser.parse_args(argv)
    entries = json.loads(args.curated_set.read_text(encoding="utf-8"))["entries"]
    if not entries:
        print("FAIL curated set: no entries to verify", file=sys.stderr)
        return 1
    if args.owner_acceptance:
        return owner_acceptance(entries)
    results: list[tuple[str, list[str]]] = []
    with tempfile.TemporaryDirectory(prefix="curated-install-") as raw:
        project = Path(raw)
        setup_failures = fresh_project(project)
        if setup_failures:
            results = [("fail", setup_failures)] * len(entries)
        else:
            results = [entry_result(entry, project, args.trust_pinned_archives) for entry in entries]
    for entry, (status, _failures) in zip(entries, results, strict=True):
        if status == "unproven":
            reason = "needs operator confirmation" if entry["kind"] == "extension" else "needs owner-run acceptance"
            print(f"UNPROVEN {entry['kind']} {entry['id']}: {reason}", file=sys.stderr)
    for failure in dict.fromkeys(failure for status, failures in results if status == "fail" for failure in failures):
        print(f"FAIL {failure}", file=sys.stderr)
    counts = {status: [result[0] for result in results].count(status) for status in ("pass", "fail", "unproven")}
    unproven_note = f", {counts['unproven']} unproven (needs owner-run acceptance)" if counts["unproven"] else ""
    print(f"run-curated-install-check: {counts['pass']}/{len(entries)} passed{unproven_note}")
    return 1 if counts["fail"] else 2 if counts["unproven"] else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
