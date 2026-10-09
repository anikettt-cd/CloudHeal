import json
import subprocess
from uuid import UUID


class ContainerExecutionError(Exception):
    pass


def run_container(
    workload_id: UUID,
    image: str,
    cpu_limit: float,
    memory_limit_mb: int,
) -> dict:
    container_name = f"cloudheal-{workload_id}"

    inspect = subprocess.run(
        ["docker", "container", "inspect", container_name],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if inspect.returncode == 0:
        try:
            container = json.loads(inspect.stdout)[0]
        except (ValueError, IndexError, KeyError) as exc:
            raise ContainerExecutionError(
                "Could not inspect the existing container"
            ) from exc
        if container["State"]["Running"]:
            return {
                "workload_id": str(workload_id),
                "container_id": container["Id"],
                "container_name": container_name,
                "status": "RUNNING",
            }
        raise ContainerExecutionError(
            f"Container already exists but is not running: {container_name}"
        )
    command = [
        "docker",
        "run",
        "--detach",
        "--name",
        container_name,
        "--cpus",
        str(cpu_limit),
        "--memory",
        f"{memory_limit_mb}m",
        image,
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise ContainerExecutionError("Docker execution timed out") from exc
    except OSError as exc:
        raise ContainerExecutionError("Could not execute Docker CLI") from exc
    if result.returncode != 0:
        raise ContainerExecutionError(
            result.stderr.strip() or "Docker failed to start the container"
        )
    container_id = result.stdout.strip()
    verify = subprocess.run(
        ["docker", "container", "inspect", container_id],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    if verify.returncode != 0:
        raise ContainerExecutionError(
            "Container was created but could not be verified"
        )
    container = json.loads(verify.stdout)[0]
    if not container["State"]["Running"]:
        raise ContainerExecutionError("Container was created but is not running")
    return {
        "workload_id": str(workload_id),
        "container_id": container_id,
        "container_name": container_name,
        "status": "RUNNING",
    }
