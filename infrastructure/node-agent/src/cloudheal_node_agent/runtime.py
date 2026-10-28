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

    try:
        inspect = subprocess.run(
            ["docker", "container", "inspect", container_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ContainerExecutionError(
            f"Could not inspect container: {exc}"
        ) from exc

    if inspect.returncode == 0:
        try:
            container = json.loads(inspect.stdout)[0]
            state = container["State"]
        except (ValueError, IndexError, KeyError, TypeError) as exc:
            raise ContainerExecutionError(
                "Could not inspect the existing container"
            ) from exc

        if not state["Running"]:
            try:
                restart = subprocess.run(
                    ["docker", "start", container_name],
                    capture_output=True,
                    text=True,
            encoding="utf-8",
            errors="replace",
                    timeout=30,
                    check=False,
                )
            except (subprocess.TimeoutExpired, OSError) as exc:
                raise ContainerExecutionError(
                    f"Could not restart container: {exc}"
                ) from exc

            if restart.returncode != 0:
                raise ContainerExecutionError(
                    restart.stderr.strip()
                    or "Docker failed to restart the container"
                )

        container_id = container["Id"]

    else:
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
            encoding="utf-8",
            errors="replace",
                timeout=300,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise ContainerExecutionError(
                "Docker execution timed out"
            ) from exc
        except OSError as exc:
            raise ContainerExecutionError(
                "Could not execute Docker CLI"
            ) from exc

        if result.returncode != 0:
            raise ContainerExecutionError(
                result.stderr.strip()
                or "Docker failed to start the container"
            )

        container_id = result.stdout.strip()

    try:
        verify = subprocess.run(
            ["docker", "container", "inspect", container_id],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ContainerExecutionError(
            f"Could not verify container: {exc}"
        ) from exc

    if verify.returncode != 0:
        raise ContainerExecutionError(
            "Container could not be verified"
        )

    try:
        container = json.loads(verify.stdout)[0]
    except (ValueError, IndexError, KeyError, TypeError) as exc:
        raise ContainerExecutionError(
            "Could not parse container verification result"
        ) from exc

    if not container["State"]["Running"]:
        raise ContainerExecutionError(
            "Container execution was attempted but it is not running"
        )

    return {
        "workload_id": str(workload_id),
        "container_id": container["Id"],
        "container_name": container_name,
        "status": "RUNNING",
    }

def get_container_status(workload_id: UUID) -> dict:
    container_name = f"cloudheal-{workload_id}"

    try:
        result = subprocess.run(
            ["docker", "container", "inspect", container_name],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise ContainerExecutionError(
            f"Could not inspect container: {exc}"
        ) from exc

    if result.returncode != 0:
        return {
            "workload_id": str(workload_id),
            "container_name": container_name,
            "status": "NOT_FOUND",
        }

    try:
        container = json.loads(result.stdout)[0]
        state = container["State"]
    except (ValueError, IndexError, KeyError, TypeError) as exc:
        raise ContainerExecutionError(
            "Could not parse container status"
        ) from exc

    if state["Running"]:
        status = "RUNNING"
    elif state["Status"] == "exited":
        status = "STOPPED"
    else:
        status = "UNKNOWN"

    return {
        "workload_id": str(workload_id),
        "container_id": container["Id"],
        "container_name": container_name,
        "status": status,
    }