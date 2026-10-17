Here’s the updated CloudHeal project context, incorporating our latest discussions about the self-healing architecture, AI agents, and our decision to finish the cloud infrastructure first. I’ve also updated the next development milestone to reflect our recent scheduler work.

CloudHeal — Complete Project Context & Development Roadmap

Document purpose: Preserve the project architecture, implementation status, verified progress, design decisions, and development roadmap so development can resume without repeating previous work.

Last updated: 18 October 2026

Current development stage: Cloud infrastructure foundation — node registration, heartbeats, workload management, basic scheduling, and the initial scheduler-to-Node-Agent execution integration work.

Immediate priority: Finish verifying the scheduler-to-Node-Agent execution lifecycle, including Docker execution, accurate workload state transitions, and failure handling.

⸻

1. Project Overview

1.1 What Are We Building?

CloudHeal is a student engineering project intended to build a small, distributed cloud platform using laptops as compute nodes.

Instead of relying entirely on an external cloud provider, we are building our own simplified cloud infrastructure to understand how distributed workload management and orchestration work.

We currently have four laptops available across the team:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.

The initial goal is to connect these machines over a private network and make their computing resources available through a centralized control system.

Each laptop will eventually be able to run workloads assigned by CloudHeal.

The platform will manage nodes, schedule workloads, execute containers, monitor health, and eventually recover from failures automatically.

The machines do not need to remain online 24/7. This is a development and demonstration environment, not a production cloud service.

1.2 Our Long-Term Goal

CloudHeal will progressively support:

1. Registering multiple computers as cloud nodes.
2. Discovering their available resources.
3. Monitoring node health and resource utilization.
4. Accepting application deployment requests.
5. Selecting appropriate nodes for workloads.
6. Starting workloads through Docker.
7. Tracking workload execution and failures.
8. Detecting unhealthy nodes and failed workloads.
9. Restarting or rescheduling workloads when possible.
10. Providing a central interface for managing the platform.
11. Using AI agents to investigate failures and recommend recovery strategies.
12. Coordinating safe recovery workflows and verifying their outcomes.

Eventually, we want to demonstrate an application running on one laptop, deliberately simulate a failure, and show CloudHeal detecting the failure and recovering the application on an appropriate node.

1.3 What Makes CloudHeal Different?

Our goal is to build more than a Docker launcher or a basic cloud-management dashboard.

The distinguishing feature will be automated workload management and self-healing, enhanced by AI where it provides genuine value.

CloudHeal should eventually be able to answer:

* Which nodes are available?
* Which node has enough resources to run a workload?
* Is the container actually running?
* Has the application become unhealthy?
* Has a node stopped responding?
* What probably caused the failure?
* What recovery actions are appropriate?
* Is the proposed action safe?
* Did the recovery actually work?

The underlying infrastructure must provide reliable execution and state information before we introduce sophisticated recovery logic.

⸻

2. Our Core Development Philosophy

2.1 Build the Cloud Infrastructure First

Our immediate focus is building a working cloud infrastructure.

The intended sequence is:

1. Node identity and registration.
2. Heartbeat and health reporting.
3. Workload models and management.
4. Basic workload scheduling.
5. Actual Docker execution through Node Agents.
6. Reliable workload state transitions and execution failure handling.
7. Resource-aware scheduling.
8. Multi-laptop networking and distributed execution.
9. Persistent state and stronger health monitoring.
10. Rule-based self-healing.
11. AI-assisted diagnosis and recovery planning.
12. Dashboard and demonstration.

We must continue from the current repository rather than rebuilding the project.

2.2 Build Our Own Simplified Cloud

We are deliberately implementing our own small orchestration layer.

We will use:

* Python and FastAPI for the Control Plane and Node Agents.
* Docker as the initial container runtime.
* HTTP APIs for communication.
* uv for Python environment and package management.
* A private network for communication between our laptops.

We should not introduce Kubernetes, a service mesh, or large orchestration frameworks without a specific requirement.

The purpose is to understand and implement the essential infrastructure ourselves.

2.3 Implement and Verify One Component at a Time

For each major feature:

1. Understand its purpose.
2. Inspect the existing implementation.
3. Identify which component should own the responsibility.
4. Make the smallest appropriate change.
5. Run the component.
6. Test its API.
7. Verify actual system behavior.
8. Record the verified result.
9. Update the project documentation.

A successful HTTP response does not necessarily mean that the underlying operation succeeded.

For example, assigning a workload to a node does not prove that Docker started its container.

2.4 Preserve Working Code

Before modifying an existing component, inspect its implementation.

Do not repeatedly rewrite the workspace, package configuration, or architecture.

Prefer incremental, testable changes.

2.5 Engineer for Future Extensions

We want to avoid major architectural changes when we eventually introduce self-healing and AI agents.

To support this goal:

* Keep component responsibilities separate.
* Keep scheduling separate from execution.
* Keep Docker operations inside the Node Agent.
* Represent workload state accurately.
* Report execution failures to the Control Plane.
* Maintain clear API contracts.
* Record important events and errors.
* Make resource information available to the scheduler.

We do not need to implement the agents or the complete self-healing architecture now.

We only need to ensure that the current infrastructure is designed sensibly enough to support them.

⸻

3. Current and Future Architecture

3.1 Current Infrastructure Components

Control Plane

Central management service responsible for nodes, workloads, and scheduling.

Node Agent

A small service running on each participating laptop. It communicates with the Control Plane and manages permitted operations on its own machine.

Docker Runtime

Runs application containers locally on each node.

Workload Scheduler

Selects a suitable node for a workload.

Workload Service and Registry

Manage workload records and their current state.

3.2 Intended Cloud Infrastructure Flow

             User / Client
                   |
                   v
             Control Plane
              (FastAPI)
                   |
          Workload Management
                   |
                   v
               Scheduler
                   |
            Select a Node
                   |
                   v
             Node Agent
                   |
                   v
             Docker Runtime
                   |
                   v
            Running Container
                   |
                   v
         Execution Result / Status
                   |
                   v
             Control Plane

The Control Plane decides where a workload should run.

The Node Agent executes it locally.

Docker runs the container.

The Control Plane updates the workload record based on the execution result.

3.3 Future Self-Healing Architecture

The following components will be added after the infrastructure foundation is reliable.

       Monitoring and Health Signals
                    |
                    v
             Failure Detection
                    |
                    v
          Self-Healing Coordinator
                    |
             Failure Diagnosis
                    |
                    v
          Recovery Planning Agent
                    |
                    v
             Policy Validation
                    |
                    v
             Workload Scheduler
                    |
                    v
               Node Agent
                    |
                    v
             Docker Execution
                    |
                    v
           Recovery Verification
                    |
                    v
             Updated Workload State

The AI components will use the existing infrastructure rather than replace it.

The recovery coordinator will orchestrate the process. The policy engine will validate proposed actions. The scheduler and Node Agents will carry out permitted operations.

This architecture is a future design target, not a claim that these components already exist.

⸻

4. Repository Structure

The relevant known repository structure is:

CloudHeal/
|
|-- CloudHeal_CONTEXT.md
|-- README.md
|-- pyproject.toml
|-- uv.lock
|
|-- docs/
|   |-- SPEC-001-cloudheal.md
|
|-- control-plane/
|   |-- src/
|       |-- cloudheal_control_plane/
|           |-- api.py
|           |-- main.py
|           |-- registry.py
|           |
|           |-- workloads/
|               |-- models.py
|               |-- registry.py
|               |-- service.py
|               |-- scheduler.py
|
|-- infrastructure/
    |-- node-agent/
        |-- src/
            |-- cloudheal_node_agent/
                |-- api.py
                |-- identity.py
                |-- main.py
                |-- models.py
                |-- network.py
                |-- registration.py
                |-- heartbeat.py
                |-- system.py
                |-- runtime.py

This is the last documented structure. Inspect the actual repository before adding files or modifying APIs.

The root project uses uv for Python environment and package management.

The workspace configuration has previously required attention, so preserve the working package configuration unless an actual issue requires a change.

⸻

5. Control Plane

Location: control-plane/

Package: cloudheal-control-plane

Default API address: http://127.0.0.1:9000

The Control Plane is responsible for centralized management.

Its current responsibilities include:

* Node registration.
* Node registry management.
* Heartbeat processing.
* Node lookup and listing.
* Workload creation and retrieval.
* Workload state management.
* Workload scheduling.

The registries currently use in-memory Python data structures.

This is acceptable for the initial development stage, but records do not survive a Control Plane restart.

5.1 Current API

Endpoint	Purpose
GET /health	Check Control Plane availability
POST /nodes/register	Register a node
GET /nodes	List registered nodes
GET /nodes/{node_id}	Retrieve a node
POST /nodes/{node_id}/heartbeat	Receive node heartbeat information
POST /workloads	Create a workload
GET /workloads	List workloads
GET /workloads/{workload_id}	Retrieve a workload
POST /workloads/{workload_id}/schedule	Request workload scheduling

The scheduling endpoint currently selects and assigns a healthy node.

The latest development session also involved extending the scheduler toward actual Node Agent execution and handling execution failures.

The current repository must be inspected to establish exactly which execution changes are now present and which tests have passed.

Do not assume that an earlier verified scheduling implementation proves the complete execution lifecycle.

⸻

6. Node Registry and Health Information

File: control-plane/src/cloudheal_control_plane/registry.py

The registry maintains node records and supports registration, lookup, listing, and heartbeat updates.

Node records contain information such as:

* Node ID.
* Hostname.
* Network address.
* Health status.
* Last heartbeat timestamp.
* System information.
* Runtime information.

The current registry is in memory.

The scheduler uses the registry to identify eligible nodes.

Eventually, node eligibility should consider more than a recorded healthy status. The Control Plane must account for stale heartbeats, Docker availability, resource capacity, and connectivity.

The health-monitoring improvements will be implemented after the execution lifecycle is reliable.

⸻

7. Workload Management

7.1 Workload Models

File: control-plane/src/cloudheal_control_plane/workloads/models.py

The documented desired-state enum contains:

* RUNNING
* STOPPED

The actual-state enum contains:

* PENDING
* SCHEDULED
* RUNNING
* FAILED
* STOPPED

Inspect the current model before making changes because recent development may have extended it.

The distinction between desired and actual state must remain intact.

For example:

desired_state = RUNNING
actual_state  = FAILED

This means the user still wants the workload running, but its current execution has failed.

This separation is fundamental to future self-healing.

7.2 Workload Creation Model

The documented WorkloadCreate fields are:

* name
* image
* desired_state
* cpu_limit
* memory_limit_mb

Documented defaults:

* Desired state: RUNNING
* CPU limit: 1.0
* Memory limit: 256 MB

Validation includes non-empty, bounded name and image lengths, and positive CPU and memory limits.

The current implementation should be inspected before assuming the exact validation rules remain unchanged.

7.3 Workload Record

The workload record contains:

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

The model previously used Pydantic assignment validation.

7.4 Workload Registry and Service

Files:

* control-plane/src/cloudheal_control_plane/workloads/registry.py
* control-plane/src/cloudheal_control_plane/workloads/service.py

The registry stores and retrieves workload records in an in-memory dictionary.

The service provides the main abstraction for creating, retrieving, listing, and updating workloads.

Keep workload-management operations centralized through the service rather than spreading direct registry modifications across unrelated components.

⸻

8. Scheduler and Execution Integration

File: control-plane/src/cloudheal_control_plane/workloads/scheduler.py

The scheduler is a central part of our current development.

8.1 Original Scheduling Behavior

The documented scheduling process was:

1. Retrieve the workload.
2. Reject a nonexistent workload.
3. Require the workload to be in the PENDING state.
4. Require its desired state to be RUNNING.
5. Retrieve registered nodes.
6. Filter for healthy nodes.
7. Reject scheduling if no healthy node exists.
8. Select the first healthy node.
9. Assign its node ID.
10. Set the workload state to SCHEDULED.
11. Update its timestamp.
12. Save and return the record.

This basic behavior was verified on 10 October 2026.

8.2 Recent Scheduler Development

During the 17–18 October development sessions, we continued working on the scheduler and failure handling.

The recent code discussion included:

* WorkloadScheduler.
* SchedulingError.
* ExecutionError.
* The httpx dependency.
* Communication with a Node Agent.
* Tests for scheduling and execution failure behavior.

The current scheduler implementation must be inspected before making additional modifications.

Do not assume that every planned behavior is already implemented or tested.

8.3 Intended Execution Lifecycle

The intended flow is:

1. Validate the workload.
2. Select an eligible node.
3. Identify the selected node’s Node Agent address.
4. Send the workload execution request to that agent.
5. Let the Node Agent invoke its local Docker runtime.
6. Receive and validate the execution result.
7. Update the workload state.
8. Return an appropriate API response.

The scheduler should not directly manipulate a remote Docker daemon.

The Node Agent should own container execution.

8.4 Intended State Transitions

The initial execution lifecycle should be:

PENDING
   |
   v
SCHEDULED
   |
   +---- confirmed execution success ----> RUNNING
   |
   +---- confirmed execution failure ----> FAILED

The workload should not be marked RUNNING merely because a node was selected.

Network errors and timeouts require careful handling. If the Control Plane cannot determine whether a container started, it should not blindly retry the operation and risk creating a duplicate.

We may introduce a STARTING state later if the implementation benefits from representing an in-progress execution explicitly.

8.5 Error Handling

The execution integration must account for:

* Node Agent unreachable.
* HTTP connection errors.
* Execution request timeouts.
* Invalid container images.
* Docker daemon errors.
* Resource-limit errors.
* Container startup failures.
* Invalid or incomplete execution responses.

Error handling should distinguish a confirmed failure from an uncertain outcome.

If the Node Agent starts a container but the response is lost, the Control Plane may not know whether execution succeeded. Future execution requests should therefore support idempotency or container lookup by workload identity.

We should implement the smallest reliable solution appropriate to the current stage.

⸻

9. Node Agent

Location: infrastructure/node-agent/

Package: cloudheal-node-agent

Previously configured API port: 8000

The Node Agent runs on each participating laptop.

Its responsibilities include:

* Maintaining a persistent node identity.
* Reporting system information.
* Discovering the local network address.
* Registering with the Control Plane.
* Sending periodic heartbeats.
* Reporting Docker runtime information.
* Executing permitted workload operations locally.

9.1 Existing Modules

File	Responsibility
identity.py	Persistent node identity
network.py	Local network address discovery
system.py	System information collection
registration.py	Control Plane registration
heartbeat.py	Periodic heartbeat updates
api.py	Node Agent HTTP API
models.py	Request and response models
runtime.py	Docker container execution
main.py	Application startup

9.2 Persistent Node Identity

The documented identity file is:

~/.cloudheal/node_id

The Mac Node Agent previously used this node ID:

83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed

The persistent identity allows a node to retain its identity across Node Agent restarts.

9.3 Heartbeat

The previously configured heartbeat interval was 10 seconds.

The Control Plane receives heartbeat updates containing system and runtime information.

The heartbeat implementation exists, but its current runtime behavior should be verified when necessary.

9.4 Docker Runtime

The file runtime.py contains a function named:

run_container()

Before modifying it, inspect the current implementation.

We need to know:

* Its function signature.
* How it invokes Docker.
* How it applies resource limits.
* What it returns.
* How it handles exceptions.
* Whether it supports identifying an existing container.
* Whether it can distinguish container creation from successful startup.

The Node Agent should remain the component responsible for local Docker interactions.

⸻

10. Last Documented Development Node

The last documented Mac node reported:

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

These are historical observations, not guaranteed current measurements.

The Node Agent’s latest reported memory availability was approximately 2.13 GB. A separate Docker runtime memory measurement was approximately 4.11 GB.

Those values represent different measurements and should not be treated as interchangeable.

Before running resource-sensitive tests, inspect the node’s current system and Docker runtime information.

⸻

11. Verified Progress Before the Latest Development Sessions

The following items were verified on 10 October 2026.

11.1 Control Plane Startup

A NameError occurred because NodeHeartbeat was referenced before its definition.

The model definition was moved above the heartbeat endpoint.

The Control Plane subsequently started successfully.

Command:

curl http://127.0.0.1:9000/health

Response:

{"status":"ok"}

11.2 Node Registration

The registered Mac node appeared in:

curl -s http://127.0.0.1:9000/nodes

The returned record included node identity, hostname, address, health status, system information, and Docker runtime information.

11.3 Workload Creation

An Nginx workload was created using:

curl -X POST http://127.0.0.1:9000/workloads \
  -H "Content-Type: application/json" \
  -d '{
    "name": "nginx-test",
    "image": "nginx:latest",
    "desired_state": "RUNNING",
    "cpu_limit": 1.0,
    "memory_limit_mb": 256
  }'

The previously generated workload ID was:

4a2b31f2-5a0f-4b23-adac-ce5ceb78f54e

The initial record had:

desired_state = RUNNING
actual_state  = PENDING
node_id       = null

This verified workload creation and retrieval within the running Control Plane process.

11.4 Scheduling

The scheduling endpoint was called:

curl -X POST \
  http://127.0.0.1:9000/workloads/4a2b31f2-5a0f-4b23-adac-ce5ceb78f54e/schedule

The response assigned the workload to the Mac node and recorded the state as SCHEDULED.

The transition was:

PENDING -> SCHEDULED

This verified the original scheduling behavior.

It did not, by itself, prove that the container was started through CloudHeal.

11.5 Recent Scheduler and Failure-Handling Work

During the 17–18 October sessions, we continued implementing and testing the scheduler’s execution behavior and failure handling.

The work included adding or using httpx for HTTP communication and reviewing the scheduler’s execution-error handling.

The exact current implementation and latest test results must be established from the repository and test output.

Do not repeat already completed work without first checking the current code and tests.

⸻

12. Immediate Next Milestone: Complete End-to-End Execution

This is our highest priority.

Do not switch to building AI agents, the dashboard, or advanced scheduling before this milestone is verified.

Step 1: Inspect the Current Repository

From the repository root:

cd /Users/aniketsaini/Desktop/CloudHeal
source .venv/bin/activate
git status

Inspect the current Node Agent:

cat infrastructure/node-agent/src/cloudheal_node_agent/api.py
cat infrastructure/node-agent/src/cloudheal_node_agent/runtime.py
cat infrastructure/node-agent/src/cloudheal_node_agent/models.py

Inspect the Control Plane:

cat control-plane/src/cloudheal_control_plane/api.py
cat control-plane/src/cloudheal_control_plane/workloads/scheduler.py
cat control-plane/src/cloudheal_control_plane/workloads/models.py
cat control-plane/src/cloudheal_control_plane/workloads/service.py

Inspect the relevant tests and package configuration if necessary.

The repository is the source of truth.

Step 2: Verify the Execution Contract

Confirm that the Node Agent can receive a workload execution request containing:

* Workload ID.
* Workload name.
* Container image.
* CPU limit.
* Memory limit.

Reuse existing models when appropriate.

The Node Agent should return a meaningful result that lets the Control Plane determine whether execution succeeded.

A container ID, container status, or equivalent execution result may be useful.

Step 3: Verify Node Agent Execution

Confirm that the execution endpoint:

1. Validates the request.
2. Invokes the existing runtime implementation.
3. Handles Docker errors.
4. Returns the actual execution result.
5. Does not report success if the container failed to start.

Avoid duplicating Docker execution logic across services.

Step 4: Verify Scheduler Integration

Confirm that the scheduler:

1. Retrieves and validates the workload.
2. Selects an eligible node.
3. Sends the request to the selected Node Agent.
4. Handles HTTP errors and timeouts.
5. Interprets the execution response correctly.
6. Updates the workload state accurately.
7. Returns an appropriate result.

If execution fails, the workload must not remain falsely marked as running.

Step 5: Run the Existing Tests

Inspect the current tests before adding new ones.

Run the relevant scheduler, service, and Node Agent tests.

Add or update tests for:

* Successful execution.
* No eligible nodes.
* Node Agent connection failure.
* Docker execution failure.
* Invalid execution responses.
* Workload state transitions.
* Timeout or uncertain execution outcomes.

Use mocks for isolated unit tests and actual Docker execution for the integration test.

Step 6: Verify Real Docker Execution

Create a fresh Nginx workload through the Control Plane.

Request scheduling.

Inspect the returned workload record.

On the selected node, run:

docker ps

If the container is not listed, check:

docker ps -a

Inspect container logs if startup fails.

Verify HTTP accessibility according to the actual container port configuration.

A running container is not automatically reachable from another machine.

Completion Criteria

This milestone is complete when we can:

* Create a workload through the Control Plane.
* Schedule it to an eligible node.
* Execute it through that node’s Node Agent.
* Verify the resulting Docker container.
* Report the workload’s state accurately.
* Handle confirmed execution failures without falsely reporting success.

⸻

13. Next: Resource-Aware Scheduling

Once execution is reliable, improve the scheduler.

The current baseline policy selects the first healthy node.

The next version should consider:

* Node health.
* Available CPU capacity.
* Available memory.
* Docker availability.
* Workload resource requirements.
* Existing CloudHeal workload allocations.
* Node connectivity.

Total hardware capacity is not the same as available capacity.

Similarly, available host memory is not the same as Docker’s configured memory limit.

We should account for these differences when determining whether a node can accommodate a workload.

Initially, a simple capacity filter and a straightforward scoring or best-fit policy will be sufficient.

We do not need a complex optimization algorithm.

⸻

14. Next: Multi-Laptop Networking

After local end-to-end execution is verified, connect the team’s laptops.

The intended environment is:

* One macOS node.
* Three Windows nodes.
* A centralized Control Plane.
* A Node Agent and local Docker runtime on each participating machine.

The exact placement of the Control Plane can be decided when configuring the team environment.

We need to verify:

1. Every node can reach the Control Plane.
2. The Control Plane can reach the appropriate Node Agent.
3. Each agent registers with a stable node identity.
4. Host firewalls permit the necessary private-network traffic.
5. The selected remote node can start a container.
6. The Control Plane receives the execution result.
7. Workload state reflects the actual outcome.

The Control Plane URL must be configurable rather than hardcoded to localhost.

We should expose only the ports needed for the demonstration and avoid exposing the services indiscriminately to the public internet.

Authentication between nodes and the Control Plane should be added before treating the platform as more than a trusted development environment.

⸻

15. Health Monitoring and Failure Detection

The Node Agent already collects system information and sends heartbeats.

We will build on that foundation.

The Control Plane should eventually distinguish:

* Healthy and responsive nodes.
* Temporarily unreachable nodes.
* Nodes with stale heartbeats.
* Nodes with unavailable Docker runtimes.
* Nodes with insufficient capacity.

Container monitoring will also be necessary.

The system should be able to determine whether a container:

* Is running.
* Has exited.
* Has repeatedly restarted.
* Fails its application health check.

Health detection should rely on deterministic checks and reliable telemetry.

AI will not be required to decide whether a container has exited or whether a heartbeat has timed out.

⸻

16. Self-Healing System

Self-healing will be built on top of the completed cloud infrastructure.

We should not implement advanced recovery before reliable execution, status tracking, and health monitoring are available.

16.1 Initial Rule-Based Recovery

The first recovery implementation should be deterministic.

For example:

1. A workload is running.
2. Its container exits unexpectedly.
3. CloudHeal detects the failure.
4. The workload state is updated.
5. A recovery policy determines the appropriate action.
6. The scheduler selects an eligible node.
7. The Node Agent starts a replacement container.
8. CloudHeal verifies the result.
9. The workload state and recovery history are updated.

Initially, we can support a small number of well-defined recovery strategies, such as restarting a failed container or rescheduling a workload to another eligible node.

16.2 Recovery Safety

Recovery must account for:

* Retry limits.
* Duplicate execution requests.
* Node availability.
* Desired workload state.
* Container identity.
* Execution timeouts.
* Uncertain execution outcomes.
* Persistent workload data.
* Recovery verification.

A node becoming unreachable does not prove that every workload on that node has stopped.

Before rescheduling, CloudHeal must account for the possibility that the original workload is still running but disconnected from the Control Plane.

For stateful applications, simply starting a new container on another laptop may not recover the application data.

These are important engineering constraints, even if our first demonstration uses a stateless Nginx workload.

⸻

17. AI Agents and Agentic AI

Design decision: AI agents are part of our future self-healing system, not a replacement for our cloud infrastructure.

We can add them after the underlying execution and recovery mechanisms work.

Our goal is to use AI where it improves diagnosis and decision-making.

We should not attach an LLM to every infrastructure component.

17.1 Failure Diagnosis Agent

Purpose: Investigate why a workload or node failed.

It may analyze:

* Container exit codes.
* Container logs.
* Resource measurements.
* Heartbeat history.
* Application health-check results.
* Recent execution events.

Its output should be structured and evidence-based.

For example, it might report that memory pressure is a probable cause of a container failure, while distinguishing observed evidence from uncertain conclusions.

17.2 Recovery Planning Agent

Purpose: Recommend an appropriate recovery strategy based on the diagnosis and available infrastructure information.

Potential recommendations include:

* Restart the container.
* Reschedule the workload.
* Select a node with sufficient memory.
* Retry an operation within a defined limit.
* Escalate repeated failures.

The agent will recommend actions rather than directly execute arbitrary commands.

17.3 Recovery Verification

The initial verification component will use deterministic checks.

It will determine whether the container started and whether the application became healthy.

AI may later assist with investigating repeated verification failures, but it will not replace health checks.

17.4 Policy Engine

A deterministic policy engine will validate recovery actions before execution.

It should enforce:

* Permitted operations.
* Resource requirements.
* Retry limits.
* Node eligibility.
* Workload constraints.
* Human approval for sensitive actions where appropriate.

The LLM must not become a security boundary.

17.5 Multi-Agent Orchestration

Once the diagnosis and recovery-planning components exist, we can consider using LangGraph to coordinate them.

A future workflow might be:

Failure Event
     |
     v
Diagnosis Agent
     |
     v
Recovery Planning Agent
     |
     v
Policy Validation
     |
     v
Recovery Execution
     |
     v
Verification
     |
     +---- Success ----> Record Recovery
     |
     +---- Failure ----> Retry or Escalate

LangGraph would coordinate the AI-assisted workflow.

It would not replace FastAPI, the scheduler, the Node Agents, or Docker.

We should introduce it only when the workflow becomes complex enough to benefit from explicit stateful orchestration.

17.6 Graceful Degradation

The core infrastructure and safe, rule-based recovery should continue operating when the LLM API is unavailable.

AI should improve the system rather than become a dependency for basic workload execution.

⸻

18. Dashboard and Demonstration

The dashboard will be introduced after the core backend behavior is reliable.

Potential dashboard sections include:

Infrastructure

* Registered nodes.
* Online/offline status.
* CPU and memory usage.
* Docker runtime availability.

Workloads

* Workload name and ID.
* Desired and actual state.
* Assigned node.
* Container status.
* Resource limits.

Events and Recovery

* Failure events.
* Execution results.
* Scheduling decisions.
* Recovery attempts.
* Source and destination nodes.
* Verification results.
* Recovery duration.

AI Insights

* Probable failure cause.
* Supporting evidence.
* Recommended recovery action.
* Explanation of the selected strategy.

Intended Demonstration

The eventual demonstration should show:

1. A workload running on one laptop.
2. A deliberately induced failure.
3. Failure detection.
4. A recovery decision.
5. Replacement execution on an eligible node, where appropriate.
6. Application health verification.
7. An event record explaining what happened.
8. AI-generated diagnosis and recovery reasoning.

This demonstrates actual infrastructure behavior rather than simply showing an AI chatbot.

⸻

19. Current Known Limitations

The following limitations have been documented and should be rechecked as development progresses.

19.1 In-Memory State

Node and workload records are currently stored in memory.

A Control Plane restart clears them.

Persistent storage will be introduced when the execution lifecycle and data model are stable enough to justify it.

19.2 Basic Scheduling Policy

The original scheduler selected the first healthy node.

Resource-aware placement remains a planned improvement.

19.3 Execution Integration

The original implementation assigned workloads without proving that Docker started them.

Execution integration has been under active development on 17–18 October.

The exact current state must be verified from the repository and test results.

19.4 Resource Accounting

Reported system resources do not automatically guarantee that a node can safely accept another workload.

Resource accounting and workload allocation need to be implemented.

19.5 Remote Networking

Multi-laptop networking and remote execution still need to be verified.

19.6 Authentication and Security

The current platform is a development environment.

Authentication, authorization, secure communication, and stricter execution controls will be needed before expanding beyond a trusted private-network demonstration.

19.7 Self-Healing and AI

The self-healing engine, diagnosis agent, recovery-planning agent, policy engine, and multi-agent workflow are future components.

They should not be treated as implemented merely because their architecture has been planned.

⸻

20. Development Commands

Open the repository:

cd /Users/aniketsaini/Desktop/CloudHeal

Activate the existing environment:

source .venv/bin/activate

Check the working tree:

git status

Inspect the immediate execution files:

cat infrastructure/node-agent/src/cloudheal_node_agent/api.py
cat infrastructure/node-agent/src/cloudheal_node_agent/runtime.py
cat infrastructure/node-agent/src/cloudheal_node_agent/models.py

Inspect the Control Plane:

cat control-plane/src/cloudheal_control_plane/api.py
cat control-plane/src/cloudheal_control_plane/workloads/scheduler.py
cat control-plane/src/cloudheal_control_plane/workloads/models.py
cat control-plane/src/cloudheal_control_plane/workloads/service.py

Running the Control Plane

Previously documented command:

uv run --package cloudheal-control-plane cloudheal-control-plane

Default port: 9000.

Running the Node Agent

Previously documented command:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously configured port: 8000.

Before launching either service, check whether it is already running.

Verify the current Node Agent configuration before restarting it.

Checking the Control Plane

Health:

curl http://127.0.0.1:9000/health

Nodes:

curl -s http://127.0.0.1:9000/nodes

Workloads:

curl -s http://127.0.0.1:9000/workloads

Interactive API documentation:

http://127.0.0.1:9000/docs

Remember that in-memory records may disappear after a Control Plane restart.

⸻

21. Updated Development Roadmap

Priority	Task	Status
1	Control Plane health endpoint	Verified
2	Node registration	Verified
3	System and runtime information reporting	Verified previously
4	Heartbeat integration	Implemented; verify as needed
5	Workload creation and retrieval	Verified
6	Basic healthy-node scheduling	Verified
7	Scheduler-to-Node-Agent execution integration	Under active development; inspect current code
8	End-to-end Docker execution verification	Must confirm
9	Accurate execution state transitions	Must confirm
10	Execution failure and timeout handling	Under development; verify tests
11	Resource-aware scheduling	Pending
12	Multi-laptop networking	Pending
13	Distributed execution across multiple nodes	Pending
14	Persistent state storage	Pending
15	Reliable node and container health monitoring	Pending
16	Rule-based self-healing	Pending
17	Recovery verification and retry controls	Pending
18	AI Failure Diagnosis Agent	Future
19	AI Recovery Planning Agent	Future
20	Policy-validated recovery orchestration	Future
21	LangGraph integration	Future
22	Dashboard and final demonstration	Future

The exact status of items 7–10 must be updated after inspecting the latest implementation and test results.

⸻

22. Instructions for Resuming Development

When development resumes:

1. Read this context document.
2. Inspect the current Git working tree.
3. Inspect the Node Agent API, runtime, and models.
4. Inspect the latest scheduler implementation and relevant tests.
5. Identify what has already been completed.
6. Avoid repeating completed work.
7. Make the smallest necessary change.
8. Run tests and verify real behavior.
9. Update this document after the milestone is confirmed.

The immediate next task is still to complete and verify the scheduler-to-Node-Agent execution lifecycle.

Do not begin by building AI agents or the dashboard.

We need a working cloud infrastructure before building the self-healing layer.

⸻

23. Final Project Direction

CloudHeal is our attempt to build a small distributed cloud platform using our team’s laptops as compute nodes.

The Control Plane manages nodes and workloads. Each laptop runs a Node Agent. Docker provides the container runtime. The scheduler determines where workloads should run.

Our current work focuses on completing the infrastructure and making workload execution reliable.

After that, we will connect multiple laptops, improve scheduling and health monitoring, and build the self-healing system.

AI agents will eventually help diagnose failures and recommend recovery strategies. Deterministic services will validate and execute permitted actions, and verification will establish whether recovery actually succeeded.

The project should grow incrementally without requiring us to replace the existing infrastructure.

Our guiding principle: Build the cloud infrastructure first, verify real behavior, and then build intelligent self-healing on top of it.

We are not trying to build every feature immediately. We are building a foundation that can support the larger CloudHeal vision.

Important: Save this as the updated CloudHeal_CONTEXT.md after checking the current repository. The execution and failure-handling code changed during our recent sessions, so the status of those tasks should be confirmed from the actual code and test results rather than assumed from this document.