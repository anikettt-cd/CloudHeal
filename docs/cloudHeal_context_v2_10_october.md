CloudHeal — Complete Project Context & Development Roadmap

Document purpose: Preserve the project’s architecture, current implementation, verified progress, pending work, and development plan so work can resume without repeating previous discussions.

Last updated: 10 October 2026

Current development stage: Local cloud infrastructure foundation — node registration and workload scheduling are implemented and tested. Connecting workload scheduling to actual container execution is the next major task.

⸻

1. Project Overview

1.1 What Are We Building?

CloudHeal is a student engineering project intended to build a small, distributed cloud platform using laptops as its compute nodes.

Instead of immediately deploying applications to an external cloud provider, we want to build the basic infrastructure ourselves.

We currently have four laptops available across our team:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.

The initial goal is to connect these machines over a private network and make their available computing resources usable through a common control system.

Each laptop should eventually be able to contribute computing resources to the platform.

CloudHeal will manage the machines, schedule workloads, run containers, monitor their health, and eventually respond to failures.

The machines do not need to remain online 24/7. This is a development and demonstration environment, not a production cloud service.

1.2 Our Long-Term Goal

We want to build a cloud-like platform with these capabilities:

1. Register multiple computers as cloud nodes.
2. Discover their available resources.
3. Monitor node health and resource utilization.
4. Accept application deployment requests.
5. Select an appropriate node for each workload.
6. Start workloads through Docker.
7. Track workload execution and failures.
8. Detect unhealthy nodes and failed workloads.
9. Recover workloads when possible.
10. Provide a central interface for managing the platform.

Eventually, we should be able to demonstrate an application running on one laptop, simulate a failure, and show CloudHeal detecting the failure and taking an appropriate recovery action.

Potential demonstration workloads include a web server, a small e-commerce application, or a video-streaming service.

These application workloads come later. Our first priority is building the underlying cloud infrastructure correctly.

1.3 What Makes It CloudHeal?

The project should progress beyond a simple Docker launcher.

Its intended distinguishing capability is automated workload management and recovery.

The eventual system should be able to answer questions such as:

* Which nodes are currently available?
* Which node has sufficient resources to run a workload?
* Is the workload actually running?
* Has its container crashed?
* Has a node stopped responding?
* Can the workload be restarted or moved to another node?
* Did the recovery action succeed?

The self-healing functionality will be built on top of the underlying infrastructure. We should not implement recovery logic before reliable execution, status tracking, and health monitoring exist.

⸻

2. Development Philosophy

We must follow these principles throughout development.

2.1 Build the Infrastructure from the Bottom Up

The intended development order is:

1. Node identity and registration.
2. Node health and heartbeat monitoring.
3. Workload models and management.
4. Workload scheduling.
5. Actual workload execution.
6. Resource-aware scheduling.
7. Distributed networking across laptops.
8. Failure detection and recovery.
9. User interface and demonstrations.

Some foundational pieces are already implemented. We will continue from the current state rather than restart the project.

2.2 Avoid Premature Kubernetes Complexity

We are building our own simplified orchestration layer to understand the infrastructure.

Do not introduce Kubernetes, a service mesh, or a large orchestration framework unless a specific requirement justifies it.

Docker is our initial container runtime.

The Control Plane and Node Agent should remain small, understandable Python services.

2.3 Implement and Verify One Component at a Time

For each major feature:

1. Understand its purpose.
2. Identify which existing component should own the responsibility.
3. Inspect the existing code.
4. Make a minimal, well-reasoned change.
5. Run the component.
6. Test its API.
7. Verify the actual system behavior.
8. Update the project documentation.

A successful HTTP response does not necessarily prove that an underlying operation succeeded.

For example, assigning a workload to a node does not prove that Docker started its container.

2.4 Preserve Working Code

Before changing an existing component, inspect its implementation.

Do not repeatedly rewrite the workspace, package configuration, or architecture.

Prefer incremental changes that preserve existing functionality.

2.5 Keep Project Documentation Updated

The primary context document is:

CloudHeal_CONTEXT.md

Update it whenever the architecture, file structure, API contracts, implementation status, or next milestone changes significantly.

⸻

3. Current Architecture

The repository currently has two primary services.

3.1 Control Plane

Location:

control-plane/

Package:

cloudheal-control-plane

Default API address:

http://127.0.0.1:9000

The Control Plane is responsible for centralized management.

Its current responsibilities include:

* Node registration.
* Maintaining a registry of nodes.
* Receiving node heartbeat updates.
* Listing registered nodes.
* Creating workloads.
* Maintaining workload records.
* Scheduling workloads to healthy nodes.

The current registries use in-memory Python data structures.

This is acceptable for our initial development stage, but it means registered nodes and workloads are not durably stored across Control Plane restarts.

3.2 Node Agent

Location:

infrastructure/node-agent/

Package:

cloudheal-node-agent

Default API port:

8000

The Node Agent runs on each participating computer.

Its current responsibilities include:

* Maintaining a persistent node identity.
* Reporting system information.
* Discovering the local network address.
* Registering with the Control Plane.
* Sending periodic heartbeats.
* Reporting Docker runtime information.

The Node Agent also has a container execution implementation in runtime.py.

However, the complete connection between workload scheduling and actual execution still needs to be verified and implemented.

3.3 Intended Architecture

The long-term request flow is:

User or Client
|
v
Control Plane API
|
v
Workload Management
|
v
Scheduler
|
v
Selected Node Agent
|
v
Docker Runtime
|
v
Running Application Container
|
v
Execution Result and Health Updates
|
v
Control Plane Workload State

Each component should have a clear responsibility.

The Control Plane should decide where a workload belongs. The Node Agent should execute it locally. Docker should run the container.

The Control Plane should not directly manipulate another machine’s local Docker daemon.

⸻

4. Current Repository Structure

The relevant structure is:

CloudHeal/
|
|– CloudHeal_CONTEXT.md
|– README.md
|– pyproject.toml
|– uv.lock
|
|– docs/
|   |– SPEC-001-cloudheal.md
|
|– control-plane/
|   |– src/
|       |– cloudheal_control_plane/
|           |– api.py
|           |– main.py
|           |– registry.py
|           |
|           |– workloads/
|               |– models.py
|               |– registry.py
|               |– service.py
|               |– scheduler.py
|
|– infrastructure/
|– node-agent/
|– src/
|– cloudheal_node_agent/
|– api.py
|– identity.py
|– main.py
|– models.py
|– network.py
|– registration.py
|– heartbeat.py
|– system.py
|– runtime.py

This is the relevant known structure. Before adding files or changing APIs, inspect the current repository because the structure may have evolved.

The root project uses uv for Python environment and package management.

The root workspace currently includes the Node Agent package. The Control Plane is also runnable through its package configuration.

⸻

5. Control Plane Implementation

5.1 API

File:

control-plane/src/cloudheal_control_plane/api.py

The application uses FastAPI.

The current API includes the following endpoints.

Health

GET /health

Returns:

{"status": "ok"}

Verified working on 10 October 2026.

Node Registration

POST /nodes/register

Registers a node.

List Nodes

GET /nodes

Returns registered nodes.

Get Node

GET /nodes/{node_id}

Returns an individual registered node.

Node Heartbeat

POST /nodes/{node_id}/heartbeat

Accepts optional system and runtime information.

The request model is:

class NodeHeartbeat(BaseModel):
    system_info: dict[str, Any] | None = None
    runtime_info: dict[str, Any] | None = None

Important: NodeHeartbeat must be defined before the heartbeat() function in api.py, because the function uses the model in its type annotation.

This definition-order issue was encountered and fixed during the current development session. The Control Plane subsequently started successfully.

Create Workload

POST /workloads

Creates a workload record.

List Workloads

GET /workloads

Returns all registered workload records.

Get Workload

GET /workloads/{workload_id}

Returns an individual workload.

Schedule Workload

POST /workloads/{workload_id}/schedule

Requests scheduling of a workload.

The current implementation selects a healthy node and assigns its ID to the workload.

It does not yet prove that the selected Node Agent started the corresponding container.

⸻

6. Node Registry

File:

control-plane/src/cloudheal_control_plane/registry.py

The registry contains the NodeRecord model and node registration, lookup, listing, and heartbeat functionality.

The registered node record currently includes information such as:

* Node ID.
* Hostname.
* Network address.
* Health status.
* Last heartbeat timestamp.
* System information.
* Runtime information.

The current node registry is in memory.

The current scheduler uses get_nodes() to retrieve registered nodes and considers nodes with a healthy status eligible.

A future improvement will be resource-aware scheduling, rather than selecting the first healthy node.

⸻

7. Workload Management Implementation

7.1 Workload Models

File:

control-plane/src/cloudheal_control_plane/workloads/models.py

The project currently defines two enums.

DesiredState

* RUNNING
* STOPPED

This represents what the user wants the workload to do.

WorkloadState

* PENDING
* SCHEDULED
* RUNNING
* FAILED
* STOPPED

This represents the workload’s recorded execution state.

Desired state and actual state must remain separate.

For example, a workload may have:

desired_state = RUNNING
actual_state = FAILED

This means the user still wants the workload running, but its current execution has failed.

That distinction will be important when implementing recovery.

7.2 WorkloadCreate

The workload creation model contains:

* name
* image
* desired_state
* cpu_limit
* memory_limit_mb

Current validation includes:

* Name length between 1 and 100 characters.
* Image length between 1 and 255 characters.
* CPU limit greater than zero.
* Memory limit greater than zero.

Defaults:

* Desired state: RUNNING
* CPU limit: 1.0
* Memory limit: 256 MB

7.3 WorkloadRecord

The stored workload record contains:

* Workload UUID.
* Name.
* Container image.
* Desired state.
* Actual state.
* Assigned node ID.
* CPU limit.
* Memory limit.
* Creation timestamp.
* Update timestamp.

The initial actual state is PENDING.

The model validates assignments using Pydantic’s validate_assignment=True.

7.4 Workload Registry

File:

control-plane/src/cloudheal_control_plane/workloads/registry.py

The registry provides:

* create_workload()
* get_workload()
* list_workloads()
* update_workload()

It stores workload records in an in-memory dictionary keyed by workload UUID.

The registry implementation has been inspected and confirmed to exist.

7.5 Workload Service

File:

control-plane/src/cloudheal_control_plane/workloads/service.py

The service provides an abstraction over the registry.

It currently handles:

* Creating workload records.
* Retrieving workloads.
* Listing workloads.
* Updating workload records.

The service should remain the central entry point for workload-management operations.

⸻

8. Current Scheduler

File:

control-plane/src/cloudheal_control_plane/workloads/scheduler.py

The current class is:

WorkloadScheduler

Its constructor receives a WorkloadService.

The current scheduling process is:

1. Retrieve the workload by ID.
2. Raise a lookup error if the workload does not exist.
3. Ensure its actual state is PENDING.
4. Ensure its desired state is RUNNING.
5. Retrieve registered nodes.
6. Filter for healthy nodes.
7. Raise a scheduling error if no healthy nodes exist.
8. Select the first healthy node.
9. Assign the selected node ID to the workload.
10. Change its state to SCHEDULED.
11. Update the timestamp.
12. Save and return the updated record.

The current scheduler has a deliberately simple policy:

Select the first healthy node.

It does not yet check whether the selected node has sufficient available CPU or memory.

It also does not yet contact the Node Agent or start a container.

These are separate tasks.

We should first implement and verify execution. Then we can improve scheduling with resource checks.

⸻

9. Verified Node Agent Status

The Node Agent currently includes the following modules.

identity.py

Maintains a persistent node UUID in:

~/.cloudheal/node_id

This allows a node to retain its identity across agent restarts.

network.py

Discovers the local IP address.

system.py

Collects machine information using psutil.

Reported information includes:

* Operating system.
* Architecture.
* CPU core counts and usage.
* Memory capacity and usage.
* Disk capacity and usage.

registration.py

Registers the Node Agent with the Control Plane.

heartbeat.py

Sends periodic heartbeats.

The previously configured heartbeat interval was 10 seconds.

api.py

Provides the Node Agent’s FastAPI application and integrates registration and heartbeat startup behavior.

runtime.py

Contains a container execution function named:

run_container()

This function must be inspected before changing the execution architecture.

We need to verify its current parameters, Docker invocation, resource-limit handling, return value, and error behavior.

models.py

Contains Node Agent data models.

We need to inspect the actual file before deciding whether new execution request and response models are necessary.

⸻

10. Latest Verified Node

The latest registered node is the development MacBook Air.

Its reported information was:

* Node ID: 83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
* Hostname: Anikets-MacBook-Air.local
* Local address: 192.168.1.124
* Operating system: macOS
* Architecture: ARM64
* Physical CPU cores: 8
* Logical CPU cores: 8
* Physical memory: 8 GiB
* Docker version: 29.8.2
* Docker runtime available: true
* Node status: healthy

The reported runtime information identified Docker Desktop.

These values are the last observed measurements, not permanent guarantees of available capacity.

The node’s available memory was approximately 2.13 GB at the time of the reported sample. Docker reported a separate runtime memory figure of approximately 4.11 GB.

Those values describe different measurements and must not be treated as interchangeable.

⸻

11. What We Accomplished on 10 October 2026

This section records the latest verified progress.

11.1 Fixed the Control Plane Startup Error

The application initially failed with:

NameError: name 'NodeHeartbeat' is not defined

The problem occurred because the model was defined below a function that referenced it.

The model definition was moved above the heartbeat function.

After the correction, the Control Plane started successfully.

Verified command:

curl http://127.0.0.1:9000/health

Verified response:

{"status":"ok"}

11.2 Verified Node Registration

Command:

curl -s http://127.0.0.1:9000/nodes

The API returned the registered Mac node with its node ID, hostname, address, health status, system information, and Docker runtime information.

This verified that the Control Plane could retrieve the registered node.

11.3 Verified the Initial Workload Registry

Command:

curl -s http://127.0.0.1:9000/workloads

The API initially returned:

[]

This was expected because the workload registry was empty after the Control Plane restart.

11.4 Created an Nginx Workload

Command:

curl -X POST http://127.0.0.1:9000/workloads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nginx-test",
    "image": "nginx:latest",
    "desired_state": "RUNNING",
    "cpu_limit": 1.0,
    "memory_limit_mb": 256
  }'

The API returned a workload record with:

* Name: nginx-test
* Image: nginx:latest
* Desired state: RUNNING
* Actual state: PENDING
* Node ID: null
* CPU limit: 1.0
* Memory limit: 256 MB

The generated workload ID was:

4a2b31f2-5a0f-4b23-adac-ce5ceb78f54e

This operation was successful.

11.5 Verified Workload Persistence Within the Running Process

The subsequent GET /workloads request returned the created workload.

This verified that the workload registry stored and retrieved the record while the Control Plane process was running.

It does not mean the record is durably stored across restarts.

11.6 Successfully Scheduled the Workload

Command:

curl -X POST \
  http://127.0.0.1:9000/workloads/4a2b31f2-5a0f-4b23-adac-ce5ceb78f54e/schedule

The response confirmed:

* Workload ID: 4a2b31f2-5a0f-4b23-adac-ce5ceb78f54e
* Name: nginx-test
* Actual state: SCHEDULED
* Assigned node ID: 83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed

The workload’s state transitioned from:

PENDING -> SCHEDULED

A subsequent GET /workloads request confirmed the scheduled state.

This is the last verified development milestone.

Important: We have verified workload creation and scheduling, not end-to-end execution through CloudHeal.

The scheduled workload has not yet been proven to be running through the CloudHeal execution path.

Do not infer that the container is running merely because the workload state is SCHEDULED.

⸻

12. Immediate Next Task: Connect Scheduling to Container Execution

This is the first task to resume after the internal examinations.

Do not start by implementing the dashboard, advanced scheduling, or self-healing.

First, complete the execution lifecycle.

12.1 Inspect the Existing Implementation

From the repository root, inspect these files:

cat infrastructure/node-agent/src/cloudheal_node_agent/api.py
cat infrastructure/node-agent/src/cloudheal_node_agent/runtime.py
cat infrastructure/node-agent/src/cloudheal_node_agent/models.py

Also inspect the Control Plane’s current implementation:

cat control-plane/src/cloudheal_control_plane/api.py
cat control-plane/src/cloudheal_control_plane/workloads/scheduler.py

The first three files are the immediate priority.

We must understand the existing Node Agent endpoint structure and runtime implementation before changing anything.

12.2 Define the Execution Contract

The intended execution request needs enough information for the selected Node Agent to identify and start the workload.

At minimum, execution needs:

* Workload ID.
* Workload name.
* Container image.
* CPU limit.
* Memory limit.

We should reuse the existing workload model where appropriate rather than inventing unnecessary duplicate models.

The Node Agent should return a meaningful execution result, including enough information to determine whether the container started successfully.

A container ID and container state may be useful response fields.

The exact request and response models should be chosen after inspecting the existing code.

12.3 Add or Confirm a Node Agent Execution Endpoint

The Node Agent needs an API operation through which the Control Plane can request workload execution.

Responsibilities:

1. Validate the execution request.
2. Call the existing runtime function.
3. Handle Docker errors.
4. Return the execution result.
5. Avoid reporting success when the container failed to start.

The Node Agent should own the actual interaction with its local Docker runtime.

12.4 Connect the Control Plane to the Selected Node

The Control Plane must contact the Node Agent associated with the selected node.

The current scheduler only changes the workload record.

We need to establish the correct execution sequence:

1. Validate the workload.
2. Select an eligible node.
3. Request execution from that node’s Node Agent.
4. Check the execution result.
5. Update the workload record based on the result.
6. Return an appropriate response to the caller.

The design must distinguish scheduling success from execution success.

We should also define sensible behavior for network timeouts, unreachable agents, Docker errors, and failed container startup.

12.5 Correct Workload State Transitions

The intended lifecycle is:

PENDING
   |
   v
SCHEDULED
   |
   +---- execution succeeds ----> RUNNING
   |
   +---- execution fails -------> FAILED

These states should reflect actual events.

The Control Plane must not mark a workload RUNNING before receiving adequate confirmation from the Node Agent.

A more complete lifecycle may introduce a dedicated STARTING state later, but we should not add unnecessary states until their value is clear.

12.6 Test Actual Execution

After implementation, test the complete flow.

Test A: Create the workload

Create a fresh Nginx workload.

Test B: Request scheduling

Send a scheduling request through the Control Plane.

Test C: Inspect the workload record

Check that the workload has the expected node assignment and state.

Test D: Inspect Docker

On the selected node, run:

docker ps

Confirm that the Nginx container was created by the CloudHeal execution flow.

If it is not listed, inspect:

docker ps -a

The second command can reveal containers that exited after starting.

Test E: Inspect container logs

If the container fails or exits, inspect its logs and the Node Agent’s error output.

Test F: Verify HTTP accessibility

Determine how the container is exposed and test its actual HTTP endpoint.

A container can be running without being reachable from another machine. Container state and network accessibility must be verified separately.

Test G: Verify failure handling

Test a deliberately invalid image or another controlled failure scenario.

Confirm that the Control Plane does not report the workload as running when execution fails.

The final milestone is:

Create a workload through the Control Plane, schedule it to a node, start it through the Node Agent, verify its Docker container, and report its actual state correctly.

⸻

13. Second Major Task: Resource-Aware Scheduling

After end-to-end execution works, improve the scheduler.

The current policy selects the first healthy node.

That is sufficient for the initial test but not for a multi-node cloud platform.

Eventually, scheduling should consider:

* Node health.
* Available CPU capacity.
* Available memory.
* Runtime availability.
* Workload CPU requirements.
* Workload memory requirements.
* Existing workload allocations.
* Node connectivity.

A node may be healthy but unable to accommodate another workload.

For example, a workload requiring 1 CPU and 256 MB of memory should not automatically be placed on a node that lacks sufficient allocatable capacity.

We must distinguish total hardware resources from resources available to CloudHeal workloads.

The scheduler should eventually reject unsuitable nodes and select an eligible alternative.

A simple scoring or best-fit policy is enough initially. We do not need a complex optimization algorithm.

⸻

14. Third Major Task: Connect Multiple Laptops

Once local execution is verified, extend the system across the team’s machines.

Current environment:

* MacBook Air: macOS.
* Three teammate laptops: Windows.

Each machine should run a Node Agent and its own local container runtime.

The Control Plane should maintain the node registry and communicate with the selected agent over the network.

14.1 Network Connectivity

The first step is to ensure that the machines can communicate over the same private network.

We must account for:

* Different local IP addresses.
* Host firewalls.
* Node Agent port accessibility.
* Control Plane reachability.
* Changes in local IP addresses.
* Docker availability on each node.

The current development configuration uses localhost for local testing. That will not work unchanged when a remote laptop needs to contact the Control Plane.

The Node Agent’s Control Plane URL must be configurable rather than permanently hardcoded to localhost.

14.2 Bind and Configure Services Carefully

For a remote machine to reach a service, the service must listen on an appropriate network interface, and the host firewall must permit the connection.

We should expose only the ports needed for the demonstration.

The Control Plane and Node Agents should not be exposed indiscriminately to the public internet.

Authentication between nodes and the Control Plane will be necessary before treating the system as anything more than a trusted local demonstration.

14.3 Verify Remote Execution

The target test is:

1. Start the Control Plane on the designated machine.
2. Start Node Agents on the participating laptops.
3. Confirm all nodes appear in the registry.
4. Create a workload.
5. Schedule it to a remote node.
6. Verify the container on that remote machine.
7. Confirm that the workload state reflects the execution result.

At this point, CloudHeal will demonstrate actual distributed workload placement.

⸻

15. Fourth Major Task: Health Monitoring

The Node Agent already collects system information and sends heartbeats.

The next stage is to turn these signals into reliable health information.

The Control Plane should be able to distinguish:

* A node that is healthy and responsive.
* A node that is temporarily unreachable.
* A node that has stopped sending heartbeats.
* A node whose Docker runtime is unavailable.
* A node that has insufficient resources.

A future implementation should mark nodes unhealthy or unavailable when they fail to report within a configured timeout.

The system must not rely solely on the node’s last reported status.

Health detection must account for stale heartbeat timestamps.

⸻

16. Fifth Major Task: Self-Healing

Self-healing is the intended higher-level capability, but it depends on reliable execution and health tracking.

The initial self-healing implementation should be rule-based.

For example:

1. A workload is confirmed to be running.
2. The Node Agent detects or reports that its container exited.
3. The Control Plane receives the failure.
4. The Control Plane updates the workload state.
5. A recovery policy decides whether to restart or reschedule the workload.
6. The scheduler selects an eligible node.
7. The Node Agent starts the replacement container.
8. The Control Plane verifies the recovery result.

A node failure is more complicated than a container failure.

If a node becomes unreachable, the Control Plane may not know whether the workload stopped, is still running locally, or is simply disconnected from the network.

We must avoid starting duplicate instances unintentionally.

Recovery should account for:

* Retry limits.
* Duplicate execution requests.
* Node availability.
* Workload desired state.
* Container identity.
* Execution timeouts.
* Recovery verification.

We should first implement simple container restart or rescheduling behavior and verify it with controlled failures.

Advanced anomaly detection or machine-learning-based failure prediction can be considered later. It is not a prerequisite for the initial self-healing demonstration.

⸻

17. Sixth Major Task: User Interface

A dashboard will become useful after the backend behavior is reliable.

The eventual dashboard could display:

Nodes

* Registered nodes.
* Online/offline status.
* CPU and memory usage.
* Runtime availability.

Workloads

* Workload name and ID.
* Desired and actual state.
* Assigned node.
* Container status.
* Resource limits.

Events

* Workload creation.
* Scheduling decisions.
* Execution failures.
* Node disconnections.
* Recovery attempts.
* Recovery results.

The dashboard is not the immediate priority.

The backend must first support trustworthy state transitions and actual workload execution.

⸻

18. Current Technical Limitations

The following limitations are known from the current implementation.

18.1 In-Memory State

Node and workload registries are stored in memory.

A Control Plane restart clears the records.

We should introduce persistent storage when the execution lifecycle and data model have stabilized.

18.2 First-Healthy-Node Scheduling

The scheduler selects the first healthy node.

It does not yet perform resource-aware placement.

18.3 Scheduling Is Not Execution

The current scheduler assigns a node and sets the workload state to SCHEDULED.

End-to-end execution through the Node Agent has not yet been verified.

18.4 Resource Reporting Is Not Resource Reservation

Reported CPU and memory values do not automatically guarantee that a workload can safely start.

Resource accounting and allocation need to be implemented.

18.5 Remote Networking Is Not Yet Verified

The current local Control Plane and Node Agent communication works within the development setup.

Multi-laptop networking and remote execution still need to be tested.

18.6 Authentication and Security

The current system is a development environment.

Before extending it beyond a trusted local network, we need appropriate authentication, authorization, request validation, and secure communication.

⸻

19. Commands for Resuming Development

First, open the project:

cd /Users/aniketsaini/Desktop/CloudHeal

Activate the existing environment:

source .venv/bin/activate

Check the Git working tree:

git status

Read this document:

cat CloudHeal_CONTEXT.md

Then inspect the immediate execution files:

cat infrastructure/node-agent/src/cloudheal_node_agent/api.py
cat infrastructure/node-agent/src/cloudheal_node_agent/runtime.py
cat infrastructure/node-agent/src/cloudheal_node_agent/models.py

Inspect the Control Plane’s scheduling implementation:

cat control-plane/src/cloudheal_control_plane/workloads/scheduler.py
cat control-plane/src/cloudheal_control_plane/api.py

These commands are intended to establish the actual current state before making changes.

Running the Control Plane

uv run --package cloudheal-control-plane cloudheal-control-plane

The default port is 9000.

Running the Node Agent

uv run --package cloudheal-node-agent cloudheal-node-agent

The previously configured Node Agent port is 8000.

Before running either service, check whether it is already running to avoid unnecessary duplicate processes.

The Node Agent’s registration configuration should also be checked before restarting it.

Checking the Control Plane

Health:

curl http://127.0.0.1:9000/health

Nodes:

curl -s http://127.0.0.1:9000/nodes

Workloads:

curl -s http://127.0.0.1:9000/workloads

Interactive API documentation:

http://127.0.0.1:9000/docs

The Control Plane’s in-memory records may be empty after a restart. Do not assume previously created workload records still exist.

⸻

20. Development Roadmap and Priority

The following order should guide further development.

Priority	Task	Status
1	Control Plane health endpoint	Verified
2	Node registration	Verified
3	Node system and runtime information	Verified
4	Heartbeat integration	Implemented; reverify as needed
5	Workload creation and retrieval	Verified
6	Basic workload scheduling	Verified
7	Connect scheduling to Node Agent execution	Next task
8	Verify Docker container execution	Pending
9	Report actual workload state	Pending
10	Handle execution failures	Pending
11	Resource-aware scheduling	Pending
12	Multi-laptop networking	Pending
13	Multi-node execution	Pending
14	Node failure detection	Pending
15	Workload recovery and self-healing	Pending
16	Persistent state storage	Pending
17	Dashboard and demonstration	Pending

These tasks are not all independent. Execution verification must precede dependable workload recovery.

⸻

21. How the Next Development Session Should Begin

When development resumes, do not start by adding a new feature immediately.

First:

1. Read this document.
2. Check the repository’s current state.
3. Inspect the existing Node Agent API, runtime, and models.
4. Explain how the existing runtime function works.
5. Identify the smallest required changes.
6. Implement the execution connection.
7. Test the full lifecycle.
8. Update this document with the verified results.

Do not assume the current code is identical to an earlier conversation. The repository is the source of truth.

Do not replace working modules with entirely new implementations unless inspection demonstrates that a redesign is necessary.

⸻

22. Final Project Summary

CloudHeal is being built as a small distributed cloud platform using our team’s laptops as compute nodes.

The Control Plane manages nodes and workloads. Each laptop runs a Node Agent that reports system information and communicates with the Control Plane. Docker provides the initial container execution layer.

The project has already moved beyond its initial setup stage.

We have verified:

* Control Plane startup.
* Node registration.
* System and runtime information reporting.
* Workload creation.
* Workload retrieval.
* Healthy-node selection.
* Workload assignment and the PENDING to SCHEDULED transition.

The immediate missing link is actual workload execution.

Our next milestone is to make CloudHeal start an Nginx container through the selected Node Agent, verify that the container is running, and update the workload state accurately.

After that, we will make scheduling resource-aware, connect multiple laptops, strengthen health monitoring, and build the self-healing functionality.

The guiding principle is:

Build the infrastructure first, verify real behavior, and add automation only when the underlying system is reliable.

When you’re ready to resume, open CloudHeal_CONTEXT.md and use it to continue from the existing code. The first task will be inspecting infrastructure/node-agent/src/cloudheal_node_agent/api.py, runtime.py, and models.py before connecting scheduling to Docker execution.

One recommendation: Keep this file as the main project context, and update its progress and next-task sections after each significant development session. That will make it much easier to continue without losing track of the architecture or repeating work.