from pydantic import BaseModel


class NodeRecord(BaseModel):
    node_id: str
    hostname: str
    address: str
    status: str = "healthy"


_nodes: dict[str, NodeRecord] = {}


def register_node(node: NodeRecord) -> NodeRecord:
    _nodes[node.node_id] = node
    return node


def get_nodes() -> list[NodeRecord]:
    return list(_nodes.values())


def get_node(node_id: str) -> NodeRecord | None:
    return _nodes.get(node_id)