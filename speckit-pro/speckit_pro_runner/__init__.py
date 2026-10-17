"""SpecKit Pro cross-platform runner foundation."""

RUNNER_NAME = "speckit_pro_runner"
RUNNER_CONTRACT_ID = "speckit-pro-runner"
SELECTED_RUNTIME_NAME = "python-stdlib-runner"
CONTRACT_VERSION = "1.0"
RUNNER_VERSION = "0.1.0"
PYTHON_MINIMUM = (3, 11)
SOURCE_CONTEXT = "source_checkout"

UNKNOWN_DISPATCH_IDS_FIELD = "unknown_dispatch_ids"
BLOCKED_BY_FIELD = "blocked_by"
EXECUTION_HISTORY_COUNT_FIELDS = ((UNKNOWN_DISPATCH_IDS_FIELD, "unknown_dispatch_count"),
                                  (BLOCKED_BY_FIELD, "blocked_by_count"),
                                  ("completed_dispatch_ids", "completed_dispatch_count"))
