import asyncio
import logging
import os

from cloudheal_control_plane.self_healing.detector import (
    detect_deployment_incident,
)
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)

__all__ = ["detect_deployment_incident"]


logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 15


def get_monitor_targets() -> list[tuple[str, str]]:
    """Return explicitly configured Kubernetes namespace/deployment pairs."""

    raw_targets = os.getenv("CLOUDHEAL_MONITOR_TARGETS", "").strip()

    if not raw_targets:
        return []

    targets = []

    for item in raw_targets.split(","):
        parts = item.strip().split("/")

        if len(parts) != 2 or not all(parts):
            logger.warning(
                "Ignoring invalid monitoring target: %s. "
                "Expected namespace/deployment.",
                item,
            )
            continue

        targets.append((parts[0], parts[1]))

    return targets


def get_monitor_interval() -> int:
    """Return the monitoring interval, with a safe minimum of one second."""

    raw_interval = os.getenv(
        "CLOUDHEAL_MONITOR_INTERVAL_SECONDS",
        str(DEFAULT_INTERVAL_SECONDS),
    )

    try:
        return max(1, int(raw_interval))
    except ValueError:
        logger.warning(
            "Invalid monitoring interval %r; using %s seconds.",
            raw_interval,
            DEFAULT_INTERVAL_SECONDS,
        )
        return DEFAULT_INTERVAL_SECONDS


async def incident_monitor_loop() -> None:
    """Periodically inspect configured Deployments and record incidents."""

    logger.warning(
        "Incident monitor started: targets=%s interval_seconds=%s",
        get_monitor_targets(),
        get_monitor_interval(),
    )

    while True:
        try:
            targets = get_monitor_targets()

            logger.warning(
                "Incident monitor cycle: targets=%s",
                targets,
            )

            for namespace, deployment_name in targets:
                try:
                    result = await asyncio.to_thread(
                        detect_deployment_incident,
                        namespace,
                        deployment_name,
                        get_deployment_status
                    )

                    logger.warning(
                       "Incident monitor detector returned: %s/%s classification=%s",
                        namespace,
                        deployment_name,
                        result["classification"],
                    )


                    if result["incident_detected"]:
                        logger.warning(
                            "Incident detected: namespace=%s deployment=%s "
                            "classification=%s observed_at=%s",
                            namespace,
                            deployment_name,
                            result["classification"],
                            result["observed_at"],
                        )
                    else:
                        logger.info(
                            "Incident monitor check completed: namespace=%s "
                            "deployment=%s classification=%s observed_at=%s",
                            namespace,
                            deployment_name,
                            result["classification"],
                            result["observed_at"],
                        )

                except Exception:
                    logger.exception(
                        "Incident monitoring failed for %s/%s",
                        namespace,
                        deployment_name,
                    )

        except Exception:
            logger.exception("Incident monitoring cycle failed")

        await asyncio.sleep(get_monitor_interval())