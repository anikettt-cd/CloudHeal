CloudHeal — Revised Implementation Plan

Updated: 20 October 2026

1. Development Order

Phase 1 — Persistence and Event History

Implement SQLite persistence for:

* Node records and their last heartbeat.
* Workload records and desired/actual states.
* Placement generations.
* Timestamped execution and recovery events.

Record events such as workload creation, scheduling, heartbeat timeout, failure detection, recovery attempts, execution results, and recovery verification.

At Control Plane startup, reconcile persisted records with containers already running on registered nodes. Adopt identifiable containers rather than blindly creating replacements.

Phase 2 — Node Health and Failure Detection

Implement the node states:

HEALTHY → SUSPECT → UNAVAILABLE

Use heartbeat timestamps and a configurable timeout policy.

Temporary connectivity problems should not immediately trigger failover. Test detection behavior under delayed heartbeats, agent termination, and network interruptions.

Node-state transitions must produce timestamped events.

Phase 3 — Leases, Generations, and Failover Together

Treat these as one integrated milestone.

Leases

* The Control Plane grants and renews node leases.
* Lease duration must exceed the heartbeat timeout, with an explicit safety margin.
* Agents must stop or fence workloads when their authority expires.
* The protocol must account for delayed renewal messages and clock uncertainty.

Placement generations

* Every workload placement receives a monotonically increasing generation number.
* Store the workload ID and generation on the container as labels.
* Include the generation in execution, status, and recovery requests.
* Reject stale commands and prevent older generations from replacing newer placements.

Failover

* Detect sustained node unavailability.
* Determine whether recovery is safe.
* Select an eligible destination.
* Execute the new placement with a higher generation.
* Verify the replacement.
* Record the complete recovery outcome.

Do not claim zero duplicate execution until partition scenarios have been tested against the actual fencing implementation.

Phase 4 — Connect a Second Real Laptop

Connect a Windows laptop through Tailscale as soon as possible.

Verify:

* Node registration and heartbeat delivery.
* Control Plane-to-agent connectivity.
* Windows Docker execution.
* Remote container status.
* Cross-node workload recovery.
* Firewall and networking behavior.

For early development, two isolated agents on the Mac can help test scheduling and APIs, but they do not substitute for a real network-partition test across separate machines.

Phase 5 — Recovery Controls

Implement:

* Bounded retries and exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling where appropriate.

A failed workload should not consume resources indefinitely or overload every remaining node.

Phase 6 — Experimental Baselines

Introduce configurable recovery policies so the same scenarios can be compared under different strategies.

Potential modes:

* Fixed-timeout detection.
* Immediate rescheduling.
* Fencing disabled for controlled experiments.
* Unlimited retries as a deliberately unsafe baseline.

Unsafe modes must be isolated to disposable test workloads and a controlled test environment. They must never silently become production defaults.

Build an experiment runner that repeats defined scenarios and records results to the event log.

Phase 7 — Stable Application Gateway

Add a stable URL for the demonstration application.

The gateway should route requests to the workload’s current location so users can continue accessing the application after a successful migration.

Keep routing separate from scheduling and recovery. Verify what happens to active connections during failover; a stable URL does not automatically preserve existing sessions.

Phase 8 — Evaluation

Compare baseline and CloudHeal behavior across repeated failure scenarios.

Measure:

* Detection time.
* Recovery time.
* Recovery success rate.
* False-positive detections.
* Unnecessary migrations.
* Duplicate execution.
* Retry count.
* Cascade failures.
* Application downtime.

Report results from actual runs, not estimates.

Phase 9 — AI-Assisted Diagnosis and Planning

Only after the deterministic recovery path is reliable:

* Add an AI diagnosis agent.
* Add constrained recovery planning.
* Validate every proposed action through a deterministic safety gate.
* Record AI recommendations, policy decisions, and observed outcomes.
* Compare rules-only recovery with AI-assisted recovery.

The infrastructure must remain functional when the model API is unavailable.

A dashboard can be developed alongside later phases if it helps the demonstration, but it should not delay the recovery milestones.

2. Resource-Scheduling Correction

Do not assume a laptop’s physical RAM equals the memory available to containers.

On Docker Desktop, containers execute inside a Linux VM with its own resource configuration.

Inspect Docker’s actual memory constraints and runtime information on each supported platform. Define clearly whether reported memory represents host capacity, VM capacity, or remaining allocatable workload capacity.

Test scheduling decisions against the capacity the runtime can actually provide.

3. Minimum Final Scope

The minimum defensible final version should include:

1. Distributed workload execution across at least two real laptops.
2. Persistent workload state and timestamped event history.
3. Node failure detection with a tested suspect/unavailable policy.
4. Leases and enforced fencing integrated with generation-based placement.
5. Safe cross-node workload failover.
6. Crash-loop backoff and bounded retries.
7. Limits that prevent recovery from overwhelming remaining nodes.
8. A stable application URL across successful recovery.
9. Configurable baseline policies and a repeatable experiment runner.
10. Measured results across multiple failure scenarios.

AI agents, sophisticated adaptive failure detection, image-aware scheduling, and an advanced dashboard are additional features if time permits.

4. Documentation and Project Coordination

Maintain two forms of project context:

* Repository context: CloudHeal_CONTEXT.md, using relative repository paths and instructions teammates can follow.
* Personal development notes: Local commands, machine-specific addresses, and environment details that should not be assumed to apply to other teammates.

Before expanding the agreed project scope, confirm the revised direction and evaluation expectations with the project guide.