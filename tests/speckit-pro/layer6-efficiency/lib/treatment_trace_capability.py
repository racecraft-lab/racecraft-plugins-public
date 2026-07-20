#!/usr/bin/env python3
"""Checkout-bound capability loading for treatment validation and replay."""

from __future__ import annotations

import importlib.util
import sys
import threading
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from uuid import uuid4


CAPABILITY_MODULE_PATH = Path(__file__).with_name("codex_capabilities.py")
_CAPABILITY_DEPENDENCY_NAMES = (
    "codex_capability_contract",
    "codex_capability_io",
    "codex_capability_sources",
    "codex_capability_observations",
    "codex_capability_matrix",
    "codex_capability_private",
    "codex_capability_retention_records",
    "codex_capability_retention",
    "codex_capability_freeze",
    "codex_capability_publish_io",
    "codex_capability_cli",
)
_CAPABILITY_LOAD_LOCK = threading.RLock()


def _resolved_module_file(module: object, name: str) -> Path:
    module_file = getattr(module, "__file__", None)
    try:
        resolved = Path(module_file).resolve(strict=True) if isinstance(module_file, str) else None
    except OSError as exc:
        raise RuntimeError(f"capability dependency {name} cannot be resolved") from exc
    expected = Path(__file__).with_name(f"{name}.py").resolve(strict=True)
    if resolved != expected:
        raise RuntimeError(f"capability dependency {name} does not resolve to {expected}")
    return expected


def _capability_module() -> object:
    with _CAPABILITY_LOAD_LOCK:
        for name in _CAPABILITY_DEPENDENCY_NAMES:
            existing = sys.modules.get(name)
            if existing is not None:
                _resolved_module_file(existing, name)

        package_name = f"_g56r_treatment_capability_{uuid4().hex}"
        package = ModuleType(package_name)
        package.__package__ = package_name
        package.__path__ = [str(CAPABILITY_MODULE_PATH.parent.resolve(strict=True))]
        package.__spec__ = ModuleSpec(package_name, loader=None, is_package=True)
        facade_name = f"{package_name}.codex_capabilities"
        sys.modules[package_name] = package
        try:
            facade_spec = importlib.util.spec_from_file_location(
                facade_name, CAPABILITY_MODULE_PATH.resolve(strict=True),
            )
            if facade_spec is None or facade_spec.loader is None:
                raise RuntimeError("cannot load capability freeze validator")
            facade = importlib.util.module_from_spec(facade_spec)
            sys.modules[facade_name] = facade
            facade_spec.loader.exec_module(facade)
            contract = sys.modules.get(f"{package_name}.codex_capability_contract")
            tuple_factory = getattr(contract, "_AuthorityTupleSet", None)
            if not callable(tuple_factory):
                raise RuntimeError("capability authority tuple factory is unavailable")
            setattr(
                facade,
                "_treatment_authority_tuple_set",
                tuple_factory,
            )
            return facade
        finally:
            for name in tuple(sys.modules):
                if name == package_name or name.startswith(f"{package_name}."):
                    sys.modules.pop(name, None)


def _capability_authority_tuple_set(capability: object, tuples: list[dict]) -> list[dict]:
    factory = getattr(capability, "_treatment_authority_tuple_set", None)
    if not callable(factory):
        raise RuntimeError("capability authority tuple factory is unavailable")
    return factory(tuples)


__all__ = ("CAPABILITY_MODULE_PATH", "_capability_authority_tuple_set", "_capability_module")
