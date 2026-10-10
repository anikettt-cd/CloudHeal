import asyncio

import httpx
from fastapi.encoders import jsonable_encoder

from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.runtime_info import get_runtime_info
from cloudheal_node_agent.system import get_system_info


HEARTBEAT_INTERVAL = 10


async def send_heartbeat(control_plane_url: str) -> None:
    node_id = get_node_id()

    payload = {
        "system_info": jsonable_encoder(get_system_info()),
        "runtime_info": get_runtime_info(),
    }

    response = await asyncio.to_thread(
        httpx.post,
        f"{control_plane_url}/nodes/{node_id}/heartbeat",
        json=payload,
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