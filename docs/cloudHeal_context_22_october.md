CloudHeal — Complete Project Context & Revised Implementation Roadmap

Last updated: 22 October 2026
Project stage: Core workload execution and basic recovery implemented; SQLite persistence and event history partially implemented; second real laptop integration pending.
Immediate priority: Connect and verify the Windows laptop as the second real compute node.
Latest recorded automated test result: 23 Control Plane tests passed.
Development environment: MacBook Air running macOS, Python, FastAPI, uv, Docker Desktop, and Tailscale.

⸻

1. Project Overview

1.1 What Are We Building?

CloudHeal is a student engineering project that aims to build a small distributed cloud platform using our team’s laptops as compute nodes.

The intended environment consists of four laptops:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.
* Tailscale for private networking.
* A Python/FastAPI Control Plane.
* A Node Agent on each participating laptop.
* Docker for container execution.
* SQLite for persistent state.
* A logically separate Self-Healing Control System.
* A future AI-assisted intelligence layer for diagnosis and recovery planning.

The laptops do not need to remain online continuously. CloudHeal is a development and demonstration platform rather than a production cloud service.

1.2 Core Project Objective

CloudHeal should demonstrate that distributed workloads can be executed, monitored, recovered, and evaluated across multiple real computers.

Its primary contribution should be measurable self-healing behavior, including:

1. Detecting and classifying failures.
2. Determining whether recovery is safe.
3. Selecting an eligible destination node.
4. Executing a replacement workload.
5. Verifying the actual execution and health state.
6. Preventing stale recovery commands from overriding newer decisions.
7. Recording a complete, persistent event history.
8. Measuring recovery performance and failure behavior.
9. Providing a stable application URL across successful recovery.
10. Supporting AI-assisted diagnosis without making the infrastructure dependent on AI.

A dashboard or chatbot alone is not sufficient to demonstrate the project’s contribution.

1.3 Intended Final Demonstration

The final demonstration should show:

1. Deploying an application through CloudHeal.
2. Identifying which laptop is executing it.
3. Observing workload and container states.
4. Introducing a controlled failure.
5. Detecting and classifying the failure.
6. Evaluating whether recovery is safe.
7. Selecting a suitable destination.
8. Executing a replacement workload.
9. Verifying the replacement’s actual state and application health.
10. Maintaining application access through a stable URL.
11. Recording the execution and recovery history.
12. Comparing recovery policies through repeated experiments.
13. Demonstrating AI-assisted diagnosis and constrained recovery planning if time permits.

⸻

2. Agreed Architecture

2.1 Overall Design

CloudHeal will retain its existing distributed execution foundation and introduce a logically separate Self-Healing Control System.

The system will have two distinct responsibilities:

A. Deterministic self-healing engine

Responsible for:

* Failure detection and classification.
* Node eligibility.
* Workload desired-state validation.
* Resource and capacity checks.
* Recovery policy enforcement.
* Leases and placement generations.
* Agent-enforced fencing.
* Recovery execution.
* Execution and health verification.
* Retry limits and concurrency controls.
* Persistent decisions and event history.

B. AI-assisted intelligence layer

Responsible for:

* Analyzing failure evidence.
* Diagnosing likely causes.
* Summarizing logs and execution history.
* Recommending constrained recovery plans.
* Explaining why a recovery might have failed.
* Comparing possible actions and their risks.

The AI layer may recommend actions, but it must not authorize or execute unrestricted infrastructure operations directly.

Every AI recommendation must pass through the deterministic safety engine.

The infrastructure must continue to operate when the model API is unavailable.

2.2 Control Plane

Package:

cloudheal-control-plane

The existing Control Plane is a FastAPI service responsible for:

* Node registration and lookup.
* Heartbeat processing.
* Node and workload records.
* Scheduling decisions.
* Remote Node Agent communication.
* Docker execution coordination.
* Workload state management.
* Periodic reconciliation.
* Execution-result recording.
* Persistent state and events.

The Self-Healing Control System will be introduced alongside this functionality rather than replacing the existing platform.

The Control Plane currently runs on the MacBook.

Local address:

http://127.0.0.1:9000

Remote agents must be able to reach it through the Mac’s Tailscale address.

2.3 Node Agent

Package:

cloudheal-node-agent

The Node Agent runs on every participating laptop.

Existing responsibilities include:

* Maintaining a persistent node identity.
* Registering with the Control Plane.
* Sending heartbeats.
* Reporting system information.
* Reporting Docker runtime information.
* Executing permitted Docker operations.
* Reporting container status.

Future responsibilities include:

* Validating execution authority.
* Enforcing lease expiry.
* Enforcing placement generations.
* Rejecting stale commands.
* Self-fencing when execution authority expires.
* Validating destructive operations against current authority.

Lease enforcement and generation-based fencing are not yet established as complete.

2.4 Docker Runtime

Each laptop uses Docker Desktop to execute workload containers.

The execution flow is:

Control Plane → selected Node Agent → local Docker runtime → execution result → Control Plane.

The Control Plane must not assume that a remote container is running merely because an HTTP request was sent successfully or a scheduling decision was made.

Actual container status must be checked through the Node Agent and, when necessary, independently through Docker.

2.5 SQLite Persistence

SQLite is being integrated into the Control Plane.

The implementation includes:

* Database schema.
* Node and workload persistence logic.
* An events table.
* Execution-event recording.
* WAL configuration and busy-timeout handling in the existing database implementation.

Persistence is partially implemented, not fully verified.

Remaining work includes:

* Verifying the complete node lifecycle.
* Verifying persistence across Control Plane restarts.
* Persisting placement generations.
* Recording the full scheduling and recovery lifecycle.
* Making related state changes and events atomic.
* Discovering and safely adopting existing containers after restart.

2.6 Scheduler

The scheduler has progressed beyond a simple first-healthy-node selection strategy.

Existing behavior considers node suitability, reported resource information, and available capacity. It coordinates execution through Node Agents and evaluates returned execution results.

The scheduler must distinguish:

* A scheduling decision.
* An execution request.
* Confirmed container execution.
* Verified application health.

These are separate stages.

2.7 Reconciler

The reconciler periodically compares desired workload state with observed execution state.

Previously configured interval: approximately 10 seconds.

Documented behavior includes:

* Processing pending workloads.
* Retrying eligible failed workloads.
* Querying container status.
* Detecting stopped or missing containers.
* Updating workload states.
* Initiating replacement execution.
* Verifying execution results.

A node communication timeout does not prove that the node or its containers have stopped.

The reconciler must eventually distinguish container failure from node unavailability and uncertain execution outcomes.

2.8 Future Application Gateway

A future gateway will expose a stable application URL and route requests to the workload’s current location.

Routing must remain separate from scheduling and recovery.

A stable URL does not guarantee uninterrupted TCP connections, session continuity, or application-state preservation.

2.9 Architecture Principle

The implementation order is:

Real multi-node execution → reliable persistence → deterministic failure detection → leases and fencing → verified recovery → measured evaluation → AI-assisted diagnosis and planning.

Do not introduce the AI layer as a substitute for deterministic infrastructure behavior.

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

3.2 Known Repository Structure

The previously documented structure is:

CloudHeal/
├── CloudHeal_CONTEXT.md
├── README.md
├── pyproject.toml
├── uv.lock
├── docs/
│   ├── SPEC-001-cloudheal.md
│   └── current_progress.md
├── control-plane/
│   ├── src/
│   │   └── cloudheal_control_plane/
│   │       ├── api.py
│   │       ├── main.py
│   │       ├── registry.py
│   │       ├── database.py
│   │       └── workloads/
│   │           ├── models.py
│   │           ├── registry.py
│   │           ├── service.py
│   │           ├── scheduler.py
│   │           └── reconciler.py
│   └── tests/
└── infrastructure/
    └── node-agent/
        ├── pyproject.toml
        └── src/
            └── cloudheal_node_agent/
                ├── api.py
                ├── identity.py
                ├── main.py
                ├── models.py
                ├── network.py
                ├── registration.py
                ├── heartbeat.py
                ├── system.py
                └── runtime.py

Additional documented test files include:

* control-plane/tests/test_database_events.py
* control-plane/tests/test_scheduler.py
* control-plane/tests/test_reconciler.py

This is a known structure, not a guarantee that every path remains unchanged. Inspect the actual repository before editing or creating files.

3.3 Development Rules

* Inspect existing code before editing.
* Preserve working code and uncommitted changes.
* Make incremental changes.
* Do not rebuild completed components unnecessarily.
* Run relevant tests after meaningful changes.
* Verify actual Docker behavior where appropriate.
* Distinguish implementation, automated testing, and real-world verification.
* Do not mark a feature complete solely because tests pass.
* Do not claim a phase is complete without meeting its acceptance criteria.
* Update the project context after verified milestones.

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

Inspect the current API implementation before assuming that endpoint behavior has not changed.

4.2 Node Agent

Package:

cloudheal-node-agent

Previously configured port: 8000.

Startup command:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously documented identity file:

~/.cloudheal/node_id

Previously configured heartbeat interval: 10 seconds.

The Node Agent provides registration, heartbeats, resource reporting, Docker execution, and container status queries.

4.3 Mac Development Node

Previously recorded values:

Property	Historical value
Node ID	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Hostname	Anikets-MacBook-Air.local
Tailscale IP	100.90.104.13
Operating system	macOS
Architecture	ARM64
Physical CPU cores	8
Logical CPU cores	8
Physical memory	8 GiB
Docker version	29.8.2

Previously recorded LAN addresses included 192.168.1.124 and 192.168.0.7.

These values are historical. Query the live node and Docker runtime before capacity-sensitive experiments.

4.4 Current Mac Status

The latest recorded context indicates that:

* The Mac Control Plane is running.
* The Mac Node Agent is running.
* The Mac node is healthy.
* Docker is available.
* The recorded runtime memory was approximately 3.82 GiB.

The actual runtime values must be queried again when needed.

Do not launch duplicate service processes if the existing ones are healthy.

4.5 Windows Node

The Windows laptop is the immediate integration target.

A previously reported Windows Tailscale IP was:

100.127.235.82

This address is historical and must be checked on Windows.

The integration is not complete until the Windows node has registered, sent heartbeats, executed a workload, and returned correct status information.

⸻

5. Workload State and Execution

5.1 Desired States

The existing workload model uses:

* RUNNING
* STOPPED

Desired state represents what the system should do.

Recovery must respect desired state. A workload whose desired state is STOPPED must not be restarted automatically.

5.2 Actual States

The existing model uses:

* PENDING
* SCHEDULED
* RUNNING
* FAILED
* STOPPED

Actual state represents what the Control Plane believes has happened.

For example:

desired_state = RUNNING
actual_state  = FAILED

This means the workload should be running, but execution has failed or is considered unsuccessful.

5.3 Execution Lifecycle

The intended lifecycle is:

PENDING → SCHEDULED → RUNNING
                     ↘ FAILED

A successful scheduling decision is not proof of successful execution.

The Control Plane must validate the execution result.

Timeouts and uncertain HTTP responses require special treatment because the remote agent may have started a container even if the response never reached the Control Plane.

Future generation-aware execution and reconciliation must handle such uncertainty safely.

⸻

6. Verified Work Completed

This section distinguishes recorded implementation from incomplete verification.

6.1 Core Foundation

Previously implemented and demonstrated:

* FastAPI Control Plane.
* Node registration and lookup.
* Heartbeat processing.
* System and Docker runtime information reporting.
* Workload creation and retrieval.
* Scheduler-to-Agent communication.
* Docker container execution through Node Agents.
* Container status queries.
* Periodic reconciliation.
* Basic recovery from stopped or missing containers.

6.2 Persistence and Event Recording

Recent work introduced:

* A SQLite database module.
* Database schema for nodes, workloads, and events.
* Workload persistence through the existing registry.
* Persistence of workload state changes associated with scheduling and execution.
* WAL configuration and busy-timeout handling.
* Timestamped execution-event recording.
* Persistence- and event-related tests.

Previously verified execution-event types include:

* EXECUTION_SUCCEEDED
* EXECUTION_FAILED

The exact current event coverage must be established by inspecting the implementation.

The presence of a database table does not prove that every state transition is persisted correctly.

Outstanding verification:

1. Node registration persistence.
2. Heartbeat persistence and timestamp updates.
3. Workload lifecycle persistence.
4. Complete event coverage.
5. Consistency between related state changes and events.
6. Restart restoration.
7. Startup discovery and safe adoption of existing containers.
8. Persistent placement generations when implemented.

6.3 Scheduler and Execution Results

The scheduler has been updated and tested for execution outcomes.

Recorded behavior includes:

* Sending execution requests to selected Node Agents.
* Receiving execution results.
* Recording success or failure.
* Treating a missing container status as execution failure.
* Considering reported resources during placement decisions.

Resource-related behavior still needs verification against the actual Docker runtime on macOS and Windows.

6.4 Basic Recovery

Previously demonstrated:

1. A workload was started through CloudHeal.
2. Its container was deliberately stopped or removed.
3. The reconciliation path detected the stopped or missing container.
4. CloudHeal initiated recovery.
5. A replacement container was created.
6. Docker independently confirmed the replacement was running.
7. The workload returned to RUNNING.

One recorded test used workload ID:

1b5b2f07-169a-47c8-a6c0-b1a0026f821e

The recorded replacement start time was:

2026-10-19T19:11:42.747967761Z

The replacement reported RestartCount=0.

This demonstrates basic stopped/missing-container recovery. It does not establish safe failover when an entire laptop becomes unreachable.

6.5 Latest Recorded Test Result

Command:

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Recorded result on 21 October 2026:

23 passed in 0.33s

This is the latest recorded complete Control Plane test result, not a newly executed test run on 22 October.

The Node Agent’s earlier recorded result was 8 passing tests. An older combined run reported 21 Control Plane tests and 8 Node Agent tests.

These historical results must not be presented as current test results without rerunning the suites.

6.6 Recorded Workload Execution

A workload named event-test was successfully executed through the Mac Node Agent.

Property	Recorded value
Workload ID	ff02cc16-e20b-43a6-a41c-62fc996dd3b9
Image	nginx:latest
Desired state	RUNNING
Actual state	RUNNING
Assigned node	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Recorded update time	2026-10-21T15:43:14.019430Z

This verifies Mac-hosted execution at the recorded time. It does not establish Windows execution or cross-node recovery.

6.7 Current Limitations

The following remain incomplete or unverified:

* Complete persistence across the node and workload lifecycles.
* Startup restoration and safe adoption of existing containers.
* Full event history.
* Atomic placement and event transactions.
* Persistent placement generations.
* HEALTHY → SUSPECT → UNAVAILABLE node state machine.
* Lease grants, renewal, and expiry enforcement.
* Agent-enforced fencing.
* Safe cross-node failover.
* Windows Node Agent integration.
* Real network-partition testing.
* Duplicate-execution overlap measurement.
* Application-level health checks.
* Crash-loop detection and bounded retries.
* Recovery concurrency controls.
* Stable application gateway.
* Repeatable experiment runner.
* AI-assisted diagnosis and recovery planning.
* Final evaluation and demonstration.

⸻

7. Immediate Priority: Connect the Windows Laptop

Do this before implementing additional recovery mechanisms.

The goal is to add the Windows laptop as the second real compute node using the existing Node Agent.

Step 1 — Inspect the Mac Setup

On the Mac:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status

Inspect uncommitted changes before editing.

Check the Control Plane:

curl -s http://127.0.0.1:9000/health

List registered nodes:

curl -s http://127.0.0.1:9000/nodes

Confirm that the Mac node is healthy and its heartbeat is current.

Verify that the Mac Node Agent is running. Start it only if necessary:

uv run --package cloudheal-node-agent cloudheal-node-agent

Start the Control Plane only if it is not already running:

uv run --package cloudheal-control-plane cloudheal-control-plane

Step 2 — Verify Windows Tailscale and Docker

On Windows PowerShell:

tailscale status
tailscale ip -4
docker info

Confirm that:

* Tailscale is connected.
* The current Windows Tailscale IP is known.
* Docker Desktop is running.
* docker info succeeds.

Do not use the historical Windows IP without checking it.

Step 3 — Test Windows-to-Mac Connectivity

From Windows PowerShell:

Test-NetConnection 100.90.104.13 -Port 9000

Use the current verified Mac Tailscale IP if it differs.

Expected result:

TcpTestSucceeded : True

If connectivity fails, investigate:

* Control Plane listening interfaces.
* macOS firewall rules.
* Tailscale connectivity and ACLs.
* Correct IP addresses.
* Whether the Control Plane is reachable from the Windows machine.

Do not change application code until the networking issue is understood.

Step 4 — Configure the Windows Node Agent

Inspect the existing agent configuration and startup behavior.

Configure the agent to use the verified Mac Tailscale address:

CONTROL_PLANE_URL=http://100.90.104.13:9000

Reuse the existing registration, heartbeat, system reporting, runtime reporting, and execution implementation.

Make platform-specific changes only when testing identifies a concrete issue.

Step 5 — Verify Registration and Heartbeats

On the Mac:

curl -s http://127.0.0.1:9000/nodes

Confirm that both nodes appear.

Verify:

* The Mac node is present.
* The Windows node is present.
* The Windows node has a stable identity.
* Heartbeat timestamps update.
* The Windows operating system is reported correctly.
* Docker runtime information is reported correctly.
* The Windows node’s reported capacity is plausible.

If registration fails, inspect the Node Agent logs before modifying code.

Step 6 — Verify Actual Windows Execution

Create a test workload suitable for the Windows node.

Verify:

1. The Control Plane selects the Windows node.
2. The scheduler sends a request to the Windows Node Agent.
3. The agent creates the container in the local Docker runtime.
4. Docker confirms that the container is running.
5. The agent returns the actual execution result.
6. The Control Plane records the correct assignment and state.
7. Remote status queries work over Tailscale.

On Windows:

docker ps
docker ps -a

Do not treat a database value of RUNNING as sufficient evidence.

Step 7 — Test Controlled Cross-Node Recovery

Only after Windows execution is verified:

1. Start a test workload on one laptop.
2. Verify the actual container state.
3. Introduce a controlled failure.
4. Observe the detection behavior.
5. Determine whether the original container could still be running.
6. Observe destination selection.
7. Verify replacement execution on the other laptop.
8. Record state transitions, events, and timing.
9. Document uncertain or inconclusive outcomes.

Until leases and agent-enforced fencing are implemented and tested, this is a controlled recovery experiment, not proof of safe failover under arbitrary network partitions.

⸻

8. Revised Implementation Roadmap

The roadmap reflects the actual implementation state. Testing existing code does not automatically count as implementing a new feature or completing a phase.

The Windows integration is a separate milestone that starts now. Persistence verification continues incrementally.

Phase 1 — Persistence and Event History

Status: Partially implemented; verification remains.

Existing work:

* SQLite schema and persistence logic.
* Node and workload database structures.
* Execution-event recording.
* Persistence-related tests.

Remaining work:

* Verify node persistence through registration and heartbeat.
* Verify workload persistence through creation, scheduling, execution, and recovery.
* Record all significant lifecycle events.
* Persist placement generations when implemented.
* Verify WAL mode and controlled state-changing writes.
* Use transactions for related state changes and events.
* Make generation allocation atomic with placement.
* Restore persisted state after restart.
* Discover and safely adopt identifiable running containers.

Completion test: Restart the Control Plane and verify that node/workload state and events persist, existing containers are identified correctly, and the system does not blindly create replacements.

Do not mark this phase complete until the restart behavior is tested against real containers.

Phase 2 — Node Health and Failure Detection

Status: Not implemented to the full specification.

Existing heartbeats provide the foundation.

Implement:

HEALTHY → SUSPECT → UNAVAILABLE

Definitions:

* HEALTHY: Recent communication and no detected failure.
* SUSPECT: Heartbeat or communication information has become stale.
* UNAVAILABLE: The failure-detection policy has determined that the node is ineligible for new placements and recovery evaluation may begin.

Requirements:

* Configurable timeouts.
* Explicit node-state transitions.
* Timestamped transition events.
* Delayed-heartbeat handling.
* Agent-termination tests.
* Temporary network-interruption tests.
* Recovery after communication resumes.
* Separation between node unavailability and container termination.

Completion test: Demonstrate the expected state transitions under controlled failure scenarios and verify their recorded events.

A node becoming unavailable does not prove that its containers have stopped.

Phase 3 — Leases, Generations, Fencing, and Failover

Status: Not implemented as an integrated safety protocol.

Implement these components together.

Leases

The Control Plane grants and renews time-limited execution authority.

Requirements:

* Explicit lease duration and safety margin.
* Authenticated and validated renewal messages.
* Monotonic-clock-based agent expiry.
* Safe handling of delayed renewal responses.
* Agent self-fencing after authority expires.
* Revalidation after laptop sleep or prolonged pauses.
* Careful treatment of clock uncertainty and process suspension.

Lease expiry alone does not prove that a container has stopped.

Placement Generations

Each workload placement receives a monotonically increasing generation.

Example:

Generation 1 → Node A
Generation 2 → Node B
Generation 3 → Node C

Requirements:

* Persistent generations.
* Atomic generation allocation.
* Container labels containing workload ID and generation.
* Generation information in execution and recovery requests.
* Rejection of stale commands.
* Protection against old placements overriding newer placements.
* Safe handling of repeated requests.
* Authority validation before destructive operations.

A generation stored only in the database or container labels is insufficient. The Node Agent must enforce the protocol.

Failover

When a node becomes unavailable:

1. Identify affected workloads.
2. Check desired state.
3. Evaluate recovery safety.
4. Select an eligible destination.
5. Allocate a higher generation.
6. Execute the replacement.
7. Verify container state and application health.
8. Persist the outcome.
9. Handle uncertain execution results safely.
10. Record failures, retries, and blocked actions.

Completion test: Demonstrate lease enforcement, stale-command rejection, generation protection, and cross-node recovery in controlled failure and network-partition tests.

Do not claim zero duplicate execution unless the fencing mechanism has been tested against the relevant failure scenarios.

Phase 4 — Second Real Laptop Integration

Status: Pending verification; immediate priority.

This phase begins now.

Requirements:

* Tailscale connectivity.
* Node registration.
* Heartbeat delivery.
* Control Plane-to-Agent communication.
* Windows Docker execution.
* Remote container status.
* Runtime resource reporting.
* Workload execution across both laptops.
* Controlled cross-node recovery.

Reuse the existing Node Agent wherever possible.

Two agents running on one computer do not substitute for a real network-partition test between separate laptops.

Phase 5 — Recovery Controls

Status: Basic recovery exists; advanced controls remain unverified.

Implement:

* Bounded retries.
* Exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling.
* Explicit failure and escalation states.

The system must not restart a failing workload indefinitely or overload the remaining nodes.

Phase 6 — Experimental Baselines

Status: Not implemented.

Support configurable policies such as:

1. No automated recovery.
2. Basic Docker restart behavior.
3. Fixed-timeout detection.
4. Deterministic CloudHeal recovery.
5. Controlled immediate-rescheduling baseline.
6. Fencing-disabled baseline in isolated tests.
7. Unlimited-retry baseline in isolated tests.

Unsafe baselines must be restricted to disposable workloads and controlled environments.

Build an experiment runner that executes scenarios repeatedly and records actual outcomes.

Phase 7 — Stable Application Gateway

Status: Not implemented.

Provide a stable application URL.

Test:

* Routing before failure.
* Routing during recovery.
* Routing after recovery.
* Unhealthy applications.
* Stale destination information.
* Active connection behavior.
* Session behavior across recovery.

A stable URL does not guarantee preservation of active connections or application state.

Phase 8 — Evaluation

Status: Not implemented.

Measure the system using repeated, controlled failure scenarios.

Metric	Purpose
Detection time	Time required to identify a failure
Recovery time	Time required to restore the workload
Recovery success rate	Fraction of successful recoveries
False-positive rate	Incorrect failure detections
Unnecessary migrations	Workloads moved without sufficient justification
Duplicate execution	Whether multiple copies execute concurrently
Overlap duration	Duration of duplicate execution
Retry count	Repeated work caused by failures
Cascade failures	Whether recovery overloads remaining nodes
Application downtime	Time the application is unavailable
Unsafe actions blocked	Actions rejected by safety policies
AI diagnosis accuracy	Agreement between diagnosis and observed evidence
Added latency	Additional delay introduced by AI
API cost	Cost of AI-assisted decisions

Aim for approximately 20 repetitions per scenario when time and hardware permit.

Report failed and inconclusive trials. Distinguish measured values from estimates.

Phase 9 — AI-Assisted Diagnosis and Planning

Status: Deferred until deterministic recovery is reliable.

Introduce the AI-assisted intelligence layer after the deterministic safety and recovery mechanisms are sufficiently mature.

The diagnosis component may analyze:

* Container exit codes.
* Container logs.
* Heartbeat history.
* Resource measurements.
* Application health checks.
* Scheduling decisions.
* Recovery history.

The planning component may recommend constrained actions, such as:

* Restarting a stopped container.
* Moving a workload.
* Waiting for a temporary problem to clear.
* Escalating a repeated failure.

Every proposed action must pass a deterministic safety gate that checks:

* Node eligibility.
* Resource constraints.
* Retry limits.
* Workload requirements.
* Lease and generation rules.
* Recovery safety.
* Required approvals.

The model must not receive unrestricted shell access or direct access to the Docker socket.

Record the evidence, recommendation, policy decision, executed action, and observed outcome.

The infrastructure must continue functioning if the model API is unavailable.

A dashboard can be developed alongside later phases if it helps the demonstration, but it must not delay the recovery milestones.

⸻

9. Resource-Scheduling Requirements

CloudHeal must not assume that host physical RAM equals the memory available to Docker containers.

Docker Desktop executes containers inside a Linux VM with its own resource configuration.

Distinguish:

1. Host physical memory.
2. Runtime/VM memory capacity.
3. Runtime memory availability where reliably measurable.
4. CloudHeal allocatable workload capacity.
5. Existing CloudHeal allocations.
6. Remaining schedulable capacity.

Inspect runtime information on both macOS and Windows.

The scheduler must not interpret missing or stale resource reports as unlimited capacity.

Recovery decisions must preserve enough capacity to avoid destabilizing the remaining nodes.

⸻

10. Development Commands

Start the Control Plane

cd ~/Desktop/CloudHeal
source .venv/bin/activate
uv run --package cloudheal-control-plane cloudheal-control-plane

Start the Mac Node Agent

cd ~/Desktop/CloudHeal
source .venv/bin/activate
uv run --package cloudheal-node-agent cloudheal-node-agent

Avoid starting duplicate processes if the services are already running.

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

This result is historical and should be refreshed when tests are next run.

Inspect Docker Containers on the Mac

docker ps
docker ps -a

Check Windows Tailscale

tailscale status
tailscale ip -4

Check Windows Docker

docker info
docker ps

Test Windows-to-Mac Connectivity

Test-NetConnection 100.90.104.13 -Port 9000

Replace the historical Mac IP with the verified current address if necessary.

⸻

11. Documentation and Project Coordination

Maintain two kinds of context.

Repository Context

File:

CloudHeal_CONTEXT.md

It should contain:

* Project architecture.
* Repository-relative paths.
* Implementation status.
* Verified milestones.
* Pending milestones.
* Shared protocol decisions.
* Safety requirements.
* Test commands.
* Integration instructions.

Do not make repository context depend on an individual’s local network addresses.

Personal Development Notes

These may contain:

* Local startup commands.
* Machine-specific addresses.
* Environment details.
* Debugging notes.
* Current individual tasks.

Before expanding project scope, confirm the direction and evaluation expectations with the project guide.

The lease/fencing protocol should be reviewed by the team before implementation.

After each milestone, update repository documentation with the actual changes and test evidence.

⸻

12. Minimum Final Scope

The minimum defensible final implementation should demonstrate:

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

AI-assisted diagnosis, constrained AI planning, adaptive failure detection, image-aware scheduling, and an advanced dashboard are additional features if time permits.

⸻

13. Current Development Position and Handoff

As of 22 October 2026:

* The Control Plane and Node Agent foundations exist.
* Workload scheduling and Docker execution are implemented.
* Basic stopped/missing-container recovery has been demonstrated.
* SQLite persistence and execution-event recording have been introduced.
* The latest recorded Control Plane test run passed 23 tests.
* A Mac-hosted nginx:latest workload was verified as running at the recorded time.
* The Mac Control Plane and Node Agent are recorded as running and healthy in the latest context.
* The Windows laptop has not yet been verified as a registered, executing CloudHeal node.
* Complete persistence, startup adoption, the node-health state machine, leases, fencing, and safe cross-node failover remain unfinished.
* The agreed architecture separates deterministic self-healing from AI-assisted diagnosis and planning.
* AI recommendations must pass the deterministic safety gate.
* Infrastructure operation must not depend on AI availability.

Next Session: Start Here

First priority: connect the Windows laptop as the second real node.

1. Inspect the current Git working tree.
2. Verify the Mac Control Plane and Node Agent.
3. Verify the Windows Tailscale IP and Docker installation.
4. Test Windows-to-Mac connectivity.
5. Configure and start the Windows Node Agent.
6. Verify registration and heartbeats.
7. Execute a test workload on Windows.
8. Verify actual Docker state and Control Plane status.
9. Test controlled cross-node recovery once both nodes are operational.
10. Continue persistence and event-history verification.
11. Implement node-health detection.
12. Design and implement leases, generations, and fencing as an integrated safety protocol.
13. Add bounded recovery controls.
14. Build repeatable experiments and evaluate results.
15. Introduce AI-assisted diagnosis and constrained planning only after deterministic recovery is reliable.

Do not rebuild existing components or jump directly into a large failover rewrite.

Guiding principle: Establish real multi-node execution first, persist the state, define and enforce the recovery protocol, test actual failures, measure the results, and then add AI where it genuinely helps.