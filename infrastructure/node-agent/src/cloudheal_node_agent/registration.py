import socket

import httpx

from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.network import get_local_ip


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
    }

    response = httpx.post(
        f"{control_plane_url}/nodes/register",
        json=payload,
        timeout=5.0,
    )

    response.raise_for_status()