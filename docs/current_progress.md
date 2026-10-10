CloudHeal — Project Context, Current Progress & Code Reference

Last Updated: 10 October 2026
Project: CloudHeal — Laptop-Based Cloud Platform with Resource-Aware Scheduling and Future Self-Healing
Current Development Stage: Infrastructure Discovery and Resource-Aware Scheduling Preparation

⸻

1. Project Overview

1.1 What We Are Building

CloudHeal is a cloud platform built using our own laptops instead of relying on an external cloud provider.

The initial cluster will consist of four laptops:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.

The laptops will connect over a private network and contribute resources while they are switched on and connected.

The goal is to build the fundamental capabilities of a cloud platform before introducing application workloads such as video streaming or e-commerce.

1.2 Development Approach

We are building the platform from the infrastructure layer upward.

The development sequence is:

1. Node identity and discovery.
2. Node registration and heartbeats.
3. Host resource monitoring.
4. Container runtime discovery.
5. Runtime capacity reporting.
6. Resource-aware workload scheduling.
7. Workload dispatch to the selected node.
8. Container execution and verification.
9. Workload state reconciliation.
10. Monitoring and self-healing.
11. Dashboard and demonstration workloads.

We are currently working on steps 4 and 5: discovering Docker’s actual resources and making those resources available to the Control Plane.

We must not assume that the resources of a laptop are the same as the resources available to its containers.

1.3 Development Rules

* Explain the architecture before implementing a new component.
* Implement one logical change at a time.
* Test each component before moving forward.
* Preserve existing working code.
* Inspect existing implementations before replacing files.
* Avoid introducing Kubernetes or unnecessary infrastructure at this stage.
* Keep registries in memory for now.
* Update this document after important architecture or progress changes.
* Do not mark a workload RUNNING merely because a node has been assigned.
* Use actual runtime information instead of hardcoded machine capacities.

⸻

2. Current Architecture

CloudHeal currently has two main components.

2.1 Control Plane

The Control Plane manages the cluster and makes scheduling decisions.

Its responsibilities include:

* Maintaining the node registry.
* Tracking registered nodes and heartbeats.
* Accepting workload requests.
* Maintaining workload records.
* Selecting a node for a workload.
* Eventually dispatching workloads to the selected Node Agent.
* Tracking workload state.

The Control Plane currently runs on port 9000.

2.2 Node Agent

A Node Agent runs on every participating laptop.

Its responsibilities include:

* Generating and maintaining a persistent node identity.
* Discovering the laptop’s local network address.
* Registering with the Control Plane.
* Sending periodic heartbeats.
* Reporting host system information.
* Executing Docker containers.
* Eventually reporting runtime capacity and workload status.

The Node Agent currently runs on port 8000.

2.3 Architecture Diagram

                    USER / CLIENT
                         |
                         | Create workload
                         v
                 +-------------------+
                 |   CONTROL PLANE   |
                 |                   |
                 | Node Registry     |
                 | Workload Registry |
                 | Workload Service  |
                 | Scheduler         |
                 +---------+---------+
                           |
                           | Select node
                           | Dispatch workload
                           v
                +----------------------+
                |      NODE AGENT      |
                |                      |
                | Node Identity        |
                | Registration         |
                | Heartbeat            |
                | Host Metrics         |
                | Runtime Discovery    |
                | Container Execution  |
                +-----------+----------+
                            |
                            v
                     Docker Runtime
                            |
                            v
                    Running Containers

The dispatch connection between the Control Plane and Node Agent must be completed or verified. Scheduling and container execution are separate responsibilities.

⸻

3. Repository Structure

The current repository root is:

/Users/aniketsaini/Desktop/CloudHeal

Known project structure:

CloudHeal/
│
├── CloudHeal_CONTEXT.md
├── README.md
├── pyproject.toml
├── uv.lock
│
├── docs/
│   └── SPEC-001-cloudheal.md
│
├── control-plane/
│   └── src/
│       └── cloudheal_control_plane/
│           ├── api.py
│           ├── registry.py
│           │
│           └── workloads/
│               ├── models.py
│               ├── registry.py
│               ├── service.py
│               └── scheduler.py
│
└── infrastructure/
    └── node-agent/
        └── src/
            └── cloudheal_node_agent/
                ├── api.py
                ├── heartbeat.py
                ├── identity.py
                ├── models.py
                ├── network.py
                ├── registration.py
                ├── runtime.py
                └── system.py

Important

The following file is planned but has not yet been confirmed as created:

infrastructure/node-agent/src/cloudheal_node_agent/runtime_info.py

Its purpose will be to discover and report Docker runtime capabilities. It must remain separate from the module that executes containers.

The root uv workspace was previously configured to include the Node Agent package. Inspect the current pyproject.toml before making any workspace changes.

⸻

4. Node Agent — Code Context

4.1 identity.py

Purpose: Maintain a stable identity for each laptop.

Known behavior:

* Generates a UUID when the Node Agent runs for the first time.
* Stores the UUID at ~/.cloudheal/node_id.
* Reuses the same UUID after restarts.

This prevents a node from receiving a new identity every time its agent restarts.

Status: Implemented.

Avoid changing this component unless a specific problem is found.

4.2 network.py

Purpose: Discover the laptop’s local IP address.

Known behavior:

* Uses a UDP socket technique to determine the local network address.
* Supplies the address used during node registration.

This will matter when teammates’ laptops join the cluster.

Important: A node’s address must be reachable from the Control Plane. The current 127.0.0.1 configuration is appropriate only for the single-machine test.

Status: Local address discovery implemented.

4.3 system.py

Purpose: Collect host-level resource information using platform and psutil.

Known responsibilities:

* Hostname.
* Operating system.
* Machine architecture.
* Physical and logical CPU core counts.
* CPU usage.
* Total and available memory.
* Root filesystem total and free space.
* Disk usage percentage.

The latest implementation discussed is:

import platform
import psutil
from cloudheal_node_agent.models import (
    CPUInfo,
    DiskInfo,
    MemoryInfo,
)
def get_system_info() -> dict:
    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    return {
        "hostname": platform.node(),
        "operating_system": platform.system(),
        "architecture": platform.machine(),
        "cpu": CPUInfo(
            physical_cores=psutil.cpu_count(logical=False),
            logical_cores=psutil.cpu_count(logical=True),
            usage_percent=cpu_usage,
        ),
        "memory": MemoryInfo(
            total_bytes=memory.total,
            available_bytes=memory.available,
            usage_percent=memory.percent,
        ),
        "disk": DiskInfo(
            total_bytes=disk.total,
            free_bytes=disk.free,
            usage_percent=disk.percent,
        ),
    }

Note: This is the latest known version from our conversation. If the file has changed since then, inspect the current local implementation before editing it.

Why we refactored it

Previously, disk usage was queried multiple times in the same function.

Now the function captures one snapshot:

disk = psutil.disk_usage("/")

The same snapshot supplies all disk fields.

Memory is handled similarly:

memory = psutil.virtual_memory()

This keeps the returned metrics internally consistent.

Current status

Host metrics are working and have been verified through the Node Agent API.

Architectural limitation

These metrics describe the laptop itself, not the Docker runtime.

For example, the Mac has 8 GiB of physical RAM, but Docker Desktop previously reported approximately 3.825 GiB of memory for its Linux runtime.

CloudHeal must report those as separate resource categories.

4.4 models.py — Node Agent

Purpose: Define the Pydantic models used for host information.

Known models:

from pydantic import BaseModel
class CPUInfo(BaseModel):
    physical_cores: int | None
    logical_cores: int | None
    usage_percent: float
class MemoryInfo(BaseModel):
    total_bytes: int
    available_bytes: int
    usage_percent: float
class DiskInfo(BaseModel):
    total_bytes: int
    free_bytes: int
    usage_percent: float
class Node(BaseModel):
    node_id: str
    hostname: str
    operating_system: str
    architecture: str
    cpu: CPUInfo
    memory: MemoryInfo
    disk: DiskInfo

This represents host-level information.

Docker runtime information has not yet been confirmed as part of this model.

Do not merge host and Docker fields together without a clear reason. Keeping the two categories separate will make scheduling easier to reason about.

4.5 registration.py

Purpose: Register the Node Agent with the Control Plane.

The current known registration payload includes:

{
  "node_id": "...",
  "hostname": "...",
  "address": "...",
  "status": "healthy"
}

The registration endpoint is:

POST /nodes/register

The registration flow currently does not have a confirmed implementation for sending Docker runtime capacity to the Control Plane.

Status: Basic registration works.

Future responsibility: Send the node’s runtime capabilities and relevant resource information once the runtime-info contract is implemented.

4.6 heartbeat.py

Purpose: Keep the Control Plane informed that the Node Agent is alive.

Known behavior:

* Sends a heartbeat approximately every 10 seconds.
* Calls:

POST /nodes/{node_id}/heartbeat

The Control Plane currently refreshes the node’s last_seen timestamp.

The heartbeat contract has not yet been confirmed to update runtime resource information.

Status: Heartbeat works.

4.7 api.py — Node Agent

Purpose: Expose Node Agent functionality through FastAPI.

Known endpoints:

Endpoint	Purpose
GET /health	Check whether the agent is responding
GET /identity	Inspect the node identity
GET /system	Retrieve host metrics
POST /containers	Request local container execution

The application lifespan currently:

1. Registers the Node Agent with the Control Plane.
2. Starts the periodic heartbeat loop.

The configured Control Plane URL is currently:

http://127.0.0.1:9000

This is the local testing configuration. It must be adapted when the Control Plane and Node Agents run on separate laptops.

Status: Basic API, registration, heartbeat, and host information are working.

Before changing this file, inspect its current imports, lifespan logic, endpoint definitions, and runtime calls.

4.8 runtime.py

Purpose: Execute containers through Docker.

The known implementation uses the Docker CLI through subprocess calls.

The command has this general structure:

docker run --detach \
  --name cloudheal-{workload_id} \
  --cpus <cpu_limit> \
  --memory <memory_limit_mb>m \
  <image>

The module then inspects the container to verify that it is running.

Known behavior:

* Starts a detached container.
* Applies CPU and memory limits.
* Verifies the container after startup.
* Handles an existing container with the same name.
* Uses ContainerExecutionError to represent runtime failures.

The Node Agent’s container request uses these fields:

workload_id
image
cpu_limit
memory_limit_mb

Status: Docker container execution has been tested successfully with Nginx.

Important distinction: runtime.py executes workloads. It should not become responsible for collecting all runtime discovery information.

⸻

5. Control Plane — Code Context

5.1 registry.py — Node Registry

Purpose: Store registered nodes and their latest known status.

The known implementation is:

from datetime import datetime, timezone
from pydantic import BaseModel
class NodeRecord(BaseModel):
    node_id: str
    hostname: str
    address: str
    status: str = "healthy"
    last_seen: datetime | None = None
_nodes: dict[str, NodeRecord] = {}
def register_node(node: NodeRecord) -> NodeRecord:
    node.last_seen = datetime.now(timezone.utc)
    _nodes[node.node_id] = node
    return node
def get_nodes() -> list[NodeRecord]:
    return list(_nodes.values())
def get_node(node_id: str) -> NodeRecord | None:
    return _nodes.get(node_id)
def heartbeat_node(node_id: str) -> NodeRecord | None:
    node = _nodes.get(node_id)
    if node is None:
        return None
    node.last_seen = datetime.now(timezone.utc)
    return node

This is the known implementation from the previous code context. Confirm it locally before making changes.

Current limitations

* The registry is in memory.
* Restarting the Control Plane clears registered nodes.
* NodeRecord does not yet have confirmed Docker runtime capacity fields.
* Heartbeats update last_seen, but do not yet have a confirmed resource-update contract.

Planned evolution

NodeRecord will eventually need to represent:

* Node identity and address.
* Node health and last heartbeat.
* Host resource information.
* Runtime availability.
* Runtime CPU and memory capacity.
* Resource capacity reserved by CloudHeal workloads, or enough information to derive it.

The exact model should be designed after inspecting the current implementation and deciding which values need to be persisted in the in-memory record.

5.2 api.py — Control Plane

Purpose: Expose the cluster management API.

Known node endpoints:

Endpoint	Purpose
GET /health	Check Control Plane health
POST /nodes/register	Register a node
GET /nodes	List registered nodes
GET /nodes/{node_id}	Inspect a node
POST /nodes/{node_id}/heartbeat	Update node heartbeat

Workload API endpoints are also present.

The Control Plane maintains shared in-memory objects for workload management, including:

* workload_registry
* workload_service
* workload_scheduler

Status: Node registry and workload API have been implemented.

Before modifying the API, inspect the current file to avoid accidentally removing routes or creating duplicate service instances.

⸻

6. Workload Management

The workload system currently contains four primary files.

6.1 workloads/models.py

Purpose: Define workload requests, records, and lifecycle states.

Known desired states:

class DesiredState(StrEnum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

Known actual states:

class WorkloadState(StrEnum):
    PENDING = "PENDING"
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    STOPPED = "STOPPED"

WorkloadCreate

Known fields:

Field	Purpose	Default / validation
name	Workload name	1–100 characters
image	Container image	1–255 characters
desired_state	Requested state	RUNNING
cpu_limit	Requested CPU limit	1.0, greater than zero
memory_limit_mb	Requested memory	256, greater than zero

WorkloadRecord

Known fields:

* workload_id: UUID generated automatically.
* name
* image
* desired_state
* actual_state, initially PENDING.
* node_id, initially None.
* cpu_limit
* memory_limit_mb
* created_at
* updated_at

Assignment validation is enabled on the record.

6.2 workloads/registry.py

Purpose: Store workload records in memory.

Known behavior:

* Maintains a dictionary keyed by workload UUID.
* Provides CRUD operations.

This keeps the workload state accessible to the API, service, and scheduler without introducing a database at this stage.

6.3 workloads/service.py

Purpose: Provide a thin service layer around the workload registry.

The service separates workload operations from the API and scheduler.

Keep this layer simple unless a real requirement justifies adding more abstraction.

6.4 workloads/scheduler.py

Purpose: Select a node for a pending workload.

The latest known scheduling logic:

1. Retrieves the workload.
2. Fails if the workload does not exist.
3. Requires the actual state to be PENDING.
4. Requires the desired state to be RUNNING.
5. Retrieves registered nodes.
6. Filters for nodes whose status is healthy.
7. Selects the first eligible node.
8. Assigns its UUID to node_id.
9. Changes the workload state to SCHEDULED.
10. Updates updated_at.
11. Saves and returns the workload.

The current scheduler is effectively a first-healthy-node scheduler.

Critical limitation

Scheduling currently means assignment, not confirmed execution.

The scheduler’s known implementation does not itself send a request to the Node Agent or launch a container. Check whether a later change has added dispatch before modifying this behavior.

What must change next

The scheduler needs to consider runtime capacity.

A node should not be selected merely because its status says healthy.

It must also have:

* An available container runtime.
* Sufficient allocatable CPU.
* Sufficient allocatable memory.
* A reachable Node Agent for workload dispatch.

The scheduler should reserve capacity for workloads in SCHEDULED and RUNNING states.

Workloads in PENDING have not reserved resources. FAILED and STOPPED workloads should not consume scheduling reservations once their states are confirmed.

Selection and reservation must eventually be protected against concurrent scheduling requests so that two workloads cannot both claim the same remaining capacity.

⸻

7. Current Host and Docker Environment

The following are previously verified snapshots, not hardcoded configuration.

7.1 Host Resource Snapshot

The latest successful response from:

GET http://127.0.0.1:8000/system

was:

{
  "hostname": "Anikets-MacBook-Air.local",
  "operating_system": "Darwin",
  "architecture": "arm64",
  "cpu": {
    "physical_cores": 8,
    "logical_cores": 8,
    "usage_percent": 7.3
  },
  "memory": {
    "total_bytes": 8589934592,
    "available_bytes": 1892499456,
    "usage_percent": 78.0
  },
  "disk": {
    "total_bytes": 245107195904,
    "free_bytes": 88692178944,
    "usage_percent": 12.5
  }
}

Interpretation

* Physical RAM: 8 GiB.
* CPU: 8 physical cores and 8 logical cores as reported by psutil.
* Available host RAM at that moment: approximately 1.76 GiB.
* Disk usage percentage: 12.5%.

CPU usage and available memory vary over time, so these values are not permanent.

7.2 Disk Metric Verification

The following command was run:

python -c "import psutil; d=psutil.disk_usage('/'); print({'total_bytes': d.total, 'used_bytes': d.used, 'free_bytes': d.free, 'percent': d.percent})"

Output:

{
    'total_bytes': 245107195904,
    'used_bytes': 12637204480,
    'free_bytes': 88707842048,
    'percent': 12.5
}

The API now obtains a single disk snapshot and uses disk.percent directly.

We should not calculate disk usage as (total - free) / total, because that calculation did not match the percentage reported by psutil in this environment.

Status: Verified.

7.3 Docker Runtime Snapshot

Previously, docker info reported:

Property	Reported value
Docker client version	29.8.2
Docker server version	29.8.2
Docker context	desktop-linux
Runtime operating system	Docker Desktop / Linux
Runtime architecture	aarch64
Runtime CPU count	8
Runtime memory	Approximately 3.825 GiB
Storage driver	overlayfs
Docker root directory	/var/lib/docker

These values were observed during a previous test and must be queried dynamically in the implementation.

Docker Desktop runs containers inside a Linux environment. Therefore, the host’s physical RAM and Docker’s reported memory capacity are different measurements.

Design rule

Keep these three concepts separate:

1. Host resources: what the laptop reports.
2. Runtime resources: what Docker reports as available to its environment.
3. CloudHeal allocatable resources: what the scheduler is permitted to promise to workloads.

We have not yet finalized an allocatable-capacity policy or safety margin.

7.4 Container Execution Verification

A previously inspected Nginx container had these settings:

Image: nginx:latest
Running: true
HostConfig.Memory: 268435456 bytes
HostConfig.NanoCpus: 1000000000

This corresponds to:

* A 256 MiB memory limit.
* A CPU limit of approximately one CPU.

Four Nginx containers were running during a previous test.

Do not assume those containers are still running. Check docker ps and the current workload registry before calculating present capacity.

⸻

8. Current Progress Checklist

Completed

* Created the initial Control Plane service.
* Created the Node Agent service.
* Implemented persistent node identity.
* Implemented local IP discovery.
* Implemented node registration.
* Implemented periodic heartbeats.
* Added host resource reporting through /system.
* Verified host CPU, memory, disk, OS, and architecture fields.
* Refactored get_system_info() to collect one CPU, memory, and disk snapshot per call.
* Verified the corrected disk usage reporting.
* Implemented in-memory node registry.
* Implemented workload models.
* Implemented in-memory workload registry and service.
* Implemented basic scheduling to the first healthy node.
* Implemented Node Agent Docker container execution with resource limits.
* Successfully tested Nginx container execution.

In Progress

* Implement Docker runtime discovery.
* Separate host metrics from runtime metrics in the Node Agent’s data model.
* Handle Docker being unavailable without crashing the Node Agent.
* Decide how runtime information is returned and refreshed.
* Send runtime capabilities to the Control Plane.
* Extend NodeRecord to represent current runtime capacity.
* Implement resource-aware scheduling.
* Verify whether workload dispatch has been implemented; otherwise, connect scheduling to the Node Agent.
* Test the complete workload lifecycle.

⸻

9. Immediate Next Task — Docker Runtime Discovery

The next component should be:

infrastructure/node-agent/src/cloudheal_node_agent/runtime_info.py

Its responsibility is to inspect Docker and report its current capabilities. It should not execute workloads.

9.1 Information to Discover

The module should report:

* Whether Docker is available.
* Runtime type.
* Runtime version.
* Runtime operating system.
* Runtime architecture.
* Runtime CPU count.
* Runtime memory capacity.
* A concise error when the runtime cannot be queried.

The data should be discovered dynamically.

9.2 Expected Response Shape

This is a proposed contract, not an implemented model:

{
  "available": true,
  "runtime_type": "docker",
  "version": "29.8.2",
  "operating_system": "linux",
  "architecture": "aarch64",
  "cpu_count": 8,
  "memory_bytes": 4102029312,
  "error": null
}

The example memory value is illustrative of the previously reported capacity. The actual implementation must query Docker at runtime.

9.3 Error Handling Requirements

If Docker is stopped, unavailable, or inaccessible:

* Report available: false.
* Include a useful error or status message.
* Keep the Node Agent running.
* Keep host metrics available through /system.
* Do not treat the node as eligible for container workloads.

The runtime discovery command must have a timeout so the Node Agent does not hang indefinitely if Docker is unresponsive.

9.4 First Implementation Step

Before writing runtime_info.py, inspect these current files:

sed -n '1,240p' infrastructure/node-agent/src/cloudheal_node_agent/runtime.py
sed -n '1,240p' infrastructure/node-agent/src/cloudheal_node_agent/models.py
sed -n '1,240p' infrastructure/node-agent/src/cloudheal_node_agent/api.py

We are inspecting them to avoid duplicating existing logic and to integrate the new module correctly.

After inspection:

1. Implement runtime discovery.
2. Test it independently.
3. Test its behavior when Docker is unavailable, where practical.
4. Add an API endpoint or integrate it into the existing API, depending on the resulting design.
5. Only then integrate runtime information into node registration and scheduling.

⸻

10. Future Resource-Aware Scheduling

After runtime discovery works, the next phase will be resource-aware scheduling.

The scheduler should consider:

Workload request
    |
    v
Find healthy nodes
    |
    v
Check runtime availability
    |
    v
Check CPU capacity
    |
    v
Check memory capacity
    |
    v
Account for existing reservations
    |
    v
Select an eligible node
    |
    v
Reserve resources and mark SCHEDULED
    |
    v
Dispatch to Node Agent
    |
    v
Verify container execution
    |
    v
Mark RUNNING or FAILED

The exact reservation policy must be designed from actual runtime capacity and existing workloads rather than guessed.

For the first version, derive allocations from workload records where practical. If the scheduler permits concurrent requests, protect selection and reservation with a lock or equivalent mechanism.

Do not introduce a separate resource database or complex placement engine at this stage.

⸻

11. Commands for Running and Testing

Run commands from the CloudHeal repository root unless specified otherwise.

Start the Control Plane

uv run --package cloudheal-control-plane cloudheal-control-plane

Start the Node Agent

In another terminal:

uv run --package cloudheal-node-agent cloudheal-node-agent

Check Service Health

curl http://127.0.0.1:9000/health
curl http://127.0.0.1:8000/health

Check Node Registration

curl http://127.0.0.1:9000/nodes

Check Host Metrics

curl http://127.0.0.1:8000/system

Check Node Identity

curl http://127.0.0.1:8000/identity

Inspect Docker

docker info
docker ps

Inspect Container Resource Limits

docker inspect <container-name-or-id>

⸻

12. Important Design Decisions

12.1 Do Not Confuse Host and Runtime Capacity

The Mac’s physical RAM is 8 GiB, while Docker previously reported approximately 3.825 GiB.

The scheduler must use runtime capacity, not the host’s total physical memory.

12.2 Keep Runtime Discovery Separate from Container Execution

* runtime_info.py will discover and report Docker capabilities.
* runtime.py will execute and inspect workload containers.

Keeping these responsibilities separate makes the implementation easier to test and maintain.

12.3 Keep the Control Plane in Charge of Scheduling

The Control Plane decides where a workload should run.

The Node Agent performs local container operations.

The Control Plane should not execute local Docker commands directly.

12.4 Scheduling Is Not Execution

A workload marked SCHEDULED has a placement assignment. That does not prove the container has started.

The workload should become RUNNING only after the Node Agent or runtime confirms successful execution.

12.5 Plan for Multiple Laptops

The current setup is a single-Mac development environment.

When the teammates’ Windows laptops join:

* The Control Plane must be reachable over the private network.
* Each Node Agent must know the Control Plane’s reachable address.
* The Control Plane must be able to reach each Node Agent’s advertised address.
* 127.0.0.1 must not be used as a remote node address.
* Each node must report its own runtime capacity.
* A node with an unavailable runtime must not be scheduled for container workloads.

⸻

13. Instructions for Continuing Development in a New Chat

When continuing CloudHeal development:

1. Read this document first.
2. Start from the current progress checklist.
3. Do not rebuild working node identity, registration, heartbeat, host metrics, workload models, or container execution without a concrete reason.
4. Inspect the current implementation before modifying an existing file.
5. Explain the intended change and the data flow.
6. Implement one stage at a time.
7. Provide verification commands and wait for the actual result before declaring success.
8. Keep architecture and code context up to date.
9. Distinguish verified implementation from planned implementation.
10. Avoid unnecessary abstraction, databases, and Kubernetes.

Current checkpoint: Host metrics are working. The disk reporting change has been verified. The next task is to inspect the existing Node Agent files and implement Docker runtime discovery in runtime_info.py.

Do not proceed directly to resource-aware scheduling until runtime discovery and reporting have been tested.