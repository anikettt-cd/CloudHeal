CloudHeal — Complete Project Context & Revised Implementation Roadmap

Last updated: 20 October 2026
Project stage: Distributed infrastructure foundation with basic container recovery
Immediate priority: Inspect the current implementation, establish test results, and plan persistence and recovery safety before implementing cross-node failover.

⸻

1. Project Overview

1.1 What Are We Building?

CloudHeal is a student engineering project that aims to build a small distributed cloud platform using our team’s laptops as compute nodes.

The intended development environment consists of four laptops:

* One MacBook Air running macOS.
* Three teammates’ laptops running Windows.
* Tailscale for private network connectivity.
* A centralized Python/FastAPI Control Plane.
* A Node Agent running on each participating laptop.
* Docker for container execution.
* SQLite for persistent Control Plane state.
* A future AI-assisted self-healing layer.

CloudHeal will progressively support:

1. Registering and monitoring compute nodes.
2. Collecting node and runtime resource information.
3. Accepting workload deployment requests.
4. Scheduling workloads onto eligible nodes.
5. Executing Docker containers through Node Agents.
6. Detecting container, application, and node failures.
7. Recovering workloads when recovery is safe.
8. Preventing stale commands and reducing duplicate-execution risk.
9. Recording and measuring recovery behavior.
10. Providing a stable application endpoint across successful recovery.
11. Using AI to assist with ambiguous failure diagnosis and constrained recovery planning.

This is a development and demonstration platform. The laptops do not need to remain online 24/7.

1.2 Final Demonstration

The intended demonstration is:

1. Deploy an application through CloudHeal.
2. Show which laptop is running it.
3. Introduce a controlled failure.
4. Detect and classify the failure.
5. Decide whether recovery is appropriate.
6. Select an eligible destination node.
7. Execute a replacement workload.
8. Verify the replacement’s actual health.
9. Keep the application accessible through a stable URL.
10. Record detection time, recovery time, and other relevant events.
11. Compare recovery policies using repeatable experiments.
12. Demonstrate AI-assisted diagnosis and constrained planning if time permits.

The project’s contribution must be demonstrated through actual infrastructure behavior, reliable recovery, and measurable results—not just a dashboard or chatbot.

⸻

2. Core Engineering Problems

CloudHeal should address the following practical problems.

2.1 Container and Application Failures

A container may stop, disappear, repeatedly crash, or remain running while its application is unhealthy.

CloudHeal should distinguish these situations and select an appropriate response.

Basic stopped/missing-container recovery has previously been verified. Application-level health monitoring and crash-loop protection remain future work.

2.2 Node Failure

A laptop may shut down, its agent may crash, or connectivity may be lost.

CloudHeal should detect sustained unavailability, identify affected workloads, and recover them on eligible nodes when it is safe to do so.

2.3 Temporary Network Problems

A temporary connection failure does not prove that a laptop or its containers have stopped.

The failure detector must distinguish suspicion from confirmed policy-level unavailability.

2.4 Duplicate Execution

An unreachable laptop may still be running its container.

If the Control Plane starts a replacement elsewhere, two copies may run concurrently.

Leases, generation numbers, and agent-enforced fencing must be designed together to reduce this risk.

The defensible target is:

Stale commands must not take effect, and duplicate-execution overlap must be measured and bounded in the tested scenarios.

Do not claim that zero duplicate execution is guaranteed under every failure condition.

2.5 Recovery Storms

When a node fails, moving all its workloads immediately may overload the remaining nodes.

CloudHeal should use capacity-aware placement, bounded concurrency, retry controls, and recovery priorities where appropriate.

2.6 Crash Loops

Repeatedly restarting a failing workload wastes resources.

CloudHeal needs retry limits, exponential backoff, failure history, and a clear escalation or terminal state.

2.7 Difficult Diagnosis

Some failures cannot be classified reliably using simple rules alone.

A future AI layer may inspect structured evidence and recommend actions, but a deterministic safety layer must remain responsible for authorizing recovery operations.

⸻

3. Architecture

3.1 Existing Components

Control Plane

A Python/FastAPI service responsible for:

* Node registration and health tracking.
* Workload management.
* Scheduling.
* Execution coordination.
* Reconciliation.
* Recovery decisions.

Node Agent

A service running on each participating laptop. It is responsible for:

* Persistent node identity.
* Registration and heartbeats.
* System and runtime information.
* Permitted Docker operations.
* Container status reporting.
* Future lease enforcement and stale-command rejection.

Docker Runtime

Runs workload containers locally on each participating laptop.

Scheduler

Selects an eligible node using health, runtime availability, and reported resource information.

The scheduler has progressed beyond its original first-healthy-node policy. Its current implementation and test results must be rechecked before making further changes.

Reconciler

Periodically compares desired workload state with observed execution state and initiates appropriate actions.

Basic stopped/missing-container recovery has previously been verified.

Persistent State

SQLite is the planned initial persistence layer for node records, workload records, placement generations, and execution/recovery events.

Future Application Gateway

A stable endpoint will route application requests to the workload’s current location.

Routing must remain separate from scheduling and recovery.

Future AI Layer

AI-assisted diagnosis and constrained recovery planning will be added only after the deterministic recovery path is sufficiently reliable.

⸻

4. Repository and Development Environment

Repository:

/Users/aniketsaini/Desktop/CloudHeal

Activate the environment:

cd /Users/aniketsaini/Desktop/CloudHeal
source .venv/bin/activate
git status

The project uses uv.

4.1 Known Repository Structure

CloudHeal/
├── CloudHeal_CONTEXT.md
├── README.md
├── pyproject.toml
├── uv.lock
├── docs/
│   ├── SPEC-001-cloudheal.md
│   └── current_progress.md
├── control-plane/
│   └── src/
│       └── cloudheal_control_plane/
│           ├── api.py
│           ├── main.py
│           ├── registry.py
│           └── workloads/
│               ├── models.py
│               ├── registry.py
│               ├── service.py
│               ├── scheduler.py
│               └── reconciler.py
└── infrastructure/
    └── node-agent/
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

This is the previously documented structure, not a guarantee that every file remains unchanged.

Inspect the actual repository before creating files, changing interfaces, or assuming that a documented implementation still exists.

⸻

5. Existing Infrastructure and Known State

5.1 Control Plane

Package: cloudheal-control-plane

Previously configured address:

http://127.0.0.1:9000

Previously documented startup command:

uv run --package cloudheal-control-plane cloudheal-control-plane

Known endpoints:

Endpoint	Purpose
GET /health	Check Control Plane availability
POST /nodes/register	Register a node
GET /nodes	List nodes
GET /nodes/{node_id}	Retrieve node information
POST /nodes/{node_id}/heartbeat	Receive heartbeat information
POST /workloads	Create a workload
GET /workloads	List workloads
GET /workloads/{workload_id}	Retrieve a workload
POST /workloads/{workload_id}/schedule	Request scheduling

Persistence limitation: The documented node and workload registries currently use in-memory data structures. Their records do not survive a Control Plane restart.

Confirm this against the current code before beginning the persistence milestone.

5.2 Node Agent

Package: cloudheal-node-agent

Previously configured port: 8000

Startup command:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously documented persistent identity file:

~/.cloudheal/node_id

Previously configured heartbeat interval: 10 seconds.

The agent already supports registration, heartbeats, system/runtime information reporting, Docker execution, and container status queries.

Lease renewal, reliable self-fencing, and generation enforcement are not yet established as complete.

5.3 Known Mac Development Node

Previously recorded information:

* Node ID: 83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed
* Hostname: Anikets-MacBook-Air.local
* Last recorded local address: 192.168.1.124
* Operating system: macOS
* Architecture: ARM64
* Physical CPU cores: 8
* Logical CPU cores: 8
* Physical memory: 8 GiB
* Docker version: 29.8.2
* Docker runtime: Available

These values are historical. Query the current node and Docker runtime before conducting capacity-sensitive experiments.

⸻

6. Workload Management and Scheduling

6.1 Workload States

Previously documented desired states:

* RUNNING
* STOPPED

Previously documented actual states:

* PENDING
* SCHEDULED
* RUNNING
* FAILED
* STOPPED

Desired state indicates what should happen.

Actual state describes what the Control Plane currently believes has happened.

For example:

desired_state = RUNNING
actual_state  = FAILED

The workload should be running, but execution has failed.

Recovery must check desired state before taking action.

6.2 Resource-Aware Scheduling

The documented scheduler considers:

* Node health.
* Runtime availability.
* CPU information.
* Memory information.
* Workload CPU requirements.
* Workload memory requirements.
* Existing scheduled/running workload allocations.
* Remaining node capacity.

The scheduler filters unsuitable nodes and chooses a destination using a remaining-capacity score.

The exact implementation and latest tests must be rechecked.

Docker Memory Correction

A laptop’s physical RAM must not be treated as equivalent to memory available to containers.

On Docker Desktop, containers run inside a Linux VM with its own resource configuration.

CloudHeal must distinguish:

1. Host physical memory.
2. Runtime/VM memory capacity.
3. Current runtime memory availability, where reliably measurable.
4. CloudHeal’s allocated workload capacity.

Inspect Docker’s actual runtime information and configured limits on macOS and Windows.

Scheduling estimates must not exceed the capacity CloudHeal intends to allocate.

6.3 Scheduler-to-Agent Execution

The Control Plane requests execution from the selected Node Agent.

The Node Agent invokes the local Docker runtime and returns an execution result.

The intended lifecycle is:

PENDING → SCHEDULED → RUNNING
                     ↘ FAILED

The Control Plane must not report successful execution merely because it selected a node.

Timeouts and uncertain HTTP responses require special care: a request may have started a container even if the Control Plane never received the response.

Future generation-aware execution and reconciliation must account for this possibility.

⸻

7. Existing Reconciliation and Container Recovery

7.1 Previously Implemented Behavior

The reconciler is documented as running approximately every 10 seconds.

Previously documented capabilities include:

* Scheduling pending workloads whose desired state is RUNNING.
* Retrying certain failed workloads whose desired state remains RUNNING.
* Querying Node Agent container status.
* Detecting stopped or missing containers.
* Updating workload state.
* Initiating recovery.
* Scheduling and executing replacement containers.

Inspect the current implementation before modifying this logic.

7.2 Previously Verified Results

During the 19 October 2026 development session:

1. A workload was running through CloudHeal.
2. Its container was deliberately stopped or removed.
3. The reconciliation/recovery path detected the stopped or missing container.
4. CloudHeal initiated recovery.
5. Docker independently confirmed that the replacement was running.
6. The workload returned to RUNNING.

One recorded recovery test used workload ID:

1b5b2f07-169a-47c8-a6c0-b1a0026f821e

A subsequent Docker start time was recorded as:

2026-10-19T19:11:42.747967761Z

The replacement container reported RestartCount=0 in the recorded inspection.

Separate recorded test runs reported:

* 14 passing tests.
* 24 passing tests.
* Four reconciler tests passing after a test-fixture adjustment.

These were separate runs. They must not be treated as proof that every test passes in the current working tree.

7.3 Outstanding Reconciliation Problem

A critical issue was identified: when the Control Plane cannot query a running workload’s Node Agent, communication errors such as timeouts may be ignored.

This prevents every temporary network interruption from triggering recovery, but an unreachable laptop can leave its workloads recorded as RUNNING indefinitely.

The next implementation must address sustained node unavailability without treating every failed HTTP request as proof that a container has stopped.

⸻

8. Revised Development Order

The previous roadmap placed several safety mechanisms too late. The revised plan treats persistence, node detection, leases, generations, and failover as dependent engineering milestones.

Phase 1 — Persistence and Event History

Implement SQLite persistence for:

* Node records and last heartbeat information.
* Workload records and desired/actual states.
* Placement generations.
* Execution and recovery events.

Record timestamped events for:

* Workload creation.
* Scheduling decisions.
* Node state transitions.
* Heartbeat timeouts.
* Failure detection.
* Recovery attempts.
* Execution results.
* Recovery verification.
* Recovery failures and retry decisions.

Persistence requirements

* Enable SQLite WAL mode.
* Use a controlled single-writer strategy for state changes.
* Use database transactions for related state updates.
* Make generation allocation atomic with the placement decision.
* Ensure concurrent recovery attempts cannot allocate the same generation.
* Preserve event history across Control Plane restarts.

At startup, reconcile persisted records with containers already running on registered nodes.

Adopt identifiable containers where appropriate instead of blindly creating replacements.

Container adoption must validate workload identity and placement generation where available. If a container cannot be safely identified, record the uncertainty rather than assuming it is safe to duplicate.

Completion criteria: Restart the Control Plane and verify that node/workload records and events persist, and existing containers are discovered or adopted correctly.

Phase 2 — Node Health and Failure Detection

Implement the node state machine:

HEALTHY → SUSPECT → UNAVAILABLE

Use heartbeat timestamps and a configurable timeout policy.

The state meanings are:

* HEALTHY: Recent communication and no detected failure.
* SUSPECT: Heartbeat or communication information has become stale.
* UNAVAILABLE: The failure-detection policy has determined that the node is no longer eligible for new placement and that recovery evaluation may begin.

A node becoming UNAVAILABLE does not prove that its containers have stopped.

Test:

* Recent heartbeat.
* Stale heartbeat.
* Delayed heartbeat.
* Agent termination.
* Temporary communication failure.
* Sustained node unavailability.
* Recovery after communication resumes.

Every node state transition should produce a timestamped event.

Start with a straightforward, measurable timeout policy. Evaluate adaptive failure detection later only if the baseline measurements justify it.

Phase 3 — Leases, Generations, and Failover

Treat leases, generation enforcement, and cross-node failover as one integrated safety milestone.

Implement and test them together before claiming safe failover.

A. Lease Protocol

The Control Plane grants and renews time-limited authority to Node Agents.

Let:

* D = lease duration.
* t_send = local monotonic time when the agent sends a heartbeat requesting renewal.
* M = explicit safety margin accounting for clock-rate uncertainty and implementation delays.

Protocol requirements:

1. A successful heartbeat reply renews the agent’s lease for duration D.
2. The agent starts its local expiry timer at t_send, not when the reply arrives.
3. The agent uses a monotonic clock for elapsed-time calculations.
4. A delayed reply must not extend the lease beyond the safe deadline derived from t_send.
5. If the lease expires, the agent self-fences: it stops or otherwise disables the workloads it is no longer authorized to run and refuses workload commands until authority is renewed.
6. The Control Plane must not authorize replacement execution before the previous authority is considered expired under the agreed timing model.
7. The Control Plane must account for clock-rate tolerance and message/processing delays. Do not rely on synchronized wall clocks alone.
8. After a long process pause, laptop sleep, or suspected clock discontinuity, the agent must re-confirm authority before continuing to serve workloads.
9. A successful renewal must be validated against the current lease/grant so delayed responses cannot restore obsolete authority.

Lease duration must be consistent with heartbeat timing and failure-detection policy. The timeout, lease duration, and safety margin must be explicitly defined and tested.

B. Important Lease Limitations

Lease expiry does not automatically guarantee that the old container has stopped.

Potential failures include:

* The Node Agent process crashes while its containers continue running.
* The laptop sleeps or freezes.
* A process pauses between checking its lease and performing an action.
* A partition prevents the agent from receiving renewal messages.
* The runtime remains active even after the agent loses contact.

Monotonic-clock behavior during sleep must be checked separately on macOS and Windows.

After a sufficiently long pause, the agent must re-confirm authority before continuing to serve workloads.

If the agent process dies and the container continues running, a replacement may overlap until stale execution is detected and fenced. The system must measure and report that possibility rather than claiming it cannot happen.

C. Placement Generations

Each workload placement receives a monotonically increasing generation number.

For example:

Workload W
Generation 1 → Node A
Generation 2 → Node B
Generation 3 → Node C

Requirements:

* Allocate generations atomically in the same transaction as the placement decision.
* Persist generation values in SQLite.
* Attach workload ID and generation labels to Docker containers.
* Include the generation in execution, status, stop, and recovery requests where applicable.
* Reject commands carrying older generations.
* Prevent an older placement from replacing a newer placement.
* Make repeated requests for the same placement safe to handle.
* Validate generation ownership before destructive operations.

A generation number is useful only if the agent enforces it. Storing it in the database or container labels is not fencing by itself.

The agent must reject stale commands based on authoritative, persisted placement information and must not allow delayed requests to reverse a newer placement.

D. Failover

When a node becomes unavailable:

1. Identify its affected workloads.
2. Confirm that each workload still has desired state RUNNING.
3. Check whether recovery is permitted under the current safety policy.
4. Select an eligible destination node with sufficient capacity.
5. Allocate a higher generation atomically.
6. Execute the new placement through the destination agent.
7. Verify the replacement’s container state and application health where supported.
8. Persist the outcome and timestamped events.
9. Handle timeouts and uncertain execution results without blindly issuing duplicate commands.
10. Record failed or blocked recovery decisions and their reasons.

Do not claim safe failover when fencing has not been implemented and verified.

E. Honest Safety Objective

The target for tested scenarios is:

* Stale commands are rejected.
* Old generations cannot overwrite newer placements.
* Duplicate-execution overlap is measured.
* Any observed overlap is reported.
* Failover decisions are based on explicit safety rules.

Zero duplicate execution is a goal for defined and tested scenarios, not a universal guarantee that can be inferred from lease expiry alone.

Phase 4 — Connect a Second Real Laptop

Begin second-laptop integration as early as practical, in parallel with persistence work where possible.

The Windows laptop is a major integration risk because Tailscale, Docker Desktop, Windows Firewall, and platform-specific behavior may differ from macOS.

Verify:

* Tailscale connectivity.
* Node registration.
* Heartbeat delivery.
* Control Plane-to-agent HTTP connectivity.
* Windows Docker execution.
* Remote container status.
* Resource reporting.
* Cross-node workload recovery.
* Partition and recovery behavior.

Two isolated agents on the Mac can help test APIs and scheduling, but they do not substitute for a real network-partition test between separate machines.

Phase 5 — Recovery Controls

Implement:

* Bounded retries.
* Exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling where appropriate.
* Clear failure and escalation states.

The system must avoid endlessly restarting failing workloads or overloading all remaining nodes during recovery.

Phase 6 — Experimental Baselines

Add configurable recovery policies so the same failure scenarios can be compared under different strategies.

Potential experimental modes:

1. No automated recovery.
2. Basic Docker restart behavior.
3. Fixed-timeout detection.
4. CloudHeal deterministic recovery.
5. Controlled immediate-rescheduling baseline.
6. Fencing-disabled baseline for isolated experiments only.
7. Unlimited-retry baseline for isolated experiments only.

Unsafe policies must be restricted to disposable test workloads and controlled environments. They must never silently become normal defaults.

Build an experiment runner that:

* Executes defined failure scenarios.
* Records timestamps and observed outcomes.
* Repeats each scenario.
* Captures the selected policy.
* Records failed and inconclusive trials.
* Produces comparable results.

Phase 7 — Stable Application Gateway

Add a stable URL for the demonstration application.

The gateway should route requests to the workload’s current location.

Keep routing separate from scheduling and recovery.

Test:

* Routing before failure.
* Routing after successful recovery.
* Behavior while recovery is in progress.
* Health-check failure.
* Stale destination information.
* Active connection behavior during failover.

A stable URL does not automatically preserve existing TCP connections, sessions, or application state.

Phase 8 — Evaluation

Compare baseline and CloudHeal behavior across repeated failure scenarios.

Measure:

Metric	Purpose
Detection time	Time required to identify a failure
Recovery time	Time required to restore the workload
Recovery success rate	Fraction of recoveries that succeed
False-positive rate	Incorrect failure detections
Unnecessary migrations	Workloads moved without sufficient justification
Duplicate execution	Whether multiple copies execute concurrently
Overlap duration	Duration of any duplicate execution
Retry count	Repeated work caused by failures
Cascade failures	Whether recovery overloads other nodes
Application downtime	Time the application is unavailable
AI diagnosis accuracy	Whether explanations match the evidence
Unsafe actions blocked	Whether policy checks prevent prohibited actions
Added latency	Additional delay from AI assistance
API cost	Cost of AI-assisted decisions

A target of approximately 20 repetitions per scenario is a useful initial goal when time and hardware permit it.

Report actual results. Distinguish measured results from estimates, expectations, and untested claims.

Phase 9 — AI-Assisted Diagnosis and Planning

Introduce AI only after the deterministic recovery path is reliable.

Diagnosis Agent

The diagnosis component may inspect:

* Container exit codes.
* Container logs.
* Heartbeat history.
* Resource measurements.
* Application health checks.
* Scheduling decisions.
* Recovery history.
* Previous failed attempts.

It should produce structured assessments that distinguish observed facts from hypotheses.

Recovery Planning Agent

The planning component may recommend a constrained action such as:

* Restart a stopped container.
* Reschedule a workload.
* Choose a node with sufficient capacity.
* Wait for a temporary problem to clear.
* Stop retrying a crash-looping workload.
* Escalate a failure that cannot be resolved safely.

Deterministic Safety Gate

The LLM must not be the security boundary.

Every proposed action must be checked against:

* An explicit action registry.
* Node eligibility.
* Resource constraints.
* Retry limits.
* Workload requirements.
* Recovery safety.
* Lease and generation rules.
* Approval requirements for sensitive actions.

Logs and external text are untrusted inputs. AI components must not receive unrestricted shell access or direct access to the Docker socket.

Record:

1. Evidence supplied.
2. Diagnosis or recommendation.
3. Policy decision.
4. Executed action.
5. Observed outcome.

The infrastructure must continue working if the model API is unavailable.

LangGraph may be introduced later if explicit stateful workflow orchestration provides a clear benefit.

A dashboard can be developed alongside later phases if it helps the demonstration, but it must not delay the recovery milestones.

⸻

9. SQLite and Persistence Design Requirements

SQLite is the initial persistence choice because CloudHeal is a small student platform and does not need a large distributed database.

The initial schema should cover these logical entities:

Nodes

* Node ID.
* Hostname and relevant metadata.
* Current health state.
* Last heartbeat timestamp.
* Runtime information.
* Last-known resource information.
* Lease/grant metadata where required.

Workloads

* Workload ID.
* Name and image.
* Desired state.
* Actual state.
* Current node assignment.
* Current placement generation.
* CPU and memory requirements.
* Creation/update timestamps.
* Recovery and retry metadata.

Placement History

* Workload ID.
* Generation.
* Assigned node.
* Placement status.
* Creation timestamp.
* Relevant lease/authority metadata.

Events

* Event ID.
* Event type.
* Node/workload identifiers where applicable.
* Generation where applicable.
* Timestamp.
* Structured event details.

Use database constraints and transactions to protect consistency.

Enable WAL mode and keep state-changing writes under a controlled single-writer strategy.

Do not assume WAL makes concurrent distributed writes safe by itself. Only the Control Plane should be responsible for the authoritative placement transaction.

Event history should be append-oriented. Corrections or state changes should produce additional events rather than silently erasing the record of what happened.

⸻

10. Resource-Scheduling Requirements

The scheduler must use clearly defined resource semantics.

For each node, distinguish:

* Host CPU and memory information.
* Runtime/VM CPU and memory limits.
* Allocatable capacity reserved for CloudHeal workloads.
* Existing CloudHeal allocations.
* Remaining schedulable capacity.

Do not subtract workload allocations from host physical RAM and then assume the result represents free Docker memory.

Inspect Docker’s actual limits on every supported platform.

Resource measurements may become stale. The scheduler should account for the timestamp of the latest report and avoid treating missing information as proof of unlimited capacity.

Capacity-aware recovery should reserve enough capacity to avoid making the remaining nodes unstable.

⸻

11. Current Verified Status

11.1 Previously Implemented or Verified

* Control Plane health endpoint.
* Node registration and lookup.
* Heartbeat processing.
* System/runtime information reporting.
* Workload creation and retrieval.
* Basic scheduling.
* Resource-aware scheduling logic.
* Scheduler-to-Node-Agent Docker execution integration.
* Periodic reconciliation.
* Container status queries.
* Detection of stopped or missing containers.
* Basic stopped/missing-container recovery.
* Replacement container verified running after recovery.
* Relevant automated test runs reported during earlier sessions.

These are historical results. Confirm current behavior and test output before relying on them.

11.2 Under Investigation

* Latest scheduler and recovery behavior.
* Handling of Node Agent timeouts.
* Distinguishing temporary communication failures from sustained node unavailability.
* Workload failover after a node becomes unavailable.
* Idempotent execution under uncertain HTTP outcomes.
* Runtime resource reporting and memory-limit semantics.

11.3 Not Yet Established as Complete

* SQLite persistence.
* Startup adoption/reconciliation of existing containers.
* Persisted placement generations.
* Lease renewal and expiry enforcement.
* Agent-enforced fencing.
* Reliable cross-node failover.
* Real network-partition verification.
* Duplicate-execution overlap measurement.
* Windows/macOS multi-laptop integration.
* Application health checks.
* Crash-loop backoff and retry limits.
* Recovery storm prevention.
* Stable application gateway.
* Experiment runner and comparative evaluation.
* AI diagnosis and recovery planning.
* Dashboard and final demonstration.

Do not mark these features complete until their relevant behavior has been implemented and tested.

⸻

12. Immediate Development Instructions

The next session should not begin by writing a new failover implementation immediately.

First establish the actual state of the repository.

Step 1 — Inspect the Working Tree

cd /Users/aniketsaini/Desktop/CloudHeal
source .venv/bin/activate
git status
git diff

Do not overwrite uncommitted changes.

Step 2 — Inspect the Relevant Implementation

cat control-plane/src/cloudheal_control_plane/registry.py
cat control-plane/src/cloudheal_control_plane/workloads/reconciler.py
cat control-plane/src/cloudheal_control_plane/workloads/scheduler.py
cat control-plane/src/cloudheal_control_plane/workloads/models.py
cat infrastructure/node-agent/src/cloudheal_node_agent/heartbeat.py
cat infrastructure/node-agent/src/cloudheal_node_agent/runtime.py

Inspect the current test locations and relevant fixtures.

Step 3 — Establish Current Test Results

Run the appropriate tests using the repository’s actual configuration.

Previously documented example:

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Adjust the command if the current test layout differs.

Inspect failures before modifying code.

Step 4 — Confirm the Current Recovery Behavior

Verify:

* How node health is calculated.
* How heartbeat timeouts are handled.
* How the reconciler handles agent communication failures.
* How a workload’s assigned node is stored.
* How containers are identified.
* How uncertain execution results are handled.
* Whether duplicate recovery attempts are possible.

Step 5 — Confirm the Persistence Design

Before coding, agree on:

* Initial SQLite schema.
* Transaction boundaries.
* Single-writer strategy.
* WAL configuration.
* Event structure.
* Placement generation allocation.
* Startup reconciliation/adoption behavior.

Step 6 — Implement Incrementally

Start with persistence and event history, then verify node detection and recovery safety in the revised development order.

Do not combine all phases into one large code change.

Step 7 — Use a Consistent Test Pattern

For each feature:

1. Inspect.
2. Implement the smallest appropriate change.
3. Run unit tests.
4. Run integration tests where possible.
5. Inspect actual Docker state.
6. Verify workload state.
7. Record the result.
8. Update project documentation after the milestone is confirmed.

⸻

13. Important Development Commands

Activate the environment:

cd /Users/aniketsaini/Desktop/CloudHeal
source .venv/bin/activate

Check the working tree:

git status

Check Control Plane health:

curl -s http://127.0.0.1:9000/health

List nodes:

curl -s http://127.0.0.1:9000/nodes

List workloads:

curl -s http://127.0.0.1:9000/workloads

Open API documentation:

http://127.0.0.1:9000/docs

Inspect running containers:

docker ps

Inspect all containers, including stopped ones:

docker ps -a

Use current repository configuration and current runtime information rather than assuming historical commands or addresses remain unchanged.

⸻

14. Project Coordination and Documentation

Maintain two forms of context.

Repository Context

CloudHeal_CONTEXT.md

This should contain:

* Project architecture.
* Repository-relative paths.
* Current implementation status.
* Verified milestones.
* Pending milestones.
* Important design decisions.
* Test commands teammates can run.
* Shared protocol and safety requirements.

Avoid making the repository context dependent on one person’s local addresses or machine-specific configuration.

Personal Development Notes

These may contain:

* Local startup commands.
* Machine-specific network addresses.
* Local environment details.
* Individual debugging notes.
* Current personal development tasks.

Before expanding the project scope, discuss the revised plan and evaluation expectations with the project guide.

The lease/fencing design should be reviewed by the team before implementation.

⸻

15. Minimum Final Scope

The minimum defensible final CloudHeal implementation should include:

1. Distributed workload execution across at least two real laptops.
2. Persistent workload state and timestamped event history.
3. Tested node health and suspect/unavailable detection.
4. Leases and agent-enforced fencing integrated with generation-based placement.
5. Safe, verified cross-node workload recovery.
6. Bounded retries and crash-loop protection.
7. Recovery concurrency/capacity controls.
8. A stable application URL across successful recovery.
9. Configurable baseline policies and a repeatable experiment runner.
10. Measured results across multiple failure scenarios.

AI diagnosis, AI-assisted recovery planning, adaptive failure detection, image-aware scheduling, and an advanced dashboard are additional features if time permits.

⸻

16. Final Project Direction

CloudHeal is a small distributed cloud platform that uses our team’s laptops as compute nodes.

The initial infrastructure for node management, scheduling, Docker execution, reconciliation, and basic stopped-container recovery has been established.

The next objective is to make recovery reliable when an entire laptop becomes unavailable.

That requires more than detecting a missed heartbeat. The system needs persistent state, explicit node-health transitions, safe placement decisions, lease handling, agent-enforced fencing, generation-based execution, and verification of the recovered workload.

The project must also account for resource limits, retries, recovery storms, and the possibility that an unreachable node is still executing its workload.

After the deterministic recovery path works reliably, AI can assist with ambiguous diagnosis and constrained recovery planning.

Guiding principle: Build the infrastructure, persist the state, define the protocol, enforce recovery safety, test real failures, measure the results, and then add AI where it genuinely helps.