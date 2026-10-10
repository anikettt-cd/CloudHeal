import socket

import httpx
from fastapi.encoders import jsonable_encoder
from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.network import get_local_ip
from cloudheal_node_agent.runtime_info import get_runtime_info
from cloudheal_node_agent.system import get_system_info


def get_hostname() -> str:
    return socket.gethostname()


def register_with_control_plane(
    control_plane_url: str,
) -> None:
    payload = {
        "node_id": get_node_id(),
        "hostname": get_hostname(),
        "address": get_local_ip(),
        "status": "healthy",
        "system_info": jsonable_encoder(get_system_info()),
        "runtime_info": get_runtime_info(),
    }

    response = httpx.post(
        f"{control_plane_url}/nodes/register",
        json=payload,
        timeout=5.0,
    )

    response.raise_for_status()