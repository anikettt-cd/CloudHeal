import asyncio

import httpx

from cloudheal_node_agent.identity import get_node_id


HEARTBEAT_INTERVAL = 10


async def send_heartbeat(control_plane_url: str) -> None:
    node_id = get_node_id()

    response = await asyncio.to_thread(
        httpx.post,
        f"{control_plane_url}/nodes/{node_id}/heartbeat",
        timeout=5.0,
    )

    response.raise_for_status()


async def heartbeat_loop(control_plane_url: str) -> None:
    while True:
        try:
            await send_heartbeat(control_plane_url)
        except Exception as exc:
            print(f"Heartbeat failed: {exc}")

        await asyncio.sleep(HEARTBEAT_INTERVAL)