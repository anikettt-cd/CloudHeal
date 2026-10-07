from fastapi import FastAPI

from cloudheal_control_plane.registry import (
    NodeRecord,
    get_node,
    get_nodes,
    heartbeat_node,
    register_node,
)


app = FastAPI(
    title="CloudHeal Control Plane",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/nodes/register", response_model=NodeRecord)
def register(node: NodeRecord):
    return register_node(node)


@app.get("/nodes", response_model=list[NodeRecord])
def nodes():
    return get_nodes()


@app.get("/nodes/{node_id}", response_model=NodeRecord)
def node(node_id: str):
    result = get_node(node_id)

    if result is None:
        return {"detail": "Node not found"}

    return result

@app.post("/nodes/{node_id}/heartbeat", response_model=NodeRecord)
def heartbeat(node_id: str):
    result = heartbeat_node(node_id)

    if result is None:
        return {"detail": "Node not found"}

    return result