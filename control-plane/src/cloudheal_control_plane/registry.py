from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class NodeRecord(BaseModel):
    node_id: str
    hostname: str
    address: str
    status: str = "healthy"
    last_seen: datetime | None = None

    system_info: dict[str, Any] = Field(default_factory=dict)
    runtime_info: dict[str, Any] = Field(default_factory=dict)


_nodes: dict[str, NodeRecord] = {}


def register_node(node: NodeRecord) -> NodeRecord:
    node.last_seen = datetime.now(timezone.utc)
    _nodes[node.node_id] = node
    return node


def get_nodes() -> list[NodeRecord]:
    return list(_nodes.values())


def get_node(node_id: str) -> NodeRecord | None:
    return _nodes.get(node_id)


def heartbeat_node(
    node_id: str,
    system_info: dict[str, Any] | None = None,
    runtime_info: dict[str, Any] | None = None,
) -> NodeRecord | None:
    node = _nodes.get(node_id)

    if node is None:
        return None

    node.last_seen = datetime.now(timezone.utc)

    if system_info is not None:
        node.system_info = system_info

    if runtime_info is not None:
        node.runtime_info = runtime_info

    return node