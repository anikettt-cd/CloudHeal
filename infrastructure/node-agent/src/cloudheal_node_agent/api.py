import asyncio
import os
from contextlib import asynccontextmanager
from uuid import UUID

from cloudheal_node_agent.runtime_info import get_runtime_info
from cloudheal_node_agent.heartbeat import heartbeat_loop
from cloudheal_node_agent.identity import get_node_id
from cloudheal_node_agent.registration import register_with_control_plane
from cloudheal_node_agent.system import get_system_info
from fastapi import FastAPI, HTTPException, status

from cloudheal_node_agent.runtime import (
    ContainerExecutionError,
    get_container_status,
    run_container,
)
from cloudheal_node_agent.workload_models import ContainerRunRequest

CONTROL_PLANE_URL = os.getenv(
    "CLOUDHEAL_CONTROL_PLANE_URL",
    "http://127.0.0.1:9000",
)

async def _register_until_success(control_plane_url: str) -> None:
    """Register in the background so startup is not blocked by CP availability."""
    delay_seconds = 2

    while True:
        try:
            await asyncio.to_thread(register_with_control_plane, control_plane_url)
            print("Node registered with CloudHeal Control Plane")
            return
        except Exception as exc:  # noqa: BLE001
            print(f"Node registration failed: {exc}; retrying in {delay_seconds}s")

        await asyncio.sleep(delay_seconds)
        delay_seconds = min(delay_seconds * 2, 30)


@asynccontextmanager
async def lifespan(app: FastAPI):
    registration_task = asyncio.create_task(
        _register_until_success(CONTROL_PLANE_URL),
        name="node-registration",
    )
    heartbeat_task = asyncio.create_task(
        heartbeat_loop(CONTROL_PLANE_URL),
        name="node-heartbeat",
    )

    try:
        yield
    finally:
        for task in (registration_task, heartbeat_task):
            task.cancel()
        await asyncio.gather(
            registration_task, heartbeat_task, return_exceptions=True
        )


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
       message = str(exc)
       if message.startswith("Container already exists"):
            status_code = status.HTTP_409_CONFLICT
       else:
           status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
       raise HTTPException(
          status_code=status_code,
          detail=message,
        ) from exc

@app.get("/runtime")
def runtime():
    return get_runtime_info()

@app.get("/containers/{workload_id}/status")
def container_status(workload_id: UUID):
    try:
        return get_container_status(workload_id)
    except ContainerExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc