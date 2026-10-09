from uuid import UUID

from fastapi import FastAPI, HTTPException, status

from cloudheal_control_plane.registry import (
    NodeRecord,
    get_node,
    get_nodes,
    heartbeat_node,
    register_node,
)
from cloudheal_control_plane.workloads.models import (
    WorkloadCreate,
    WorkloadRecord,
)
from cloudheal_control_plane.workloads.registry import WorkloadRegistry
from cloudheal_control_plane.workloads.service import WorkloadService

from cloudheal_control_plane.workloads.scheduler import (
    SchedulingError,
    WorkloadScheduler,
)
app = FastAPI(
    title="CloudHeal Control Plane",
    version="0.1.0",
)

# Shared workload-management instances.
workload_registry = WorkloadRegistry()
workload_service = WorkloadService(workload_registry)
workload_scheduler = WorkloadScheduler(workload_service)


@app.get("/health")
def health():
    return {"status": "ok"}


# Node endpoints


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    return result


@app.post("/nodes/{node_id}/heartbeat", response_model=NodeRecord)
def heartbeat(node_id: str):
    result = heartbeat_node(node_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Node not found",
        )
    return result


# Workload endpoints


@app.post(
    "/workloads",
    response_model=WorkloadRecord,
    status_code=status.HTTP_201_CREATED,
)
def create_workload(request: WorkloadCreate):
    return workload_service.create_workload(request)


@app.get("/workloads", response_model=list[WorkloadRecord])
def list_workloads():
    return workload_service.list_workloads()


@app.get("/workloads/{workload_id}", response_model=WorkloadRecord)
def get_workload(workload_id: UUID):
    result = workload_service.get_workload(workload_id)

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workload not found",
        )
    return result

@app.post(
    "/workloads/{workload_id}/schedule",
    response_model=WorkloadRecord,
)
def schedule_workload(workload_id: UUID):
    try:
        return workload_scheduler.schedule(workload_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except SchedulingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc