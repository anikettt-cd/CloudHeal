from types import SimpleNamespace
from unittest.mock import patch

import pytest
from kubernetes.client.rest import ApiException

from cloudheal_control_plane.infrastructure.kubernetes_discovery import (
    KubernetesAuthenticationError,
    KubernetesAuthorizationError,
    KubernetesConnectivityError,
    KubernetesTimeoutError,
    discover_kubernetes_cluster,
    get_kubernetes_version,
    list_deployments,
    list_events,
    list_namespaces,
    list_nodes,
    list_pods,
)


def V():
    return SimpleNamespace(git_version="v1.36.5+k3s1", major="1", minor="36",
                           build_date="x", compiler="gc", go_version="go",
                           platform="linux", git_commit="abc", git_tree_state="clean")


def N(ready=True):
    cond = SimpleNamespace(type="Ready", status="True" if ready else "False",
                           reason="r", message="m", last_transition_time="t")
    info = SimpleNamespace(kubelet_version="v", container_runtime_version="containerd",
                           operating_system="linux", architecture="amd64")
    st = SimpleNamespace(conditions=[cond], addresses=[], capacity={},
                        allocatable={}, node_info=info)
    return SimpleNamespace(metadata=SimpleNamespace(name="node", labels={}),
                          spec=SimpleNamespace(unschedulable=False), status=st)

def NS():
    return SimpleNamespace(metadata=SimpleNamespace(name="default", labels={},
                                                  creation_timestamp="t"),
                          status=SimpleNamespace(phase="Active"))


def CS(ready=True, rc=0):
    st = SimpleNamespace(running=object(), waiting=None, terminated=None)
    return SimpleNamespace(name="c", ready=ready, restart_count=rc, state=st,
                          image="img")


def POD(ready=True, rc=0, partial=False):
    st = None if partial else SimpleNamespace(phase="Running", pod_ip="1.2.3.4",
                                           container_statuses=[CS(ready=ready, rc=rc)],
                                           init_container_statuses=[])
    return SimpleNamespace(metadata=SimpleNamespace(name="pod", namespace="ns"),
                          spec=SimpleNamespace(node_name="node"), status=st)


def DEP(desired=1, ready=1, avail=1, partial=False):
    sp = None if partial else SimpleNamespace(replicas=desired,
                                            selector=SimpleNamespace(match_labels={"app": "dep"}),
                                            strategy=SimpleNamespace(type="RollingUpdate"))
    st = None if partial else SimpleNamespace(ready_replicas=ready,
                                            available_replicas=avail,
                                            updated_replicas=ready,
                                            unavailable_replicas=0, conditions=[])
    return SimpleNamespace(metadata=SimpleNamespace(name="dep", namespace="ns"),
                          spec=sp, status=st)


def EVT():
    return SimpleNamespace(metadata=SimpleNamespace(name="e", namespace="ns"),
                          type="Warning", reason="BackOff", message="msg", count=1,
                          action="a", first_timestamp="t", last_timestamp="t2",
                          event_time=None,
                          involved_object=SimpleNamespace(kind="Pod", name="p",
                                                        namespace="ns", uid="u"),
                          source=SimpleNamespace(component="kubelet", host="node"))

@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_version(mock_version, mock_core, mock_apps, mock_config):
    mock_version.return_value.get_code.return_value = V()
    assert get_kubernetes_version()["git_version"] == "v1.36.5+k3s1"


@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_nodes_empty_incomplete(mock_version, mock_core, mock_apps, mock_config):
    mock_core.return_value.list_node.return_value = SimpleNamespace(items=[N()])
    assert list_nodes()[0]["ready"] is True
    mock_core.return_value.list_node.return_value = SimpleNamespace(items=[])
    assert list_nodes() == []

    # incomplete node (no status)
    inc = SimpleNamespace(metadata=SimpleNamespace(name="n", labels={}),
                          spec=SimpleNamespace(unschedulable=False), status=None)
    mock_core.return_value.list_node.return_value = SimpleNamespace(items=[inc])
    assert list_nodes()[0]["partial"] is True


@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_namespaces_pods_deployments_events(mock_version, mock_core, mock_apps, mock_config):
    mock_core.return_value.list_namespace.return_value = SimpleNamespace(items=[NS()])
    assert list_namespaces()[0]["status"] == "Active"
    mock_core.return_value.list_namespace.return_value = SimpleNamespace(items=[])
    assert list_namespaces() == []

    mock_core.return_value.list_pod_for_all_namespaces.return_value = SimpleNamespace(items=[POD(ready=False, rc=3)])
    r = list_pods()[0]
    assert r["ready"] is False and r["restart_count"] == 3
    mock_core.return_value.list_pod_for_all_namespaces.return_value = SimpleNamespace(items=[])
    assert list_pods() == []
    mock_core.return_value.list_pod_for_all_namespaces.return_value = SimpleNamespace(items=[POD(partial=True)])
    assert list_pods()[0]["partial"] is True

    mock_apps.return_value.list_deployment_for_all_namespaces.return_value = SimpleNamespace(items=[DEP(desired=2, ready=1, avail=1)])
    r = list_deployments()[0]
    assert r["desired_replicas"] == 2
    mock_apps.return_value.list_deployment_for_all_namespaces.return_value = SimpleNamespace(items=[])
    assert list_deployments() == []
    mock_apps.return_value.list_deployment_for_all_namespaces.return_value = SimpleNamespace(items=[DEP(partial=True)])
    assert list_deployments()[0]["partial"] is True

    mock_core.return_value.list_event_for_all_namespaces.return_value = SimpleNamespace(items=[EVT()])
    assert list_events()[0]["reason"] == "BackOff"
    mock_core.return_value.list_event_for_all_namespaces.return_value = SimpleNamespace(items=[])
    assert list_events() == []

@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_auth_and_permission_errors(mock_version, mock_core, mock_apps, mock_config):
    mock_core.return_value.list_node.side_effect = ApiException(status=401, reason="Unauthorized")
    with pytest.raises(KubernetesAuthenticationError):
        list_nodes()
    mock_core.return_value.list_namespace.side_effect = ApiException(status=403, reason="Forbidden")
    with pytest.raises(KubernetesAuthorizationError):
        list_namespaces()


@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_connectivity_timeout_config_errors(mock_version, mock_core, mock_apps, mock_config):
    import socket
    from kubernetes import config

    mock_core.return_value.list_pod_for_all_namespaces.side_effect = OSError("refused")
    with pytest.raises(KubernetesConnectivityError):
        list_pods()

    mock_apps.return_value.list_deployment_for_all_namespaces.side_effect = socket.timeout("t")
    with pytest.raises(KubernetesTimeoutError):
        list_deployments()

    mock_config.side_effect = config.ConfigException("bad")
    with pytest.raises(Exception):
        get_kubernetes_version()


@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery._load_kubernetes_config")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.AppsV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.CoreV1Api")
@patch("cloudheal_control_plane.infrastructure.kubernetes_discovery.client.VersionApi")
def test_discover_cluster_empty_and_success(mock_version, mock_core, mock_apps, mock_config):
    mock_version.return_value.get_code.return_value = V()
    mock_core.return_value.list_node.return_value = SimpleNamespace(items=[N()])
    mock_core.return_value.list_namespace.return_value = SimpleNamespace(items=[NS()])
    mock_core.return_value.list_pod_for_all_namespaces.return_value = SimpleNamespace(items=[POD()])
    mock_apps.return_value.list_deployment_for_all_namespaces.return_value = SimpleNamespace(items=[DEP()])
    mock_core.return_value.list_event_for_all_namespaces.return_value = SimpleNamespace(items=[EVT()])
    result = discover_kubernetes_cluster()
    assert result["empty"] is False
    assert result["counts"]["nodes"] == 1

    mock_core.return_value.list_node.return_value = SimpleNamespace(items=[])
    mock_core.return_value.list_namespace.return_value = SimpleNamespace(items=[])
    mock_core.return_value.list_pod_for_all_namespaces.return_value = SimpleNamespace(items=[])
    mock_apps.return_value.list_deployment_for_all_namespaces.return_value = SimpleNamespace(items=[])
    mock_core.return_value.list_event_for_all_namespaces.return_value = SimpleNamespace(items=[])
    empty = discover_kubernetes_cluster()
    assert empty["empty"] is True

from cloudheal_control_plane.infrastructure.kubernetes_discovery import (
    KubernetesAuthorizationError,
)


def test_discover_cluster_partial_collection(monkeypatch):
    from unittest.mock import patch
    import cloudheal_control_plane.infrastructure.kubernetes_discovery as kd

    V = lambda: SimpleNamespace(git_version="v1.36.5+k3s1", major="1", minor="36",
                                build_date="x", compiler="gc", go_version="go",
                                platform="linux", git_commit="abc", git_tree_state="clean")

    with patch.object(kd, "get_kubernetes_version", return_value={"git_version": "v1.36.5+k3s1"}), \
         patch.object(kd, "list_nodes", side_effect=KubernetesAuthorizationError("forbidden")), \
         patch.object(kd, "list_namespaces", return_value=[]), \
         patch.object(kd, "list_pods", return_value=[]), \
         patch.object(kd, "list_deployments", return_value=[]), \
         patch.object(kd, "list_events", return_value=[]):
        result = kd.discover_kubernetes_cluster()

    assert result["status"] == "partial"
    assert result["partial"] is True
    assert "nodes" in result["errors"]
    assert result["nodes"] == []
    assert result["counts"]["nodes"] == 0
