# CloudHeal --- Complete Project Context & Revised Implementation Roadmap

**Last updated:** 25 October 2026\
**Project stage:** Existing custom distributed-execution foundation
implemented; Kubernetes-backed architecture agreed; a single-node K3s
pilot is running inside Windows Ubuntu WSL2. A separate Ubuntu VM on the
Mac is connected to Tailscale, but it has **not** joined K3s.\
**Latest recorded automated test result:** 34 Control Plane tests passed
in 0.44 seconds (historical result; rerun after code changes).\
**Immediate priority:** Preserve existing work, document and validate
the Kubernetes networking design, then continue toward a repeatable
CloudHeal self-healing workflow.

------------------------------------------------------------------------

## 1. Project Vision

CloudHeal is our own private-cloud management and intelligent
self-healing platform. It should manage supported infrastructure through
adapters and provide higher-level incident classification, evidence
collection, deterministic remediation policies, safe execution,
independent verification, incident history, and quantitative evaluation.

Kubernetes will provide standard orchestration. CloudHeal will provide
the higher-level self-healing intelligence. AI-assisted diagnosis and
constrained planning come later and must never bypass deterministic
policy enforcement.

The initial development environment consists of a MacBook Air and three
Windows laptops connected through Tailscale. These machines are an
initial demonstration environment, not the permanent definition of the
architecture.

### Core workflow

**Observe → Classify → Gather Evidence → Evaluate Policy → Remediate →
Verify → Record**

A dashboard or chatbot alone is not enough. The project must demonstrate
real infrastructure behavior and measurable outcomes.

## 2. Responsibility Boundaries

  -----------------------------------------------------------------------
  Responsibility                      Owner
  ----------------------------------- -----------------------------------
  Container scheduling and ordinary   Kubernetes
  lifecycle management

  Desired-state reconciliation and    Kubernetes
  standard restart/rescheduling

  Workload and node state, Services,  Kubernetes
  and workload networking
  abstractions

  Higher-level incident               CloudHeal
  classification and correlation

  Diagnostic evidence interpretation  CloudHeal

  Deterministic remediation policy    CloudHeal
  and authorization

  Safety limits, cooldowns,           CloudHeal, where not already
  escalation, and recovery            adequately provided by Kubernetes
  coordination

  Independent remediation             CloudHeal
  verification

  Incident history, audit records,    CloudHeal
  and evaluation metrics

  AI-assisted diagnosis and           CloudHeal, later
  constrained planning
  -----------------------------------------------------------------------

Do not duplicate Kubernetes scheduling, restart, or reconciliation
behavior without a clearly justified requirement. Kubernetes is not a
complete cloud provider; future infrastructure provisioning and provider
integrations may require additional adapters.

## 3. Intended Architecture

### 3.1 Self-Healing Core

An infrastructure-independent layer for observations, incidents,
evidence references, policy decisions, remediation tracking,
verification results, audit history, and metrics.

### 3.2 Infrastructure Adapters

The first adapter is intended to target Kubernetes. Future adapters may
target AWS or other supported infrastructure. Adapters must explicitly
document supported operations and limitations and use supported APIs
rather than directly manipulating Kubernetes-managed containers through
the Docker socket.

### 3.3 AI-Assisted Intelligence

Deferred until deterministic remediation is reliable. AI may summarize
evidence, suggest likely causes, retrieve past incidents/runbooks, and
propose constrained plans. All actions must pass through deterministic
authorization. No unrestricted shell or Docker-socket access. Core
deterministic behavior must continue if an AI provider is unavailable.

## 4. Existing Custom Implementation

### Repository

Mac repository: `/Users/aniketsaini/Desktop/CloudHeal`

Activate the Mac virtual environment:

``` bash
source /Users/aniketsaini/Desktop/CloudHeal/.venv/bin/activate
```

Control Plane tests:

``` bash
uv run --package cloudheal-control-plane pytest control-plane/tests -q
```

Node Agent tests:

``` bash
uv run --package cloudheal-node-agent pytest infrastructure/node-agent/tests -q
```

Whitespace check:

``` bash
GIT_PAGER=cat git --no-pager diff --check
```

Always inspect the current working tree before editing:

``` bash
git status --short
git diff --check
git diff
```

### Existing components

-   `cloudheal-control-plane`, historically port 9000: node registry,
    heartbeat handling, workload records, scheduling, remote Node Agent
    communication, execution results, reconciliation, SQLite
    persistence, and event recording.
-   `cloudheal-node-agent`, historically port 8000: persistent node
    identity, registration, heartbeats, system/runtime reporting,
    container execution, and container status queries.
-   Existing scheduler and reconciler coordinate custom workload
    execution and recovery.
-   SQLite persistence and event history are partially implemented and
    need lifecycle/restart verification.
-   Existing custom scheduler, reconciler, and Node Agent must be
    evaluated before deciding what to retain, adapt, or retire.

Do not rewrite or delete existing code before reviewing it against the
new architecture.

### Recent uncommitted code changes to preserve

Historically recorded modified files: -
`control-plane/src/cloudheal_control_plane/registry.py` -
`control-plane/src/cloudheal_control_plane/workloads/reconciler.py` -
`control-plane/tests/test_node_registry.py` -
`control-plane/tests/test_reconciler.py`

This list may be stale; inspect `git status --short` before acting.
Never reset, discard, or commit changes unless explicitly requested.

### Existing availability behavior

Recent changes reportedly added: - A 30-second heartbeat timeout. - Node
status refresh during `get_nodes()` / `get_node()`. -
`NODE_BECAME_UNHEALTHY` and `NODE_BECAME_HEALTHY` transition events. -
Reconciler events `WORKLOAD_NODE_UNAVAILABLE` and
`WORKLOAD_NODE_AVAILABLE`. - Skipping ordinary container-status/recovery
checks while the assigned node is unavailable.

Safety property to preserve: node unavailability is not proof that a
workload has terminated. The existing implementation does not
automatically migrate a workload merely because its node becomes
unreachable.

### Historical execution evidence

-   Previously demonstrated Windows-to-Mac Control Plane connectivity,
    node registration/heartbeats, Windows workload execution through the
    Node Agent, and basic recovery from a stopped Windows container.
-   Workload `1b5b2f07-169a-47c8-a6c0-b1a0026f821e` was previously
    recovered from stopped/missing-container state; a replacement start
    was recorded at `2026-10-19T19:11:42.747967761Z`, with
    `RestartCount=0`.
-   Workload `event-test`, ID `ff02cc16-e20b-43a6-a41c-62fc996dd3b9`,
    image `nginx:latest`, was recorded running on the Mac at an earlier
    point.
-   These historical demonstrations do not prove production-grade
    failover safety or correctness under arbitrary network partitions.

### Historical tests

The last recorded Control Plane test run was **34 passed in 0.44s**, and
`git diff --check` passed. These results are historical, not current
verification.

## 5. Kubernetes Pilot --- Current State as of 25 October 2026

### 5.1 Windows K3s server

K3s is installed inside Ubuntu 26.04.1 LTS running under WSL2 on
Windows. K3s version is `v1.36.5+k3s1`, kernel
`6.18.54.1-microsoft-standard-WSL2`, amd64, containerd `2.3.4-k3s1.36`.

Windows host Tailscale IP: `100.86.103.118`\
Windows hostname / K3s node name: `desktop-dj20fek`\
Current WSL IP: `172.18.15.70`\
K3s service status: `active`

The K3s config `/etc/rancher/k3s/config.yaml` contains:

``` yaml
tls-san:
  - 100.86.103.118
```

The server currently listens on TCP `6443`, TCP `10250`, and UDP `8472`.
Flannel VXLAN appears to be the default, but the config should be
inspected to confirm before making networking changes.

### 5.2 Existing cluster health

`sudo k3s kubectl get nodes -o wide` confirmed: - `desktop-dj20fek` ---
`Ready` - Internal IP `172.18.15.70` - Kubernetes version `v1.36.5+k3s1`

`sudo k3s kubectl get pods -A` showed the following running: -
`default/cloudheal-pilot` Deployment pod --- `1/1 Running` - CoreDNS ---
Running - local-path-provisioner --- Running - metrics-server ---
Running - Traefik and its load-balancer pod --- Running

Helm-install Traefik jobs are Completed. No current failure was shown in
this check.

**Important:** plain `kubectl get nodes` inside WSL previously attempted
`http://localhost:8080` because that shell lacked a usable default
kubeconfig. This did not mean K3s was down. Use `sudo k3s kubectl ...`
on the Windows WSL server unless kubeconfig is deliberately configured.

### 5.3 Windows host forwarding to K3s API

The current Windows portproxy is:

``` text
Listen: 100.86.103.118:16443
Forward to WSL: 172.18.15.70:6443
```

Windows Firewall rule `CloudHeal K3s API from Mac` is enabled, inbound
allow, profile Any, intended to restrict remote address to the Mac
Tailscale IP `100.90.104.13`. Verify its remote-address scope before
changing it.

Windows PowerShell confirmed a listener on `100.86.103.118:16443`. The
Mac worker can reach this endpoint; `curl -k -I` returns HTTP/2 `401`,
which indicates the API endpoint is reachable but the request is
unauthenticated.

If the WSL IP changes after restart, check `hostname -I` in Ubuntu WSL
before updating the portproxy. Do not expose the Kubernetes API broadly
or remove the existing firewall restriction.

### 5.4 Mac Ubuntu worker VM

A separate Ubuntu 24.04 LTS VM was created on the Mac using Multipass
1.16.4+mac with QEMU: - VM name: `cloudheal-mac-worker` - 2 vCPUs - 2 GB
RAM - 12 GB disk - Multipass IP: `192.168.252.2` - Tailscale IP:
`100.80.149.49` - Tailscale device name: `cloudheal-mac-worker`

The VM has internet access. Tailscale 1.104.2 is installed inside it and
authenticated to the same tailnet as the Mac and Windows devices.

The VM can ping the Windows Tailscale IP:

``` text
100.86.103.118 via DERP(blr)
```

It can reach TCP `100.86.103.118:16443`. Both the Windows host and the
VM report that their connection currently goes through the Bengaluru
DERP relay; latency sometimes spikes to hundreds of milliseconds or
several seconds. Direct connectivity is not established.

The VM has **not** joined the K3s cluster and no K3s agent has been
installed.

### 5.5 Networking gap --- do not assume worker join will work

Tests from `cloudheal-mac-worker` showed: - TCP `16443`: connected. -
TCP `10250` at Windows Tailscale IP: timed out. - UDP `8472` probe
reported success, but UDP `nc` is not proof that VXLAN packets reach the
K3s server.

The API portproxy only forwards TCP `16443` to the server's TCP `6443`.
It does not prove that K3s agent traffic, kubelet communication, or
Flannel pod networking will work across the machines.

K3s uses additional node-to-node communication beyond the API. A worker
join must not be attempted until the networking path and required ports
are understood and tested. Do not add random forwards or change WSL
networking mode without a clear plan. Preserve the healthy single-node
pilot.

Windows system details observed: - Windows 10 Home Single Language, OS
build `26200` (`10.0.26200.9711`) - WSL version `3.0.3.0`, kernel
`6.18.54.1-1` - No existing `%USERPROFILE%\.wslconfig` content was
found. - Tailscale is installed on Windows, not inside the WSL Ubuntu
distribution. `tailscale` is not installed in WSL; do not assume it is
available there. - Windows Tailscale IP: `100.86.103.118`. - Mac host
Tailscale IP: `100.90.104.13`. - Mac worker VM Tailscale IP:
`100.80.149.49`.

### 5.6 Kubeconfig handling

The K3s kubeconfig was copied to the Mac at
`~/.kube/cloudheal-k3s.yaml`, with its server address edited to
`https://100.86.103.118:16443`. The Mac can query the existing
single-node cluster with this kubeconfig, although transient TLS
handshake / I/O timeouts have occurred due to relay latency.

Treat kubeconfig files as sensitive. Do not ask the user to paste
credentials or private key data into chat.

## 6. Next Session --- Exact Starting Plan

### Step 1: Preserve and inspect the repository

On Mac:

``` bash
cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status --short
git diff --check
git diff
```

Do not reset or discard any modifications.

### Step 2: Finish read-only inspection of Windows K3s networking

In Ubuntu WSL on Windows, the next pending commands are:

``` bash
sudo grep -E 'flannel|node-ip|node-external-ip|advertise-address|tls-san|disable' /etc/rancher/k3s/config.yaml /etc/systemd/system/k3s.service.env 2>/dev/null
```

and:

``` bash
sudo k3s kubectl get nodes -o yaml | grep -A12 -E 'addresses:|podCIDR:'
```

These were requested but not yet run at the end of the session.

Use results to document the actual Flannel backend, node addresses, and
pod CIDR. Do not edit the config yet.

### Step 3: Decide the smallest viable network design

Investigate how to provide stable K3s server-to-agent and pod networking
between a Mac Ubuntu VM and a K3s server inside Windows WSL2. Consider
the relay latency and WSL NAT/portproxy limitations. Do not assume that
making the API reachable or opening a single port is enough. Keep the
existing Windows server and workloads working.

### Step 4: Validate the environment end-to-end

Before joining a worker, define the required ports/routes and test them.
If the current WSL-based server topology cannot provide reliable
multi-node networking without fragile workarounds, reconsider the
topology instead of repeatedly adding forwards. Document trade-offs
before any disruptive change.

### Step 5: Finalize the CloudHeal architecture

Inspect actual code and docs, then specify: - What Kubernetes owns. -
What CloudHeal owns. - Self-healing core and adapter contracts. -
Security and permission boundaries. - Verification and audit model. -
Existing components to reuse, adapt, retain temporarily, or retire.

### Step 6: Build one small deterministic workflow

After the Kubernetes adapter can observe a real workload, implement:
**Observe → Classify → Policy Check → Remediate → Verify → Record**

Start with one failure type and one explicitly permitted remediation.
Keep AI deferred until this workflow works end-to-end.

## 7. Roadmap

1.  **Repository and architecture validation** --- inspect actual code
    and preserve modifications.
2.  **Kubernetes environment** --- validate the single-node pilot and
    choose a stable multi-machine topology.
3.  **Self-healing core and adapter contract** --- define structured
    observations, incidents, decisions, actions, verification, and audit
    records.
4.  **Deterministic workflow** --- demonstrate an actual controlled
    failure and safe remediation.
5.  **Persistence and recovery controls** --- durable incident history,
    bounded attempts, cooldowns, concurrency controls, escalation.
6.  **Evaluation and baselines** --- detection time, recovery duration,
    downtime, success rate, false positives, unnecessary actions,
    blocked unsafe actions.
7.  **Stable application access** --- evaluate Kubernetes-native
    networking/gateway options before building custom routing.
8.  **AI-assisted diagnosis and constrained planning** --- only after
    deterministic workflow is reliable.
9.  **Multi-provider support** --- consider a second adapter after the
    Kubernetes adapter and core contract stabilize.

## 8. Safety and Development Rules

-   AI recommendations never authorize their own execution.
-   Use least-privilege Kubernetes permissions; avoid cluster-admin by
    default.
-   No unrestricted AI shell access or Docker socket access.
-   A timeout is not proof that an action failed; use explicit
    unknown/inconclusive states.
-   Independently verify recovery using workload readiness and, where
    appropriate, application health checks.
-   Node unavailability is not proof that a workload stopped.
-   Avoid duplicate recovery actions and uncontrolled retry loops.
-   Preserve existing code and uncommitted changes.
-   Inspect before editing; make small changes; run tests after
    meaningful edits.
-   Distinguish implementation, automated tests, and real infrastructure
    verification.
-   Keep machine-specific IPs in operational notes, not shared
    architecture design.
-   Do not claim planned features are implemented.
-   Update context after verified milestones.

## 9. Current Development Position

As of 25 October 2026: - Existing custom FastAPI Control Plane and Node
Agent are implemented. - Docker workload execution and basic
stopped/missing-container recovery have been demonstrated. - SQLite
persistence and event recording exist but require broader
verification. - Node availability transitions and reconciler safety
behavior were recently updated; preserve these changes. - Kubernetes is
the agreed foundation for standard orchestration, but the
Kubernetes-backed CloudHeal adapter/core is not implemented. - A
Windows-hosted WSL2 K3s single-node cluster is healthy, with the
`cloudheal-pilot` workload running. - A separate Ubuntu ARM64 VM on the
Mac has been created and joined to Tailscale. - The Mac VM can reach the
Windows K3s API through TCP `16443`, but it has **not** joined K3s. -
The current API portproxy is not a complete multi-node networking
solution; worker join is blocked pending a reliable design for
server/agent and pod networking. - Current Windows K3s config and node
PodCIDR inspection are the next pending read-only checks. - Latest
historical test result: 34 Control Plane tests passed in 0.44 seconds;
rerun before relying on it. - The old scheduler/reconciler/Node Agent
must be evaluated before deciding what to retain or retire. - AI and
multi-provider support remain future work.

### Guiding principle

CloudHeal is our own private-cloud management and self-healing platform.
Kubernetes provides standard orchestration; CloudHeal provides
independent intelligence, deterministic policies, safe remediation,
verification, incident history, and measurable evaluation. Preserve
existing work, validate the architecture before changing code, and build
the smallest complete self-healing workflow before expanding into AI or
multiple providers.
