from datetime import UTC, datetime
from uuid import UUID

import httpx

from cloudheal_control_plane.registry import get_nodes
from cloudheal_control_plane.workloads.models import WorkloadState
from cloudheal_control_plane.workloads.service import WorkloadService


class SchedulingError(Exception):
    pass

class ExecutionError(Exception):
    pass


class WorkloadScheduler:

    def __init__(self, workload_service: WorkloadService) -> None:
        self.workload_service = workload_service

    def schedule(self, workload_id: UUID):
        workload = self.workload_service.get_workload(workload_id)

        if workload is None:
            raise LookupError("Workload not found")

        if workload.actual_state != WorkloadState.PENDING:
            raise SchedulingError(
                f"Cannot schedule workload in state {workload.actual_state}"
            )

        if workload.desired_state.value != "RUNNING":
            raise SchedulingError("Workload is not intended to run")

        nodes = get_nodes()
        eligible_nodes = []

        required_memory_bytes = workload.memory_limit_mb * 1024 * 1024

        active_workloads = self.workload_service.list_workloads()

        for node in nodes:
            if node.status.lower() != "healthy":
                continue

            if node.runtime_info.get("available") is not True:
                continue

            if not node.address:
                continue

            cpu_count = node.runtime_info.get("cpu_count")
            memory_bytes = node.runtime_info.get("memory_bytes")

            # Unknown capacity: do not assume the node has enough resources.
            if cpu_count is None or memory_bytes is None:
                continue

            try:
                cpu_count = float(cpu_count)
                memory_bytes = int(memory_bytes)
            except (TypeError, ValueError):
                continue

            if cpu_count <= 0 or memory_bytes <= 0:
                continue

            allocated_cpu = sum(
                w.cpu_limit
                for w in active_workloads
                if str(w.node_id) == str(node.node_id)
                and w.actual_state in {
                    WorkloadState.SCHEDULED,
                    WorkloadState.RUNNING,
                }
            )
            allocated_memory_bytes = sum(
                w.memory_limit_mb * 1024 * 1024
                for w in active_workloads
                if str(w.node_id) == str(node.node_id)
                and w.actual_state in {
                    WorkloadState.SCHEDULED,
                    WorkloadState.RUNNING,
                }
            )
            available_cpu = cpu_count - allocated_cpu
            available_memory_bytes = memory_bytes - allocated_memory_bytes
            if available_cpu < workload.cpu_limit:
                continue
            if available_memory_bytes < required_memory_bytes:
                continue
            eligible_nodes.append(node)

        if not eligible_nodes:
            raise SchedulingError(
                "No healthy Docker nodes have sufficient reported CPU "
                "and memory capacity"
            )

        def remaining_capacity(node):
            allocated_workloads = [
                w
                for w in active_workloads
                if str(w.node_id) == str(node.node_id)
                and w.actual_state in {
                    WorkloadState.SCHEDULED,
                    WorkloadState.RUNNING,
                }
            ]
            allocated_cpu = sum(w.cpu_limit for w in allocated_workloads)
            allocated_memory = sum(
                w.memory_limit_mb * 1024 * 1024
                for w in allocated_workloads
            )
            cpu_count = float(node.runtime_info["cpu_count"])
            memory_bytes = int(node.runtime_info["memory_bytes"])
            remaining_cpu = cpu_count - allocated_cpu
            remaining_memory = memory_bytes - allocated_memory
            # Prefer nodes with more remaining capacity relative to their size.
            cpu_ratio = remaining_cpu / cpu_count
            memory_ratio = remaining_memory / memory_bytes
            return min(cpu_ratio, memory_ratio)

        selected_node = max(eligible_nodes, key=remaining_capacity)

        workload.node_id = UUID(str(selected_node.node_id))
        workload.actual_state = WorkloadState.SCHEDULED
        workload.updated_at = datetime.now(UTC)
        self.workload_service.update_workload(workload)

        execution_url = f"http://{selected_node.address}:8000/containers"

        payload = {
            "workload_id": str(workload.workload_id),
            "image": workload.image,
            "cpu_limit": workload.cpu_limit,
            "memory_limit_mb": workload.memory_limit_mb,
        }

        try:
            response = httpx.post(
                execution_url,
                json=payload,
                timeout=310.0,
            )
            response.raise_for_status()

            result = response.json()

            if result.get("status") != "RUNNING":
                raise SchedulingError(
                    "Node Agent did not confirm that the container is running"
                )

            workload.actual_state = WorkloadState.RUNNING

        except httpx.HTTPError as exc:
            workload.actual_state = WorkloadState.FAILED
            raise ExecutionError(
                f"Node Agent execution request failed: {exc}"
            ) from exc

        except SchedulingError:
            workload.actual_state = WorkloadState.FAILED
            raise

        finally:
            workload.updated_at = datetime.now(UTC)
            self.workload_service.update_workload(workload)

        return workload
