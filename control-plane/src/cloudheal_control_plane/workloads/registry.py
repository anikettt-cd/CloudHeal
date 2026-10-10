from uuid import UUID

from cloudheal_control_plane.workloads.models import WorkloadRecord


class WorkloadRegistry:
    def __init__(self) -> None:
        self._workloads: dict[UUID, WorkloadRecord] = {}

    def create_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        self._workloads[workload.workload_id] = workload
        return workload

    def get_workload(self, workload_id: UUID) -> WorkloadRecord | None:
        return self._workloads.get(workload_id)

    def list_workloads(self) -> list[WorkloadRecord]:
        return list(self._workloads.values())

    def update_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        self._workloads[workload.workload_id] = workload
        return workload