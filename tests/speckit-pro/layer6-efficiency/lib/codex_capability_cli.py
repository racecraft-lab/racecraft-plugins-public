#!/usr/bin/env python3
"""Command-line dispatch for capability evidence workflows."""

from __future__ import annotations

if __package__:
    from .codex_capability_publish_io import *
else:
    from codex_capability_publish_io import *

def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    refresh = sub.add_parser("refresh-sources"); refresh.add_argument("--manifest", required=True); refresh.add_argument("--captured-refresh", required=True); refresh.add_argument("--raw-evidence-root", required=True); refresh.add_argument("--output", required=True)
    identify = sub.add_parser("identify-client"); identify.add_argument("--reported-version", required=True); group = identify.add_mutually_exclusive_group(required=True); group.add_argument("--build-id"); group.add_argument("--executable"); identify.add_argument("--distribution", required=True); identify.add_argument("--output", required=True)
    collect = sub.add_parser("collect"); collect.add_argument("--surface", choices=SURFACES, required=True); collect.add_argument("--client-identity", required=True); collect.add_argument("--raw-evidence-root", required=True); collect.add_argument("--work-item-kind", choices=("task", "fixture", "objective"), required=True); collect.add_argument("--work-item-id", required=True); collect.add_argument("--output", required=True)
    canary = sub.add_parser("canary"); canary.add_argument("--manifest", required=True); canary.add_argument("--freeze", required=True); canary.add_argument("--model", required=True); canary.add_argument("--effort", required=True); canary.add_argument("--executor-result", required=True); canary.add_argument("--raw-evidence-root", required=True); canary.add_argument("--published-at"); canary.add_argument("--expected-telemetry-profile-id"); canary.add_argument("--expected-treatment-contract-digest"); canary.add_argument("--expected-treatment-evidence-digest"); canary.add_argument("--output", required=True)
    freeze = sub.add_parser("freeze"); freeze.add_argument("--manifest", required=True); freeze.add_argument("--source-refresh", required=True); freeze.add_argument("--client-identity", required=True); freeze.add_argument("--app-server", required=True); freeze.add_argument("--cli", required=True); freeze.add_argument("--interactive-picker", required=True); freeze.add_argument("--raw-evidence-root", required=True); freeze.add_argument("--aliases"); freeze.add_argument("--predecessor-freeze"); freeze.add_argument("--expected-predecessor-telemetry-profile-id"); freeze.add_argument("--expected-predecessor-treatment-contract-digest"); freeze.add_argument("--expected-predecessor-treatment-evidence-digest"); freeze.add_argument("--published-at"); freeze.add_argument("--output", required=True)
    published = sub.add_parser("validate-freeze"); published.add_argument("--manifest", required=True); published.add_argument("--freeze", required=True); published.add_argument("--predecessor-freeze"); published.add_argument("--expected-telemetry-profile-id"); published.add_argument("--expected-treatment-contract-digest"); published.add_argument("--expected-treatment-evidence-digest"); published.add_argument("--expected-predecessor-telemetry-profile-id"); published.add_argument("--expected-predecessor-treatment-contract-digest"); published.add_argument("--expected-predecessor-treatment-evidence-digest")
    retention = sub.add_parser("retention"); retention.add_argument("--raw-evidence-root", required=True); retention.add_argument("--as-of"); retention.add_argument("--mode", choices=("verify", "cleanup"), default="verify"); retention.add_argument("--output", required=True)
    args, repo = parser.parse_args(argv), Path(__file__).resolve().parents[4]
    now = lambda: datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if args.command == "refresh-sources":
        _, capture_bytes = read_content_addressed_private_file(args.captured_refresh, repo, "captured refresh")
        capture_digest, _ = materialize_source_capture(args.raw_evidence_root, repo, capture_bytes)
        output, output_parent_identity = _private_external_file_binding(
            args.output, repo, "normalized refresh output", output=True,
        )
        _write(
            output,
            normalize_source_refreshes(
                _read(args.manifest), _parse_json_bytes(capture_bytes),
                source_capture_digest=capture_digest,
            ),
            private=True, expected_parent_identity=output_parent_identity,
        ); return 0
    if args.command == "identify-client":
        kind, identifier = ("vendor_build_id", args.build_id) if args.build_id else ("executable_sha256", digest_regular_file(args.executable))
        _write(args.output, build_client_identity({"reported_version": args.reported_version, "build_identifier_kind": kind, "build_identifier": identifier, "distribution": args.distribution})); return 0
    if args.command == "collect":
        validate_raw_evidence_root(args.raw_evidence_root, repo); identity = build_client_identity(_read(args.client_identity))
        binding = repository_binding_from_checkout(repo); work_item = validate_work_item({"kind": args.work_item_kind, "id": args.work_item_id})
        captured_at = now(); raw_digest, _ = materialize_unknown_capture(args.raw_evidence_root, repo, args.surface, identity["client_identity_id"], binding, work_item, captured_at)
        _write(args.output, unknown_observation(args.surface, identity["client_identity_id"], binding, work_item, raw_evidence_digest=raw_digest, captured_at=captured_at)); return 0
    if args.command == "canary":
        raise ValueError(
            "trusted canary invocation and attestation are unavailable in this slice; "
            "caller-supplied executor results cannot establish provenance"
        )
    if args.command == "validate-freeze":
        predecessor = _read(args.predecessor_freeze, require_canonical=True) if args.predecessor_freeze else None
        binding_arguments = (
            args.expected_telemetry_profile_id,
            args.expected_treatment_contract_digest,
            args.expected_treatment_evidence_digest,
        )
        if any(value is None for value in binding_arguments) and any(value is not None for value in binding_arguments):
            raise ValueError("treatment-aware freeze validation requires all three expected binding arguments")
        predecessor_binding_arguments = (
            args.expected_predecessor_telemetry_profile_id,
            args.expected_predecessor_treatment_contract_digest,
            args.expected_predecessor_treatment_evidence_digest,
        )
        if any(value is None for value in predecessor_binding_arguments) and any(value is not None for value in predecessor_binding_arguments):
            raise ValueError("treatment-aware predecessor validation requires all three expected binding arguments")
        validate_freeze(
            _read(args.freeze, require_canonical=True), _read(args.manifest), predecessor=predecessor,
            expected_telemetry_profile_id=args.expected_telemetry_profile_id,
            expected_treatment_contract_digest=args.expected_treatment_contract_digest,
            expected_treatment_evidence_digest=args.expected_treatment_evidence_digest,
            expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
            expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
            expected_predecessor_treatment_evidence_digest=args.expected_predecessor_treatment_evidence_digest,
        ); return 0
    if args.command == "retention":
        if args.mode == "verify" and args.as_of is None: raise ValueError("retention verification requires --as-of")
        if args.mode == "cleanup" and args.as_of is not None: raise ValueError("retention cleanup uses current UTC and does not accept --as-of")
        output, output_parent_identity = _private_external_file_binding(
            args.output, repo, "retention report output", output=True,
        )
        report = reconcile_raw_evidence_retention(args.raw_evidence_root, repo, args.as_of, apply=args.mode == "cleanup")
        _write(output, report, private=True, expected_parent_identity=output_parent_identity); return 0
    _, source_refresh_bytes = read_private_external_file(args.source_refresh, repo, "normalized source refresh")
    manifest, refreshes, identity = _read(args.manifest), _parse_json_bytes(source_refresh_bytes), build_client_identity(_read(args.client_identity)); validate_source_refreshes(manifest, refreshes)
    tuples = candidate_tuples_from_manifest(manifest, refreshes)
    aliases = _read(args.aliases) if args.aliases else {}
    matrix, decisions = evaluate_surface_matrix([_read(args.app_server), _read(args.cli), _read(args.interactive_picker)], tuples, aliases=aliases)
    predecessor = _read(args.predecessor_freeze, require_canonical=True) if args.predecessor_freeze else None
    predecessor_binding_arguments = (
        args.expected_predecessor_telemetry_profile_id,
        args.expected_predecessor_treatment_contract_digest,
        args.expected_predecessor_treatment_evidence_digest,
    )
    if any(value is None for value in predecessor_binding_arguments) and any(value is not None for value in predecessor_binding_arguments):
        raise ValueError("treatment-aware predecessor validation requires all three expected binding arguments")
    result = build_freeze(
        identity, refreshes, matrix, decisions, args.published_at or now(), manifest=manifest, predecessor=predecessor,
        raw_evidence_root=args.raw_evidence_root, repository_root=repo,
        expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
        expected_predecessor_treatment_evidence_digest=args.expected_predecessor_treatment_evidence_digest,
    )
    publish_with_raw_evidence_retention(
        result, args.output, args.raw_evidence_root, repo, manifest=manifest, predecessor=predecessor,
        expected_predecessor_telemetry_profile_id=args.expected_predecessor_telemetry_profile_id,
        expected_predecessor_treatment_contract_digest=args.expected_predecessor_treatment_contract_digest,
        expected_predecessor_treatment_evidence_digest=args.expected_predecessor_treatment_evidence_digest,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

__all__ = [name for name in globals() if not name.startswith("__")]
