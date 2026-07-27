"""Shared helpers for selecting isolated treatment replay fixture cases."""

from __future__ import annotations

import copy


def replay_trace(bundle: dict, case_id: str) -> dict:
    slug = case_id.removeprefix("TRACE-").lower()
    return next(
        item for item in bundle["treatment_traces"]
        if item["context"]["turnId"] == f"turn-fixture-{slug}"
    )


def single_treatment_case(bundle: dict, case_id: str) -> dict:
    isolated = copy.deepcopy(bundle)
    trace = replay_trace(isolated, case_id)
    execution_trace_id = trace["objective_binding"]["execution_trace_id"]
    isolated["treatment_traces"] = [trace]
    isolated["controlled_environments"] = [
        item for item in isolated["controlled_environments"]
        if item["controlled_environment_id"] == trace["controlled_environment_id"]
    ]
    isolated["route_resolutions"] = [
        item for item in isolated["route_resolutions"]
        if item["route_resolution_id"] == trace["objective_binding"]["route_resolution_id"]
    ]
    referenced_qualifications = {
        item["prequalification_evidence_id"]
        for item in trace["reroute_destination_assessments"]
        if item["prequalification_evidence_id"] is not None
    }
    isolated["qualification_evidence_registry"] = [
        item for item in isolated["qualification_evidence_registry"]
        if item["qualification_evidence_id"] in referenced_qualifications
    ]
    isolated["fixture_provenance"]["expected_dispositions"] = [{
        "execution_trace_id": execution_trace_id,
        "treatment_disposition": trace["treatment_disposition"],
    }]
    return isolated
