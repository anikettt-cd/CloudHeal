from kubernetes import client, config
from kubernetes.client.rest import ApiException


def get_deployment_status(namespace: str, name: str) -> dict:
    """Read a Kubernetes Deployment and its Pods without modifying them."""

    # Load the user's existing kubectl configuration.
    config.load_kube_config()

    apps_api = client.AppsV1Api()
    core_api = client.CoreV1Api()

    # Read the Deployment.
    deployment = apps_api.read_namespaced_deployment(
        name=name,
        namespace=namespace,
    )

    spec = deployment.spec
    status = deployment.status

    # Find Pods belonging to this Deployment.
    match_labels = spec.selector.match_labels or {}

    label_selector = ",".join(
        f"{key}={value}"
        for key, value in match_labels.items()
    )

    pods_response = core_api.list_namespaced_pod(
        namespace=namespace,
        label_selector=label_selector,
    )

    pods = []

    for pod in pods_response.items:
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
        "namespace": namespace,
        "deployment": name,
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