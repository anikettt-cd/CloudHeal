import json
import shutil
import subprocess


def get_runtime_info() -> dict:
    """
    Discover Docker runtime availability and resource information.

    This function only inspects the runtime.
    It does not start, stop, or modify containers.
    """

    if shutil.which("docker") is None:
        return {
            "available": False,
            "runtime": "docker",
            "version": None,
            "operating_system": None,
            "architecture": None,
            "cpu_count": None,
            "memory_bytes": None,
            "error": "Docker CLI was not found",
        }

    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{json .}}"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )

    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "runtime": "docker",
            "version": None,
            "operating_system": None,
            "architecture": None,
            "cpu_count": None,
            "memory_bytes": None,
            "error": "Docker runtime discovery timed out",
        }

    except OSError as exc:
        return {
            "available": False,
            "runtime": "docker",
            "version": None,
            "operating_system": None,
            "architecture": None,
            "cpu_count": None,
            "memory_bytes": None,
            "error": f"Could not execute Docker CLI: {exc}",
        }

    if result.returncode != 0:
        return {
            "available": False,
            "runtime": "docker",
            "version": None,
            "operating_system": None,
            "architecture": None,
            "cpu_count": None,
            "memory_bytes": None,
            "error": result.stderr.strip() or "Docker runtime is unavailable",
        }

    try:
        info = json.loads(result.stdout)

    except json.JSONDecodeError:
        return {
            "available": False,
            "runtime": "docker",
            "version": None,
            "operating_system": None,
            "architecture": None,
            "cpu_count": None,
            "memory_bytes": None,
            "error": "Docker returned invalid JSON",
        }

    try:
        version_result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )

        version = (
            version_result.stdout.strip()
            if version_result.returncode == 0
            else None
        )

        return {
            "available": True,
            "runtime": "docker",
            "version": version,
            "operating_system": info.get("OperatingSystem"),
            "architecture": info.get("Architecture"),
            "cpu_count": info.get("NCPU"),
            "memory_bytes": (
                int(info["MemTotal"])
                if info.get("MemTotal") is not None
                else None
            ),
            "error": None,
        }

    except (OSError, subprocess.TimeoutExpired):
        # Docker info succeeded, so runtime discovery is still usable.
        return {
            "available": True,
            "runtime": "docker",
            "version": None,
            "operating_system": info.get("OperatingSystem"),
            "architecture": info.get("Architecture"),
            "cpu_count": info.get("NCPU"),
            "memory_bytes": (
                int(info["MemTotal"])
                if info.get("MemTotal") is not None
                else None
            ),
            "error": None,
        }
        