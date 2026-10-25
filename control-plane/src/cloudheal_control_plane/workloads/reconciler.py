from datetime import UTC, datetime

import httpx
from cloudheal_control_plane.registry import get_node
from cloudheal_control_plane.workloads.models import WorkloadState
from cloudheal_control_plane.workloads.scheduler import (
    ExecutionError,
    SchedulingError,
    WorkloadScheduler,
)
from cloudheal_control_plane.database import (
    get_connection,
    record_event,
)
from cloudheal_control_plane.workloads.service import WorkloadService


class WorkloadReconciler:
    def __init__(self, workload_service: WorkloadService) -> None:
        self.workload_service = workload_service
        self.workload_scheduler = WorkloadScheduler(workload_service)

    def _record_node_availability_transition(
        self,
        workload_id: str,
        node_id: str,
        available: bool,
    ) -> None:
        """Record workload-node availability changes without duplicates."""
        unavailable_event = "WORKLOAD_NODE_UNAVAILABLE"
        available_event = "WORKLOAD_NODE_AVAILABLE"

        with get_connection() as connection:
            row = connection.execute(
                """
                SELECT event_type
                FROM events
                WHERE workload_id = ?
                  AND node_id = ?
                  AND event_type IN (?, ?)
                ORDER BY event_id DESC
                LIMIT 1
                """,
                (
                    workload_id,
                    node_id,
                    unavailable_event,
                    available_event,
                ),
            ).fetchone()

        last_event = row["event_type"] if row else None

        if available:
            if last_event != unavailable_event:
                return

            record_event(
                event_type=available_event,
                workload_id=workload_id,
                node_id=node_id,
                details={"reason": "assigned_node_healthy"},
            )
        else:
            if last_event == unavailable_event:
                return

            record_event(
                event_type=unavailable_event,
                workload_id=workload_id,
                node_id=node_id,
                details={"reason": "assigned_node_missing_or_unhealthy"},
            )

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
                self._record_node_availability_transition(
                    workload_id=workload_id,
                    node_id=str(workload.node_id),
                    available=False,
                )
                continue

            self._record_node_availability_transition(
                workload_id=workload_id,
                node_id=str(workload.node_id),
                available=True,
            )

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

            record_event(
                event_type="CONTAINER_FAILURE_DETECTED",
                workload_id=workload_id,
                node_id=str(workload.node_id),
                details={
                    "container_status": container_status,
                    "previous_state": WorkloadState.RUNNING.value,
                },
            )

            workload.actual_state = WorkloadState.FAILED
            workload.updated_at = datetime.now(UTC)
            self.workload_service.update_workload(workload)

            detected_failures.append(workload_id)

            record_event(
                event_type="RECOVERY_ATTEMPTED",
                workload_id=workload_id,
                node_id=str(workload.node_id),
                details={
                    "container_status": container_status,
                    "reason": "container_failure_detected",
                },
            )
            try:
                self.workload_scheduler.schedule(workload.workload_id)

                recovered_workload = self.workload_service.get_workload(
                    workload.workload_id
                )

                if (
                    recovered_workload is not None
                    and recovered_workload.actual_state == WorkloadState.RUNNING
                ):
                    record_event(
                        event_type="RECOVERY_SUCCEEDED",
                        workload_id=workload_id,
                        node_id=str(recovered_workload.node_id),
                        details={
                            "verified_state": WorkloadState.RUNNING.value,
                        },
                    )
                else:
                    record_event(
                        event_type="RECOVERY_FAILED",
                        workload_id=workload_id,
                        node_id=str(workload.node_id),
                        details={
                            "reason": "workload_not_confirmed_running",
                            "actual_state": (
                                recovered_workload.actual_state.value
                                if recovered_workload is not None
                                else None
                            ),
                        },
                    )

            except (
                SchedulingError,
                ExecutionError,
                LookupError,
            ) as exc:
                record_event(
                    event_type="RECOVERY_FAILED",
                    workload_id=workload_id,
                    node_id=str(workload.node_id),
                    details={
                        "reason": "recovery_execution_error",
                        "error": str(exc),
                    },
                )

                print(
                    f"[CloudHeal] Could not recover workload "
                    f"{workload_id}: {exc}"
                )

        return detected_failures
