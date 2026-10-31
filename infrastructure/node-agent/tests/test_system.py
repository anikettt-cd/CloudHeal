from types import SimpleNamespace

from cloudheal_node_agent import system


def mock_metrics(monkeypatch):
    monkeypatch.setattr(system.platform, "node", lambda: "test-node")
    monkeypatch.setattr(system.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system.psutil, "cpu_percent", lambda interval: 12.5)
    monkeypatch.setattr(system.psutil, "cpu_count", lambda logical: 4 if logical else 2)
    monkeypatch.setattr(
        system.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=16000, available=8000, percent=50.0),
    )

    disk_calls = []

    def fake_disk_usage(path):
        disk_calls.append(path)
        return SimpleNamespace(total=10000, free=4000, percent=60.0)

    monkeypatch.setattr(system.psutil, "disk_usage", fake_disk_usage)
    return disk_calls


def test_linux_uses_root_filesystem(monkeypatch):
    disk_calls = mock_metrics(monkeypatch)
    monkeypatch.setattr(system.platform, "system", lambda: "Linux")

    result = system.get_system_info()

    assert disk_calls == ["/"]
    assert result["operating_system"] == "Linux"
    assert result["disk"].total_bytes == 10000


def test_windows_uses_system_drive_root(monkeypatch):
    disk_calls = mock_metrics(monkeypatch)
    monkeypatch.setattr(system.platform, "system", lambda: "Windows")
    monkeypatch.setattr(
        system.Path,
        "home",
        lambda: SimpleNamespace(anchor="C:\\"),
    )

    result = system.get_system_info()

    assert disk_calls == ["C:\\"]
    assert result["operating_system"] == "Windows"
    assert result["disk"].free_bytes == 4000
def test_metric_collection_failure_does_not_prevent_other_metrics(monkeypatch):
    monkeypatch.setattr(system.platform, "node", lambda: "test-node")
    monkeypatch.setattr(system.platform, "machine", lambda: "x86_64")
    monkeypatch.setattr(system.platform, "system", lambda: "Linux")
    monkeypatch.setattr(system.psutil, "cpu_percent", lambda interval: 12.5)
    monkeypatch.setattr(system.psutil, "cpu_count", lambda logical: 4 if logical else 2)
    monkeypatch.setattr(
        system.psutil,
        "virtual_memory",
        lambda: (_ for _ in ()).throw(RuntimeError("memory unavailable")),
    )

    def fake_disk_usage(path):
        return SimpleNamespace(total=10000, free=4000, percent=60.0)

    monkeypatch.setattr(system.psutil, "disk_usage", fake_disk_usage)

    result = system.get_system_info()

    assert result["cpu"] is not None
    assert result["memory"] is None
    assert result["disk"] is not None
    assert "memory" in result["metric_errors"]

