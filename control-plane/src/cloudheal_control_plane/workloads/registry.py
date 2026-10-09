from uuid import UUID

from cloudheal_control_plane.workloads.models import WorkloadRecord


class WorkloadRegistry:

    def __init__(self) -> None:
        self._workloads: dict[UUID, WorkloadRecord] = {}

    def create_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        if workload.workload_id in self._workloads:
            raise ValueError(
                f"Workload {workload.workload_id} already exists"
            )
        self._workloads[workload.workload_id] = workload
        return workload

    def get_workload(self, workload_id: UUID) -> WorkloadRecord | None:
        return self._workloads.get(workload_id)

    def update_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        if workload.workload_id not in self._workloads:
            raise LookupError("Workload not found")
        self._workloads[workload.workload_id] = workload
        return workload

    def list_workloads(self) -> list[WorkloadRecord]:
        return list(self._workloads.values())
