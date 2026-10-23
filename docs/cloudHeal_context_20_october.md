CloudHeal — Complete Project Context & Revised Implementation Roadmap

Last updated: 22 October 2026
Current stage: Control Plane, Docker execution, basic reconciliation, and initial SQLite/event-recording implementation exist. Persistence verification is ongoing.
Immediate priority: Connect and verify a Windows laptop as the second real compute node.
Latest recorded Control Plane test result: 23 passed in 0.33 seconds on 21 October 2026. This is the latest recorded result, not a new test run today.

⸻

1. Project Overview

1.1 What Are We Building?

CloudHeal is a student engineering project to build a small distributed cloud platform using our team’s laptops as compute nodes, with a focus on reliable, measurable, and safe self-healing.

The intended environment consists of:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.
* Tailscale for private networking.
* A Python/FastAPI Control Plane.
* A Node Agent on each participating laptop.
* Docker Desktop for workload execution.
* SQLite for persistent Control Plane state and event history.
* A future AI-assisted diagnosis and recovery-planning layer.

CloudHeal should support:

1. Node registration and monitoring.
2. Heartbeat processing and node-health detection.
3. System and Docker runtime information collection.
4. Resource-aware workload scheduling.
5. Docker execution through Node Agents.
6. Persistent workload state and timestamped event history.
7. Container and node failure detection.
8. Safe, verified cross-node workload recovery.
9. Leases, placement generations, and agent-enforced fencing.
10. Bounded retries and recovery-storm protection.
11. Recovery concurrency and capacity controls.
12. A stable application URL across successful recovery.
13. Repeatable experiments and measured results.
14. AI-assisted diagnosis and constrained recovery planning.

The laptops do not need to remain online continuously. CloudHeal is a development and demonstration platform, not a production cloud service.

1.2 Intended Final Demonstration

The final demonstration should show:

1. Deploying an application through CloudHeal.
2. Identifying which laptop is executing it.
3. Observing workload and actual container state.
4. Introducing a controlled failure.
5. Detecting and classifying the failure.
6. Evaluating whether recovery is safe.
7. Selecting an eligible destination node.
8. Executing a replacement workload.
9. Verifying its actual runtime state and application health.
10. Maintaining access through a stable application URL.
11. Recording execution and recovery events.
12. Comparing recovery policies through repeated experiments.
13. Demonstrating AI-assisted diagnosis and constrained planning, if time permits.

The project’s contribution must be demonstrated through actual infrastructure behavior, recovery safety, and measured results—not merely a dashboard or chatbot.

⸻

2. Agreed Architecture

2.1 The Central Architecture Decision

CloudHeal will have two major parts:

A. Cloud infrastructure: The machines, Docker runtimes, containers, networking, and applications being managed.

B. Self-Healing Control System: The management intelligence that observes the infrastructure, detects failures, evaluates recovery options, and coordinates authorized actions.

The Self-Healing Control System will be logically separate from individual workloads. It will extend the existing Control Plane rather than replace it or require a complete rebuild.

It will contain two cooperating layers.

Layer 1 — Deterministic Self-Healing Engine

Responsible for safety-critical infrastructure behavior:

* Failure detection.
* Node-health state transitions.
* Recovery policies.
* Workload ownership and lease management.
* Placement generations and fencing.
* Recovery authorization.
* Destination selection and capacity checks.
* Recovery execution.
* Bounded retries and concurrency limits.
* Runtime and application-health verification.
* Persistent event recording.

These decisions must not depend on an LLM making a correct recommendation.

Layer 2 — AI-Assisted Intelligence

Responsible for assisting with decisions:

* Analyzing failure evidence.
* Suggesting likely causes.
* Summarizing relevant logs and event history.
* Recommending permitted recovery strategies.
* Proposing constrained recovery plans.
* Explaining why an action may be appropriate.
* Comparing observed outcomes with previous incidents.

AI may propose an action, but it must not directly authorize arbitrary infrastructure operations.

Mandatory safety rule

AI proposal → deterministic safety validation → authorized execution → runtime verification.

If the safety gate rejects a recommendation, the system must reject, defer, or escalate the action according to policy.

The infrastructure must continue operating when the AI model or external model API is unavailable. Deterministic recovery must remain functional without an LLM.

2.2 Target Architecture

                    USER / DEVELOPER
                           |
                           v
                CLOUDHEAL APPLICATION GATEWAY
                           |
                           v
             +--------------------------------+
             |    SELF-HEALING CONTROL SYSTEM |
             |                                |
             | Deterministic Engine           |
             | - Failure detection            |
             | - Recovery policies            |
             | - Lease and fencing checks     |
             | - Placement generations        |
             | - Recovery and verification    |
             |                                |
             | AI-Assisted Intelligence       |
             | - Diagnosis agent              |
             | - Recovery planning agent      |
             |                                |
             | Deterministic Safety Gate      |
             +---------------+----------------+
                             |
                             v
                    CONTROL PLANE API
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
          NODE AGENT: MAC         NODE AGENT: WINDOWS
                 |                       |
                 v                       v
            Docker Runtime          Docker Runtime
                 |                       |
                 v                       v
             Workloads               Workloads

This is the target architecture, not a claim that every component has been implemented.

The current Control Plane is the foundation. We should evolve the existing implementation incrementally.

2.3 Where Should the Self-Healing Code Live?

The recommendation is a separate Python package within the existing Control Plane package.

A possible future structure is:

control-plane/
└── src/
    └── cloudheal_control_plane/
        ├── main.py
        ├── api.py
        ├── database.py
        ├── registry.py
        ├── workloads/
        │   ├── models.py
        │   ├── registry.py
        │   ├── service.py
        │   ├── scheduler.py
        │   └── reconciler.py
        └── self_healing/
            ├── detector.py
            ├── recovery_engine.py
            ├── recovery_policy.py
            ├── lease_manager.py
            ├── diagnosis_agent.py
            ├── planning_agent.py
            └── safety_gate.py

This is a proposed organization only. Some responsibilities already exist under different names.

Do not create, move, or rename these files immediately. Inspect the actual repository and existing implementation before deciding where each responsibility belongs.

Component	Responsibility
Detector	Detect suspicious or unavailable nodes using defined policies
Recovery engine	Coordinate authorized recovery actions
Recovery policy	Enforce retries, limits, priorities, and permitted actions
Lease manager	Manage time-limited execution authority
Scheduler	Select a suitable destination using health and capacity
Reconciler	Compare desired state with observed state and correct discrepancies
Diagnosis agent	Analyze failure evidence and suggest likely causes
Planning agent	Propose constrained recovery strategies
Safety gate	Validate proposed actions against deterministic policies
Database/event store	Persist state transitions, decisions, and outcomes

2.4 Node Agents Versus AI Agents

These are different components.

Node Agent:

* Runs on each participating laptop.
* Registers with the Control Plane.
* Sends heartbeats.
* Reports system and Docker runtime information.
* Executes authorized local Docker operations.
* Reports actual container status.
* Will eventually enforce lease expiry and generation fencing.

AI Agent:

* Analyzes evidence.
* Helps diagnose failures.
* Recommends recovery strategies.
* Proposes constrained plans.
* Does not receive unrestricted shell access or direct unrestricted access to the Docker socket.

The AI agent does not need to run on every laptop.

2.5 Controller Availability Limitation

The Control Plane currently runs on the MacBook.

If the Mac becomes unavailable, the controller itself may also become unavailable. The current design does not establish controller high availability.

We should acknowledge this limitation in the project report rather than claim that CloudHeal can always recover from controller failure.

A separate management machine or replicated controller could be a future extension. It is not our immediate priority.

⸻

3. Repository and Development Environment

3.1 Repository

Local repository:

/Users/aniketsaini/Desktop/CloudHeal

Activate the environment:

cd ~/Desktop/CloudHeal
source .venv/bin/activate

Inspect the working tree:

git status
git diff
git diff --check

The project uses uv.

Development rules

* Inspect existing code before editing.
* Preserve all uncommitted changes.
* Do not reset or discard work to obtain a clean working tree.
* Make incremental changes.
* Reuse existing implementations.
* Run relevant tests after meaningful changes.
* Verify actual Docker state where appropriate.
* Distinguish implementation, automated testing, and real-environment verification.
* Update the repository context after verified milestones.
* Do not report a phase as complete merely because its tests pass.

3.2 Known Documentation

Previously identified project documentation includes:

* CloudHeal_CONTEXT.md
* docs/SPEC-001-cloudheal.md
* docs/current_progress.md
* docs/Implementation_plan_20_oct.md
* docs/cloudHeal_context_21_october.md

Inspect the current repository before assuming every file is present or unchanged.

Maintain two forms of context:

Repository context: Shared architecture, implementation status, protocols, safety requirements, and test evidence.

Personal development notes: Machine-specific IP addresses, local startup commands, and individual debugging notes.

Do not make shared repository documentation depend on a developer’s current local IP address.

⸻

4. Current Infrastructure

4.1 Control Plane

Package:

cloudheal-control-plane

Local address:

http://127.0.0.1:9000

Startup command:

uv run --package cloudheal-control-plane cloudheal-control-plane

Known endpoints:

Endpoint	Purpose
GET /health	Check Control Plane availability
POST /nodes/register	Register a node
GET /nodes	List registered nodes
GET /nodes/{node_id}	Retrieve node information
POST /nodes/{node_id}/heartbeat	Receive heartbeat information
POST /workloads	Create a workload
GET /workloads	List workloads
GET /workloads/{workload_id}	Retrieve a workload
POST /workloads/{workload_id}/schedule	Request workload scheduling

Inspect the current API before assuming route behavior is unchanged. The workload event endpoint was previously found to return 404; do not assume it has since been implemented.

4.2 Node Agent

Package:

cloudheal-node-agent

Previously configured port:

8000

Startup command:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously documented persistent identity file:

~/.cloudheal/node_id

Previously configured heartbeat interval: approximately 10 seconds.

The Node Agent already supports registration, heartbeats, system/runtime reporting, Docker operations, and container status queries.

Lease enforcement and generation-based fencing are not yet established as complete.

4.3 Mac Development Node

Previously recorded values:

Property	Recorded value
Node ID	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Hostname	Anikets-MacBook-Air.local
Tailscale IP	100.90.104.13
Operating system	macOS
Architecture	ARM64 / aarch64
Physical memory	8 GiB
Docker Desktop version	29.8.2

These values are historical observations and must be checked before capacity-sensitive experiments.

The Control Plane and Mac Node Agent were recently observed to be running. The Mac node was registered and reporting a healthy state. Docker runtime information was available in the latest observed node response.

Previously reported Docker runtime memory was approximately 4.1 billion bytes. This is runtime/VM memory information, not necessarily the Mac’s physical RAM.

4.4 Windows Node

The Windows laptop remains the immediate integration target.

A previously reported Windows Tailscale IP was:

100.127.235.82

This is historical and must be rechecked on Windows.

Before making application changes, verify:

* Tailscale connectivity.
* Current Windows and Mac Tailscale IP addresses.
* Docker Desktop availability.
* Successful docker info.
* Windows-to-Mac connectivity on port 9000.
* Control Plane-to-Agent communication.
* Registration and heartbeat delivery.

Reuse the existing Node Agent unless testing identifies a specific Windows compatibility issue.

⸻

5. Workload Management and Execution

5.1 Desired and Actual States

Existing desired states:

* RUNNING
* STOPPED

Existing actual states:

* PENDING
* SCHEDULED
* RUNNING
* FAILED
* STOPPED

Desired state represents what the system should do. Actual state represents what the Control Plane believes has happened.

Example:

desired_state = RUNNING
actual_state  = FAILED

The workload should be running, but execution has failed.

Recovery must check desired state. A workload whose desired state is STOPPED must not be automatically restarted.

5.2 Execution Lifecycle

The intended lifecycle is:

PENDING → SCHEDULED → RUNNING
                     ↘ FAILED

A successful scheduling decision is not proof of successful execution.

The Control Plane must validate the result returned by the Node Agent.

An HTTP timeout is also not proof that execution failed. A request may have started a container even if the response never reached the Control Plane.

Future generation-aware execution and reconciliation must account for uncertain outcomes.

5.3 Remote Execution

The intended execution flow is:

Control Plane
    → Selected Node Agent
        → Local Docker Runtime
            → Container
        ← Actual execution result
    ← Control Plane updates state and events

The Control Plane must communicate with the remote Node Agent rather than assume it can execute Docker commands directly on another laptop.

The database state must be checked against actual container state.

⸻

6. Current Implementation Status

This section distinguishes previously implemented behavior from incomplete or unverified requirements.

6.1 Implemented Foundation

Previously implemented and tested:

* FastAPI Control Plane.
* Node registration and lookup.
* Heartbeat processing.
* System information reporting.
* Docker runtime information reporting.
* Workload creation and retrieval.
* Scheduler-to-Agent communication.
* Docker execution through the Node Agent.
* Container status queries.
* Periodic reconciliation.
* Basic stopped/missing-container recovery.

6.2 SQLite Persistence and Event History

Recent work introduced:

* A database module.
* SQLite schema for nodes, workloads, and events.
* Workload persistence through the existing workload registry.
* Persistence of workload state changes associated with scheduling and execution.
* WAL and busy-timeout configuration in the existing implementation.
* Timestamped execution-event recording.
* Persistence and event-related tests.

The implementation remains partially verified.

Required follow-up:

1. Verify complete node lifecycle persistence.
2. Verify workload state through creation, scheduling, execution, and recovery.
3. Verify restoration after a Control Plane restart.
4. Record all important scheduling, health, and recovery transitions.
5. Ensure related state changes and events are transactionally consistent.
6. Persist placement generations when implemented.
7. Discover and safely adopt identifiable containers at startup.
8. Verify that restart reconciliation does not blindly create replacements.

Previously observed event types include:

* EXECUTION_SUCCEEDED
* EXECUTION_FAILED

The exact current event coverage must be checked in the implementation.

The event history ultimately needs to cover workload creation, scheduling decisions, node-state transitions, failure detection, recovery attempts, retries, execution results, and recovery verification.

A database schema existing does not prove that the full lifecycle is persisted correctly.

6.3 Scheduler and Execution Results

The scheduler has progressed beyond a simple first-healthy-node approach.

It considers node suitability, runtime information, and reported resource capacity. It coordinates execution through Node Agents.

Recent tests covered scheduling behavior, execution outcomes, and failure cases, including missing execution status.

However, resource assumptions must be verified against live Docker runtime information on both macOS and Windows.

6.4 Reconciliation and Basic Recovery

The reconciler periodically compares desired workload state with observed execution state. Its previously configured interval is approximately 10 seconds.

Previously demonstrated behavior includes:

1. A workload was running through CloudHeal.
2. Its container was deliberately stopped or removed.
3. Reconciliation detected the stopped or missing container.
4. CloudHeal initiated recovery.
5. A replacement container was created.
6. Docker independently confirmed that the replacement was running.
7. The workload returned to RUNNING.

A previously recorded recovery test used workload ID:

1b5b2f07-169a-47c8-a6c0-b1a0026f821e

The recorded replacement start time was:

2026-10-19T19:11:42.747967761Z

The replacement reported RestartCount=0 in the recorded inspection.

This demonstrates basic recovery from a stopped or missing container. It does not establish safe recovery after an entire laptop becomes unreachable.

6.5 Latest Recorded Test Result

On 21 October 2026, this command passed:

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Recorded output:

23 passed in 0.33s

This is the latest recorded full Control Plane test result, not a fresh run on 22 October.

The Node Agent previously had a recorded result of 8 passing tests. An older combined run reported 21 Control Plane tests and 8 Node Agent tests. Those are historical results and should not be described as current test results.

6.6 Previously Verified Workload

A workload named event-test was successfully executed through the Mac Node Agent.

Property	Recorded value
Workload ID	ff02cc16-e20b-43a6-a41c-62fc996dd3b9
Image	nginx:latest
Desired state	RUNNING
Actual state	RUNNING
Assigned node	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Recorded update time	2026-10-21T15:43:14.019430Z

This verifies successful Mac-hosted execution at the recorded time. It does not establish Windows execution or cross-node recovery.

6.7 Known Unfinished Areas

The following are not yet established as complete:

* Complete node and workload persistence.
* Restart restoration and safe container adoption.
* Complete timestamped event history.
* Atomic placement and event updates.
* Persistent placement generations.
* HEALTHY → SUSPECT → UNAVAILABLE failure detection.
* Lease grants, renewals, and expiry enforcement.
* Agent-enforced fencing.
* Safe cross-node failover.
* Windows Node Agent integration.
* Real network-partition testing.
* Duplicate-execution overlap measurement.
* Application-level health checks.
* Bounded retry and crash-loop protection.
* Recovery concurrency controls.
* Stable application gateway.
* Repeatable experiment runner.
* Comparative evaluation results.
* AI-assisted diagnosis and recovery planning.

⸻

7. Immediate Priority: Connect Windows

Do not jump directly into a large failover rewrite. First establish actual distributed execution on two real laptops.

The Windows integration is a separate milestone, but it starts now because it is an important networking and platform risk.

Step 1 — Check the Mac

From the Mac:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status

Preserve all uncommitted work.

If the Control Plane is not running, start it:

uv run --package cloudheal-control-plane cloudheal-control-plane

In another terminal, start the Mac Node Agent only if necessary:

uv run --package cloudheal-node-agent cloudheal-node-agent

Verify:

curl -s http://127.0.0.1:9000/health
curl -s http://127.0.0.1:9000/nodes

Do not launch duplicate service processes if they are already running.

Step 2 — Check Windows

Open PowerShell on the Windows laptop and run:

tailscale status
tailscale ip -4
docker info

These checks establish the current network address and whether Docker Desktop is available.

Step 3 — Test Windows-to-Mac Connectivity

Using the latest observed Mac Tailscale IP, run:

Test-NetConnection 100.90.104.13 -Port 9000

Expected result:

TcpTestSucceeded : True

Use the verified current Mac IP if it differs.

If connectivity fails, investigate:

* Whether the Control Plane is listening on an interface reachable through Tailscale.
* macOS firewall behavior.
* Tailscale connectivity and ACLs.
* Whether the IP address is current.
* Whether the service is actually listening on port 9000.

Do not change application code before identifying the cause of a network failure.

Step 4 — Configure and Start the Windows Node Agent

Inspect the existing agent configuration and startup behavior first.

Configure the Windows agent to reach the Control Plane at:

CONTROL_PLANE_URL=http://100.90.104.13:9000

Use the verified current Mac Tailscale address.

Reuse the existing registration, heartbeat, resource reporting, Docker execution, and status-reporting code.

Make platform-specific changes only when testing demonstrates that they are necessary.

Step 5 — Verify Registration and Heartbeats

On the Mac:

curl -s http://127.0.0.1:9000/nodes

Confirm:

* The Mac node is present.
* The Windows node is present.
* The Windows node has a stable identity.
* Heartbeat timestamps update.
* The Windows operating system is reported correctly.
* Docker runtime information is available and accurate.

If registration fails, inspect the agent logs and network connectivity before modifying the architecture.

Step 6 — Verify Real Windows Execution

Once Windows is registered and reporting healthy runtime information:

1. Create a test workload.
2. Confirm that the scheduler selects Windows.
3. Confirm that the Control Plane contacts the Windows Node Agent.
4. Confirm that the agent starts the container locally.
5. Check the container using Windows Docker.
6. Confirm that the agent reports the actual execution result.
7. Confirm that the Control Plane records the correct workload state and node assignment.
8. Verify remote container-status queries.

On Windows:

docker ps
docker ps -a

A database state of RUNNING is not sufficient evidence on its own.

Step 7 — Attempt Controlled Cross-Node Recovery

Only after Windows execution works:

1. Start a test workload on one laptop.
2. Verify its actual container state.
3. Introduce a controlled failure.
4. Observe the detection and reconciliation behavior.
5. Determine whether the original container may still be executing.
6. Verify destination selection.
7. Verify replacement execution on the other laptop.
8. Record the outcome and any uncertainty.

Until lease enforcement and generation fencing have been implemented and tested, treat this as a controlled recovery experiment—not proof of safe failover under arbitrary network partitions.

⸻

8. Revised Implementation Roadmap

Phase 1 — Persistence and Event History

Status: Partially implemented; verification ongoing.

Existing work includes SQLite schema and persistence logic, execution-event recording, and related tests.

Remaining work:

* Verify node registration and heartbeat persistence.
* Verify workload state through creation, scheduling, execution, and recovery.
* Record all significant scheduling and recovery transitions.
* Persist placement generations when introduced.
* Verify WAL mode and controlled state-changing writes.
* Use transactions for related state changes and events.
* Make generation allocation atomic with placement.
* Restore persisted records after restart.
* Discover and safely adopt identifiable running containers.

Completion test: Restart the Control Plane and verify that node/workload state and event history survive, existing containers are identified correctly, and the system does not blindly create replacements.

Do not mark Phase 1 complete until this behavior has been demonstrated.

Phase 2 — Node Health and Failure Detection

Status: Not implemented to the full specification.

Implement the state machine:

HEALTHY → SUSPECT → UNAVAILABLE

Definitions:

* HEALTHY: Recent communication and no detected failure.
* SUSPECT: Communication or heartbeat information has become stale.
* UNAVAILABLE: The configured failure-detection policy has made the node ineligible for new placements and eligible for recovery evaluation.

A node becoming unavailable does not prove that its containers have stopped.

Requirements:

* Heartbeat timestamps and configurable timeouts.
* Timestamped node-state transition events.
* Tests for delayed heartbeats and agent termination.
* Tests for temporary network interruption and recovery.
* Distinction between a stopped container and an unreachable node.
* No unsafe failover triggered solely by an HTTP timeout.

Completion test: Demonstrate the expected state transitions under controlled failures and verify their corresponding events.

Phase 3 — Leases, Generations, and Fencing

Status: Not implemented as an integrated safety protocol.

Implement leases, generations, and failover as one coordinated milestone.

Leases

The Control Plane grants and renews time-limited execution authority.

Requirements:

* Explicit lease duration and safety margin.
* A defined, validated renewal protocol.
* Agent-enforced lease expiry.
* Safe handling of delayed renewal responses.
* Monotonic-clock-based expiry checks.
* Revalidation after long pauses or laptop sleep.
* Self-fencing after execution authority expires.
* Safe handling of uncertainty about whether a previous execution remains active.

Lease expiry alone does not prove that an existing container has stopped.

Placement generations

Each placement receives a monotonically increasing generation.

Example:

Generation 1 → Node A
Generation 2 → Node B
Generation 3 → Node C

Requirements:

* Persist generations.
* Allocate them atomically.
* Label containers with workload ID and generation.
* Include generation information in execution and recovery requests.
* Reject stale commands at the Node Agent.
* Prevent older placements from overriding newer placements.
* Handle repeated requests safely.
* Validate authority before destructive operations.

Storing a generation in SQLite or in container labels is not sufficient. The Node Agent must enforce the relevant rules.

Failover

When a node becomes unavailable:

1. Identify affected workloads.
2. Check desired state.
3. Evaluate recovery safety.
4. Select an eligible destination.
5. Allocate a higher generation.
6. Execute the replacement.
7. Verify container state and application health.
8. Persist the result.
9. Handle uncertain execution outcomes safely.
10. Record failures, retries, and blocked decisions.

Completion test: Demonstrate lease enforcement, stale-command rejection, generation protection, and cross-node recovery through controlled failure and network-partition tests.

Do not claim zero duplicate execution without evidence from the actual fencing implementation.

Phase 4 — Second Real Laptop Integration

Status: Pending verification; immediate priority.

Verify:

* Tailscale connectivity.
* Node registration and heartbeat delivery.
* Control Plane-to-Agent HTTP connectivity.
* Windows Docker execution.
* Remote container status.
* Runtime resource reporting.
* Workload execution on both laptops.
* Controlled cross-node recovery.

This phase starts immediately. It does not replace the requirement to complete persistence and recovery safety.

Phase 5 — Recovery Controls

Status: Basic recovery exists; remaining controls need verification and implementation.

Implement:

* Bounded retries.
* Exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling.
* Clear failure and escalation states.

The system must prevent endless restarts and recovery storms.

Phase 6 — Experimental Baselines

Status: Not implemented.

Support configurable policies such as:

1. No automated recovery.
2. Basic Docker restart behavior.
3. Fixed-timeout detection.
4. CloudHeal deterministic recovery.
5. Controlled immediate-rescheduling baseline.
6. Fencing-disabled baseline in isolated tests.
7. Unlimited-retry baseline in isolated tests.

Unsafe policies must be restricted to disposable workloads and controlled environments.

Build an experiment runner that repeats scenarios and records actual outcomes.

Phase 7 — Stable Application Gateway

Status: Not implemented.

Provide a stable URL for the demonstration application.

Test:

* Routing before failure.
* Routing during recovery.
* Routing after recovery.
* Unhealthy applications.
* Stale destination information.
* Active connection behavior during failover.

A stable URL does not guarantee preservation of active TCP connections, sessions, or application state.

Phase 8 — Evaluation

Status: Not implemented.

Measure:

Metric	Purpose
Detection time	Time required to identify a failure
Recovery time	Time required to restore the workload
Recovery success rate	Fraction of successful recoveries
False-positive rate	Incorrect failure detections
Unnecessary migrations	Workloads moved without sufficient justification
Duplicate execution	Whether multiple copies execute concurrently
Overlap duration	Duration of duplicate execution
Retry count	Repeated attempts caused by failures
Cascade failures	Whether recovery overloads other nodes
Application downtime	Time the application is unavailable
Unsafe actions blocked	Actions rejected by safety policies
AI diagnosis accuracy	Agreement between diagnosis and observed evidence
Added latency	Extra delay from AI assistance
API cost	Cost of AI-assisted decisions

Aim for approximately 20 repetitions per scenario when time and hardware permit.

Report measured results, including failed and inconclusive trials. Distinguish actual measurements from estimates.

Phase 9 — AI-Assisted Diagnosis and Planning

Status: Deferred until deterministic recovery is reliable.

The diagnosis component may inspect:

* Container exit codes.
* Container logs.
* Heartbeat history.
* Resource measurements.
* Application-health checks.
* Scheduling decisions.
* Recovery history.

The planning component may recommend constrained actions such as restarting a stopped container, moving a workload, waiting for a temporary problem to clear, or escalating a repeated failure.

A deterministic safety gate must validate proposed actions against:

* Node eligibility.
* Resource constraints.
* Retry limits.
* Workload requirements.
* Lease and generation rules.
* Recovery safety.
* Required approvals.

The model must not receive unrestricted shell access or direct unrestricted Docker-socket access.

Record:

1. Evidence available.
2. Diagnosis or recommendation.
3. Policy and safety decision.
4. Authorized action.
5. Actual execution result.
6. Observed outcome.

The infrastructure must continue functioning when the model API is unavailable.

A dashboard can be developed alongside later phases if useful, but it must not delay recovery milestones.

⸻

9. Resource-Scheduling Requirements

CloudHeal must not assume that host physical RAM equals memory available to containers.

Docker Desktop runs containers inside a Linux VM with its own resource configuration.

Distinguish:

1. Host physical memory.
2. Runtime/VM memory capacity.
3. Runtime memory availability, where reliably measurable.
4. CloudHeal’s allocatable workload capacity.
5. Existing CloudHeal workload allocations.
6. Remaining schedulable capacity.

Inspect Docker runtime information on both macOS and Windows.

The scheduler must not interpret missing or stale resource reports as unlimited capacity.

Recovery decisions must preserve sufficient capacity to avoid destabilizing the remaining nodes.

⸻

10. Immediate Development Commands

Start the Control Plane

cd ~/Desktop/CloudHeal
source .venv/bin/activate
uv run --package cloudheal-control-plane cloudheal-control-plane

Start the Mac Node Agent

cd ~/Desktop/CloudHeal
source .venv/bin/activate
uv run --package cloudheal-node-agent cloudheal-node-agent

Avoid launching duplicate processes if the services are already running.

Check Control Plane Health

curl -s http://127.0.0.1:9000/health

List Nodes

curl -s http://127.0.0.1:9000/nodes

List Workloads

curl -s http://127.0.0.1:9000/workloads

Run Control Plane Tests

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Latest recorded result:

23 passed in 0.33s

This result is from 21 October 2026.

Inspect Docker on the Mac

docker ps
docker ps -a

Check Windows Tailscale and Docker

tailscale status
tailscale ip -4
docker info
docker ps

Test Windows-to-Mac Connectivity

Test-NetConnection 100.90.104.13 -Port 9000

Use the verified current Mac Tailscale IP if it differs.

⸻

11. Minimum Final Scope

The minimum defensible final implementation must demonstrate:

1. Distributed workload execution across at least two real laptops.
2. Persistent workload state and timestamped event history.
3. Tested node-health and suspect/unavailable detection.
4. Leases and agent-enforced fencing integrated with generation-based placement.
5. Safe, verified cross-node workload recovery.
6. Bounded retries and crash-loop protection.
7. Recovery concurrency and capacity controls.
8. A stable application URL across successful recovery.
9. Configurable baseline policies and a repeatable experiment runner.
10. Measured results across multiple failure scenarios.

AI diagnosis, constrained AI planning, adaptive failure detection, image-aware scheduling, and an advanced dashboard are optional extensions if time permits.

⸻

12. Current Development Position and Handoff

As of 22 October 2026:

* The Control Plane and Node Agent foundations exist.
* Workload scheduling and Docker execution have been implemented.
* Basic stopped/missing-container recovery has been demonstrated.
* SQLite persistence and execution-event recording have been introduced.
* The latest recorded Control Plane test run passed 23 tests on 21 October.
* A Mac-hosted nginx:latest workload was verified as running at the recorded time.
* The Mac Control Plane and Node Agent were recently observed to be available, with Docker runtime reporting available.
* Complete persistence, startup adoption, node-state transitions, leases, fencing, safe cross-node failover, the stable gateway, and experimental evaluation remain unfinished or unverified.
* The Windows laptop has not yet been verified as a registered and executing CloudHeal node.
* The Self-Healing Control System architecture is agreed, but its proposed package and AI modules have not yet been implemented.

Next session: Start here

Immediate task: Connect the Windows laptop as the second real node.

1. Inspect the Git working tree and preserve uncommitted changes.
2. Verify the Mac Control Plane and Node Agent.
3. Check the Windows Tailscale IP and Docker installation.
4. Test Windows-to-Mac connectivity.
5. Configure and start the existing Windows Node Agent.
6. Verify registration and heartbeats.
7. Execute a test workload on Windows.
8. Verify actual Docker state and Control Plane workload state.
9. Attempt controlled cross-node recovery only after both nodes can execute workloads.
10. Continue persistence and event-history verification.
11. Implement the node-health state machine.
12. Implement leases, generations, and fencing as an integrated safety protocol.
13. Strengthen recovery controls and perform repeatable experiments.
14. Introduce AI diagnosis and planning only after deterministic recovery is reliable.

Guiding principle: Establish real multi-node execution first, persist state and events, define and enforce the recovery protocol, test actual failures, measure the results, and then introduce AI where it genuinely improves diagnosis and planning.

Documentation note: This updated context has been written in this chat and incorporated into the ongoing project context. The local CloudHeal_CONTEXT.md, implementation plan, and source files have not been changed by this response. Repository files should be updated separately, preserving existing changes and recording only implementation and test evidence that has actually been verified.