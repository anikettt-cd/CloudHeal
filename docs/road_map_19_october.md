CloudHeal — Project Roadmap & Current Progress

CloudHeal is your college project: a lightweight, cloud-like platform that uses multiple laptops to run containerized workloads, monitor their health, schedule deployments, and eventually recover workloads when failures occur.

The goal is to demonstrate distributed workload execution, resource-aware scheduling, failure detection, and automatic recovery without the complexity of Kubernetes.

1. Where We Are Right Now

Current milestone: Core workload execution and failure detection — VERIFIED.

You have successfully tested the following on your MacBook:

* Control Plane API
* Node Agent registration and heartbeats
* Docker runtime integration
* Workload creation and scheduling
* CPU and memory-aware node selection
* Container execution
* Background reconciliation
* Failure detection when a running container stops

Your latest integration test confirmed this transition:

PENDING → RUNNING → FAILED

The container ran successfully, you stopped it manually, and the Control Plane detected the stopped container and updated its state to FAILED.

⸻

2. Complete Project Roadmap

This roadmap is organized around the actual CloudHeal implementation, not a generic cloud-platform checklist.

Phase 1 — Project foundation and infrastructure

Status: ✅ Completed

Task	Status
Establish the CloudHeal project structure	✅
Set up Python environment using uv	✅
Create the FastAPI Control Plane	✅
Create the Node Agent	✅
Integrate Docker runtime	✅
Configure communication between components	✅

What we achieved: The Control Plane and Node Agent can communicate, and the Node Agent can interact with Docker on the host machine.

Phase 2 — Node registration and monitoring

Status: ✅ Core functionality completed

Task	Status
Register nodes with the Control Plane	✅
Maintain node identity	✅
Send periodic heartbeats	✅
Collect CPU, memory, and disk information	✅
Report Docker runtime availability	✅
Expose node status through API endpoints	✅

Your MacBook currently registers as a healthy node.

The Control Plane receives information about the node’s operating system, architecture, CPU, memory, and Docker runtime.

Limitation: We have verified the Mac node, but the multi-laptop setup with Windows teammates still needs testing.

Phase 3 — Workload management

Status: ✅ Core functionality completed

Task	Status
Create workloads through the API	✅
Track desired and actual workload states	✅
Store workload records in the registry	✅
Assign workloads to nodes	✅
Expose workload information through API endpoints	✅

The workload model currently tracks:

* Workload ID and name
* Docker image
* Desired state
* Actual state
* Assigned node
* CPU limit
* Memory limit
* Creation and update timestamps

The registry is currently in memory, so workload records do not persist across Control Plane restarts.

Phase 4 — Resource-aware scheduling

Status: ✅ Initial implementation completed; further validation needed

Your scheduler now:

1. Retrieves registered nodes.
2. Filters unhealthy nodes.
3. Excludes nodes without an available Docker runtime.
4. Checks reported CPU and memory capacity.
5. Accounts for resources allocated to scheduled and running workloads.
6. Selects an eligible node based on remaining capacity.

The implementation prefers nodes with more remaining capacity relative to their reported resources.

Still needed: Validate scheduling decisions with multiple nodes and concurrent workloads, and account for the fact that reported resource capacity can change after scheduling.

Phase 5 — Actual workload execution

Status: ✅ Verified

This was an important milestone.

The scheduler doesn’t merely assign a workload to a node anymore. It sends an execution request to the Node Agent.

The Node Agent then requests container execution through Docker.

The Control Plane marks the workload RUNNING only when the agent confirms successful execution.

You verified this with the nginx:latest container.

Phase 6 — Failure detection and reconciliation

Status: ✅ Verified

Your Control Plane has a background reconciliation loop that runs approximately every 10 seconds.

The reconciler:

1. Examines workloads recorded as RUNNING.
2. Contacts the assigned Node Agent.
3. Checks the container’s status.
4. Marks the workload FAILED if the container has stopped or disappeared.
5. Leaves the workload unchanged if the status request fails, because a communication failure alone doesn’t prove that the container stopped.

Integration test completed successfully:

Event	Observed state
Workload created	PENDING
Container executed	RUNNING
Container manually stopped	Docker reports stopped
Reconciliation runs	Detects stopped container
Control Plane updates record	FAILED

You have verified the complete execution-to-failure-detection path.

Phase 7 — Automatic recovery

Status: 🔜 NEXT MAJOR MILESTONE

This is the next major feature to implement.

Currently, CloudHeal detects a failed workload, but detection does not automatically restore it.

The intended recovery workflow is:

1. Detect a failed workload.
2. Check whether its desired state remains RUNNING.
3. Identify a healthy, eligible node.
4. Attempt to restart the existing container or recreate it if necessary.
5. Verify that the container is actually running.
6. Update the workload’s actual state.
7. Retry safely if recovery fails.

We need to implement recovery with appropriate safeguards:

* Avoid creating duplicate containers.
* Limit repeated recovery attempts.
* Handle Node Agent communication failures.
* Handle a failed node and choose another eligible node.
* Preserve the distinction between desired state and actual state.

Completion criterion: When a running workload fails, CloudHeal detects the failure and automatically restores the workload to RUNNING, provided an eligible node is available.

Phase 8 — Multi-node cluster

Status: 🔜 Not yet verified

CloudHeal is intended to run across your MacBook and three Windows laptops.

Tasks:

* Connect the Windows Node Agents.
* Register all available nodes.
* Verify heartbeats from every node.
* Confirm that every node reports its own Docker capacity.
* Schedule workloads across different machines.
* Stop or disconnect one node and observe the platform’s behavior.
* Verify that recovery can use another healthy node.

This phase will demonstrate that CloudHeal operates as a distributed system rather than simply controlling Docker on one laptop.

Phase 9 — Persistent state and reliability

Status: 🔜 Planned

The current registries store nodes and workloads in memory.

For a more reliable platform, we should introduce persistent storage for:

* Node records
* Workload records
* Workload state transitions
* Recovery attempts
* Execution failures

We should also improve handling of Control Plane restarts, stale heartbeats, timeouts, and inconsistent execution states.

This phase matters because a workload should not become invisible simply because the Control Plane restarts.

Phase 10 — Demonstration and final validation

Status: 🔜 Planned

The final demonstration should show a complete scenario:

1. Start the Control Plane and multiple Node Agents.
2. Register the laptops as nodes.
3. Deploy an application container.
4. Show the selected node and workload status.
5. Stop the container to simulate a failure.
6. Demonstrate failure detection.
7. Demonstrate automatic recovery.
8. Show the workload returning to RUNNING.
9. Optionally disconnect a node and demonstrate recovery on another node.

For a stronger project demonstration, use a small web application instead of relying exclusively on Nginx.

⸻

3. Visual Progress Tracker

Here is the current milestone overview.

Phase	Milestone	Progress
1	Project foundation	✅ Completed
2	Node registration and monitoring	✅ Core functionality
3	Workload management	✅ Core functionality
4	Resource-aware scheduling	🟡 Implemented; validation needed
5	Actual Docker execution	✅ Verified
6	Failure detection	✅ Verified
7	Automatic recovery	🔜 Next
8	Multi-laptop cluster	🔜 Pending
9	Persistent state and reliability	🔜 Pending
10	Final integration and demonstration	🔜 Pending

The checkmarks reflect the implementation and tests we’ve discussed. They do not imply that every possible failure scenario has been validated.

⸻

4. What We Should Do Next

I recommend the following order.

Step 1 — Implement automatic recovery.

Build on the existing scheduler and reconciler. Do not rewrite them.

Step 2 — Test recovery locally.

Run Nginx, stop its container, and verify that CloudHeal automatically restores the workload to RUNNING.

Step 3 — Improve failure handling.

Test recovery failures, duplicate execution requests, and unavailable Node Agents.

Step 4 — Connect the three Windows laptops.

Verify multi-node registration and workload execution.

Step 5 — Test node failure and recovery.

Demonstrate that CloudHeal can detect a failed node and recover workloads on another eligible node.

Step 6 — Add persistence and finish the demonstration.

Store workload state reliably and prepare the final project walkthrough.

One important detail: before implementing automatic recovery, we should inspect the existing Node Agent container APIs and workload models. Recovery needs to be idempotent so that repeated reconciliation cycles don’t accidentally launch duplicate containers.

⸻

5. The Big Picture

Your current architecture consists of three main responsibilities:

* Control Plane: Maintains node and workload records, schedules workloads, and reconciles their states.
* Node Agent: Reports node information and executes container operations.
* Docker: Runs the actual application containers.

The next milestone transforms CloudHeal from a platform that can detect failure into one that can respond to it.

My recommendation: focus exclusively on automatic recovery next. Once that works reliably on your MacBook, move to multi-node execution and cross-node recovery. Those two capabilities will make the project demonstration substantially stronger.