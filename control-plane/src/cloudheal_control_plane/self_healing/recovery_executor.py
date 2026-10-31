"""Execute approved Kubernetes recovery actions and persist their outcomes."""

from typing import Any, Callable
import time

from cloudheal_control_plane.database import finish_recovery_attempt
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    restart_deployment,
    get_deployment_status,
    is_kubernetes_rollout_in_progress,
)
from cloudheal_control_plane.self_healing.recovery_coordinator import (
    coordinate_recovery,
)


def execute_recovery(
    detection: dict[str, Any],
    trigger: str = "manual",
    restart_fn: Callable = restart_deployment,
    get_status_fn: Callable = get_deployment_status,
    finish_fn: Callable = finish_recovery_attempt,
    verification_timeout_seconds: float = 30.0,
    poll_interval_seconds: float = 2.0,
    sleep_fn: Callable = time.sleep,
    monotonic_fn: Callable = time.monotonic,
    capacity_available: bool | None = None,
    capacity_required: bool = False,
    is_rollout_in_progress_fn: Callable = is_kubernetes_rollout_in_progress,
) -> dict[str, Any]:
    """Claim, execute, verify, and persist one approved recovery attempt."""

    namespace = detection["namespace"]
    deployment = detection["deployment"]

    # Derive Kubernetes-native rollout state before claiming recovery. A
    # restart must not conflict with a rollout Kubernetes is already
    # progressing. Unavailable status is treated conservatively.
    kubernetes_recovery_in_progress = False
    try:
        preflight_status = get_status_fn(namespace, deployment)
        kubernetes_recovery_in_progress = bool(
            is_rollout_in_progress_fn(preflight_status)
        )
    except Exception:
        kubernetes_recovery_in_progress = True

    claim = coordinate_recovery(
        detection,
        trigger=trigger,
        capacity_available=capacity_available,
        capacity_required=capacity_required,
        kubernetes_recovery_in_progress=kubernetes_recovery_in_progress,
    )

    if not claim["accepted"]:
        return claim

    attempt_id = claim["attempt_id"]

    started_at = monotonic_fn()
    try:
        restart_result = restart_fn(namespace, deployment)
        claim["execution_started"] = True
    except Exception:
        claim["execution_started"] = False
        finish_fn(
            attempt_id=attempt_id,
            status="UNKNOWN",
            reason_code="RESTART_OUTCOME_UNCERTAIN",
            details={
                "namespace": namespace,
                "deployment": deployment,
            },
        )
        return {
            **claim,
            "stage": "EXECUTION",
            "status": "UNKNOWN",
            "reason_code": "RESTART_OUTCOME_UNCERTAIN",
        }

    current = None
    healthy = False
    verification_error = False
    deadline = monotonic_fn() + max(0.0, verification_timeout_seconds)

    while True:
        try:
            current = get_status_fn(namespace, deployment)
            desired = current["desired_replicas"]
            ready = current["ready_replicas"]
            available = current["available_replicas"]
            pods = current["pods"]

            healthy = (
                desired > 0
                and ready >= desired
                and available >= desired
                and bool(pods)
                and all(
                    pod["ready"] and pod["phase"] == "Running"
                    for pod in pods
                )
            )
        except Exception:
            verification_error = True
            current = None
            break

        if healthy or monotonic_fn() >= deadline:
            break

        sleep_fn(min(
            max(0.0, poll_interval_seconds),
            max(0.0, deadline - monotonic_fn()),
        ))

    if healthy:
        outcome = "SUCCEEDED"
        reason_code = "DEPLOYMENT_HEALTHY_AFTER_RESTART"
    elif current is None or verification_error:
        outcome = "UNKNOWN"
        reason_code = "POST_RESTART_VERIFICATION_UNAVAILABLE"
    else:
        outcome = "FAILED"
        reason_code = "DEPLOYMENT_STILL_DEGRADED"

    finish_result = finish_fn(
        attempt_id=attempt_id,
        status=outcome,
        reason_code=reason_code,
        details={
            "namespace": namespace,
            "deployment": deployment,
            "restart_result": restart_result,
            "verification": current,
            "duration_seconds": monotonic_fn() - started_at,
        },
    )

    return {
        **claim,
        "stage": "VERIFICATION",
        "status": outcome,
        "reason_code": reason_code,
        "finish_result": finish_result,
    }
