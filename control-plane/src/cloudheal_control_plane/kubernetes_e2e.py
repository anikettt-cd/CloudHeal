"""Repeatable Kubernetes end-to-end lifecycle validation for CloudHeal.

This module is intentionally not part of the default pytest suite. It performs
real Kubernetes mutations and must be invoked explicitly by an operator.
"""

from __future__ import annotations

import os
import sys
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

import httpx
from kubernetes import client, config
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.infrastructure import kubernetes_adapter
from cloudheal_control_plane.infrastructure import kubernetes_deployments


PROTECTED_NAMESPACES = {
    "cloudheal-test",
    "kube-system",
    "kube-public",
    "kube-node-lease",
    "default",
}

PROTECTED_DEPLOYMENTS = {
    "cloudheal-test": ["cloudheal-demo", "cloudheal-recovery-demo"],
}


class E2EError(Exception):
    """Raised when the E2E lifecycle cannot continue safely."""


@dataclass
class E2EConfig:
    api_url: str
    namespace: str
    deployment: str
    service: str
    image: str
    replicas_up: int = 2
    replicas_down: int = 1
    timeout_seconds: int = 120
    poll_interval: int = 5


def validate_config(config: E2EConfig) -> None:
    if not config.api_url:
        raise E2EError("CLOUDHEAL_API_URL is required")
    if not config.namespace:
        raise E2EError("CLOUDHEAL_E2E_NAMESPACE is required")
    if not config.deployment:
        raise E2EError("CLOUDHEAL_E2E_DEPLOYMENT is required")
    if not config.image:
        raise E2EError("CLOUDHEAL_E2E_IMAGE is required")
    if config.namespace in PROTECTED_NAMESPACES:
        raise E2EError(f"Refusing to use protected namespace: {config.namespace}")
    if config.replicas_up < 1 or config.replicas_down < 0:
        raise E2EError("Replica counts must be non-negative and scale-up must be >= 1")
    if config.timeout_seconds <= 0 or config.poll_interval <= 0:
        raise E2EError("Timeout and poll interval must be positive")


def is_protected_namespace(namespace: str) -> bool:
    return namespace in PROTECTED_NAMESPACES


def _load_kube_config() -> None:
    kubernetes_adapter._load_kubernetes_config()


def deployment_exists(namespace: str, name: str) -> bool:
    try:
        kubernetes_adapter.get_deployment_status(namespace, name)
        return True
    except ApiException as exc:
        if exc.status == 404:
            return False
        raise


def service_exists(namespace: str, name: str) -> bool:
    _load_kube_config()
    core_api = client.CoreV1Api()
    try:
        core_api.read_namespaced_service(name=name, namespace=namespace)
        return True
    except ApiException as exc:
        if exc.status == 404:
            return False
        raise


def check_collisions(config: E2EConfig) -> None:
    if deployment_exists(config.namespace, config.deployment):
        raise E2EError(f"Deployment already exists: {config.namespace}/{config.deployment}")
    if service_exists(config.namespace, config.service):
        raise E2EError(f"Service already exists: {config.namespace}/{config.service}")


def wait_for_deployment_ready(
    fetch_status: Callable[[], Dict[str, Any]],
    desired_replicas: int,
    timeout_seconds: int,
    poll_interval: int,
) -> Dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    last_status: Optional[Dict[str, Any]] = None
    while time.monotonic() < deadline:
        status = fetch_status()
        last_status = status
        ready_replicas = int(status.get("ready_replicas") or 0)
        available_replicas = int(status.get("available_replicas") or 0)
        pods = status.get("pods") or []
        all_pods_ready = bool(pods) and all(p.get("ready") is True for p in pods)
        if ready_replicas >= desired_replicas and available_replicas >= desired_replicas:
            if desired_replicas == 0 or all_pods_ready:
                return status
        time.sleep(poll_interval)
    raise TimeoutError(
        f"Deployment did not reach {desired_replicas} ready replicas within "
        f"{timeout_seconds}s; last status: {last_status}"
    )
def protected_baseline() -> Dict[str, Optional[Dict[str, Any]]]:
    baseline: Dict[str, Optional[Dict[str, Any]]] = {}
    for namespace, deployments in PROTECTED_DEPLOYMENTS.items():
        for name in deployments:
            try:
                baseline[f"{namespace}/{name}"] = kubernetes_adapter.get_deployment_status(namespace, name)
            except ApiException as exc:
                if exc.status == 404:
                    baseline[f"{namespace}/{name}"] = None
                else:
                    raise
            except Exception:
                baseline[f"{namespace}/{name}"] = None
    return baseline


def protected_changed(
    baseline: Dict[str, Optional[Dict[str, Any]]],
    current: Dict[str, Optional[Dict[str, Any]]],
) -> bool:
    return baseline != current


def create_namespace_if_needed(namespace: str) -> bool:
    _load_kube_config()
    result = kubernetes_deployments.ensure_namespace(namespace)
    return bool(result.get("created"))


def delete_namespace_if_created(namespace: str) -> None:
    _load_kube_config()
    core_api = client.CoreV1Api()
    core_api.delete_namespace(name=namespace)
def run_lifecycle(config: E2EConfig) -> int:
    api_url = ""
    created_namespace = False
    created_deployment = False
    created_service = False
    cleanup_errors: List[str] = []
    baseline: Dict[str, Optional[Dict[str, Any]]] = {}

    def fetch_status() -> Dict[str, Any]:
        return kubernetes_adapter.get_deployment_status(config.namespace, config.deployment)

    try:
        validate_config(config)
        check_collisions(config)

        api_url = config.api_url.rstrip("/")
        baseline = protected_baseline()

        health = httpx.get(f"{api_url}/health", timeout=5.0)
        health.raise_for_status()

        created_namespace = create_namespace_if_needed(config.namespace)

        response = httpx.post(
            f"{api_url}/infrastructure/kubernetes/namespaces/{config.namespace}/deployments",
            json={
                "name": config.deployment,
                "image": config.image,
                "replicas": config.replicas_down,
                "container_port": 80,
                "service_type": "ClusterIP",
                "service_port": 80,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        created_deployment = True
        created_service = True

        wait_for_deployment_ready(
            fetch_status, config.replicas_down, config.timeout_seconds, config.poll_interval
        )

        scale_up = httpx.post(
            f"{api_url}/infrastructure/kubernetes/namespaces/{config.namespace}/deployments/{config.deployment}/scale",
            json={"replicas": config.replicas_up},
            timeout=30.0,
        )
        scale_up.raise_for_status()
        wait_for_deployment_ready(
            fetch_status, config.replicas_up, config.timeout_seconds, config.poll_interval
        )

        scale_down = httpx.post(
            f"{api_url}/infrastructure/kubernetes/namespaces/{config.namespace}/deployments/{config.deployment}/scale",
            json={"replicas": config.replicas_down},
            timeout=30.0,
        )
        scale_down.raise_for_status()
        wait_for_deployment_ready(
            fetch_status, config.replicas_down, config.timeout_seconds, config.poll_interval
        )

        delete_response = httpx.delete(
            f"{api_url}/infrastructure/kubernetes/namespaces/{config.namespace}/deployments/{config.deployment}",
            timeout=30.0,
        )
        delete_response.raise_for_status()
        created_deployment = False
        created_service = False

        deadline = time.monotonic() + config.timeout_seconds
        while time.monotonic() < deadline:
            if not deployment_exists(config.namespace, config.deployment):
                break
            time.sleep(config.poll_interval)
        else:
            raise E2EError("Deployment still exists after deletion")
        if service_exists(config.namespace, config.service):
            raise E2EError("Service still exists after deletion")

        if created_namespace:
            delete_namespace_if_created(config.namespace)
            created_namespace = False

        current = protected_baseline()
        if protected_changed(baseline, current):
            raise E2EError("Protected workloads changed during E2E run")

        print("PASS: Kubernetes E2E lifecycle completed successfully")
        return 0

    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        if created_deployment:
            try:
                httpx.delete(
                    f"{api_url}/infrastructure/kubernetes/namespaces/{config.namespace}/deployments/{config.deployment}",
                    timeout=30.0,
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                cleanup_errors.append(f"deployment cleanup: {cleanup_exc}")
            created_deployment = False
            created_service = False
        if created_service:
            try:
                kubernetes_deployments.delete_service(config.namespace, config.service)
            except Exception as cleanup_exc:  # noqa: BLE001
                cleanup_errors.append(f"service cleanup: {cleanup_exc}")
            created_service = False
        if created_namespace:
            try:
                delete_namespace_if_created(config.namespace)
            except Exception as cleanup_exc:  # noqa: BLE001
                cleanup_errors.append(f"namespace cleanup: {cleanup_exc}")
            created_namespace = False

        for error in cleanup_errors:
            print(f"CLEANUP ERROR: {error}")

        try:
            current = protected_baseline()
            if protected_changed(baseline, current):
                print("WARNING: Protected workloads changed during failed run")
        except Exception as check_exc:  # noqa: BLE001
            print(f"Protected workload check failed: {check_exc}")

        return 1
def _config_from_env() -> E2EConfig:
    return E2EConfig(
        api_url=os.environ.get("CLOUDHEAL_API_URL", "").strip(),
        namespace=os.environ.get("CLOUDHEAL_E2E_NAMESPACE", "").strip(),
        deployment=os.environ.get("CLOUDHEAL_E2E_DEPLOYMENT", "").strip(),
        service=os.environ.get("CLOUDHEAL_E2E_SERVICE", "").strip()
        or os.environ.get("CLOUDHEAL_E2E_DEPLOYMENT", "").strip(),
        image=os.environ.get("CLOUDHEAL_E2E_IMAGE", "").strip(),
        replicas_up=int(os.environ.get("CLOUDHEAL_E2E_REPLICAS_UP", "2")),
        replicas_down=int(os.environ.get("CLOUDHEAL_E2E_REPLICAS_DOWN", "1")),
        timeout_seconds=int(os.environ.get("CLOUDHEAL_E2E_TIMEOUT", "120")),
        poll_interval=int(os.environ.get("CLOUDHEAL_E2E_POLL_INTERVAL", "5")),
    )


def main(argv: Optional[List[str]] = None) -> int:
    try:
        config = _config_from_env()
        return run_lifecycle(config)
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    import sys as _sys

    _sys.exit(main())
