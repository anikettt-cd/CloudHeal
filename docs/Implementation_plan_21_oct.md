You’re right. We need to distinguish code implementation, testing, and verified completion. Yesterday’s plan is our source of truth; running tests and inspecting behavior doesn’t automatically mean we implemented a new feature.

1. Where CloudHeal stands right now

As of 21 October 2026, we’re working on the MacBook, with the Windows laptop still needing to be connected and verified.

The latest confirmed test result is:

uv run --package cloudheal-control-plane pytest control-plane/tests -q
23 passed in 0.33s

We also tested workload execution and inspected the scheduler and reconciler.

Our current position: We have a working foundation for workload scheduling, Docker execution, and basic container recovery. We’ve been testing the existing implementation and checking persistence-related behavior. We haven’t established that the entire persistence phase is complete, and we haven’t implemented the lease/fencing protocol or verified real cross-node recovery.

Current status by phase

Phase	Status	What we know
1. Persistence and Event History	🟡 Under development/testing	SQLite and event-recording code exist, but complete persistence and restart reconciliation aren’t verified.
2. Node Health and Failure Detection	⬜ Not implemented as specified	We have heartbeats, but the HEALTHY → SUSPECT → UNAVAILABLE policy isn’t established as complete.
3. Leases, Generations, and Failover	⬜ Not implemented as an integrated milestone	Lease enforcement, agent fencing, generation-based placement, and safe failover remain outstanding.
4. Second Real Laptop	🟡 Pending	The Windows laptop must be connected and its registration, execution, and networking verified.
5. Recovery Controls	🟡 Partially covered by existing behavior	Basic recovery exists; bounded retries, exponential backoff, crash-loop protection, and concurrency limits need verification and implementation.
6. Experimental Baselines	⬜ Not implemented	No verified experiment runner or comparative baseline results yet.
7. Stable Application Gateway	⬜ Not implemented	Stable routing across recovery remains future work.
8. Evaluation	⬜ Not implemented	No completed set of repeatable, measured failure experiments.
9. AI-Assisted Diagnosis and Planning	⬜ Not implemented	Deferred until deterministic recovery is reliable.

The Windows integration is a separate milestone in the roadmap, but we should start it now rather than wait until every persistence detail is finished.

⸻

2. What have we actually done?

Based on our recorded work, here’s the distinction.

Implemented and previously demonstrated

* Control Plane and Node Agent foundations.
* Node registration and heartbeat processing.
* Workload creation and scheduling.
* Scheduler-to-Agent Docker execution.
* Container status queries.
* Periodic reconciliation.
* Basic recovery from stopped or missing containers.
* SQLite database and event-recording code.

Tested during our recent sessions

* Scheduler behavior and execution results.
* Reconciler behavior.
* Failure cases, including unavailable or missing container status.
* Persistence and event-related test cases.
* Workload execution and actual Docker container state.

The latest recorded Control Plane test run passed 23 tests.

Not yet proven complete

* All node and workload state survives a Control Plane restart.
* Events cover the complete lifecycle.
* Existing containers are safely adopted after restart.
* Node failure detection distinguishes suspicion from sustained unavailability.
* Windows can execute workloads through CloudHeal.
* Cross-node recovery works between the Mac and Windows.
* Leases and fencing prevent stale commands from taking effect.
* Generations prevent old placements from replacing newer placements.

Important: We should not count a test of existing code as a newly implemented feature. Likewise, passing a persistence test doesn’t prove that all persistence requirements are satisfied.

⸻

3. Updated implementation plan

I’ve updated the plan below to reflect the current development position without claiming that testing alone completed a phase.

CloudHeal — Revised Implementation Plan

Updated: 21 October 2026
Current stage: Testing the existing Control Plane, workload execution, and persistence-related implementation.
Immediate priority: Connect and verify the Windows laptop as the second real node, while continuing to validate Phase 1.

1. Development Order and Current Status

Phase 1 — Persistence and Event History

Status: Partially implemented; testing and verification ongoing.

SQLite schema, persistence logic, and execution-event recording have been introduced. The latest Control Plane test suite passed 23 tests.

Remaining work:

* Verify node records and heartbeat information survive Control Plane restarts.
* Verify workload desired and actual states persist through creation, scheduling, execution, and recovery.
* Persist placement generations when generation-based placement is implemented.
* Record timestamped workload creation, scheduling, failure detection, recovery attempts, execution results, and recovery verification.
* Verify database transactions for related state changes and events.
* Verify WAL configuration and controlled state-changing writes.
* Reconcile persisted state with containers already running at startup.
* Adopt identifiable containers safely instead of blindly creating replacements.

Completion criteria: Restart the Control Plane and verify persisted node/workload state, event history, and correct discovery or adoption of existing containers.

Do not mark Phase 1 complete until these behaviors are tested.

Phase 2 — Node Health and Failure Detection

Status: Not implemented to the full specification.

Existing heartbeat processing provides a foundation, but the required health state machine remains outstanding.

Implement:

HEALTHY → SUSPECT → UNAVAILABLE

Requirements:

* Use heartbeat timestamps and configurable timeouts.
* Distinguish temporary communication problems from sustained unavailability.
* Record timestamped node-state transitions.
* Test delayed heartbeats, agent termination, network interruption, and recovery after connectivity returns.
* Prevent an ordinary HTTP timeout from immediately triggering unsafe failover.

Completion criteria: Demonstrate the expected state transitions using controlled tests and verify the corresponding events.

Phase 3 — Leases, Generations, and Failover Together

Status: Not implemented as an integrated safety protocol.

Implement these components together rather than treating them as independent features.

Leases

* Control Plane grants and renews execution authority.
* Lease duration exceeds the heartbeat timeout with an explicit safety margin.
* Agents enforce lease expiry.
* Delayed renewal responses and clock uncertainty are handled safely.
* Agents revalidate authority after prolonged pauses or laptop sleep.
* Expired authority prevents stale workload commands from taking effect.

Placement generations

* Every placement receives a monotonically increasing generation.
* Generation allocation is persisted and atomic.
* Containers are labelled with workload ID and generation.
* Execution, status, and recovery operations validate generation.
* Stale commands are rejected.
* Older placements cannot overwrite newer placements.

Failover

* Identify affected workloads when a node becomes unavailable.
* Confirm that desired state remains RUNNING.
* Evaluate whether recovery is safe.
* Select an eligible destination.
* Allocate a higher generation.
* Execute and verify the replacement.
* Record the complete recovery outcome.
* Handle uncertain execution results without blindly creating duplicates.

Completion criteria: Demonstrate lease enforcement, stale-command rejection, generation protection, and cross-node recovery in controlled failure and network-partition tests.

Do not claim zero duplicate execution without evidence from the actual fencing implementation.

Phase 4 — Connect a Second Real Laptop

Status: Pending verification. Immediate priority.

Connect the Windows laptop through Tailscale as the second real compute node.

Verify:

* Tailscale connectivity between laptops.
* Node registration and heartbeat delivery.
* Control Plane-to-Agent HTTP connectivity.
* Windows Docker execution.
* Remote container status.
* Runtime resource reporting.
* Firewall and networking behavior.
* Workload execution on both laptops.
* Controlled cross-node recovery.

Reuse the existing Node Agent implementation wherever possible.

This phase begins now because Windows integration is an important platform and networking risk. It does not replace the need to finish persistence and recovery safety.

Phase 5 — Recovery Controls

Status: Partially covered by existing recovery behavior; remaining requirements unverified.

Implement and test:

* Bounded retries.
* Exponential backoff.
* Crash-loop detection.
* Limits on concurrent recovery operations.
* Capacity-aware recovery.
* Recovery priorities or staggered scheduling.
* Clear failure and escalation states.

A failing workload must not consume resources indefinitely or overload remaining nodes.

Phase 6 — Experimental Baselines

Status: Not implemented.

Introduce configurable recovery policies, including:

* Fixed-timeout detection.
* Immediate rescheduling.
* Fencing disabled for controlled experiments.
* Unlimited retries as a deliberately unsafe baseline.

Unsafe modes must be restricted to disposable test workloads.

Build an experiment runner that repeats defined scenarios and records timestamps, selected policies, failures, and observed outcomes.

Phase 7 — Stable Application Gateway

Status: Not implemented.

Provide a stable URL for the demonstration application.

Route requests to the workload’s current location while keeping routing separate from scheduling and recovery.

Test behavior before failure, during recovery, and after successful recovery. Document the effect on active connections and application sessions.

Phase 8 — Evaluation

Status: Not implemented.

Compare baseline and CloudHeal behavior across repeated failure scenarios.

Measure:

* Detection time.
* Recovery time.
* Recovery success rate.
* False-positive detections.
* Unnecessary migrations.
* Duplicate execution and overlap duration.
* Retry count.
* Cascade failures.
* Application downtime.

Report actual measurements rather than estimates.

Phase 9 — AI-Assisted Diagnosis and Planning

Status: Deferred.

After deterministic recovery is reliable:

* Introduce an AI diagnosis agent.
* Add constrained recovery planning.
* Validate proposed actions through a deterministic safety gate.
* Record recommendations, policy decisions, and observed outcomes.
* Compare rules-only recovery with AI-assisted recovery.

The infrastructure must continue operating when the model API is unavailable.

2. Resource-Scheduling Correction

Do not assume host physical RAM equals the memory available to Docker containers.

On Docker Desktop, containers run inside a Linux VM with its own resource configuration.

Inspect runtime memory limits and available capacity on both macOS and Windows.

Distinguish host capacity, VM/runtime capacity, existing workload allocations, and CloudHeal’s remaining allocatable capacity.

Verify scheduling decisions against the capacity the runtime can actually provide.

3. Minimum Final Scope

The final implementation must demonstrate:

1. Distributed workload execution across at least two real laptops.
2. Persistent workload state and timestamped event history.
3. Tested node health and suspect/unavailable detection.
4. Leases and enforced fencing integrated with generation-based placement.
5. Safe, verified cross-node workload recovery.
6. Crash-loop backoff and bounded retries.
7. Recovery concurrency and capacity controls.
8. A stable application URL across successful recovery.
9. Configurable baseline policies and a repeatable experiment runner.
10. Measured results across multiple failure scenarios.

AI agents, sophisticated adaptive failure detection, image-aware scheduling, and an advanced dashboard remain optional extensions if time permits.

4. Immediate Next Actions

1. Inspect the current Git working tree and preserve uncommitted changes.
2. Confirm the current test results.
3. Start or verify the Mac Control Plane and Node Agent.
4. Verify the Windows Tailscale address and Docker installation.
5. Establish Windows-to-Mac connectivity.
6. Configure and start the Windows Node Agent.
7. Verify registration and heartbeats.
8. Execute a test workload on Windows.
9. Verify the real container state and reported workload state.
10. Continue Phase 1 persistence verification.
11. Proceed to node health detection.
12. Implement leases, generations, and fencing together before claiming safe failover.

After each milestone, update the repository context with the exact implementation changes and test evidence.

Maintain repository documentation separately from machine-specific personal development notes.

⸻

4. What should we do next?

I recommend we connect Windows now, rather than spend another session repeatedly testing the Mac-only setup.

Our next immediate task is:

1. Verify the Control Plane is running on the Mac.
2. Verify the Windows laptop’s Tailscale connection and Docker installation.
3. Establish connectivity between the two machines.
4. Start the existing Node Agent on Windows.
5. Confirm that both nodes appear in GET /nodes.

Once that’s working, we can test actual distributed execution.

One clarification: The plan above is updated in this response, but I haven’t changed the local CloudHeal_CONTEXT.md or source files. We should update the repository documentation when the corresponding changes are made and verified.