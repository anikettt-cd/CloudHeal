import uuid
from pathlib import Path

from cloudheal_node_agent import identity


def test_get_node_id_persists_value(tmp_path, monkeypatch):
    identity_file = tmp_path / "node_id"
    monkeypatch.setattr(identity, "IDENTITY_FILE", identity_file)

    first = identity.get_node_id()
    second = identity.get_node_id()

    assert first == second
    assert identity_file.read_text(encoding="utf-8").strip() == first
    # Validate UUID format
    uuid.UUID(first)


def test_get_node_id_reads_existing_value(tmp_path, monkeypatch):
    identity_file = tmp_path / "node_id"
    expected = "existing-node-id"
    identity_file.parent.mkdir(parents=True, exist_ok=True)
    identity_file.write_text(expected, encoding="utf-8")
    monkeypatch.setattr(identity, "IDENTITY_FILE", identity_file)

    assert identity.get_node_id() == expected
