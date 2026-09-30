"""Frozen evidence pins and arithmetic for the reviewed 217-case trigger campaign.

The generic admission and validation logic lives in ``trigger_carry_forward``,
``trigger_campaign`` and ``trigger_comparison``. Everything specific to one
historical campaign, meaning digests, case ids and counts, lives only here, and
every count that follows from another is derived from it. Nothing here imports
another trigger module, so each of them can read it.
"""
from __future__ import annotations

OLD_OBSERVER_SHA256 = "c5faa93ab3c25340e38933b69ba1968835a501ff78a4344354f5c36e45470a72"
PARTIAL_EXPERIMENT_SHA256 = "959b2740ff161e155f5d1f5d645944a7f603d614479a92b3c056c29bafb96f51"
BEHAVIOR_FAILURES = frozenset({
    "l2-1b43ca2d753dec02b20c5e17",
    "l2-d714c484e5bbf90475418772",
})
PARTIAL_CASE_ID = "l2-f714040c928fadaabb26eab2"
EXPECTED_RAW_SHA256 = {
    "manifest": "32189f6581d6b78b1910305755b3107421fb13f3d6c9f7faf5c8b7bb8f36a98b",
    "approval": "54b0c442743c6d53bd6615795692239f44f464fc598d78d4fb155a7e68c98afb",
    "ledger": "933372dd5118219b83d79f537049e9a46345d626f651342fb4b934105103cddc",
    "interrupted_ledger": "432a3afbf6cdc39723e49f047c70ed66e3fe9a8f24dfacd3388cba54b8e04c5a",
    "terminal_evidence": "913c1b9063ce98d49f43a119115b9dc4b069aa8d22a0ff50f168d6e444979f17",
    "terminal_review": "7170f3429f8c81c2d34f545e6d48f0ae43392c0d2de368a6a881fc0d1f2b215a",
    "cohort": "3f2bcbf40d4424da12764d23843d40d177006a5d21db3da386a50216acd2cdc8",
    "partial_index": "3b4282e2d4df37bf69c15aff00d56f693ede851f3b4fd19dc0b11ab01c2eb6d5",
    "source_stability_review": "e079e1dc4b7aa86c1abc7291cb2e45194a60e4ce9cdf04a7f6b44e56ec65a201",
    "compatibility_review": "10fadc231a41c23298802aab8f847745bd00b19652ce07bbad7b43ab1c5337bb",
    "terminal_cleanup": "161a9e8ace4f9116a9ee9f5d48af3f77a8001bb23c534fab7d1a90dfa28fa49a",
    "terminal_launch": "772151829c4aa62686545046b92600897d2d1fd731bb67a674aa58d2f411afdf",
}
EXPECTED_TERMINAL_TRIAL_SHA256 = [
    "6faec4e8785907fa491a07a68375a8ec3c421c6bc0a0413591b92485daecf42b",
    "ce6895049987bb7414cecbd8a219a7fd4c6c8521bc52cd8448642822380e2a9a",
    "832f2926c955b73bef82d8d168c8a1947e516d10ff081ef2172bedf8190a6621",
]

LOGICAL_CASES = 217
TRIALS_PER_CASE = 3
ARM_COUNT = 2
LOGICAL_FULL_TRIALS = LOGICAL_CASES * TRIALS_PER_CASE * ARM_COUNT
CARRIED_CASES = 137
CARRIED_TRIALS = CARRIED_CASES * TRIALS_PER_CASE
FRESH_CASES = LOGICAL_CASES - CARRIED_CASES
FRESH_PAIRS = FRESH_CASES + LOGICAL_CASES
FRESH_LAUNCH_CEILING = LOGICAL_FULL_TRIALS - CARRIED_TRIALS
TERMINAL_RESERVED_CASES = CARRIED_CASES + 1
HISTORICAL_CHARGED_LAUNCHES = 414
TERMINAL_INVALID_TRIALS = TRIALS_PER_CASE
CARRIED_DISTINCT_GROUPS = 410
MAXIMUM_TOTAL_CHARGED_ATTEMPTS = HISTORICAL_CHARGED_LAUNCHES + FRESH_LAUNCH_CEILING
EXPECTED_ACCOUNTING = {
    "logical_full_trials": LOGICAL_FULL_TRIALS,
    "carried_trials": CARRIED_TRIALS,
    "fresh_launch_ceiling": FRESH_LAUNCH_CEILING,
    "historical_charged_launches": HISTORICAL_CHARGED_LAUNCHES,
    "maximum_total_charged_attempts": MAXIMUM_TOTAL_CHARGED_ATTEMPTS,
}
