from pydantic import BaseModel


class CPUInfo(BaseModel):
    physical_cores: int | None
    logical_cores: int | None
    usage_percent: float


class MemoryInfo(BaseModel):
    total_bytes: int
    available_bytes: int
    usage_percent: float


class DiskInfo(BaseModel):
    total_bytes: int
    free_bytes: int
    usage_percent: float


class Node(BaseModel):
    node_id: str
    hostname: str
    operating_system: str
    architecture: str

    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo