"""Architecture vocabulary shared by the container and hosted Windows preflight scripts."""

from __future__ import annotations

from typing import NamedTuple

FAMILY_ALIASES = {
    "amd64": "x64",
    "x64": "x64",
    "x86_64": "x64",
    "aarch64": "arm64",
    "arm64": "arm64",
}


class Architectures(NamedTuple):
    process: str
    native: str
    process_family: str
    native_family: str
    emulated: bool


def architecture_family(value: str) -> str:
    """Map a machine or processor name to "x64" or "arm64"; unknown names map to ""."""
    return FAMILY_ALIASES.get(value.strip().lower().replace("-", "_"), "")


def resolve_architectures(
    machine: str,
    processor_architecture: str = "",
    processor_architew6432: str = "",
) -> Architectures:
    """Resolve process and native architectures, each falling back to the machine name."""
    process = processor_architecture.strip() or machine
    native = processor_architew6432.strip() or machine
    process_family = architecture_family(process)
    native_family = architecture_family(native)
    emulated = bool(process_family and native_family and process_family != native_family)
    return Architectures(process, native, process_family, native_family, emulated)
