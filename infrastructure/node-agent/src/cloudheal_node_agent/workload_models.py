from uuid import UUID

from pydantic import BaseModel, Field


class ContainerRunRequest(BaseModel):
    workload_id: UUID
    image: str = Field(min_length=1, max_length=255)
    cpu_limit: float = Field(gt=0, le=8)
    memory_limit_mb: int = Field(gt=0, le=2048)
