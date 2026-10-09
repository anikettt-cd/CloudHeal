from datetime import UTC, datetime
from uuid import UUID

from cloudheal_control_plane.registry import get_nodes
from cloudheal_control_plane.workloads.models import WorkloadState
from cloudheal_control_plane.workloads.service import WorkloadService


class SchedulingError(Exception):
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
        eligible_nodes = [
            node for node in nodes if node.status.lower() == "healthy"
        ]
        if not eligible_nodes:
            raise SchedulingError("No healthy nodes available")
        # Initial scheduling policy: select the first healthy node.
        selected_node = eligible_nodes[0]
        workload.node_id = UUID(str(selected_node.node_id))
        workload.actual_state = WorkloadState.SCHEDULED
        workload.updated_at = datetime.now(UTC)
        return self.workload_service.update_workload(workload)
