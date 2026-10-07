from contextlib import asynccontextmanager

from fastapi import FastAPI

from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.registration import register_with_control_plane
from cloudheal_node_agent.system import get_system_info


CONTROL_PLANE_URL = "http://127.0.0.1:9000"


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_with_control_plane(CONTROL_PLANE_URL)
    yield


app = FastAPI(
    title="CloudHeal Node Agent",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/identity")
def identity():
    return {
        "node_id": get_node_id(),
    }


@app.get("/system")
def system():
    return get_system_info()
