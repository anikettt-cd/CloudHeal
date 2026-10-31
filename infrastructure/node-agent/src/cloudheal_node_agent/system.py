import platform
from pathlib import Path

import psutil

from cloudheal_node_agent.models import CPUInfo, DiskInfo, MemoryInfo


def get_system_info() -> dict:
    hostname = platform.node()
    operating_system = platform.system()
    architecture = platform.machine()

    cpu = None
    memory = None
    disk = None
    metric_errors = {}

    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        cpu = CPUInfo(
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            usage_percent=cpu_usage,
        )
    except Exception as exc:  # noqa: BLE001
        metric_errors["cpu"] = str(exc)

    try:
        memory_result = psutil.virtual_memory()
        memory = MemoryInfo(
            total_bytes=memory_result.total,
            available_bytes=memory_result.available,
            usage_percent=memory_result.percent,
        )
    except Exception as exc:  # noqa: BLE001
        metric_errors["memory"] = str(exc)

    try:
        disk_path = (
            Path.home().anchor
            if operating_system == "Windows"
            else "/"
        )
        disk_result = psutil.disk_usage(disk_path)
        disk = DiskInfo(
            total_bytes=disk_result.total,
            free_bytes=disk_result.free,
            usage_percent=disk_result.percent,
        )
    except Exception as exc:  # noqa: BLE001
        metric_errors["disk"] = str(exc)

    result = {
        "hostname": hostname,
        "operating_system": operating_system,
        "architecture": architecture,
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
    }

    if metric_errors:
        result["metric_errors"] = metric_errors

    return result
