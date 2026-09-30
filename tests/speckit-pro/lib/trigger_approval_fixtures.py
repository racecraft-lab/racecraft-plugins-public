"""Retained-conversation observations shared by the trigger campaign approval tests."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class RetainedConversation:
    """One retained session whose messages a trusted orchestrator observed."""

    session: str
    request_id: str
    response_id: str
    ordinals: tuple[int, int]
    line_prefix: str = "retained"

    def observation(self, role: str, message_id: str, position: tuple[str, int], content: str) -> dict:
        timestamp, ordinal = position
        return {
            "role": role, "message_id": message_id, "session_id": self.session,
            "timestamp": timestamp, "source_ordinal": ordinal, "content": content,
            "content_sha256": hashlib.sha256(content.encode()).hexdigest(),
            "source_line_sha256": hashlib.sha256(
                f"{self.line_prefix}:{message_id}:{content}".encode()).hexdigest(),
        }

    def contextual_approval(self, digest: str, budget: int, response: str) -> dict:
        """A v2 approval: the assistant's request and the user's adjacent reply."""
        request = f"Approve trigger campaign {digest} with launch budget {budget}."
        request_ordinal, response_ordinal = self.ordinals
        return {
            "schema_version": "trigger-campaign-approval/v2", "manifest_sha256": digest,
            "launch_budget": budget, "recorder_observation": {
                "observer": "trusted-orchestrator", "session_id": self.session,
                "adjacent_user_visible_message_ids": [self.request_id, self.response_id],
                "request": self.observation("assistant", self.request_id,
                                            ("2026-09-14T16:00:00.000Z", request_ordinal), request),
                "response": self.observation("user", self.response_id,
                                             ("2026-09-14T16:00:01.000Z", response_ordinal), response),
            },
        }
