#!/usr/bin/env python3
"""Checkout-bound capability loading for treatment validation and replay."""

from __future__ import annotations

import importlib.util
import sys
import threading
from pathlib import Path


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
_CAPABILITY_DEPENDENCY_FILES = {
    name: Path(__file__).with_name(f"{name}.py")
    for name in _CAPABILITY_DEPENDENCY_NAMES
}
_CAPABILITY_LOAD_LOCK = threading.RLock()
_MISSING_MODULE = object()


def _resolved_module_file(module: object, name: str) -> Path:
    module_file = getattr(module, "__file__", None)
    try:
        resolved = Path(module_file).resolve(strict=True) if isinstance(module_file, str) else None
    except OSError as exc:
        raise RuntimeError(f"capability dependency {name} cannot be resolved") from exc
    expected = _CAPABILITY_DEPENDENCY_FILES[name].resolve(strict=True)
    if resolved != expected:
        raise RuntimeError(f"capability dependency {name} does not resolve to {expected}")
    return expected


def _fresh_expected_module(name: str, path: Path) -> object:
    expected = path.resolve(strict=True)
    private_name = f"_g56r_treatment_{name}"
    spec = importlib.util.spec_from_file_location(private_name, expected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load capability dependency {name}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[private_name] = module
    sys.modules[name] = module
    spec.loader.exec_module(module)
    if sys.modules.get(name) is not module:
        raise RuntimeError(f"capability dependency {name} replaced itself during loading")
    return module


def _restore_modules(originals: dict[str, object]) -> None:
    for name, module in originals.items():
        if module is _MISSING_MODULE:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = module


def _capability_module() -> object:
    with _CAPABILITY_LOAD_LOCK:
        for name in _CAPABILITY_DEPENDENCY_NAMES:
            existing = sys.modules.get(name)
            if existing is not None:
                _resolved_module_file(existing, name)

        canonical_names = (*_CAPABILITY_DEPENDENCY_NAMES,)
        private_names = tuple(f"_g56r_treatment_{name}" for name in canonical_names)
        facade_name = "_g56r_treatment_codex_capabilities"
        original_modules = {
            name: sys.modules.get(name, _MISSING_MODULE)
            for name in (*canonical_names, *private_names, facade_name)
        }
        loaded: dict[str, object] = {}
        try:
            for name in canonical_names:
                loaded[name] = _fresh_expected_module(name, _CAPABILITY_DEPENDENCY_FILES[name])
            facade_spec = importlib.util.spec_from_file_location(
                facade_name, CAPABILITY_MODULE_PATH.resolve(strict=True),
            )
            if facade_spec is None or facade_spec.loader is None:
                raise RuntimeError("cannot load capability freeze validator")
            facade = importlib.util.module_from_spec(facade_spec)
            sys.modules[facade_name] = facade
            facade_spec.loader.exec_module(facade)
            setattr(
                facade,
                "_treatment_authority_tuple_set",
                getattr(loaded["codex_capability_contract"], "_AuthorityTupleSet"),
            )
            return facade
        finally:
            _restore_modules(original_modules)


def _capability_authority_tuple_set(capability: object, tuples: list[dict]) -> list[dict]:
    factory = getattr(capability, "_treatment_authority_tuple_set", None)
    if not callable(factory):
        raise RuntimeError("capability authority tuple factory is unavailable")
    return factory(tuples)


__all__ = ("CAPABILITY_MODULE_PATH", "_capability_authority_tuple_set", "_capability_module")
