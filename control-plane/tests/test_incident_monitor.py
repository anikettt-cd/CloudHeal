import asyncio
from unittest.mock import AsyncMock, patch

from cloudheal_control_plane.infrastructure.incident_monitor import (
    get_monitor_interval,
    get_monitor_targets,
    incident_monitor_loop,
)
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)


def test_monitor_targets_are_read_from_environment(monkeypatch):
    monkeypatch.setenv(
        "CLOUDHEAL_MONITOR_TARGETS",
        "cloudheal-test/nginx-test,default/my-api",
    )

    assert get_monitor_targets() == [
        ("cloudheal-test", "nginx-test"),
        ("default", "my-api"),
    ]


def test_monitor_targets_default_to_empty(monkeypatch):
    monkeypatch.delenv("CLOUDHEAL_MONITOR_TARGETS", raising=False)

    assert get_monitor_targets() == []


def test_invalid_monitor_targets_are_ignored(monkeypatch):
    monkeypatch.setenv(
        "CLOUDHEAL_MONITOR_TARGETS",
        "cloudheal-test/nginx-test,invalid-target,default/my-api",
    )

    assert get_monitor_targets() == [
        ("cloudheal-test", "nginx-test"),
        ("default", "my-api"),
    ]


def test_monitor_interval_defaults_to_15_seconds(monkeypatch):
    monkeypatch.delenv(
        "CLOUDHEAL_MONITOR_INTERVAL_SECONDS",
        raising=False,
    )

    assert get_monitor_interval() == 15


def test_monitor_interval_has_minimum_of_one_second(monkeypatch):
    monkeypatch.setenv("CLOUDHEAL_MONITOR_INTERVAL_SECONDS", "0")

    assert get_monitor_interval() == 1


def test_invalid_monitor_interval_uses_default(monkeypatch):
    monkeypatch.setenv("CLOUDHEAL_MONITOR_INTERVAL_SECONDS", "invalid")

    assert get_monitor_interval() == 15


def test_monitor_continues_after_one_target_fails(monkeypatch):
    monkeypatch.setenv(
        "CLOUDHEAL_MONITOR_TARGETS",
        "default/broken-app,default/healthy-app",
    )
    monkeypatch.setenv("CLOUDHEAL_MONITOR_INTERVAL_SECONDS", "15")

    def fake_detector(namespace, deployment_name, get_deployment_status):
        if deployment_name == "broken-app":
            raise RuntimeError("Simulated Kubernetes API failure")

        return {"incident_detected": False}

    async def stop_after_one_cycle(_seconds):
        raise asyncio.CancelledError

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "detect_deployment_incident",
            side_effect=fake_detector,
        ) as mock_detector,
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "asyncio.sleep",
            new=AsyncMock(side_effect=stop_after_one_cycle),
        ),
    ):
        try:
            asyncio.run(incident_monitor_loop())
        except asyncio.CancelledError:
            pass

    assert mock_detector.call_count == 2
    mock_detector.assert_any_call(
    "default",
    "broken-app",
    get_deployment_status,
    )
    mock_detector.assert_any_call(
    "default",
    "healthy-app",
    get_deployment_status,
    )

def test_auto_recovery_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv(
        "CLOUDHEAL_AUTO_RECOVERY_ENABLED",
        raising=False,
    )

    from cloudheal_control_plane.infrastructure.incident_monitor import (
        is_auto_recovery_enabled,
    )

    assert is_auto_recovery_enabled() is False


def test_monitor_invokes_recovery_when_enabled(monkeypatch):
    monkeypatch.setenv(
        "CLOUDHEAL_MONITOR_TARGETS",
        "cloudheal-test/cloudheal-recovery-demo",
    )
    monkeypatch.setenv("CLOUDHEAL_AUTO_RECOVERY_ENABLED", "true")

    result = {
        "incident_detected": True,
        "classification": "DEPLOYMENT_DEGRADED",
        "namespace": "cloudheal-test",
        "deployment": "cloudheal-recovery-demo",
        "observed_at": "2026-10-26T10:00:00+00:00",
        "incident": {"incident_id": 123},
        "evidence": {"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
    }

    async def stop_after_one_cycle(_seconds):
        raise asyncio.CancelledError

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "detect_deployment_incident",
            return_value=result,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "execute_recovery",
        ) as mock_executor,
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "asyncio.sleep",
            new=AsyncMock(side_effect=stop_after_one_cycle),
        ),
    ):
        try:
            asyncio.run(incident_monitor_loop())
        except asyncio.CancelledError:
            pass

    mock_executor.assert_called_once_with(
        result ,
        trigger="automatic",
        )


def test_monitor_does_not_recover_when_disabled(monkeypatch):
    monkeypatch.setenv(
        "CLOUDHEAL_MONITOR_TARGETS",
        "cloudheal-test/cloudheal-recovery-demo",
    )
    monkeypatch.setenv("CLOUDHEAL_AUTO_RECOVERY_ENABLED", "false")

    result = {
        "incident_detected": True,
        "classification": "DEPLOYMENT_DEGRADED",
        "namespace": "cloudheal-test",
        "deployment": "cloudheal-recovery-demo",
        "observed_at": "2026-10-26T10:00:00+00:00",
        "incident": {"incident_id": 124},
        "evidence": {"reasons": ["READY_REPLICAS_BELOW_DESIRED"]},
    }

    async def stop_after_one_cycle(_seconds):
        raise asyncio.CancelledError

    with (
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "detect_deployment_incident",
            return_value=result,
        ),
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "execute_recovery",
        ) as mock_executor,
        patch(
            "cloudheal_control_plane.infrastructure.incident_monitor."
            "asyncio.sleep",
            new=AsyncMock(side_effect=stop_after_one_cycle),
        ),
    ):
        try:
            asyncio.run(incident_monitor_loop())
        except asyncio.CancelledError:
            pass

    mock_executor.assert_not_called()
