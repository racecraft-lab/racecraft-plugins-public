"""A real counter implementation with an atomic state/event trace snapshot."""

from __future__ import annotations

import json
import sys


class Counter:
    def __init__(self, start: int, limit: int):
        if start > limit:
            raise ValueError("start must not exceed limit")
        self.count = start
        self.limit = limit

    def advance(self) -> tuple[str, int]:
        action = "hold"
        if self.count < self.limit:
            self.count += 1
            action = "increment"
        return action, self.count


def trace(start: int, limit: int) -> dict:
    counter = Counter(start, limit)
    states = [{"#meta": {"index": 0}, "count": {"#bigint": str(start)}}]
    for index in range(1, 4):
        action, count = counter.advance()
        states.append({"#meta": {"index": index, "action": action}, "count": {"#bigint": str(count)}})
    return {"vars": ["count"], "states": states}


if __name__ == "__main__":
    start, limit = map(int, sys.argv[1:] or ("0", "2"))
    print(json.dumps(trace(start, limit), allow_nan=False, sort_keys=True))
