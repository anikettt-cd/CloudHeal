import importlib

from cloudheal_node_agent import api


def test_control_plane_url_defaults_to_localhost(monkeypatch):
    monkeypatch.delenv("CLOUDHEAL_CONTROL_PLANE_URL", raising=False)

    importlib.reload(api)

    assert api.CONTROL_PLANE_URL == "http://127.0.0.1:9000"


def test_control_plane_url_can_be_configured(monkeypatch):
    configured_url = "http://100.100.100.10:9000"
    monkeypatch.setenv("CLOUDHEAL_CONTROL_PLANE_URL", configured_url)

    importlib.reload(api)

    assert api.CONTROL_PLANE_URL == configured_url


def teardown_module():
    importlib.reload(api)
