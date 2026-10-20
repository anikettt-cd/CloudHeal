import json
from uuid import UUID

from cloudheal_control_plane.database import get_connection
from cloudheal_control_plane.workloads.models import WorkloadRecord


class WorkloadRegistry:
    @staticmethod
    def _to_record(row) -> WorkloadRecord:
        return WorkloadRecord.model_validate(
            {
                "workload_id": row["workload_id"],
                "name": row["name"],
                "image": row["image"],
                "desired_state": row["desired_state"],
                "actual_state": row["actual_state"],
                "node_id": row["node_id"],
                "cpu_limit": row["cpu_limit"],
                "memory_limit_mb": row["memory_limit_mb"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )

    def create_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        with get_connection() as connection:
            connection.execute(
                """
                INSERT INTO workloads (
                    workload_id, name, image, desired_state,
                    actual_state, node_id, cpu_limit,
                    memory_limit_mb, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(workload.workload_id),
                    workload.name,
                    workload.image,
                    workload.desired_state.value,
                    workload.actual_state.value,
                    str(workload.node_id) if workload.node_id else None,
                    workload.cpu_limit,
                    workload.memory_limit_mb,
                    workload.created_at.isoformat(),
                    workload.updated_at.isoformat(),
                ),
            )
        return workload

    def get_workload(self, workload_id: UUID) -> WorkloadRecord | None:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT * FROM workloads WHERE workload_id = ?",
                (str(workload_id),),
            ).fetchone()

        return self._to_record(row) if row else None

    def list_workloads(self) -> list[WorkloadRecord]:
        with get_connection() as connection:
            rows = connection.execute(
                "SELECT * FROM workloads ORDER BY created_at"
            ).fetchall()

        return [self._to_record(row) for row in rows]

    def update_workload(self, workload: WorkloadRecord) -> WorkloadRecord:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE workloads
                SET name = ?,
                    image = ?,
                    desired_state = ?,
                    actual_state = ?,
                    node_id = ?,
                    cpu_limit = ?,
                    memory_limit_mb = ?,
                    created_at = ?,
                    updated_at = ?
                WHERE workload_id = ?
                """,
                (
                    workload.name,
                    workload.image,
                    workload.desired_state.value,
                    workload.actual_state.value,
                    str(workload.node_id) if workload.node_id else None,
                    workload.cpu_limit,
                    workload.memory_limit_mb,
                    workload.created_at.isoformat(),
                    workload.updated_at.isoformat(),
                    str(workload.workload_id),
                ),
            )

            if cursor.rowcount == 0:
                raise LookupError(
                    f"Workload not found: {workload.workload_id}"
                )

        return workload
