from datetime import datetime, timezone

from pydantic import BaseModel


class NodeRecord(BaseModel):
    node_id: str
    hostname: str
    address: str
    status: str = "healthy"
    last_seen: datetime | None = None


_nodes: dict[str, NodeRecord] = {}


def register_node(node: NodeRecord) -> NodeRecord:
    node.last_seen = datetime.now(timezone.utc)
    _nodes[node.node_id] = node
    return node


def get_nodes() -> list[NodeRecord]:
    return list(_nodes.values())


def get_node(node_id: str) -> NodeRecord | None:
    return _nodes.get(node_id)


def heartbeat_node(node_id: str) -> NodeRecord | None:
    node = _nodes.get(node_id)

    if node is None:
        return None

    node.last_seen = datetime.now(timezone.utc)

    return node