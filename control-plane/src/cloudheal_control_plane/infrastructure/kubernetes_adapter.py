
import os
import re
from pathlib import Path

from kubernetes import client, config
from kubernetes.client.rest import ApiException

DEFAULT_KUBECONFIG_PATH = Path.home() / ".kube" / "cloudheal-k3s.yaml"

# Kubernetes DNS label/subdomain patterns used for resource names.
_DNS_LABEL_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
_DNS_SUBDOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$")


def _resolve_kubeconfig_path() -> str:
    """Resolve the kubeconfig value passed to the Kubernetes client.

    KUBECONFIG is honored verbatim so the client can perform its standard
    multi-file merge.  When it is unset, CloudHeal's dedicated kubeconfig is
    used.  An invalid or missing file is not replaced with a fallback; the
    Kubernetes client raises a clear configuration error instead.
    """

    raw = os.environ.get("KUBECONFIG", "").strip()

    if raw:
        return raw

    return str(DEFAULT_KUBECONFIG_PATH)


def _load_kubernetes_config() -> None:
    # persist_config=False prevents token/context updates from being written
    # back to the user's kubeconfig files.
    config.load_kube_config(
        config_file=_resolve_kubeconfig_path(),
        persist_config=False,
    )


def _name(value: str, field_name: str, *, namespace: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} is required")

    max_length = 63 if namespace else 253
    if len(value) > max_length:
        raise ValueError(f"{field_name} is too long")

    pattern = _DNS_LABEL_RE if namespace else _DNS_SUBDOMAIN_RE
    if not pattern.fullmatch(value):
        raise ValueError(f"{field_name} is not a valid Kubernetes name")

    return value


def get_deployment_status(namespace: str, name: str) -> dict:
    """Read a Kubernetes Deployment and its Pods without modifying them."""

    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    _load_kubernetes_config()

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()

    # Read the Deployment.
    deployment = apps_api.read_namespaced_deployment(
        name=nm,
        namespace=ns,
    )

    spec = deployment.spec
    status = deployment.status

    # Find Pods belonging to this Deployment.
    selector = getattr(spec, "selector", None)
    match_labels = getattr(selector, "match_labels", None) or {}

    pods = []

    if match_labels:
        label_selector = ",".join(
            f"{key}={value}"
            for key, value in match_labels.items()
        )

        pods_response = core_api.list_namespaced_pod(
            namespace=ns,
            label_selector=label_selector,
        )
        pod_items = pods_response.items
    else:
        pod_items = []

    for pod in pod_items:
        pod_status = pod.status
        container_statuses = pod_status.container_statuses or []

        pods.append(
            {
                "name": pod.metadata.name,
                "phase": pod_status.phase,
                "pod_ip": pod_status.pod_ip,
                "node_name": pod.spec.node_name,
                "ready": all(
                    container.ready for container in container_statuses
                ) if container_statuses else False,
                "containers": [
                    {
                        "name": container.name,
                        "ready": container.ready,
                        "restart_count": container.restart_count,
                        "state": (
                            next(
                                (
                                    state
                                    for state in ["running", "waiting", "terminated"]
                                    if getattr(container.state, state, None)
                                ),
                                "unknown",
                            )
                        ),
                    }
                    for container in container_statuses
                ],
            }
        )

    return {
        "namespace": ns,
        "deployment": nm,
        "desired_replicas": spec.replicas or 0,
        "ready_replicas": status.ready_replicas or 0,
        "available_replicas": status.available_replicas or 0,
        "conditions": [
            {
                "type": condition.type,
                "status": condition.status,
                "reason": condition.reason,
                "message": condition.message,
            }
            for condition in (status.conditions or [])
        ],
        "pods": pods,
    }

def restart_deployment(namespace: str, name: str) -> dict:
    """Trigger a Deployment rollout restart through the Kubernetes API."""

    from datetime import UTC, datetime

    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    _load_kubernetes_config()

    apps_api = client.AppsV1Api()
    restarted_at = datetime.now(UTC).isoformat()

    apps_api.patch_namespaced_deployment(
        name=nm,
        namespace=ns,
        body={
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "cloudheal.io/restarted-at": restarted_at,
                        }
                    }
                }
            }
        },
    )

    return {
        "namespace": ns,
        "deployment": nm,
        "restarted_at": restarted_at,
        "accepted": True,
    }


# Read-only Kubernetes discovery helpers (re-exported for backwards compatibility).
from .kubernetes_discovery import *  # noqa: F401,F403

