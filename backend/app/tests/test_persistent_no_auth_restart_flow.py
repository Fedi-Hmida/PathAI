import os
from dataclasses import dataclass

import pytest

TRUE_VALUES = {"1", "true", "yes", "on"}
RUN_RESTART_TESTS_FLAG = "PATHAI_RUN_PERSISTENCE_RESTART_TESTS"
PERSISTENCE_BACKEND_FLAG = "PATHAI_PERSISTENCE_BACKEND"
MONGO_REPOSITORIES_FLAG = "PATHAI_MONGO_REPOSITORIES_ENABLED"

# Backend-Persistence-5 creates the guarded validation harness only. Flip this
# only when Mongo-backed repositories exist and fake repositories are no longer
# the runtime storage for this restart test.
MONGO_BACKED_REPOSITORIES_IMPLEMENTED = False

PERSISTENT_RESTART_FLOW_STEPS = [
    "create assessment",
    "finalize knowledge map",
    "generate curriculum",
    "attach resources",
    "run critic review",
    "initialize and update progress",
    "generate and submit quiz",
    "run adapter check and replan",
    "run evaluation sample",
    "restart backend or cross a real process boundary",
    "fetch the same IDs again",
    "assert records survived",
]


@dataclass(frozen=True)
class PersistenceRestartReadiness:
    can_run: bool
    reason: str


def _flag_enabled(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in TRUE_VALUES


def _persistence_restart_readiness() -> PersistenceRestartReadiness:
    if not _flag_enabled(RUN_RESTART_TESTS_FLAG):
        return PersistenceRestartReadiness(
            can_run=False,
            reason=(
                f"Set {RUN_RESTART_TESTS_FLAG}=true only after Mongo-backed "
                "repositories and a persistent backend are available."
            ),
        )

    persistence_backend = os.getenv(PERSISTENCE_BACKEND_FLAG, "").strip().lower()
    if persistence_backend != "mongodb":
        return PersistenceRestartReadiness(
            can_run=False,
            reason=f"Set {PERSISTENCE_BACKEND_FLAG}=mongodb for restart durability tests.",
        )

    if not _flag_enabled(MONGO_REPOSITORIES_FLAG):
        return PersistenceRestartReadiness(
            can_run=False,
            reason=(
                f"Set {MONGO_REPOSITORIES_FLAG}=true only when runtime services use "
                "Mongo-backed repositories."
            ),
        )

    if not MONGO_BACKED_REPOSITORIES_IMPLEMENTED:
        return PersistenceRestartReadiness(
            can_run=False,
            reason=(
                "Mongo-backed repositories are not implemented yet; fake repositories "
                "cannot prove backend restart durability."
            ),
        )

    return PersistenceRestartReadiness(can_run=True, reason="Persistent backend ready.")


def test_persistent_restart_harness_documents_required_flow() -> None:
    assert PERSISTENT_RESTART_FLOW_STEPS == [
        "create assessment",
        "finalize knowledge map",
        "generate curriculum",
        "attach resources",
        "run critic review",
        "initialize and update progress",
        "generate and submit quiz",
        "run adapter check and replan",
        "run evaluation sample",
        "restart backend or cross a real process boundary",
        "fetch the same IDs again",
        "assert records survived",
    ]


def test_persistent_no_auth_restart_flow_is_guarded_until_real_persistence() -> None:
    readiness = _persistence_restart_readiness()
    if not readiness.can_run:
        pytest.skip(readiness.reason)

    pytest.fail(
        "Persistent restart validation must be implemented with a real Mongo-backed "
        "repository runtime and backend restart control before this test can pass."
    )
