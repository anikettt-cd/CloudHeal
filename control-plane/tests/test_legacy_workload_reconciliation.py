import os

from cloudheal_control_plane.api import is_legacy_workload_reconciliation_enabled


def test_legacy_workload_reconciliation_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CLOUDHEAL_LEGACY_WORKLOAD_RECONCILIATION_ENABLED", raising=False)
    assert is_legacy_workload_reconciliation_enabled() is False


def test_legacy_workload_reconciliation_can_be_enabled(monkeypatch):
    monkeypatch.setenv("CLOUDHEAL_LEGACY_WORKLOAD_RECONCILIATION_ENABLED", "true")
    assert is_legacy_workload_reconciliation_enabled() is True
