import asyncio
import logging
from contextlib import asynccontextmanager
from uuid import UUID
from typing import Any, Literal
from cloudheal_control_plane.workloads.reconciler import WorkloadReconciler
from pydantic import BaseModel, Field, field_validator
from fastapi import FastAPI, HTTPException, status
from cloudheal_control_plane.database import initialize_database, list_incident_history
from kubernetes.client.rest import ApiException
from kubernetes import config
from cloudheal_control_plane.infrastructure.incident_detector import (
    detect_deployment_incident,
)
from cloudheal_control_plane.infrastructure.incident_monitor import (
    incident_monitor_loop,
)
from cloudheal_control_plane.self_healing.recovery_executor import execute_recovery

from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)
from cloudheal_control_plane.infrastructure.kubernetes_deployments import (
    create_deployment as create_k8s_deployment,
    create_service as create_k8s_service,
    delete_deployment as delete_k8s_deployment,
    ensure_namespace as ensure_k8s_namespace,
    scale_deployment as scale_k8s_deployment,
)

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
    ExecutionError,
    SchedulingError,
    WorkloadScheduler,
)

logger = logging.getLogger(__name__)


async def reconciliation_loop():
    while True:
        try:
            failures = await asyncio.to_thread(
                workload_reconciler.reconcile
            )

            for workload_id in failures:
                print(
                    f"[CloudHeal] Detected failed workload: {workload_id}"
                )

        except Exception as exc:
            print(f"[CloudHeal] Reconciliation error: {exc}")

        await asyncio.sleep(10)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()

    reconciliation_task = asyncio.create_task(
        reconciliation_loop(),
        name="workload-reconciliation",
    )

    incident_monitor_task = asyncio.create_task(
        incident_monitor_loop(),
        name="incident-monitor",
    )

    try:
        yield
    finally:
        tasks = [
            reconciliation_task,
            incident_monitor_task,
        ]

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

app = FastAPI(
    title="CloudHeal Control Plane",
    version="0.1.0",
    lifespan=lifespan,
)

class NodeHeartbeat(BaseModel):
    system_info: dict[str, Any] | None = None
    runtime_info: dict[str, Any] | None = None


class KubernetesDeploymentCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=253,
        pattern=r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$",
    )
    image: str = Field(min_length=1)
    replicas: int = Field(default=1, ge=1, le=20)
    container_port: int = Field(default=80, ge=1, le=65535)
    service_type: Literal["ClusterIP", "NodePort", "LoadBalancer"] = "NodePort"
    service_port: int = Field(default=80, ge=1, le=65535)
    target_port: int | None = Field(default=None, ge=1, le=65535)

    @field_validator("image")
    @classmethod
    def validate_image(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("image is required")
        return value


class KubernetesDeploymentScale(BaseModel):
    replicas: int = Field(ge=0, le=20)

# Shared workload-management instances.
workload_registry = WorkloadRegistry()
workload_service = WorkloadService(workload_registry)
workload_scheduler = WorkloadScheduler(workload_service)
workload_reconciler = WorkloadReconciler(workload_service)


@app.get("/incidents/history")
def incident_history(limit: int = 50):
    """Return recent incidents and their recovery attempts."""
    try:
        return {"incidents": list_incident_history(limit)}
    except (ValueError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid incident history limit",
        ) from exc


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
def heartbeat(node_id: str, request: NodeHeartbeat):
    result = heartbeat_node(
        node_id,
        system_info=request.system_info,
        runtime_info=request.runtime_info,
    )

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
    except ExecutionError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except SchedulingError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

@app.get("/infrastructure/kubernetes/namespaces/{namespace}/deployments/{name}")
def inspect_kubernetes_deployment(namespace: str, name: str):
    try:
        return get_deployment_status(
            namespace=namespace,
            name=name,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kubernetes Deployment not found",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Kubernetes API request failed",
        ) from exc

    except (config.ConfigException, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes configuration is unavailable",
        ) from exc

@app.get(
    "/incidents/kubernetes/namespaces/{namespace}/deployments/{name}"
)
def inspect_deployment_incident(namespace: str, name: str):
    try:
        return detect_deployment_incident(
            namespace=namespace,
            deployment_name=name,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kubernetes Deployment not found",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Kubernetes API request failed",
        ) from exc

    except (config.ConfigException, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes configuration is unavailable",
        ) from exc


@app.post(
    "/incidents/kubernetes/namespaces/{namespace}/deployments/{name}/recover"
)
def recover_deployment(namespace: str, name: str):
    """Attempt policy-approved recovery of a currently degraded Deployment."""

    try:
        detection = detect_deployment_incident(
            namespace=namespace,
            deployment_name=name,
        )

        if not detection.get("incident_detected"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Deployment is healthy; recovery was not started",
            )

        result = execute_recovery(detection)

        if not result.get("accepted"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result,
            )

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Kubernetes Deployment not found",
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Kubernetes API request failed",
        ) from exc

    except (config.ConfigException, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Kubernetes configuration is unavailable",
        ) from exc



@app.post("/infrastructure/kubernetes/namespaces/{namespace}/deployments", status_code=201)
def create_kubernetes_deployment(namespace: str, request: KubernetesDeploymentCreate):
    deployment_created = False
    created_deployment_name = request.name

    try:
        ensure_k8s_namespace(namespace)

        deployment = create_k8s_deployment(
            namespace=namespace,
            name=request.name,
            image=request.image,
            replicas=request.replicas,
            container_port=request.container_port,
        )
        deployment_created = True

        target_port = request.target_port or request.container_port

        service = create_k8s_service(
            namespace=namespace,
            name=request.name,
            selector={"app": request.name},
            port=request.service_port,
            target_port=target_port,
            service_type=request.service_type,
        )

        return {"deployment": deployment, "service": service}

    except ValueError as exc:
        if deployment_created:
            _cleanup_created_deployment(namespace, created_deployment_name)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    except ApiException as exc:
        if deployment_created:
            _cleanup_created_deployment(namespace, created_deployment_name)

        if exc.status == 409:
            raise HTTPException(status_code=409, detail="Kubernetes resource already exists") from exc
        raise HTTPException(status_code=502, detail="Kubernetes API request failed") from exc

    except (config.ConfigException, OSError) as exc:
        if deployment_created:
            _cleanup_created_deployment(namespace, created_deployment_name)
        raise HTTPException(status_code=503, detail="Kubernetes configuration is unavailable") from exc


def _cleanup_created_deployment(namespace: str, name: str) -> None:
    try:
        delete_k8s_deployment(namespace=namespace, name=name)
    except Exception as cleanup_exc:  # pragma: no cover - best effort
        logger.warning(
            "Failed to clean up Deployment %s/%s after partial application creation: %s",
            namespace,
            name,
            cleanup_exc,
        )


@app.post("/infrastructure/kubernetes/namespaces/{namespace}/deployments/{name}/scale")
def scale_kubernetes_deployment(namespace: str, name: str, request: KubernetesDeploymentScale):
    try:
        return scale_k8s_deployment(
            namespace=namespace,
            name=name,
            replicas=request.replicas,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(status_code=404, detail="Kubernetes Deployment not found") from exc
        raise HTTPException(status_code=502, detail="Kubernetes API request failed") from exc
    except (config.ConfigException, OSError) as exc:
        raise HTTPException(status_code=503, detail="Kubernetes configuration is unavailable") from exc


@app.delete("/infrastructure/kubernetes/namespaces/{namespace}/deployments/{name}")
def delete_kubernetes_deployment(namespace: str, name: str):
    try:
        return delete_k8s_deployment(namespace=namespace, name=name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ApiException as exc:
        if exc.status == 404:
            raise HTTPException(status_code=404, detail="Kubernetes Deployment not found") from exc
        raise HTTPException(status_code=502, detail="Kubernetes API request failed") from exc
    except (config.ConfigException, OSError) as exc:
        raise HTTPException(status_code=503, detail="Kubernetes configuration is unavailable") from exc