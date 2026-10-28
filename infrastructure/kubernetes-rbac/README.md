# CloudHeal read-only Kubernetes discovery RBAC

These manifests create a dedicated, least-privilege Kubernetes identity for
CloudHeal's read-only discovery client. They are intentionally separate from
application deployment and are never applied automatically by CloudHeal.

## Permissions granted

ClusterRole `cloudheal-discovery-readonly` allows only:

- core: nodes, namespaces, pods, events: `get`, `list`
- apps: deployments: `get`, `list`

No create, update, patch, delete, scale, restart, watch, or exec permissions
are granted. CloudHeal's discovery code also performs only read operations.

## Manual validation before applying

Review the manifests:

```bash
kubectl diff -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac
```

Check what the identity will be allowed to do after applying (using `--as`):

```bash
kubectl auth can-i list nodes --as=system:serviceaccount:cloudheal-system:cloudheal-discovery
kubectl auth can-i list pods --all-namespaces --as=system:serviceaccount:cloudheal-system:cloudheal-discovery
kubectl auth can-i list deployments --all-namespaces --as=system:serviceaccount:cloudheal-system:cloudheal-discovery
kubectl auth can-i create deployments --all-namespaces --as=system:serviceaccount:cloudheal-system:cloudheal-discovery
```

The last command must return `no`.

## Manual apply

Apply only after review:

```bash
kubectl apply -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/00-namespace.yaml
kubectl apply -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/10-serviceaccount.yaml
kubectl apply -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/20-clusterrole.yaml
kubectl apply -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/30-clusterrolebinding.yaml
```

## Establish a kubeconfig for the dedicated identity

Kubernetes 1.24+ does not create a long-lived token secret automatically. Create
a short-lived token with:

```bash
kubectl -n cloudheal-system create token cloudheal-discovery --duration=24h
```

Then build a kubeconfig that uses that token against
`https://192.168.252.2:6443` (or your current K3s endpoint) and point CloudHeal
at it through `KUBECONFIG`. Never commit that kubeconfig or token.

## Validate discovery

With the dedicated kubeconfig:

```bash
KUBECONFIG=/path/to/cloudheal-discovery.kubeconfig \
  /Users/aniketsaini/Desktop/CloudHeal/.venv/bin/python -c \
  'from cloudheal_control_plane.infrastructure.kubernetes_discovery import discover_kubernetes_cluster; import pprint; pprint.pprint(discover_kubernetes_cluster())'
```

Or run the Control Plane with that kubeconfig and call:

```bash
curl http://localhost:9000/infrastructure/kubernetes/discovery
```

## Cleanup

Delete the binding and role when no longer needed:

```bash
kubectl delete -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/30-clusterrolebinding.yaml
kubectl delete -f /Users/aniketsaini/Desktop/CloudHeal/infrastructure/kubernetes-rbac/20-clusterrole.yaml
```
