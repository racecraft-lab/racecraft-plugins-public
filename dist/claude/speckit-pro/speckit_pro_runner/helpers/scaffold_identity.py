"""One branch identity for scaffold on every host."""

from __future__ import annotations

import re
import unicodedata
from typing import Any

from ..envelope import response
from ..spec_identity import normalize_spec_identity
from ..strict_input import SelectionError, has_hidden_characters, require_fields, require_text


def derive_scaffold_branch(inputs: dict[str, Any]) -> str:
    require_fields(inputs, {"spec_id", "spec_name"}, "derive-scaffold-branch inputs")
    spec_id = require_text(inputs["spec_id"], "spec_id")
    identity = normalize_spec_identity(spec_id)
    if re.fullmatch(r"[a-z]+ [0-9]{3}[a-z]?", identity) is None or identity.replace(" ", "-") != spec_id.lower():
        raise SelectionError("spec_id must be an ASCII letter namespace followed by three ASCII digits and an optional letter suffix")
    namespace, number = identity.split(" ", 1)
    prefix = number if namespace == "spec" else f"{namespace}-{number}"
    spec_name = require_text(inputs["spec_name"], "spec_name")
    if has_hidden_characters(spec_name):
        raise SelectionError("spec_name must not contain hidden characters")
    ascii_name = unicodedata.normalize("NFKD", spec_name).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    if not slug:
        raise SelectionError("spec_name must contain an ASCII letter or digit after normalization")
    return f"{prefix}-{slug}"


def run_scaffold_branch_helper(entry: Any, request: Any) -> dict[str, Any]:
    status = "ok"
    try:
        data: dict[str, Any] = {"branch_name": derive_scaffold_branch(request.inputs)}
    except SelectionError as exc:
        status = "input_error"
        data = {"verdict": "stop", "problems": [str(exc)]}
    return response(status, request_id=request.request_id, data=data)
