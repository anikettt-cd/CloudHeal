import pytest

from cloudheal_control_plane import database


@pytest.fixture(autouse=True)
def isolated_database(tmp_path, monkeypatch):
    monkeypatch.setattr(
        database,
        "DB_PATH",
        tmp_path / "cloudheal-test.db",
    )
    database.initialize_database()