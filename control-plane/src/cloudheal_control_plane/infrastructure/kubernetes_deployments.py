from kubernetes import client
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.infrastructure import kubernetes_adapter
from cloudheal_control_plane.infrastructure.kubernetes_adapter import (
    _DNS_LABEL_RE,
    _DNS_SUBDOMAIN_RE,
)


def _load_kubernetes_config() -> None:
    # Keep a module-local binding so tests can patch this name; the actual
    # implementation lives in kubernetes_adapter.
    return kubernetes_adapter._load_kubernetes_config()


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


def create_deployment(namespace, name, image, replicas=1, container_port=80):
    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    if not image or not image.strip():
        raise ValueError("image is required")

    if replicas < 1 or replicas > 20:
        raise ValueError("replicas must be between 1 and 20")

    if container_port < 1 or container_port > 65535:
        raise ValueError("container_port must be between 1 and 65535")

    _load_kubernetes_config()
    apps_api = client.AppsV1Api()

    apps_api.create_namespaced_deployment(
        namespace=ns,
        body={
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": nm, "namespace": ns, "labels": {"app": nm}},
            "spec": {
                "replicas": replicas,
                "selector": {"matchLabels": {"app": nm}},
                "template": {
                    "metadata": {"labels": {"app": nm}},
                    "spec": {
                        "containers": [
                            {
                                "name": nm,
                                "image": image,
                                "ports": [{"containerPort": container_port}],
                            }
                        ]
                    },
                },
            },
        },
    )

    return {
        "namespace": ns,
        "deployment": nm,
        "image": image,
        "replicas": replicas,
        "container_port": container_port,
        "created": True,
    }


def scale_deployment(namespace, name, replicas):
    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    if replicas < 0 or replicas > 20:
        raise ValueError("replicas must be between 0 and 20")

    _load_kubernetes_config()
    apps_api = client.AppsV1Api()

    apps_api.patch_namespaced_deployment(
        name=nm,
        namespace=ns,
        body={"spec": {"replicas": replicas}},
    )

    return {"namespace": ns, "deployment": nm, "replicas": replicas, "accepted": True}


def delete_deployment(namespace, name):
    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    _load_kubernetes_config()
    apps_api = client.AppsV1Api()

    apps_api.delete_namespaced_deployment(name=nm, namespace=ns)

    # CloudHeal creates a same-named Service with each Deployment. Remove it
    # only when ownership can be established; missing or foreign Services are
    # left untouched. Unexpected API errors are propagated to the caller.
    delete_service(ns, nm)

    return {"namespace": ns, "deployment": nm, "deleted": True}


def _metadata_value(metadata, field_name):
    if metadata is None:
        return None
    if isinstance(metadata, dict):
        return metadata.get(field_name)
    return getattr(metadata, field_name, None)


def _service_is_cloudheal_owned(service, expected_name):
    metadata = _metadata_value(service, "metadata")
    labels = _metadata_value(metadata, "labels")

    if not isinstance(labels, dict):
        return False

    return labels.get("cloudheal.io/managed-by") == "cloudheal"


def delete_service(namespace, name):
    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    _load_kubernetes_config()
    core_api = client.CoreV1Api()

    try:
        service = core_api.read_namespaced_service(name=nm, namespace=ns)
    except ApiException as exc:
        if exc.status == 404:
            return {"namespace": ns, "service": nm, "deleted": True}
        raise

    if not _service_is_cloudheal_owned(service, nm):
        return {"namespace": ns, "service": nm, "deleted": False, "reason": "not_owned"}

    try:
        core_api.delete_namespaced_service(name=nm, namespace=ns)
    except ApiException as exc:
        if exc.status == 404:
            return {"namespace": ns, "service": nm, "deleted": True}
        raise

    return {"namespace": ns, "service": nm, "deleted": True}


def create_service(namespace, name, selector, port, target_port, service_type="NodePort"):

    ns = _name(namespace, "namespace", namespace=True)
    nm = _name(name, "name")

    if service_type not in {"ClusterIP", "NodePort", "LoadBalancer"}:
        raise ValueError("invalid service_type")

    if port < 1 or port > 65535 or target_port < 1 or target_port > 65535:
        raise ValueError("port and target_port must be between 1 and 65535")

    _load_kubernetes_config()
    core_api = client.CoreV1Api()

    created = core_api.create_namespaced_service(
        namespace=ns,
        body={
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": nm,
                "namespace": ns,
                "labels": {"app": nm, "cloudheal.io/managed-by": "cloudheal"},
                "annotations": {"cloudheal.io/managed-by": "cloudheal"},
            },
            "spec": {
                "type": service_type,
                "selector": selector,
                "ports": [{"port": port, "targetPort": target_port, "protocol": "TCP"}],
            },
        },
    )

    node_port = None

    try:
        ports = created.spec.ports or []
        node_port = ports[0].node_port if ports else None
    except (AttributeError, IndexError, TypeError):
        node_port = None

    return {
        "namespace": ns,
        "service": nm,
        "type": service_type,
        "port": port,
        "target_port": target_port,
        "node_port": node_port,
        "created": True,
    }


def ensure_namespace(namespace):
    ns = _name(namespace, "namespace", namespace=True)

    _load_kubernetes_config()
    core_api = client.CoreV1Api()

    try:
        core_api.read_namespace(name=ns)
        created = False
    except ApiException as exc:
        if exc.status != 404:
            raise

        try:
            core_api.create_namespace(
                body={"apiVersion": "v1", "kind": "Namespace", "metadata": {"name": ns}}
            )
            created = True
        except ApiException as exc:
            if exc.status == 409:
                created = False
            else:
                raise

    return {"namespace": ns, "created": created}
