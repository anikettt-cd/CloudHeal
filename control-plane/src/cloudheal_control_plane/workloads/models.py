from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class DesiredState(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"


class WorkloadState(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class WorkloadCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    image: str = Field(min_length=1, max_length=255)

    desired_state: DesiredState = DesiredState.RUNNING

    cpu_limit: float = Field(default=1.0, gt=0)
    memory_limit_mb: int = Field(default=256, gt=0)


class WorkloadRecord(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    workload_id: UUID = Field(default_factory=uuid4)

    name: str
    image: str

    desired_state: DesiredState = DesiredState.RUNNING
    actual_state: WorkloadState = WorkloadState.PENDING

    node_id: UUID | None = None

    cpu_limit: float
    memory_limit_mb: int

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC)
    )