CloudHeal — Project Context

Project: CloudHeal
Type: Laptop-based private cloud infrastructure with future self-healing capabilities
Current Stage: Infrastructure foundation and Control Plane development

⸻

1. Project Vision

CloudHeal aims to build a small, private cloud platform using available laptops as computing nodes.

The initial demonstration environment consists of:

* A MacBook running macOS.
* Windows laptops that can join the private cloud as additional nodes.
* A private network connecting participating machines.
* A central Control Plane that manages nodes and, eventually, workloads.

The laptops do not need to operate 24/7. Nodes can participate while their machines are switched on and connected to the CloudHeal network.

The objective is to build the underlying cloud infrastructure first and introduce application workloads and self-healing capabilities incrementally.

CloudHeal is not intended to become a full Kubernetes replacement. The project will begin with a simpler architecture that can be understood, implemented, tested, and extended step by step.

2. Long-Term Objectives

CloudHeal will progressively develop the following capabilities:

1. Private networking between cloud nodes.
2. Node registration and identity management.
3. Node health monitoring and heartbeat tracking.
4. Workload submission and lifecycle management.
5. Workload scheduling across available nodes.
6. Workload execution on selected nodes.
7. Resource monitoring and workload health detection.
8. Failure detection and recovery.
9. Self-healing actions and post-recovery verification.
10. A dashboard for observing nodes, workloads, and recovery activity.

These are long-term goals, not features that must all be implemented immediately.

Each capability must be implemented and tested before the next major component is introduced.

3. Current Architecture

CloudHeal currently has two primary components.

3.1 Control Plane

The Control Plane is the central management service.

Current responsibilities:

* Accept node registrations.
* Maintain an in-memory node registry.
* Retrieve registered nodes.
* Retrieve individual nodes.
* Receive heartbeat requests.
* Update a node’s last_seen timestamp.

The Control Plane currently uses FastAPI and runs on port 9000.

3.2 Node Agent

The Node Agent runs on each participating laptop.

Current responsibilities:

* Generate and persist a unique node identity.
* Report hostname and network information.
* Collect system resource information.
* Register with the Control Plane.
* Send periodic heartbeat requests.

The Node Agent uses FastAPI, HTTPX, Pydantic, and psutil. Its API runs on port 8000.

The Node Agent and Control Plane are separate applications.

3.3 Current Architecture Diagram

                 CloudHeal Private Network
                         (Tailscale)
        ┌─────────────────────────────────┐
        │          MacBook                │
        │                                 │
        │  Control Plane                  │
        │  FastAPI :9000                  │
        │  ├── Node Registry              │
        │  ├── Registration API           │
        │  └── Heartbeat API              │
        │                                 │
        └────────────────┬────────────────┘
                         │
                 Private Connectivity
                         │
        ┌────────────────▼────────────────┐
        │        Windows Laptop           │
        │                                 │
        │  Node Agent                     │
        │  FastAPI :8000                  │
        │  ├── Node Identity              │
        │  ├── System Information         │
        │  ├── Registration Client        │
        │  └── Heartbeat Client           │
        │                                 │
        └─────────────────────────────────┘

This illustrates the intended communication model. Successful communication between remote machines must be verified before considering remote-node connectivity complete.

4. Networking Decision

Selected networking approach: Tailscale.

Tailscale provides private connectivity between participating machines without requiring them to be on the same local Wi-Fi network or exposing the Control Plane directly to the public internet.

The Control Plane currently listens on 0.0.0.0:9000, allowing it to accept connections through its available network interfaces, subject to firewall and network configuration.

The Node Agent currently uses the configured Control Plane URL:

CONTROL_PLANE_URL = "http://100.90.104.13:9000"

This is the MacBook’s previously identified Tailscale IP and must be verified if the network configuration changes.

Important: A successful local heartbeat test does not prove that a remote node can reach the Control Plane. Remote connectivity, firewall rules, and the address reported during node registration must be verified separately.

The current focus is building CloudHeal’s management capabilities. Troubleshooting or adding another remote node is paused unless required by a later implementation or test.

5. Repository Structure

The current project structure is approximately:

CloudHeal/
├── README.md
├── pyproject.toml
├── uv.lock
├── docs/
│   ├── CloudHeal_CONTEXT.md
│   ├── SPEC-001-cloudheal.md
│   └── current_progress.md
├── control-plane/
│   ├── pyproject.toml
│   ├── src/
│   │   └── cloudheal_control_plane/
│   │       ├── __init__.py
│   │       ├── api.py
│   │       ├── main.py
│   │       └── registry.py
│   └── tests/
└── infrastructure/
    └── node-agent/
        ├── pyproject.toml
        ├── src/
        │   └── cloudheal_node_agent/
        │       ├── __init__.py
        │       ├── api.py
        │       ├── heartbeat.py
        │       ├── identity.py
        │       ├── main.py
        │       ├── models.py
        │       ├── network.py
        │       ├── registration.py
        │       └── system.py
        └── tests/

The repository uses uv for Python dependency and package management.

Do not restructure the workspace unless a demonstrated technical requirement makes it necessary.

6. Current Control Plane API

The Control Plane currently exposes the following endpoints:

Method	Endpoint	Purpose
GET	/health	Check Control Plane health
POST	/nodes/register	Register a node
GET	/nodes	List registered nodes
GET	/nodes/{node_id}	Retrieve a specific node
POST	/nodes/{node_id}/heartbeat	Update a node’s last-seen timestamp

The node registry is currently stored in process memory.

Consequently:

* Node records are lost when the Control Plane process restarts.
* Heartbeats update timestamps but do not yet implement automatic offline detection.
* Persistent storage has not been implemented.

These limitations are acceptable at the current development stage.

7. Current Implementation Status

Completed

* Initial Control Plane application.
* Node Agent application.
* Persistent node identity generation.
* Local system resource collection.
* Node registration endpoint.
* In-memory node registry.
* Node listing and individual-node retrieval.
* Heartbeat endpoint.
* Node Agent heartbeat loop.
* Initial Tailscale networking decision.
* Python workspace setup using uv.

Not Yet Implemented

* Workload management.
* Workload scheduling.
* Container execution.
* Workload placement and migration.
* Persistent Control Plane storage.
* Automatic offline-node detection.
* Self-healing execution.
* Dashboard.

These features must be added incrementally.

8. Next Component: Workload Management

Immediate objective: Implement the first Workload Management component without modifying the existing node registry or heartbeat implementation.

The first milestone is:

CloudHeal accepts a workload, assigns it a unique identity, stores its state, and allows the user to inspect it through the API.

This is a management capability only. Submitting a workload will not yet execute a container or application.

8.1 First Component

The first file to implement is:

control-plane/
└── src/
    └── cloudheal_control_plane/
        └── workloads/
            ├── __init__.py
            └── models.py

Initially, create only the package and its data model. Do not create every planned workload file in advance.

The workload model will define the data needed to represent a workload, including:

* Unique workload ID.
* Workload name.
* Container image or workload specification.
* Desired state.
* Actual state.
* Assigned node ID, if applicable.
* Creation timestamp.
* Other execution metadata when justified.

The initial lifecycle states should distinguish between desired state and actual state.

Desired state describes what the user wants CloudHeal to achieve.

Actual state describes the workload’s currently recorded condition.

Initial actual states may include:

State	Meaning
PENDING	Accepted but not yet scheduled
SCHEDULED	Assigned to a node
RUNNING	Confirmed as running
FAILED	Execution failed
STOPPED	Workload has stopped

These are conceptual lifecycle states. The first implementation may use only the states needed for workload submission and inspection.

A workload must not be marked RUNNING merely because its record was created. CloudHeal must wait until execution is implemented and running status can be verified.

8.2 First Milestone: Workload Records

After defining and testing the data model, add only the components required to support workload records.

The eventual initial API will include:

Method	Endpoint	Purpose
POST	/workloads	Accept a workload submission
GET	/workloads	List workload records
GET	/workloads/{workload_id}	Inspect a workload

A stop endpoint may be added later when its behavior can be defined correctly.

The initial implementation will:

1. Accept a workload request.
2. Generate a unique workload ID.
3. Create a workload record.
4. Store it in an in-memory workload registry.
5. Return the created workload.
6. Allow the user to list and inspect workload records.

For the initial version, a newly submitted workload should normally have:

* Desired state: RUNNING.
* Actual state: PENDING.
* Assigned node: None.

This means CloudHeal has accepted the request but has not scheduled or executed it.

8.3 Scope Boundaries

During the first workload milestone:

* Do not modify registry.py for nodes.
* Do not modify the heartbeat implementation.
* Do not add a scheduler.
* Do not add Docker execution.
* Do not add a database.
* Do not introduce Kubernetes.
* Do not create unnecessary abstractions or additional packages.

Keep workload management separate from node management.

After each small implementation step, run tests and verify the behavior through the API before proceeding.

9. Planned Development Sequence

The intended implementation order is:

1. Workload data model and lifecycle states.
2. In-memory workload registry.
3. Workload submission and inspection APIs.
4. Tests for workload creation, listing, and retrieval.
5. Node eligibility and resource information needed for scheduling.
6. Initial scheduler.
7. Node Agent communication for workload execution.
8. Container runtime integration.
9. Workload health monitoring.
10. Failure detection and self-healing.
11. Dashboard and operational visibility.
12. Persistent storage and further reliability improvements.

The order may change if implementation or testing reveals a necessary dependency.

10. Development Principles

All future CloudHeal work should follow these principles:

1. Understand before implementing: Explain the component’s purpose and design before introducing code.
2. Build incrementally: Implement one working capability at a time.
3. Preserve working components: Avoid unrelated changes to the Node Agent, node registry, or heartbeat system.
4. Test every milestone: Verify behavior before moving to the next component.
5. Avoid premature complexity: Do not introduce Kubernetes, databases, or complex orchestration until the project needs them.
6. Keep responsibilities separate: Node management, workload management, scheduling, execution, and self-healing should remain distinct responsibilities.
7. Be accurate about state: Do not claim that a workload is scheduled or running unless that condition has actually been established.
8. Maintain documentation: Update this context file and the relevant progress documentation when meaningful architecture or implementation decisions change.
9. Keep the project demonstrable: Each major stage should produce a working capability that can be shown and tested.
10. Prioritize engineering understanding: Explain important code, APIs, data flow, and design decisions without unnecessary theoretical detours.

11. Immediate Next Action

Begin with Section 8.1: Workload Data Model.

Inspect the existing Control Plane package, create the workloads package, and implement workloads/models.py.

Define and test the workload model and its lifecycle states before building the registry or adding workload API endpoints.

The existing node registry and heartbeat implementation must remain unchanged during this first step.