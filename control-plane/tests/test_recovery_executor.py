from unittest.mock import Mock, patch

from cloudheal_control_plane.self_healing.recovery_executor import (
    execute_recovery,
)


def make_detection():
    return {
        "namespace": "cloudheal-test",
        "deployment": "demo",
        "incident": {
            "id": 7,
            "status": "OPEN",
            "classification": "DEPLOYMENT_DEGRADED",
        },
        "evidence": {"reasons": ["replicas_not_ready"]},
    }


def healthy_status():
    return {
        "desired_replicas": 1,
        "ready_replicas": 1,
        "available_replicas": 1,
        "pods": [
            {"name": "demo-pod", "phase": "Running", "ready": True},
        ],
    }


CLAIM = {
    "accepted": True,
    "attempt_id": 42,
    "incident_id": 7,
    "action": "RESTART_DEPLOYMENT",
    "status": "IN_PROGRESS",
    "execution_started": False,
}


@patch(
    "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
    side_effect=lambda *args, **kwargs: CLAIM.copy(),
)
def test_successful_restart_is_verified_and_persisted(_claim):
    restart = Mock(return_value={"accepted": True})
    status = Mock(return_value=healthy_status())
    finish = Mock(return_value={"updated": True})

    result = execute_recovery(
        make_detection(),
        restart_fn=restart,
        get_status_fn=status,
        finish_fn=finish,
    )

    assert result["accepted"] is True
    assert result["status"] == "SUCCEEDED"
    assert result["execution_started"] is True
    restart.assert_called_once_with("cloudheal-test", "demo")
    finish.assert_called_once()
    assert finish.call_args.kwargs["status"] == "SUCCEEDED"


@patch(
    "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
    side_effect=lambda *args, **kwargs: CLAIM.copy(),
)
def test_restart_exception_keeps_outcome_unknown(_claim):
    restart = Mock(side_effect=RuntimeError("connection lost"))
    status = Mock()
    finish = Mock(return_value={"updated": True})

    result = execute_recovery(
        make_detection(),
        restart_fn=restart,
        get_status_fn=status,
        finish_fn=finish,
    )

    assert result["status"] == "UNKNOWN"
    assert result["execution_started"] is False
    status.assert_not_called()
    assert finish.call_args.kwargs["status"] == "UNKNOWN"


@patch(
    "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
    side_effect=lambda *args, **kwargs: CLAIM.copy(),
)
def test_verification_failure_keeps_outcome_unknown(_claim):
    restart = Mock(return_value={"accepted": True})
    status = Mock(side_effect=RuntimeError("API unavailable"))
    finish = Mock(return_value={"updated": True})

    result = execute_recovery(
        make_detection(),
        restart_fn=restart,
        get_status_fn=status,
        finish_fn=finish,
    )

    assert result["status"] == "UNKNOWN"
    assert finish.call_args.kwargs["status"] == "UNKNOWN"


@patch(
    "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
    side_effect=lambda *args, **kwargs: CLAIM.copy(),
)
def test_degraded_deployment_is_recorded_as_failed(_claim):
    restart = Mock(return_value={"accepted": True})
    status = Mock(return_value={
        "desired_replicas": 1,
        "ready_replicas": 0,
        "available_replicas": 0,
        "pods": [
            {"name": "demo-pod", "phase": "Pending", "ready": False},
        ],
    })
    finish = Mock(return_value={"updated": True})

    result = execute_recovery(
        make_detection(),
        restart_fn=restart,
        get_status_fn=status,
        finish_fn=finish,
        verification_timeout_seconds=0,
    )

    assert result["status"] == "FAILED"
    assert finish.call_args.kwargs["status"] == "FAILED"


@patch(
    "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
    return_value={"accepted": False, "reason_code": "TEST_STOP"},
)
def test_automatic_trigger_is_forwarded_to_coordinator(mock_coordinator):
    result = execute_recovery(
        make_detection(),
        trigger="automatic",
    )

    assert result["accepted"] is False
    mock_coordinator.assert_called_once_with(
        make_detection(),
        trigger="automatic",
    )


def test_degraded_deployment_stops_verifying_at_deadline():
    class FakeClock:
        now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, seconds):
            self.now += seconds

    clock = FakeClock()
    restart = Mock(return_value={"accepted": True})
    status = Mock(return_value={
        "desired_replicas": 1,
        "ready_replicas": 0,
        "available_replicas": 0,
        "pods": [
            {"name": "demo-pod", "phase": "Pending", "ready": False},
        ],
    })
    finish = Mock(return_value={"updated": True})

    with patch(
        "cloudheal_control_plane.self_healing.recovery_executor.coordinate_recovery",
        side_effect=lambda *args, **kwargs: CLAIM.copy(),
    ):
        result = execute_recovery(
            make_detection(),
            restart_fn=restart,
            get_status_fn=status,
            finish_fn=finish,
            verification_timeout_seconds=5,
            poll_interval_seconds=2,
            sleep_fn=clock.sleep,
            monotonic_fn=clock.monotonic,
        )

    assert result["status"] == "FAILED"
    assert clock.now == 5.0
    assert status.call_count == 4
    assert finish.call_args.kwargs["status"] == "FAILED"
