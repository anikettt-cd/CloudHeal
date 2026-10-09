import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from cloudheal_node_agent.heartbeat import heartbeat_loop
from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.registration import register_with_control_plane
from cloudheal_node_agent.system import get_system_info
from fastapi import FastAPI, HTTPException, status

from cloudheal_node_agent.runtime import (
    ContainerExecutionError,
    run_container,
)
from cloudheal_node_agent.workload_models import ContainerRunRequest

CONTROL_PLANE_URL = "http://100.90.104.13:9000"

@asynccontextmanager
async def lifespan(app: FastAPI):
    register_with_control_plane(CONTROL_PLANE_URL)

    heartbeat_task = asyncio.create_task(
        heartbeat_loop(CONTROL_PLANE_URL)
    )

    try:
        yield
    finally:
        heartbeat_task.cancel()
        await heartbeat_task


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

@app.post("/containers", status_code=status.HTTP_201_CREATED)
def create_container(request: ContainerRunRequest):
    try:
        return run_container(
            workload_id=request.workload_id,
            image=request.image,
            cpu_limit=request.cpu_limit,
            memory_limit_mb=request.memory_limit_mb,
        )
    except ContainerExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc