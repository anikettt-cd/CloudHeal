from datetime import UTC, datetime

import httpx

from cloudheal_control_plane.registry import get_node
from cloudheal_control_plane.workloads.models import WorkloadState
from cloudheal_control_plane.workloads.scheduler import (
    ExecutionError,
    SchedulingError,
    WorkloadScheduler,
)
from cloudheal_control_plane.workloads.service import WorkloadService


class WorkloadReconciler:
    def __init__(self, workload_service: WorkloadService) -> None:
        self.workload_service = workload_service
        self.workload_scheduler = WorkloadScheduler(workload_service)

    def reconcile(self) -> list[str]:
        detected_failures: list[str] = []

        for workload in self.workload_service.list_workloads():
            workload_id = str(workload.workload_id)

            # Schedule pending workloads that are intended to run.
            if (
                workload.actual_state == WorkloadState.PENDING
                and workload.desired_state.value == "RUNNING"
            ):
                try:
                    self.workload_scheduler.schedule(workload.workload_id)
                except (
                    SchedulingError,
                    ExecutionError,
                    LookupError,
                ) as exc:
                    print(
                        f"[CloudHeal] Could not schedule workload "
                        f"{workload_id}: {exc}"
                    )

                continue

            # Retry failed workloads that are still intended to run.
            if (
                workload.actual_state == WorkloadState.FAILED
                and workload.desired_state.value == "RUNNING"
            ):
                try:
                    self.workload_scheduler.schedule(workload.workload_id)
                except (
                    SchedulingError,
                    ExecutionError,
                    LookupError,
                ) as exc:
                    print(
                        f"[CloudHeal] Could not recover workload "
                        f"{workload_id}: {exc}"
                    )

                continue

            # Only monitor workloads that are running on a node.
            if workload.actual_state != WorkloadState.RUNNING:
                continue

            if workload.node_id is None:
                continue

            node = get_node(str(workload.node_id))

            if (
               node is None
               or not node.address
               or node.status.lower() != "healthy"
            ):
               continue

            url = (
                f"http://{node.address}:8000/containers/"
                f"{workload_id}/status"
            )

            try:
                response = httpx.get(url, timeout=5.0)
                response.raise_for_status()
                result = response.json()
            except (httpx.HTTPError, ValueError):
                # A communication failure does not prove the container stopped.
                continue

            container_status = result.get("status")

            if container_status not in {"STOPPED", "NOT_FOUND"}:
                continue

            workload.actual_state = WorkloadState.FAILED
            workload.updated_at = datetime.now(UTC)
            self.workload_service.update_workload(workload)

            detected_failures.append(workload_id)

            # Attempt immediate recovery.
            try:
                self.workload_scheduler.schedule(workload.workload_id)
            except (
                SchedulingError,
                ExecutionError,
                LookupError,
            ) as exc:
                print(
                    f"[CloudHeal] Could not recover workload "
                    f"{workload_id}: {exc}"
                )

        return detected_failures