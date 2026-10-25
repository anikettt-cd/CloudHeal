from typing import Any, Callable

from cloudheal_control_plane.database import get_unresolved_recovery_attempts
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)

def reconcile_recovery_attempts(
    get_attempts_fn: Callable = get_unresolved_recovery_attempts,
    get_status_fn: Callable = get_deployment_status,
) -> dict[str, Any]:


    attempts = get_attempts_fn()
    summary = {
        "examined": len(attempts),
        "healthy": 0,
        "degraded": 0,
        "uncertain": 0,
        "results": [],
    }
    for attempt in attempts:
        details = attempt.get("details", {})
        namespace = details.get("namespace")
        deployment_name = details.get("deployment")
        if not namespace or not deployment_name:
            outcome = "UNKNOWN"
            reason_code = "TARGET_METADATA_MISSING"
            summary["uncertain"] += 1
        else:
            try:
                deployment = get_status_fn(namespace, deployment_name)
                desired = deployment["desired_replicas"]
                ready = deployment["ready_replicas"]
                available = deployment["available_replicas"]
                pods = deployment["pods"]
                healthy = (
                    ready >= desired
                    and available >= desired
                    and all(
                        pod["ready"] and pod["phase"] == "Running"
                        for pod in pods
                    )
                )
                if healthy:
                    outcome = "HEALTHY"
                    reason_code = "DEPLOYMENT_CURRENTLY_HEALTHY"
                    summary["healthy"] += 1
                else:
                    outcome = "DEGRADED"
                    reason_code = "DEPLOYMENT_STILL_DEGRADED"
                    summary["degraded"] += 1
            except Exception:
                outcome = "UNKNOWN"
                reason_code = "INFRASTRUCTURE_STATUS_UNAVAILABLE"
                summary["uncertain"] += 1
        summary["results"].append(
            {
                "attempt_id": attempt["attempt_id"],
                "outcome": outcome,
                "reason_code": reason_code,
            }
        )
    return summary
