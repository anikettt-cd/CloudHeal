import asyncio
import logging
import os

from cloudheal_control_plane.self_healing.detector import (
    detect_deployment_incident,
)
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    get_deployment_status,
)

from cloudheal_control_plane.self_healing.recovery_executor import (
    execute_recovery,
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

def is_auto_recovery_enabled() -> bool:
    """Return whether automatic recovery is explicitly enabled."""

    return os.getenv(
        "CLOUDHEAL_AUTO_RECOVERY_ENABLED",
        "false",
    ).strip().lower() in {"1", "true", "yes", "on"}


async def incident_monitor_loop() -> None:
    """Periodically inspect configured Deployments and record incidents."""

    configured_targets = get_monitor_targets()

    if configured_targets:
        logger.info(
            "Incident monitor started: targets=%s interval_seconds=%s",
            configured_targets,
            get_monitor_interval(),
        )
    else:
        logger.info(
            "Incident monitor started with no configured targets; "
            "Kubernetes monitoring is not configured. "
            "Set CLOUDHEAL_MONITOR_TARGETS to namespace/deployment pairs "
            "to enable monitoring. interval_seconds=%s",
            get_monitor_interval(),
        )
    attempted_incident_ids: set[int] = set()
    while True:
        try:
            targets = get_monitor_targets()

            if targets:
                logger.debug(
                    "Incident monitor cycle: targets=%s",
                    targets,
                )
            else:
                logger.debug(
                    "Incident monitor cycle: no targets configured"
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

                        if is_auto_recovery_enabled():
                            incident = result.get("incident")
                            incident_id = (
                                incident.get("incident_id")
                                if isinstance(incident, dict)
                                else None
                            )

                            if (
                                not isinstance(incident_id, int)
                                or isinstance(incident_id, bool)
                            ):
                                logger.error(
                                    "Automatic recovery skipped: invalid "
                                    "incident ID for %s/%s",
                                    namespace,
                                    deployment_name,
                                )
                            elif incident_id in attempted_incident_ids:
                                logger.info(
                                    "Automatic recovery already attempted "
                                    "for incident %s; skipping",
                                    incident_id,
                                )
                            else:
                                # Prevent another attempt on every monitor
                                # cycle during this monitor process.
                                attempted_incident_ids.add(incident_id)

                                recovery_result = await asyncio.to_thread(
                                    execute_recovery,
                                    result,
                                    trigger="automatic",
                                )

                                logger.info(
                                    "Automatic recovery result: "
                                    "incident_id=%s result=%s",
                                    incident_id,
                                    recovery_result,
                                )

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
