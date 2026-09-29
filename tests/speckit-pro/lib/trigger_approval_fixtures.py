"""Retained-conversation observations shared by the trigger campaign approval tests."""
from __future__ import annotations

import hashlib


def observation(
    role: str, message_id: str, session: str, timestamp: str, ordinal: int, content: str,
    *, line_prefix: str = "retained",
) -> dict:
    """One trusted-orchestrator observation of a retained conversation message."""
    return {
        "role": role, "message_id": message_id, "session_id": session,
        "timestamp": timestamp, "source_ordinal": ordinal, "content": content,
        "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
        "source_line_sha256": hashlib.sha256(f"{line_prefix}:{message_id}:{content}".encode()).hexdigest(),
    }


def contextual_approval(
    digest: str, budget: int, response: str, *, session: str, request_id: str, response_id: str,
    ordinals: tuple[int, int], line_prefix: str = "retained",
) -> dict:
    """A v2 approval: the assistant's request and the user's adjacent reply."""
    request = f"Approve trigger campaign {digest} with launch budget {budget}."
    request_ordinal, response_ordinal = ordinals
    return {
        "schema_version": "trigger-campaign-approval/v2", "manifest_sha256": digest,
        "launch_budget": budget, "recorder_observation": {
            "observer": "trusted-orchestrator", "session_id": session,
            "adjacent_user_visible_message_ids": [request_id, response_id],
            "request": observation("assistant", request_id, session, "2026-09-14T16:00:00.000Z",
                                   request_ordinal, request, line_prefix=line_prefix),
            "response": observation("user", response_id, session, "2026-09-14T16:00:01.000Z",
                                    response_ordinal, response, line_prefix=line_prefix),
        },
    }
