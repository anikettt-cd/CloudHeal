from uuid import UUID
from cloudheal_control_plane.database import record_event

from cloudheal_control_plane.workloads.models import (
    WorkloadCreate,
    WorkloadRecord,
)
from cloudheal_control_plane.workloads.registry import WorkloadRegistry


class WorkloadService:

    def __init__(self, registry: WorkloadRegistry) -> None:
        self.registry = registry

    def create_workload(self, request: WorkloadCreate) -> WorkloadRecord:
        workload = WorkloadRecord(**request.model_dump())
        created = self.registry.create_workload(workload)

        record_event(
            event_type="WORKLOAD_CREATED",
            workload_id=str(created.workload_id),
            details={
               "name": created.name,
               "image": created.image,
               "desired_state": created.desired_state.value,
            },
        )

        return created

    def get_workload(self, workload_id: UUID) -> WorkloadRecord | None:
        return self.registry.get_workload(workload_id)

    def list_workloads(self) -> list[WorkloadRecord]:
        return self.registry.list_workloads()

    def update_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        return self.registry.update_workload(workload)
