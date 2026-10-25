from typing import Any


SUPPORTED_ACTIONS = {
    "RESTART_DEPLOYMENT",
}


def evaluate_recovery_action(
    incident: dict[str, Any] | None,
    action: str,
    recovery_in_progress: bool = False,
) -> dict[str, Any]:
    """Evaluate whether a proposed recovery action is safe to permit."""

    def blocked(reason_code: str, message: str) -> dict[str, Any]:
        return {
            "allowed": False,
            "action": action,
            "reason_code": reason_code,
            "reason": message,
        }

    # 1. Reject unsupported actions.
    if action not in SUPPORTED_ACTIONS:
        return blocked(
            "UNSUPPORTED_ACTION",
            "The requested recovery action is not supported.",
        )

    # 2. Reject duplicate recovery attempts.
    if recovery_in_progress:
        return blocked(
            "RECOVERY_ALREADY_IN_PROGRESS",
            "A recovery attempt is already in progress.",
        )

    # 3. Require a valid incident.
    if not isinstance(incident, dict):
        return blocked(
            "INVALID_INCIDENT",
            "A valid incident is required.",
        )

    # 4. Only recover incidents that remain open.
    if incident.get("status") != "OPEN":
        return blocked(
            "INCIDENT_NOT_OPEN",
            "Recovery requires an open incident.",
        )

    # 5. Only handle the classification we explicitly support.
    if incident.get("classification") != "DEPLOYMENT_DEGRADED":
        return blocked(
            "UNSUPPORTED_CLASSIFICATION",
            "This incident classification is not supported.",
        )

    # 6. Require evidence explaining the degradation.
    evidence = incident.get("evidence")

    if not isinstance(evidence, dict):
        return blocked(
            "MISSING_EVIDENCE",
            "Incident evidence is missing or invalid.",
        )

    reasons = evidence.get("reasons")

    if not isinstance(reasons, list) or not reasons:
        return blocked(
            "MISSING_EVIDENCE",
            "No degradation reasons were provided.",
        )

    # All current policy checks passed.
    return {
        "allowed": True,
        "action": action,
        "reason_code": "POLICY_APPROVED",
        "reason": "The action passed the current recovery policy checks.",
    }