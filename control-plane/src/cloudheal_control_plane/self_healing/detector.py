from datetime import UTC, datetime
from typing import Callable

from cloudheal_control_plane.database import (
    observe_incident,
    record_event,
    resolve_incident,
)


def detect_deployment_incident(
    namespace: str,
    deployment_name: str,
    get_deployment_status: Callable[[str, str], dict],
    observe_incident_fn: Callable = observe_incident,
    record_event_fn: Callable = record_event,
    resolve_incident_fn: Callable = resolve_incident,
) -> dict:
    """Detect deployment degradation independently of the infrastructure provider."""

    observed_at = datetime.now(UTC).isoformat()

    deployment = get_deployment_status(namespace, deployment_name)

    desired = deployment["desired_replicas"]
    ready = deployment["ready_replicas"]
    available = deployment["available_replicas"]

    unhealthy_pods = [
        {
            "name": pod["name"],
            "phase": pod["phase"],
            "ready": pod["ready"],
            "containers": pod["containers"],
        }
        for pod in deployment["pods"]
        if not pod["ready"] or pod["phase"] != "Running"
    ]

    reasons = []

    if ready < desired:
        reasons.append("READY_REPLICAS_BELOW_DESIRED")

    if available < desired:
        reasons.append("AVAILABLE_REPLICAS_BELOW_DESIRED")

    if unhealthy_pods:
        reasons.append("UNHEALTHY_PODS_PRESENT")

    max_restart_count = 0
    for pod in deployment["pods"]:
        for container in pod.get("containers", []):
            max_restart_count = max(
                max_restart_count,
                int(container.get("restart_count") or 0),
            )

    crash_loop_detected = max_restart_count >= 5
    if crash_loop_detected:
        reasons.append("CRASH_LOOP_DETECTED")

    evidence = {
        "desired_replicas": desired,
        "ready_replicas": ready,
        "available_replicas": available,
        "unhealthy_pods": unhealthy_pods,
        "max_restart_count": max_restart_count,
        "crash_loop_detected": crash_loop_detected,
        "reasons": reasons,
    }

    resource_key = f"kubernetes:deployment:{namespace}:{deployment_name}"

    if not reasons:
        resolved_incident = resolve_incident_fn(
            resource_key=resource_key,
            resolved_at=observed_at,
        )

        resolution_blocked = (
            isinstance(resolved_incident, dict)
            and resolved_incident.get("resolution_blocked") is True
        )

        if (
            isinstance(resolved_incident, dict)
            and resolved_incident.get("status") == "RESOLVED"
        ):
            record_event_fn(
                event_type="KUBERNETES_DEPLOYMENT_HEALTHY",
                details={
                    "namespace": namespace,
                    "deployment": deployment_name,
                    "observed_at": observed_at,
                    "resolved_incident_id": resolved_incident["incident_id"],
                },
            )

        return {
            "incident_detected": False,
            "classification": "HEALTHY",
            "namespace": namespace,
            "deployment": deployment_name,
            "observed_at": observed_at,
            "incident": resolved_incident,
            "resolution_blocked": resolution_blocked,
            "evidence": evidence,
        }

    incident = observe_incident_fn(
        resource_key=resource_key,
        classification="DEPLOYMENT_DEGRADED",
        evidence=evidence,
        observed_at=observed_at,
    )

    return {
        "incident_detected": True,
        "classification": "DEPLOYMENT_DEGRADED",
        "namespace": namespace,
        "deployment": deployment_name,
        "observed_at": observed_at,
        "incident": incident,
        "evidence": evidence,
    }