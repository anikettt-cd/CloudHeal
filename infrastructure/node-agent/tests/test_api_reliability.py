import asyncio
from unittest.mock import AsyncMock, patch

from cloudheal_node_agent import api


def test_register_until_success_retries(monkeypatch):
    calls = {"count": 0}

    def fake_register(url):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("temporary failure")

    monkeypatch.setattr(api, "register_with_control_plane", fake_register)

    async def fake_sleep(_):
        return None

    monkeypatch.setattr(api.asyncio, "sleep", fake_sleep)

    asyncio.run(api._register_until_success("http://example:9000"))

    assert calls["count"] == 2
