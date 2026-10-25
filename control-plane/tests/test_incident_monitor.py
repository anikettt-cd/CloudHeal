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