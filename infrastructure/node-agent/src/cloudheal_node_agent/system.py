import platform

import psutil

from cloudheal_node_agent.models import CPUInfo, DiskInfo, MemoryInfo


def get_system_info() -> dict:
    return {
        "hostname": platform.node(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "cpu": CPUInfo(
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            usage_percent=psutil.cpu_percent(interval=1),
        ),
        "memory": MemoryInfo(
            total_bytes=psutil.virtual_memory().total,
            available_bytes=psutil.virtual_memory().available,
            usage_percent=psutil.virtual_memory().percent,
        ),
        "disk": DiskInfo(
            total_bytes=psutil.disk_usage("/").total,
            free_bytes=psutil.disk_usage("/").free,
            usage_percent=psutil.disk_usage("/").percent,
        ),
    }