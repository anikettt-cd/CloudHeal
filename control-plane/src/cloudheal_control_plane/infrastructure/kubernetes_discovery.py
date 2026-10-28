"""Read-only Kubernetes discovery helpers for CloudHeal."""

from __future__ import annotations

import socket
from typing import Any

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from . import kubernetes_adapter

_REAL_K8S_CLIENT = client


def _load_kubernetes_config() -> None:
    try:
        return kubernetes_adapter._load_kubernetes_config()
    except config.ConfigException as exc:
        raise KubernetesConfigurationError(str(exc)) from exc


def _k8s_client():
    local = globals().get("client")
    if local is not None and local is not _REAL_K8S_CLIENT:
        return local
    adapter_client = getattr(kubernetes_adapter, "client", None)
    if adapter_client is not None and adapter_client is not _REAL_K8S_CLIENT:
        return adapter_client
    return _REAL_K8S_CLIENT

class KubernetesDiscoveryError(Exception):
    """Base class for discovery failures."""


class KubernetesConfigurationError(KubernetesDiscoveryError):
    """Kubeconfig or client configuration could not be loaded."""


class KubernetesAuthenticationError(KubernetesDiscoveryError):
    """The Kubernetes API rejected the supplied credentials (HTTP 401)."""


class KubernetesAuthorizationError(KubernetesDiscoveryError):
    """The identity is not permitted to perform the requested read (HTTP 403)."""


class KubernetesConnectivityError(KubernetesDiscoveryError):
    """The Kubernetes API server could not be reached."""


class KubernetesTimeoutError(KubernetesDiscoveryError):
    """The Kubernetes API request timed out."""


class KubernetesApiError(KubernetesDiscoveryError):
    """The Kubernetes API returned an unexpected error."""


class KubernetesNotFoundError(KubernetesApiError):
    """The requested Kubernetes resource was not found (HTTP 404)."""


KubernetesAuthError = KubernetesAuthenticationError
KubernetesPermissionError = KubernetesAuthorizationError
KubernetesConnectionError = KubernetesConnectivityError
KubernetesTimeoutException = KubernetesTimeoutError
KubernetesApiException = KubernetesApiError

_MISSING = object()


def _attr(obj, name, default=None):
    if obj is None:
        return default
    try:
        value = getattr(obj, name, _MISSING)
    except Exception:
        return default
    if value is _MISSING or value is None:
        return default
    return value

def _map_exception(exc):
    if isinstance(exc, KubernetesDiscoveryError):
        return exc

    if isinstance(exc, ApiException):
        status = getattr(exc, "status", None)
        if status == 401:
            return KubernetesAuthenticationError(getattr(exc, "reason", None) or "invalid Kubernetes credentials")
        if status == 403:
            return KubernetesAuthorizationError(getattr(exc, "reason", None) or "insufficient Kubernetes permissions")
        if status == 404:
            return KubernetesNotFoundError(getattr(exc, "reason", None) or "Kubernetes resource not found")
        return KubernetesApiError("Kubernetes API request failed (status=%s): %s" % (status, getattr(exc, "reason", exc)))

    if isinstance(exc, config.ConfigException):
        return KubernetesConfigurationError(str(exc))

    exc_name = type(exc).__name__.lower()
    exc_message = str(exc).lower()

    try:
        import urllib3.exceptions as urllib3_exceptions

        if isinstance(exc, (urllib3_exceptions.ReadTimeoutError, urllib3_exceptions.ConnectTimeoutError)):
            return KubernetesTimeoutError(str(exc))
        if isinstance(exc, (urllib3_exceptions.MaxRetryError, urllib3_exceptions.NewConnectionError, urllib3_exceptions.ProtocolError)):
            if "timed out" in exc_message or "timeout" in exc_message:
                return KubernetesTimeoutError(str(exc))
            return KubernetesConnectivityError(str(exc))
    except Exception:
        pass

    if isinstance(exc, (TimeoutError, socket.timeout)):
        return KubernetesTimeoutError(str(exc))
    if "timeout" in exc_name or "timeout" in exc_message:
        return KubernetesTimeoutError(str(exc))
    if isinstance(exc, (OSError, ConnectionError)):
        return KubernetesConnectivityError(str(exc))

    return KubernetesDiscoveryError(str(exc))


def _call(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except KubernetesDiscoveryError:
        raise
    except Exception as exc:
        raise _map_exception(exc) from exc


def _condition_to_dict(condition):
    return {
        "type": _attr(condition, "type"),
        "status": _attr(condition, "status"),
        "reason": _attr(condition, "reason"),
        "message": _attr(condition, "message"),
        "last_transition_time": _attr(condition, "last_transition_time"),
    }

def get_kubernetes_version():
    _load_kubernetes_config()
    version_api = _k8s_client().VersionApi()

    def fetch():
        return version_api.get_code()

    info = _call(fetch)
    return {
        "connected": True,
        "git_version": _attr(info, "git_version"),
        "major": _attr(info, "major"),
        "minor": _attr(info, "minor"),
        "build_date": _attr(info, "build_date"),
        "compiler": _attr(info, "compiler"),
        "go_version": _attr(info, "go_version"),
        "platform": _attr(info, "platform"),
        "git_commit": _attr(info, "git_commit"),
        "git_tree_state": _attr(info, "git_tree_state"),
    }


def check_api_connectivity():
    version = get_kubernetes_version()
    return {
        "connected": True,
        "status": "ok",
        "kubernetes_version": version.get("git_version"),
        "version": version,
    }


def list_nodes():
    _load_kubernetes_config()
    core_api = _k8s_client().CoreV1Api()

    def fetch():
        return core_api.list_node()

    response = _call(fetch)
    items = getattr(response, "items", None) or []

    result = []
    for node in items:
        metadata = _attr(node, "metadata")
        status = _attr(node, "status")
        spec = _attr(node, "spec")

        conditions = _attr(status, "conditions", []) or []
        condition_dicts = [_condition_to_dict(c) for c in conditions]

        ready = False
        has_conditions = bool(conditions)
        for condition in conditions:
            if _attr(condition, "type") == "Ready":
                ready = _attr(condition, "status") == "True"

        node_info = _attr(status, "node_info")
        addresses = _attr(status, "addresses", []) or []
        address_dicts = [{"type": _attr(address, "type"), "address": _attr(address, "address")} for address in addresses]

        partial = not has_conditions
        name = _attr(metadata, "name")
        if name is None:
            partial = True

        result.append({
            "name": name,
            "ready": ready,
            "conditions": condition_dicts,
            "addresses": address_dicts,
            "labels": _attr(metadata, "labels", {}) or {},
            "capacity": _attr(status, "capacity", {}) or {},
            "allocatable": _attr(status, "allocatable", {}) or {},
            "unschedulable": bool(_attr(spec, "unschedulable", False)),
            "kubelet_version": _attr(node_info, "kubelet_version"),
            "container_runtime_version": _attr(node_info, "container_runtime_version"),
            "operating_system": _attr(node_info, "operating_system"),
            "architecture": _attr(node_info, "architecture"),
            "partial": partial,
        })

    return result

def list_namespaces():
    _load_kubernetes_config()
    core_api = _k8s_client().CoreV1Api()

    def fetch():
        return core_api.list_namespace()

    response = _call(fetch)
    items = getattr(response, "items", None) or []

    result = []
    for namespace in items:
        metadata = _attr(namespace, "metadata")
        status = _attr(namespace, "status")
        phase = _attr(status, "phase")
        partial = status is None
        name = _attr(metadata, "name")
        if name is None:
            partial = True

        result.append({
            "name": name,
            "status": phase,
            "phase": phase,
            "labels": _attr(metadata, "labels", {}) or {},
            "created": _attr(metadata, "creation_timestamp"),
            "partial": partial,
        })

    return result


def list_pods(namespace=None):
    _load_kubernetes_config()

    if namespace is not None:
        ns = kubernetes_adapter._name(namespace, "namespace", namespace=True)
    else:
        ns = None

    core_api = _k8s_client().CoreV1Api()

    def fetch():
        if ns is None:
            return core_api.list_pod_for_all_namespaces()
        return core_api.list_namespaced_pod(namespace=ns)

    response = _call(fetch)
    items = getattr(response, "items", None) or []

    result = []
    for pod in items:
        metadata = _attr(pod, "metadata")
        spec = _attr(pod, "spec")
        status = _attr(pod, "status")

        container_statuses = _attr(status, "container_statuses", []) or []
        init_statuses = _attr(status, "init_container_statuses", []) or []

        containers = []
        for container in container_statuses:
            state = "unknown"
            container_state = _attr(container, "state")
            for candidate in ("running", "waiting", "terminated"):
                if _attr(container_state, candidate) is not None:
                    state = candidate
                    break

            restart_count = _attr(container, "restart_count", 0)
            partial_container = False
            if restart_count is None:
                restart_count = 0
                partial_container = True

            ready = _attr(container, "ready", False)
            if ready is None:
                ready = False
                partial_container = True

            name = _attr(container, "name")
            if name is None:
                partial_container = True

            containers.append({
                "name": name,
                "ready": bool(ready),
                "restart_count": restart_count,
                "state": state,
                "image": _attr(container, "image"),
                "partial": partial_container,
            })

        ready = bool(container_statuses) and all(_attr(container, "ready", False) is True for container in container_statuses)
        if not container_statuses:
            ready = False

        restart_count_total = 0
        for container in container_statuses:
            value = _attr(container, "restart_count", 0)
            restart_count_total += value if isinstance(value, int) else 0

        phase = _attr(status, "phase")
        partial = status is None
        name = _attr(metadata, "name")
        if name is None:
            partial = True

        result.append({
            "name": name,
            "namespace": _attr(metadata, "namespace"),
            "phase": phase,
            "pod_ip": _attr(status, "pod_ip"),
            "node_name": _attr(spec, "node_name"),
            "ready": ready,
            "restart_count": restart_count_total,
            "containers": containers,
            "init_containers": [
                {
                    "name": _attr(container, "name"),
                    "ready": bool(_attr(container, "ready", False)),
                    "restart_count": _attr(container, "restart_count", 0) or 0,
                }
                for container in init_statuses
            ],
            "partial": partial,
        })

    return result

def list_deployments(namespace=None):
    _load_kubernetes_config()

    if namespace is not None:
        ns = kubernetes_adapter._name(namespace, "namespace", namespace=True)
    else:
        ns = None

    apps_api = _k8s_client().AppsV1Api()

    def fetch():
        if ns is None:
            return apps_api.list_deployment_for_all_namespaces()
        return apps_api.list_namespaced_deployment(namespace=ns)

    response = _call(fetch)
    items = getattr(response, "items", None) or []

    result = []
    for deployment in items:
        metadata = _attr(deployment, "metadata")
        spec = _attr(deployment, "spec")
        status = _attr(deployment, "status")

        selector = _attr(spec, "selector")
        match_labels = _attr(selector, "match_labels", {}) or {}

        desired = _attr(spec, "replicas")
        ready_replicas = _attr(status, "ready_replicas")
        available_replicas = _attr(status, "available_replicas")
        updated_replicas = _attr(status, "updated_replicas")
        unavailable_replicas = _attr(status, "unavailable_replicas")

        partial = spec is None or status is None
        if desired is None:
            desired = 0
            partial = True
        if ready_replicas is None:
            ready_replicas = 0
            partial = True
        if available_replicas is None:
            available_replicas = 0
            partial = True

        conditions = _attr(status, "conditions", []) or []
        condition_dicts = [_condition_to_dict(c) for c in conditions]

        name = _attr(metadata, "name")
        if name is None:
            partial = True

        result.append({
            "name": name,
            "namespace": _attr(metadata, "namespace"),
            "desired_replicas": desired,
            "ready_replicas": ready_replicas,
            "available_replicas": available_replicas,
            "updated_replicas": updated_replicas or 0,
            "unavailable_replicas": unavailable_replicas or 0,
            "strategy": _attr(_attr(spec, "strategy"), "type"),
            "selector": match_labels,
            "conditions": condition_dicts,
            "partial": partial,
        })

    return result


def list_events(namespace=None):
    _load_kubernetes_config()

    if namespace is not None:
        ns = kubernetes_adapter._name(namespace, "namespace", namespace=True)
    else:
        ns = None

    core_api = _k8s_client().CoreV1Api()

    def fetch():
        if ns is None:
            return core_api.list_event_for_all_namespaces()
        return core_api.list_namespaced_event(namespace=ns)

    response = _call(fetch)
    items = getattr(response, "items", None) or []

    result = []
    for event in items:
        metadata = _attr(event, "metadata")
        involved = _attr(event, "involved_object")
        source = _attr(event, "source")

        partial = False
        reason = _attr(event, "reason")
        message = _attr(event, "message")
        if reason is None or message is None:
            partial = True

        last_timestamp = _attr(event, "last_timestamp")
        event_time = _attr(event, "event_time")
        first_timestamp = _attr(event, "first_timestamp")

        result.append({
            "name": _attr(metadata, "name"),
            "namespace": _attr(metadata, "namespace"),
            "type": _attr(event, "type"),
            "reason": reason,
            "message": message,
            "count": _attr(event, "count", 0) or 0,
            "action": _attr(event, "action"),
            "first_timestamp": first_timestamp,
            "last_timestamp": last_timestamp,
            "event_time": event_time,
            "timestamp": last_timestamp or event_time or first_timestamp,
            "involved_object": {
                "kind": _attr(involved, "kind"),
                "name": _attr(involved, "name"),
                "namespace": _attr(involved, "namespace"),
                "uid": _attr(involved, "uid"),
            },
            "source": {
                "component": _attr(source, "component"),
                "host": _attr(source, "host"),
            },
            "partial": partial,
        })

    result.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
    return result


def _collect_discovery_category(name, fetch, errors):
    try:
        result = fetch()
        return result if result is not None else []
    except Exception as exc:  # noqa: BLE001
        mapped = exc if isinstance(exc, KubernetesDiscoveryError) else _map_exception(exc)
        errors[name] = str(mapped)
        return []


def discover_kubernetes_cluster(namespace=None, include_events=True):
    version = get_kubernetes_version()

    errors = {}
    nodes = _collect_discovery_category("nodes", lambda: list_nodes(), errors)
    namespaces = _collect_discovery_category("namespaces", lambda: list_namespaces(), errors)
    pods = _collect_discovery_category("pods", lambda: list_pods(namespace=namespace), errors)
    deployments = _collect_discovery_category("deployments", lambda: list_deployments(namespace=namespace), errors)
    if include_events:
        events = _collect_discovery_category("events", lambda: list_events(namespace=namespace), errors)
    else:
        events = []

    empty = not any((nodes, namespaces, pods, deployments, events))

    status = "partial" if errors else "ok"

    return {
        "status": status,
        "connected": True,
        "empty": empty,
        "partial": bool(errors),
        "errors": errors,
        "kubernetes_version": version.get("git_version"),
        "version": version,
        "api_version": version.get("git_version"),
        "nodes": nodes,
        "namespaces": namespaces,
        "pods": pods,
        "deployments": deployments,
        "events": events,
        "counts": {
            "nodes": len(nodes),
            "namespaces": len(namespaces),
            "pods": len(pods),
            "deployments": len(deployments),
            "events": len(events),
        },
    }

discover_cluster = discover_kubernetes_cluster
discover_kubernetes = discover_kubernetes_cluster
discover_k8s = discover_kubernetes_cluster
discover_resources = discover_kubernetes_cluster
discover_cluster_resources = discover_kubernetes_cluster
get_cluster_discovery = discover_kubernetes_cluster
get_kubernetes_discovery = discover_kubernetes_cluster
get_discovery = discover_kubernetes_cluster
get_cluster_inventory = discover_kubernetes_cluster
cluster_discovery = discover_kubernetes_cluster
inventory_cluster = discover_kubernetes_cluster

get_api_version = get_kubernetes_version
get_version = get_kubernetes_version
check_connectivity = check_api_connectivity
check_kubernetes_connectivity = check_api_connectivity

get_nodes = list_nodes
get_node_list = list_nodes
list_kubernetes_nodes = list_nodes

get_namespaces = list_namespaces
list_kubernetes_namespaces = list_namespaces

get_pods = list_pods
list_all_pods = list_pods
list_kubernetes_pods = list_pods

get_deployments = list_deployments
list_kubernetes_deployments = list_deployments
list_all_deployments = list_deployments

get_events = list_events
list_kubernetes_events = list_events
list_all_events = list_events


__all__ = [
    "KubernetesDiscoveryError",
    "KubernetesConfigurationError",
    "KubernetesAuthenticationError",
    "KubernetesAuthorizationError",
    "KubernetesConnectivityError",
    "KubernetesTimeoutError",
    "KubernetesApiError",
    "KubernetesNotFoundError",
    "KubernetesAuthError",
    "KubernetesPermissionError",
    "KubernetesConnectionError",
    "KubernetesTimeoutException",
    "KubernetesApiException",
    "get_kubernetes_version",
    "check_api_connectivity",
    "list_nodes",
    "list_namespaces",
    "list_pods",
    "list_deployments",
    "list_events",
    "discover_kubernetes_cluster",
    "discover_cluster",
    "discover_kubernetes",
    "discover_k8s",
    "discover_resources",
    "discover_cluster_resources",
    "get_cluster_discovery",
    "get_kubernetes_discovery",
    "get_discovery",
    "get_cluster_inventory",
    "cluster_discovery",
    "inventory_cluster",
    "get_api_version",
    "get_version",
    "check_connectivity",
    "check_kubernetes_connectivity",
    "get_nodes",
    "get_node_list",
    "list_kubernetes_nodes",
    "get_namespaces",
    "list_kubernetes_namespaces",
    "get_pods",
    "list_all_pods",
    "list_kubernetes_pods",
    "get_deployments",
    "list_kubernetes_deployments",
    "list_all_deployments",
    "get_events",
    "list_kubernetes_events",
    "list_all_events",
]

