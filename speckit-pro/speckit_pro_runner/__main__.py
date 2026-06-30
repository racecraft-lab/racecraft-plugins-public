"""Module entrypoint for ``python -m speckit_pro_runner``."""

from __future__ import annotations

import sys

from . import RUNNER_CONTRACT_ID, RUNNER_VERSION
from .envelope import emit_response, input_error, parse_request, response
from .runtime import handle_request


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--help"]:
        print("Usage: python -m speckit_pro_runner < request.json")
        print("Reads one JSON request from stdin and writes one JSON response to stdout.")
        return 0
    if args == ["--version"]:
        print(f"{RUNNER_CONTRACT_ID} {RUNNER_VERSION}")
        return 0
    if args:
        return emit_response(input_error("invalid_envelope", "runner argv is reserved for --help and --version"))

    raw_stdin = sys.stdin.read()
    request, error = parse_request(raw_stdin)
    if error is not None:
        return emit_response(error)
    try:
        body = handle_request(request)
    except Exception as exc:  # pragma: no cover - defensive contract boundary
        body = response(
            "internal_failure",
            request_id=request.request_id if request else None,
            diagnostics=[
                {
                    "severity": "error",
                    "source": "runner",
                    "code": "internal_failure",
                    "message": "runner encountered an unexpected internal failure",
                    "remediation": {
                        "summary": "Report the runner failure with the request shape and traceback context.",
                        "actions": ["Re-run with the same request after inspecting the local traceback."],
                    },
                    "details": {"exception_type": type(exc).__name__},
                }
            ],
        )
    return emit_response(body)


if __name__ == "__main__":
    raise SystemExit(main())
