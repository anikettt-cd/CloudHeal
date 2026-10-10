import platform

import psutil

from cloudheal_node_agent.models import CPUInfo, DiskInfo, MemoryInfo


def get_system_info() -> dict:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "hostname": platform.node(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "cpu": CPUInfo(
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            usage_percent=cpu_usage,
        ),
        "memory": MemoryInfo(
            total_bytes=memory.total,
            available_bytes=memory.available,
            usage_percent=memory.percent,
        ),
        "disk": DiskInfo(
            total_bytes=disk.total,
            free_bytes=disk.free,
            usage_percent=disk.percent,
        ),
    }