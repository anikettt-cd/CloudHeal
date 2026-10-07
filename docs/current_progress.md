CloudHeal — Current Implementation & Progress

1. Project Goal

CloudHeal is being built as a lightweight cloud infrastructure / compute orchestration platform.

The core idea is:

* A Control Plane manages and monitors compute nodes.
* A Node Agent runs on each worker machine.
* Nodes communicate with the Control Plane through a private network.
* The Control Plane maintains node registration, health/heartbeat information, and eventually workload scheduling and execution.

The project is currently focused on building the infrastructure foundation before implementing workload scheduling.

⸻

2. Current Architecture

                    CloudHeal Private Network
                         (Tailscale)
                              │
             ┌────────────────┴────────────────┐
             │                                 │
             ▼                                 ▼
        Control Plane                       Node Agent
          (Mac)                         (Teammate Laptop)
             │
             │
             ▼
        Node Registry
        Heartbeats
        Node Status
        Resource Info

The immediate goal is to have a real two-node CloudHeal test:

* Node 1: Developer’s Mac
* Node 2: Teammate’s laptop
* Control Plane: Currently running on the developer’s Mac
* Networking: Tailscale private network

The second laptop should behave as a genuine remote CloudHeal worker node rather than relying on localhost or the local LAN.

⸻

3. Repository Structure

Current high-level structure:

CloudHeal/
├── CloudHeal_CONTEXT.md
├── README.md
│
├── control-plane/
│   ├── pyproject.toml
│   └── src/
│       └── cloudheal_control_plane/
│           ├── __init__.py
│           └── main.py
│
└── infrastructure/
    └── node-agent/
        ├── pyproject.toml
        └── src/
            └── cloudheal_node_agent/
                ├── __init__.py
                ├── main.py
                └── models.py

The repository uses a Python workspace with uv.

⸻

4. Control Plane

The Control Plane is implemented using FastAPI + Uvicorn.

It can currently be started with:

uv run --package cloudheal-control-plane python -m cloudheal_control_plane.main

Current server:

http://0.0.0.0:<port>

The Control Plane currently provides the initial API foundation for CloudHeal and is being extended toward:

* node registration
* node discovery
* heartbeat tracking
* node health/status
* resource information
* eventually workload scheduling

The Control Plane is currently running successfully on the developer’s Mac.

⸻

5. Node Agent

The Node Agent is a separate Python package responsible for running on CloudHeal worker machines.

Its purpose is to:

1. Start on a worker machine.
2. Collect machine/resource information.
3. Register itself with the Control Plane.
4. Send periodic heartbeats.
5. Eventually receive and execute workloads assigned by CloudHeal.

The Node Agent is intentionally separated from the Control Plane because CloudHeal is designed as a distributed system.

⸻

6. Node Resource Models

The Node Agent currently contains Pydantic models for machine resources.

Example models include:

class CPUInfo(BaseModel):
    physical_cores: int | None
    logical_cores: int | None
    usage_percent: float
class MemoryInfo(BaseModel):
    total_bytes: int
    available_bytes: int
    usage_percent: float
class DiskInfo(BaseModel):
    ...

These models provide a structured representation of node resources.

The Node Agent uses psutil for system-level resource information.

psutil has already been added to the Node Agent package using:

uv add --package cloudheal-node-agent psutil

The Node Agent has been tested successfully for resource collection.

⸻

7. Heartbeat / Node Health

The current implementation has established the concept of a Node Agent heartbeat.

The purpose of the heartbeat is to allow the Control Plane to know:

Node exists
    ↓
Node is reachable
    ↓
Node is healthy
    ↓
Node resource information is available

The Control Plane will eventually maintain node state based on heartbeat timestamps.

This is the foundation for later features such as:

* detecting offline nodes
* scheduling workloads only on healthy nodes
* resource-aware scheduling
* node monitoring

⸻

8. Networking Decision

CloudHeal has decided to use Tailscale as the initial private networking layer.

This is preferred over exposing the Control Plane publicly or depending on local LAN networking.

The intended model is:

CloudHeal Node Agent
        │
        │ Tailscale
        ▼
Private CloudHeal Network
        │
        ▼
CloudHeal Control Plane

Reasons for this decision:

* works across different physical networks
* provides private connectivity
* avoids public port forwarding
* avoids exposing the Control Plane directly to the internet
* gives each machine a stable private Tailscale IP
* is suitable for the current development/testing stage

CloudHeal’s application layer should communicate using the Tailscale network rather than assuming localhost or the same LAN.

⸻

9. Current Testing Setup

The first networking experiment used another laptop temporarily.

That machine is now being disconnected from the previous test setup.

The next test will use the actual teammate’s laptop.

Target:

Developer Mac
    │
    ├── CloudHeal Control Plane
    └── Node Agent
            │
            │ Tailscale
            │
            ▼
     Teammate Laptop
            │
            └── CloudHeal Node Agent

This will become the project’s first genuine two-node environment.

⸻

10. Immediate Next Steps

Step 1 — Clean previous test machine

Disconnect the temporary friend’s laptop from the previous CloudHeal/Tailscale test.

Do not modify CloudHeal architecture because of this temporary machine.

Step 2 — Configure teammate’s laptop

Install and authenticate Tailscale on the teammate’s laptop.

Join the same Tailscale network as the developer’s Mac.

Verify both machines can communicate through their Tailscale IPs.

Step 3 — Install CloudHeal Node Agent

Set up the Node Agent environment on the teammate’s laptop.

Install the required Python dependencies.

Step 4 — Connect Node Agent to Control Plane

Configure the teammate’s Node Agent to use the Control Plane’s Tailscale IP address, not:

localhost
127.0.0.1
local LAN IP

Step 5 — Test two-node registration

Expected state:

Control Plane
├── Node 1: Developer Mac
│   ├── CPU
│   ├── Memory
│   └── Disk
│
└── Node 2: Teammate Laptop
    ├── CPU
    ├── Memory
    └── Disk

Both nodes should send heartbeats to the Control Plane.

Step 6 — Verify failure detection

After successful two-node communication, intentionally stop the Node Agent on one machine and verify that the Control Plane eventually detects the node as offline/unhealthy.

⸻

11. Architectural Direction

The implementation is intentionally being built incrementally.

Current foundation:

Node Agent
   ↓
Resource Collection
   ↓
Registration
   ↓
Heartbeat
   ↓
Control Plane
   ↓
Node Registry

Next:

Node Registry
   ↓
Health / Availability
   ↓
Resource-aware Scheduling
   ↓
Workload Assignment
   ↓
Workload Execution

Later CloudHeal can evolve toward:

* workload/task submission
* scheduler
* resource-aware placement
* workload lifecycle management
* container-based workloads
* node failure handling
* service discovery
* authentication/authorization
* persistent control-plane state
* observability
* multi-node workload execution

The current priority is not to implement all of these at once.

The immediate objective is to establish a reliable distributed foundation with:

Control Plane + two real Node Agents + Tailscale networking + registration + heartbeat + resource reporting.

Absolutely. We’ll stop here for today.

We’re at a good checkpoint:

* ✅ Control Plane running
* ✅ Node Agent running
* ✅ psutil resource collection
* ✅ Node models
* ✅ Heartbeat foundation
* ✅ Tailscale chosen as the networking model
* ⏭️ Tomorrow: Tailscale setup → teammate laptop → real two-node CloudHeal test

No need to change anything tonight. Tomorrow we can continue directly from this point.