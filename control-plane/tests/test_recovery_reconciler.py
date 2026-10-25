from cloudheal_control_plane.self_healing.recovery_reconciler import (
    reconcile_recovery_attempts,
)


def make_attempt(**overrides):
    attempt = {
        "attempt_id": 7,
        "incident_id": 3,
        "action": "RESTART_DEPLOYMENT",
        "status": "IN_PROGRESS",
        "details": {
            "namespace": "default",
            "deployment": "api",
        },
    }
    attempt.update(overrides)
    return attempt


def healthy_deployment():
    return {
        "desired_replicas": 2,
        "ready_replicas": 2,
        "available_replicas": 2,
        "pods": [
            {"name": "api-1", "phase": "Running", "ready": True},
            {"name": "api-2", "phase": "Running", "ready": True},
        ],
    }


def degraded_deployment():
    return {
        "desired_replicas": 2,
        "ready_replicas": 1,
        "available_replicas": 1,
        "pods": [
            {"name": "api-1", "phase": "Running", "ready": True},
            {"name": "api-2", "phase": "Pending", "ready": False},
        ],
    }


def test_reports_healthy_deployment_without_finalizing_attempt():
    result = reconcile_recovery_attempts(
        get_attempts_fn=lambda: [make_attempt()],
        get_status_fn=lambda namespace, deployment: healthy_deployment(),
    )

    assert result["examined"] == 1
    assert result["healthy"] == 1
    assert result["degraded"] == 0
    assert result["uncertain"] == 0
    assert result["results"][0]["outcome"] == "HEALTHY"
    assert result["results"][0]["reason_code"] == (
        "DEPLOYMENT_CURRENTLY_HEALTHY"
    )


def test_reports_degraded_deployment_without_claiming_recovery_failed():
    result = reconcile_recovery_attempts(
        get_attempts_fn=lambda: [make_attempt()],
        get_status_fn=lambda namespace, deployment: degraded_deployment(),
    )

    assert result["degraded"] == 1
    assert result["uncertain"] == 0
    assert result["results"][0]["outcome"] == "DEGRADED"
    assert result["results"][0]["reason_code"] == (
        "DEPLOYMENT_STILL_DEGRADED"
    )


def test_missing_target_metadata_remains_uncertain():
    def unexpected_status_call(namespace, deployment):
        raise AssertionError(
            "Status lookup should not run without target metadata"
        )

    result = reconcile_recovery_attempts(
        get_attempts_fn=lambda: [make_attempt(details={})],
        get_status_fn=unexpected_status_call,
    )

    assert result["uncertain"] == 1
    assert result["results"][0]["outcome"] == "UNKNOWN"
    assert result["results"][0]["reason_code"] == (
        "TARGET_METADATA_MISSING"
    )


def test_kubernetes_read_failure_remains_uncertain():
    def fail_to_read(namespace, deployment):
        raise RuntimeError("Kubernetes API unavailable")

    result = reconcile_recovery_attempts(
        get_attempts_fn=lambda: [make_attempt()],
        get_status_fn=fail_to_read,
    )

    assert result["uncertain"] == 1
    assert result["results"][0]["outcome"] == "UNKNOWN"
    assert result["results"][0]["reason_code"] == (
        "INFRASTRUCTURE_STATUS_UNAVAILABLE"
    )


def test_empty_attempt_list_returns_zero_counts():
    result = reconcile_recovery_attempts(
        get_attempts_fn=lambda: [],
    )

    assert result == {
        "examined": 0,
        "healthy": 0,
        "degraded": 0,
        "uncertain": 0,
        "results": [],
    }
