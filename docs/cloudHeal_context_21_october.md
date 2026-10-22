CloudHeal — Complete Project Context & Revised Implementation Roadmap

Last updated: 21 October 2026
Project stage: Control Plane persistence and Docker execution implemented in part; reconciliation and basic recovery implemented; second real laptop integration pending.
Immediate priority: Connect the Windows laptop to CloudHeal as the second real compute node.
Latest verified automated tests: 23 Control Plane tests passed.
Current development environment: MacBook Air running macOS, Python, FastAPI, uv, Docker Desktop, and Tailscale.

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
* SQLite for persistent Control Plane state.
* A future AI-assisted diagnosis and recovery-planning layer.

The platform is intended to support:

1. Node registration and monitoring.
2. Heartbeat processing and node health detection.
3. System and Docker runtime information collection.
4. Workload creation and scheduling.
5. Docker execution through Node Agents.
6. Persistent workload state and event history.
7. Container and node failure detection.
8. Cross-node workload recovery.
9. Leases, placement generations, and agent-enforced fencing.
10. Recovery retry limits and capacity protection.
11. A stable application URL across successful recovery.
12. Repeatable experiments and measured results.
13. AI-assisted diagnosis and constrained recovery planning.

CloudHeal is a development and demonstration platform. The laptops do not need to remain online continuously.

1.2 Intended Final Demonstration

The final demonstration should show:

1. Deploying an application through CloudHeal.
2. Identifying which laptop is executing it.
3. Observing its container and workload state.
4. Introducing a controlled failure.
5. Detecting and classifying the failure.
6. Determining whether recovery is safe.
7. Selecting an eligible destination node.
8. Executing a replacement workload.
9. Verifying the replacement’s actual state and health.
10. Maintaining application access through a stable URL.
11. Recording the complete execution and recovery history.
12. Comparing different recovery policies using repeated experiments.
13. Demonstrating AI-assisted diagnosis and constrained planning if time permits.

The project’s contribution must be established through actual infrastructure behavior, reliable recovery, and measured results—not merely a dashboard or chatbot.

⸻

2. Architecture

2.1 Control Plane

The Control Plane is a Python/FastAPI service responsible for:

* Node registration and information retrieval.
* Heartbeat processing.
* Persistent node and workload records.
* Scheduling decisions.
* Remote Node Agent communication.
* Docker execution coordination.
* Workload state management.
* Periodic reconciliation.
* Execution result recording.
* Recovery decisions.
* Future lease and placement-generation management.
* Future event history and experiment reporting.

The Control Plane runs on the MacBook during current development.

Previously configured local address:

http://127.0.0.1:9000

For remote Windows agents, the Control Plane must also be reachable through the Mac’s Tailscale IP.

2.2 Node Agent

The Node Agent runs on each participating laptop.

Responsibilities include:

* Maintaining a persistent node identity.
* Registering with the Control Plane.
* Sending heartbeats.
* Reporting system information.
* Reporting Docker runtime information.
* Executing permitted Docker operations.
* Reporting container status.
* Supporting future lease enforcement.
* Rejecting stale placement commands when generation fencing is implemented.
* Self-fencing when its authority expires.

The existing implementation already supports registration, heartbeats, resource reporting, Docker execution, and container status queries.

Lease enforcement and generation-based fencing are not yet established as complete.

2.3 Docker Runtime

Each laptop uses Docker Desktop to execute workload containers.

The Control Plane must communicate with the Node Agent rather than assume it can execute Docker commands directly on another laptop.

For remote execution, the intended flow is:

Control Plane → selected Node Agent → local Docker runtime → execution result → Control Plane.

2.4 SQLite Persistence

SQLite is being integrated into the Control Plane.

The implementation now includes database schema and persistence logic for workloads and nodes, along with an events table and execution-event recording.

However, persistence must be evaluated by component. A schema existing in SQLite does not prove that every operation, startup path, or state transition is persisted correctly.

Remaining verification includes:

* Node registration and heartbeat persistence.
* State recovery after a Control Plane restart.
* Placement generation persistence.
* Complete event coverage.
* Atomic placement and event updates.
* Startup discovery and adoption of existing containers.

2.5 Scheduler

The scheduler has progressed beyond the original first-healthy-node approach.

It considers node suitability, runtime information, and reported resource capacity. It also coordinates execution through Node Agents.

Current testing covers scheduling, resource-related behavior, execution results, and failure cases.

The scheduler must not treat a placement decision as proof of successful execution.

2.6 Reconciler

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

The reconciler and scheduler must eventually distinguish a failed container from a temporarily unreachable node. An HTTP timeout alone does not prove that the old container has stopped.

2.7 Future Application Gateway

A future gateway will provide a stable application URL and route traffic to the workload’s current location.

Routing must remain separate from scheduling and recovery.

A stable URL does not automatically preserve active TCP connections, sessions, or application state.

2.8 Future AI Layer

AI-assisted diagnosis and recovery planning will be introduced only after deterministic recovery is sufficiently reliable.

The model may recommend actions, but a deterministic safety gate must authorize them.

The infrastructure must continue functioning if the model API is unavailable.

⸻

3. Repository and Development Environment

3.1 Repository

Local repository:

/Users/aniketsaini/Desktop/CloudHeal

Activate the environment:

cd ~/Desktop/CloudHeal
source .venv/bin/activate

Check the working tree:

git status

Inspect outstanding changes before editing:

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

Additional files now include or are expected to include:

* control-plane/src/cloudheal_control_plane/database.py
* control-plane/tests/test_database_events.py
* control-plane/tests/test_scheduler.py
* control-plane/tests/test_reconciler.py

Verify the actual repository before creating files or assuming this structure is unchanged.

3.3 Development Rules

* Inspect the existing implementation before editing.
* Preserve working code.
* Make incremental changes.
* Do not rebuild completed components unnecessarily.
* Run relevant tests after every meaningful change.
* Verify real Docker state where appropriate.
* Do not report a feature as complete solely because its tests pass.
* Update this context after verified milestones.

⸻

4. Current Infrastructure

4.1 Control Plane

Package:

cloudheal-control-plane

Previously configured address:

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

Check the current API implementation before assuming that all endpoint behavior is unchanged.

4.2 Node Agent

Package:

cloudheal-node-agent

Previously configured port:

8000

Startup command:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously documented identity file:

~/.cloudheal/node_id

Previously configured heartbeat interval: 10 seconds.

The Node Agent provides registration, heartbeats, system/runtime reporting, Docker operations, and container status information.

4.3 Mac Development Node

Previously recorded details:

Property	Historical value
Node ID	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Hostname	Anikets-MacBook-Air.local
Tailscale IP	100.90.104.13
Previously recorded local IP	192.168.1.124
Operating system	macOS
Architecture	ARM64
Physical CPU cores	8
Logical CPU cores	8
Physical memory	8 GiB
Previously reported Docker version	29.8.2

These are historical values. Query the live node and Docker runtime before conducting capacity-sensitive experiments.

4.4 Windows Node

The Windows laptop is the next integration target.

The current objective is to add it as a second real compute node without creating a separate implementation of the Node Agent unnecessarily.

A previously reported Windows Tailscale IP was:

100.127.235.82

This address is historical and must be verified on the Windows laptop.

Before registering the Windows node, verify:

* Tailscale is connected.
* Docker Desktop is running.
* docker info succeeds.
* The Windows machine can reach the Mac’s Control Plane.
* The Node Agent can communicate with the Control Plane over Tailscale.
* Windows-specific Docker and networking behavior is understood.

Do not assume the Windows integration is complete until registration, heartbeats, remote execution, and status reporting have been verified.

⸻

5. Workload Management

5.1 Desired States

The existing model uses:

* RUNNING
* STOPPED

Desired state represents what the system should do.

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

The workload should be running, but execution has failed.

Recovery must check desired state before taking action. A workload whose desired state is STOPPED must not be automatically restarted.

5.3 Execution Lifecycle

The intended lifecycle is:

PENDING → SCHEDULED → RUNNING
                     ↘ FAILED

A successful scheduling decision must not automatically set the workload to RUNNING.

The Control Plane must receive and validate an execution result.

Timeouts and uncertain HTTP responses require special care. A request may have started a container even if the Control Plane never received the response.

Generation-aware execution and reconciliation must eventually account for this possibility.

⸻

6. Work Completed Through 21 October 2026

This section separates implemented and tested behavior from remaining work.

6.1 Control Plane and Node Agent Foundation

Previously implemented and tested:

* FastAPI Control Plane.
* Node registration and lookup.
* Heartbeat processing.
* System information reporting.
* Docker runtime information reporting.
* Workload creation and retrieval.
* Scheduler-to-Agent communication.
* Docker container execution through the Node Agent.
* Container status queries.
* Periodic reconciliation.
* Basic stopped/missing-container recovery.

6.2 SQLite Persistence

Recent work added SQLite persistence to the Control Plane.

The implementation includes:

* A database module.
* SQLite schema for nodes, workloads, and events.
* Workload persistence through the workload registry.
* Persistence of workload state changes associated with scheduling and execution.
* SQLite WAL configuration and busy-timeout handling in the existing database implementation.
* Timestamped execution-event recording.
* Tests covering database event behavior and scheduler behavior.

The schema and implementation are not yet equivalent to complete project-wide persistence.

The following gaps remain:

1. Full node lifecycle persistence must be verified.
2. Startup restoration after a Control Plane restart must be verified.
3. Placement generations are not yet fully implemented.
4. Every important scheduling and recovery transition must be recorded.
5. Related state changes and events must eventually be committed atomically.
6. Existing containers must be discovered and safely adopted after restart.

Event recording

The event system has been introduced, and the scheduler records execution success/failure events.

Previously verified event types include:

* EXECUTION_SUCCEEDED
* EXECUTION_FAILED

The implementation should be inspected to establish the exact current event coverage.

A complete event history still needs events for workload creation, scheduling decisions, node state transitions, failure detection, recovery attempts, retries, and recovery verification.

Persistence completion criteria

Do not mark Phase 1 complete until:

* Node and workload records survive Control Plane restarts.
* Relevant events survive restarts.
* Existing containers are discovered or safely adopted.
* Placement generations are persisted once implemented.
* Related state transitions and events are consistent.
* The restart behavior has been tested against real containers.

6.3 Scheduler and Execution Results

The scheduler has been updated and tested for workload execution outcomes.

Current behavior includes communicating with the selected Node Agent, receiving execution results, and recording success or failure rather than treating scheduling as proof of execution.

A test specifically verified that a missing container status produces an execution failure.

Resource-aware scheduling logic also exists, but its capacity assumptions and behavior must be verified against the live runtime on both macOS and Windows.

6.4 Reconciliation and Basic Recovery

The reconciler periodically processes workloads and queries their containers.

Previously verified behavior includes:

1. A workload was running through CloudHeal.
2. Its container was stopped or removed deliberately.
3. The reconciliation path detected the missing/stopped container.
4. CloudHeal initiated recovery.
5. A replacement container was created.
6. Docker independently confirmed that the replacement was running.
7. The workload returned to RUNNING.

One previously recorded recovery test used workload ID:

1b5b2f07-169a-47c8-a6c0-b1a0026f821e

A replacement container’s recorded start time was:

2026-10-19T19:11:42.747967761Z

The replacement reported RestartCount=0 in the recorded inspection.

These results demonstrate basic recovery from a stopped or missing container. They do not establish safe recovery after an entire laptop becomes unreachable.

6.5 Latest Verified Automated Tests

On 21 October 2026, the following command passed:

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Recorded result:

23 passed in 0.33s

This is the latest recorded full Control Plane test result.

The test suite includes coverage for recent scheduler, persistence/event, and reconciler work.

Passing tests do not prove that the current code handles real Windows connectivity, network partitions, leases, fencing, or cross-node recovery correctly.

The Node Agent’s previously recorded test result was 8 passing tests, and an earlier combined run reported 21 Control Plane tests plus 8 Node Agent tests. Those are historical results, not a current combined test run.

6.6 Latest Workload Execution Verification

A workload named event-test was submitted and successfully executed through the Mac Node Agent.

Recorded workload details:

Property	Value
Name	event-test
Workload ID	ff02cc16-e20b-43a6-a41c-62fc996dd3b9
Image	nginx:latest
Desired state	RUNNING
Actual state	RUNNING
Assigned node	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
Recorded update time	2026-10-21T15:43:14.019430Z

This verifies a successful workload execution on the Mac at the recorded time.

It does not establish execution on Windows or cross-node recovery.

6.7 Current Known Limitations

The following are not yet established as complete:

* Fully verified persistence of every node and workload transition.
* Startup restoration and adoption of existing containers.
* Complete timestamped event history.
* Atomic placement and event transactions.
* Persistent placement generations.
* Lease grants, renewals, and expiry enforcement.
* Agent-enforced fencing.
* Safe cross-node failover.
* Windows Node Agent integration.
* Real network-partition testing.
* Duplicate-execution overlap measurement.
* Application-level health checks.
* Crash-loop detection and bounded retry behavior.
* Recovery concurrency controls.
* Stable application gateway.
* Repeatable experiment runner.
* AI-assisted diagnosis and recovery planning.
* Final dashboard and demonstration.

⸻

7. Immediate Priority: Connect the Windows Laptop

This is our next task. Do not continue implementing additional recovery mechanisms before beginning this integration.

The second real laptop is necessary to validate distributed execution and exposes platform-specific issues early.

The integration should reuse the current Control Plane and Node Agent implementations wherever possible.

7.1 Step 1 — Inspect the Current Mac Setup

From the Mac:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status

Start the Control Plane if it is not already running:

uv run --package cloudheal-control-plane cloudheal-control-plane

In another terminal, start the Mac Node Agent if necessary:

uv run --package cloudheal-node-agent cloudheal-node-agent

Verify the Control Plane:

curl http://127.0.0.1:9000/health

List registered nodes:

curl http://127.0.0.1:9000/nodes

Confirm that the Mac node is registered and sending heartbeats.

Do not launch duplicate processes if the services are already running.

7.2 Step 2 — Inspect Windows Networking and Docker

On the Windows laptop, open PowerShell.

Check Tailscale:

tailscale status

Retrieve the current Tailscale IP:

tailscale ip -4

Check Docker:

docker info

Verify that Docker Desktop is running and that the command completes successfully.

7.3 Step 3 — Test Windows-to-Mac Connectivity

From Windows PowerShell:

Test-NetConnection 100.90.104.13 -Port 9000

The expected result is:

TcpTestSucceeded : True

If the connection fails, investigate:

* Whether the Control Plane is listening on an interface reachable through Tailscale.
* macOS firewall settings.
* Tailscale connectivity and ACLs.
* Whether the correct current Mac IP is being used.

Do not change application code until the networking problem is understood.

7.4 Step 4 — Configure the Windows Node Agent

Inspect the existing agent configuration and startup behavior.

Configure the Windows Node Agent to use the Mac Control Plane address:

CONTROL_PLANE_URL=http://100.90.104.13:9000

Use the verified current Tailscale address.

Reuse the existing registration, heartbeat, system reporting, runtime reporting, and execution implementations.

Make platform-specific changes only when testing shows they are necessary.

7.5 Step 5 — Verify Registration and Heartbeats

After starting the Windows Node Agent, check:

curl http://127.0.0.1:9000/nodes

Confirm that:

* The Mac node is present.
* The Windows node is present.
* The Windows node has a stable identity.
* Heartbeat timestamps update.
* The Windows node’s operating system and runtime information are reported correctly.

Inspect the Node Agent’s logs if registration or heartbeats fail.

7.6 Step 6 — Verify Remote Execution

Create a test workload that can run on Windows.

Verify:

1. The Control Plane selects the Windows node.
2. The scheduler sends the execution request to the Windows Node Agent.
3. The agent creates the Docker container locally.
4. Docker confirms that the container is running.
5. The agent returns the actual execution result.
6. The Control Plane records the correct node assignment and workload state.
7. Remote container status queries work over Tailscale.

Check Docker directly on Windows:

docker ps

Do not assume that a RUNNING database state proves the container is actually running.

7.7 Step 7 — Test Cross-Node Recovery

Only after basic Windows execution works:

1. Start a test workload on one laptop.
2. Verify the actual container state.
3. Introduce a controlled failure.
4. Observe the Control Plane’s detection behavior.
5. Determine whether the original container might still be executing.
6. Verify the destination selection.
7. Verify replacement execution on the other laptop.
8. Record all observed outcomes and uncertainties.

Until lease and fencing enforcement has been implemented and tested, this is a controlled recovery experiment—not proof of safe failover under arbitrary network partitions.

⸻

8. Revised Implementation Roadmap

The following roadmap preserves the original project goals but updates the immediate development priority.

The Windows integration begins now. Persistence verification and the subsequent safety milestones continue incrementally.

Phase 1 — Persistence and Event History

Status: Partially implemented; verification and completion remain.

Existing work includes SQLite schema and persistence for nodes/workloads, execution-event recording, and persistence-related tests.

Remaining work:

* Verify node persistence on registration and heartbeat.
* Verify workload persistence through creation, scheduling, execution, and recovery.
* Persist complete placement history and generations when implemented.
* Record all significant scheduling, health, and recovery events.
* Enable and verify WAL mode.
* Use a controlled single-writer strategy.
* Use transactions for related state changes.
* Make generation allocation atomic with placement.
* Restore persisted records after restart.
* Discover and safely adopt identifiable running containers.

Completion test:

Restart the Control Plane and verify that state and events persist, existing containers are correctly identified, and the system does not blindly create replacements.

Phase 2 — Node Health and Failure Detection

Implement the state machine:

HEALTHY → SUSPECT → UNAVAILABLE

Definitions:

* HEALTHY: Recent communication and no detected failure.
* SUSPECT: Heartbeat or communication information has become stale.
* UNAVAILABLE: The failure-detection policy has determined that the node is ineligible for new placements and recovery evaluation may begin.

A node becoming unavailable does not prove that its containers have stopped.

Test:

* Recent heartbeats.
* Stale heartbeats.
* Delayed heartbeats.
* Agent termination.
* Temporary network interruption.
* Sustained node unavailability.
* Recovery after communication resumes.

Every state transition must generate a timestamped event.

Phase 3 — Leases, Generations, and Failover

Implement leases, generation enforcement, and failover as one integrated safety milestone.

Leases

The Control Plane grants and renews time-limited execution authority.

Requirements:

* Explicit lease duration and safety margin.
* Renewal through authenticated, validated protocol messages.
* Monotonic-clock-based agent expiry.
* Safe handling of delayed renewal responses.
* Agent self-fencing after authority expires.
* Revalidation after prolonged pauses or laptop sleep.
* No replacement authorization before the previous authority is considered expired under the agreed timing model.

Lease expiry alone does not prove that an existing container has stopped.

Placement Generations

Every placement receives a monotonically increasing generation.

Example:

Generation 1 → Node A
Generation 2 → Node B
Generation 3 → Node C

Requirements:

* Persist generations.
* Allocate them atomically.
* Label containers with workload ID and generation.
* Include generation information in execution and recovery requests.
* Reject stale commands.
* Prevent older placements from overriding newer ones.
* Make repeated placement requests safe to handle.
* Validate authority before destructive operations.

Storing a generation in the database or container labels is not sufficient. The Node Agent must enforce it.

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
10. Record failures, retries, and blocked decisions.

Do not claim zero duplicate execution unless the actual fencing implementation has been tested against relevant failure scenarios.

Phase 4 — Second Real Laptop Integration

Status: Not yet verified complete. Immediate priority.

The Windows laptop must be connected and tested as described in Section 7.

Minimum integration requirements:

* Tailscale connectivity.
* Node registration.
* Heartbeat delivery.
* Control Plane-to-agent communication.
* Windows Docker execution.
* Remote container status.
* Runtime resource reporting.
* Cross-node workload recovery.

Two agents on the Mac can help test APIs but do not substitute for a real network-partition test between separate laptops.

Phase 5 — Recovery Controls

Implement:

* Bounded retries.
* Exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling.
* Clear terminal and escalation states.

Prevent endless restarts and recovery storms.

Phase 6 — Experimental Baselines

Support configurable policies such as:

1. No automated recovery.
2. Basic Docker restart behavior.
3. Fixed-timeout detection.
4. CloudHeal deterministic recovery.
5. Controlled immediate-rescheduling baseline.
6. Fencing-disabled baseline in isolated tests.
7. Unlimited-retry baseline in isolated tests.

Unsafe policies must be restricted to disposable workloads and controlled environments.

Build an experiment runner that executes scenarios repeatedly and records actual outcomes.

Phase 7 — Stable Application Gateway

Add a stable URL for the demonstration application.

Test:

* Routing before failure.
* Routing after recovery.
* Routing while recovery is in progress.
* Unhealthy applications.
* Stale destination information.
* Active connection behavior during failover.

Phase 8 — Evaluation

Measure:

Metric	Purpose
Detection time	Time required to identify a failure
Recovery time	Time required to restore the workload
Recovery success rate	Fraction of successful recoveries
False-positive rate	Incorrect failure detections
Unnecessary migrations	Workloads moved without sufficient justification
Duplicate execution	Whether multiple copies execute concurrently
Overlap duration	Duration of duplicate execution
Retry count	Repeated work caused by failures
Cascade failures	Whether recovery overloads other nodes
Application downtime	Time the application is unavailable
Unsafe actions blocked	Actions rejected by safety policies
AI diagnosis accuracy	Agreement between diagnosis and observed evidence
Added latency	Extra delay from AI assistance
API cost	Cost of AI-assisted decisions

Aim for approximately 20 repetitions per scenario when time and hardware permit.

Report measured results, including failed and inconclusive trials. Distinguish actual measurements from estimates.

Phase 9 — AI-Assisted Diagnosis and Planning

Introduce AI after the deterministic recovery path is reliable.

The diagnosis component may inspect:

* Container exit codes.
* Container logs.
* Heartbeat history.
* Resource measurements.
* Application health checks.
* Scheduling decisions.
* Recovery history.

The planning component may recommend constrained actions such as restarting a stopped container, moving a workload, waiting for a temporary problem to clear, or escalating a repeated failure.

A deterministic safety gate must validate every proposed action against:

* Node eligibility.
* Resource constraints.
* Retry limits.
* Workload requirements.
* Lease and generation rules.
* Recovery safety.
* Required approvals.

The model must not receive unrestricted shell access or direct access to the Docker socket.

Record the evidence, recommendation, policy decision, executed action, and observed outcome.

The infrastructure must continue functioning when the model API is unavailable.

A dashboard can be developed alongside later phases if it helps the demonstration, but it must not delay the recovery milestones.

⸻

9. Resource-Scheduling Requirements

CloudHeal must not assume that host physical RAM equals memory available to containers.

Docker Desktop executes containers inside a Linux VM with its own resource configuration.

Distinguish:

1. Host physical memory.
2. Runtime/VM memory capacity.
3. Runtime memory availability where reliably measurable.
4. CloudHeal’s allocatable workload capacity.
5. Existing CloudHeal allocations.
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

Use the verified current Mac Tailscale IP if it differs from the historical address.

⸻

11. Documentation and Project Coordination

Maintain two forms of context.

Repository Context

CloudHeal_CONTEXT.md

Contains:

* Project architecture.
* Repository-relative paths.
* Current implementation status.
* Verified milestones.
* Pending milestones.
* Shared protocol decisions.
* Safety requirements.
* Test commands.
* Integration instructions.

Do not make the repository context dependent on one person’s local network addresses.

Personal Development Notes

Contains:

* Local startup commands.
* Machine-specific network addresses.
* Environment details.
* Debugging notes.
* Current individual development tasks.

Before expanding the agreed project scope, confirm the direction and evaluation expectations with the project guide.

The lease/fencing protocol should be reviewed by the team before implementation.

After each milestone, update the repository context and record the test evidence.

⸻

12. Minimum Final Scope

The minimum defensible final implementation must include:

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

AI diagnosis, constrained AI planning, adaptive failure detection, image-aware scheduling, and an advanced dashboard are additional features if time permits.

⸻

13. Current Development Position and Handoff

As of 21 October 2026:

* The Control Plane and Node Agent foundations exist.
* Workload scheduling and Docker execution are implemented.
* Basic stopped/missing-container recovery has been demonstrated.
* SQLite persistence and execution-event recording have been introduced.
* The latest recorded Control Plane test run passed all 23 tests.
* A Mac-hosted nginx:latest workload was verified as RUNNING.
* Complete persistence, startup adoption, leases, fencing, and safe cross-node failover remain unfinished.
* The Windows laptop has not yet been verified as a registered, executing CloudHeal node.

Next session: Start here

First priority: connect the Windows laptop as the second real node.

1. Inspect the current Git working tree.
2. Verify that the Mac Control Plane and Node Agent are running.
3. Verify the Windows Tailscale IP and Docker installation.
4. Test Windows-to-Mac connectivity.
5. Configure and start the Windows Node Agent.
6. Verify registration and heartbeats.
7. Execute a test workload on Windows.
8. Verify its actual Docker state and Control Plane status.
9. Test controlled cross-node recovery once both nodes are operational.

Do not rebuild the existing implementation or jump directly into a large failover rewrite.

After the Windows node is connected, continue completing persistence and event history, node-health detection, and the integrated lease/generation/fencing protocol.

Guiding principle: Establish real multi-node execution first, persist the state, define and enforce the recovery protocol, test actual failures, measure the results, and then add AI where it genuinely helps.