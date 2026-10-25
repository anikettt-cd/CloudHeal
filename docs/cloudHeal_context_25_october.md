CloudHeal — Complete Project Context & Revised Implementation Roadmap

Last updated: 25 October 2026
Project stage: Existing distributed execution foundation implemented and tested across Mac and Windows laptops. Kubernetes-backed architecture agreed; migration and integration not yet implemented.
Latest recorded automated test result: 34 Control Plane tests passed in 0.44 seconds.
Latest recorded code-quality check: git diff --check passed.
Immediate priority: Inspect the actual repository, preserve existing changes, finalize the architecture, and evaluate a practical Kubernetes environment before implementing further infrastructure features.
Development environment: MacBook Air running macOS, three Windows laptops across the team, Python, FastAPI, uv, Docker Desktop, and Tailscale.

⸻

1. Project Vision

1.1 What Is CloudHeal?

CloudHeal is our own private-cloud management and intelligent self-healing platform.

We are building it because we need infrastructure on which to deploy and run applications and services for our project demonstration. Our initial infrastructure consists of three Windows laptops and one MacBook Air.

However, CloudHeal is not intended to remain permanently dependent on these four machines. The longer-term goal is to connect CloudHeal to supported external infrastructure and cloud providers so that it can manage infrastructure through a common interface.

The central architectural decision is to use established infrastructure technologies wherever they already solve a problem well, rather than spending our time rebuilding them.

For standard container orchestration, we can use Kubernetes. Our original engineering contribution will be CloudHeal’s higher-level self-healing intelligence, deterministic policies, safe remediation, verification, incident history, and eventual AI-assisted diagnosis.

CloudHeal should be independently deployable and logically separate from the infrastructure it manages.

1.2 Core Objective

CloudHeal should be able to:

1. Connect to supported infrastructure.
2. Observe applications, workloads, and infrastructure health.
3. Detect and classify failures.
4. Correlate related incidents and observations.
5. Gather evidence and diagnose likely causes.
6. Evaluate possible remediation actions against deterministic policies.
7. Reject unsafe or unsupported actions.
8. Execute approved actions through infrastructure adapters.
9. Independently verify whether remediation succeeded.
10. Maintain persistent incident, decision, and action history.
11. Apply appropriate recovery limits and prevent uncontrolled repeated actions.
12. Measure recovery performance and compare it against meaningful baselines.
13. Introduce AI-assisted diagnosis and constrained planning without making the system dependent on AI availability.

A dashboard, chatbot, or collection of AI-generated recommendations alone is not sufficient to demonstrate CloudHeal’s contribution.

1.3 The Main Architectural Principle

Use Kubernetes for orchestration. Build CloudHeal as the independent management and self-healing intelligence layer that works with Kubernetes and, eventually, other infrastructure providers.

We should not build duplicate versions of functionality already supplied by Kubernetes unless a clearly justified requirement demonstrates a genuine gap.

⸻

2. The Four-Machine Development Environment

Our initial infrastructure is:

* One MacBook Air.
* Three Windows laptops.
* Private connectivity using Tailscale.
* Docker-based development and execution where appropriate.
* A suitable Kubernetes environment to be selected and validated.

These machines provide our initial private infrastructure for developing, deploying, and demonstrating CloudHeal.

They are not the permanent definition of the CloudHeal architecture.

2.1 What the Initial Environment Must Demonstrate

We should be able to:

1. Connect CloudHeal to the environment.
2. Deploy a test application.
3. Observe its state.
4. Introduce a controlled failure.
5. Detect and classify the incident.
6. Evaluate a remediation action.
7. Execute an approved action.
8. Verify recovery.
9. Record the incident and outcome.
10. Measure actual recovery behavior.

The environment must be repeatable enough for teammates and project evaluators to reproduce the demonstration.

2.2 Kubernetes Environment Selection

The local Kubernetes setup has not yet been finalized.

Before choosing a distribution or installation approach, evaluate:

* macOS and Windows compatibility.
* Available CPU and memory.
* Docker Desktop compatibility.
* Private-network connectivity.
* Multi-machine requirements.
* Installation and maintenance effort.
* Repeatability across teammates’ machines.
* Ease of workload deployment and controlled failure testing.

Running Docker Desktop on Windows does not automatically make a Windows laptop a supported Kubernetes worker node. Kubernetes has specific Windows worker-node requirements, so the cluster topology must be chosen based on the actual environment.

Do not assume all four laptops must immediately join one Kubernetes cluster. Evaluate the simplest configuration that supports the demonstration and the project’s learning objectives.

⸻

3. What Kubernetes Will Handle

Kubernetes already provides standard orchestration capabilities.

CloudHeal should leverage these capabilities where appropriate.

Capability	Intended responsibility
Container scheduling	Kubernetes
Container lifecycle management	Kubernetes
Desired-state reconciliation	Kubernetes
Ordinary container restart behavior	Kubernetes
Standard workload rescheduling	Kubernetes
Workload and node status	Kubernetes
Services and workload networking abstractions	Kubernetes
Storage abstractions, where configured	Kubernetes
Declarative workload management	Kubernetes
Higher-level incident classification	CloudHeal
Correlation of related failures	CloudHeal
Diagnostic evidence collection and interpretation	CloudHeal
Deterministic remediation policy	CloudHeal
Safety checks and action authorization	CloudHeal
Higher-level recovery coordination	CloudHeal
Independent recovery verification	CloudHeal
Incident history and audit records	CloudHeal
Recovery metrics and experimental evaluation	CloudHeal
AI-assisted diagnosis and constrained planning	CloudHeal

This table describes the intended division of responsibility, not a claim that every component has already been implemented.

Some capabilities overlap. For example, Kubernetes can restart a failed container, but CloudHeal may need to recognize a recurring crash loop, correlate it with an application-level failure, and decide whether a higher-level action should be attempted or escalated.

We must define those boundaries explicitly.

Kubernetes is an orchestration platform, not a complete cloud provider. CloudHeal may also require infrastructure integrations for compute provisioning, networking, storage, access management, and other services, depending on the final scope.

⸻

4. Intended CloudHeal Architecture

The target architecture contains three main logical parts.

4.1 Self-Healing Core

This is CloudHeal’s infrastructure-independent decision-making layer.

Responsibilities include:

* Processing observations.
* Detecting abnormal conditions.
* Classifying failures.
* Correlating incidents.
* Managing diagnostic evidence.
* Evaluating remediation candidates.
* Applying deterministic policies.
* Authorizing or rejecting actions.
* Tracking remediation attempts.
* Verifying outcomes.
* Maintaining incident and decision history.
* Calculating recovery metrics.

The core should avoid depending directly on Kubernetes-specific objects and API details throughout its business logic.

It must continue to perform its deterministic responsibilities if an AI model API is unavailable.

4.2 Infrastructure Adapter Layer

Adapters translate between CloudHeal’s internal interfaces and the infrastructure systems it manages.

The first adapter will target Kubernetes.

Potential future adapters include AWS or another provider, depending on project requirements.

Conceptually:

CloudHeal Self-Healing Core → Infrastructure Adapter → Target Infrastructure

Examples:

* CloudHeal → Kubernetes adapter → Kubernetes API.
* CloudHeal → future AWS adapter → supported AWS APIs.
* CloudHeal → future private-infrastructure adapter → supported infrastructure interfaces.

The exact interfaces must be designed after inspecting the current repository and validating the initial Kubernetes environment.

Each adapter must explicitly expose its supported operations and limitations. We must not assume every provider supports identical actions or resource models.

Adapters should use the target infrastructure’s supported APIs rather than directly manipulating containers through the Docker socket when those workloads are managed by Kubernetes.

4.3 AI-Assisted Intelligence Layer

The AI layer will be introduced after the deterministic workflow is established.

Potential responsibilities:

* Analyzing application logs and infrastructure events.
* Summarizing incident evidence.
* Identifying likely root causes.
* Retrieving relevant historical incidents and runbooks.
* Proposing constrained remediation plans.
* Explaining why an action failed.
* Comparing candidate actions and their risks.

AI recommendations must always pass through CloudHeal’s deterministic policy and authorization layer.

The AI layer must not have unrestricted shell access, unrestricted Docker socket access, or independent authority to execute arbitrary infrastructure operations.

⸻

5. Intended Self-Healing Workflow

The initial end-to-end workflow is:

Observe → Classify → Gather Evidence → Evaluate Policy → Remediate → Verify → Record

Step 1: Observe

Collect actual infrastructure and application observations through the appropriate adapter.

Examples include workload status, infrastructure events, health-check results, and permitted log evidence.

Step 2: Classify

Convert the observations into a structured incident.

The incident should identify the affected resource, observed failure, relevant timestamps, and current confidence or uncertainty.

Step 3: Gather Evidence

Collect the evidence needed to determine what happened and whether an action is justified.

Evidence collection should be bounded and permission-controlled.

Step 4: Evaluate Policy

Evaluate the proposed action against deterministic rules.

Possible checks include:

* Is the action supported?
* Is the target resource valid?
* Does CloudHeal have permission?
* Is the action appropriate for the incident?
* Has the recovery attempt limit been reached?
* Is a cooldown active?
* Could the action create conflicting execution?
* Is additional approval required?
* Can the outcome be verified?

Step 5: Remediate

Execute only approved actions through the relevant infrastructure adapter.

A request being accepted does not mean the action completed.

Step 6: Verify

Observe the infrastructure after the action and determine whether the intended result was achieved.

Where necessary, combine infrastructure state with application-level health checks.

Step 7: Record

Persist the observations, evidence references, incident classification, policy decision, action, execution result, verification result, and relevant timestamps.

This workflow should be deterministic and demonstrable before we introduce autonomous AI planning.

⸻

6. Safety and Reliability Requirements

6.1 Deterministic Authorization

AI agents cannot authorize their own recommendations.

All infrastructure actions must pass through a deterministic policy and authorization layer.

6.2 Least Privilege

CloudHeal must use only the permissions required for its configured responsibilities.

The Kubernetes adapter must not receive unrestricted cluster-admin permissions by default.

6.3 No Unrestricted Execution

AI agents must not have unrestricted shell execution or unrestricted Docker socket access.

Use explicitly supported, structured operations with clear permissions and target validation.

6.4 Uncertain Outcomes

An API response or timeout must not automatically be interpreted as proof of success or failure.

The implementation should distinguish between states such as:

* Rejected.
* Accepted.
* Executing.
* Completed.
* Verified successful.
* Failed.
* Unknown or inconclusive.

The precise state model should be designed for the initial implementation.

6.5 Independent Verification

A desired state being recorded does not necessarily mean the application is healthy.

Verification should use evidence appropriate to the action, such as workload readiness, container health, endpoint availability, or application-specific health checks.

6.6 Avoid Duplicate Recovery

A heartbeat timeout or loss of contact does not prove that the workload has terminated.

CloudHeal must avoid unsafe recovery decisions based on incomplete evidence. It should account for concurrent actions, uncertain outcomes, and the possibility that an original workload is still running.

6.7 AI API Independence

The deterministic self-healing workflow must continue to operate when the AI provider is unavailable.

AI may improve diagnosis and planning, but it must not be a mandatory dependency for basic infrastructure observation, policy enforcement, or supported deterministic remediation.

⸻

7. Existing Repository and Implementation

7.1 Repository Location

Previously recorded Mac repository:

/Users/aniketsaini/Desktop/CloudHeal

Development commands:

cd ~/Desktop/CloudHeal
source .venv/bin/activate

The project uses uv.

Always inspect the current working tree before editing:

git status --short
git diff --check
git diff

Do not assume the repository structure or working tree remains identical to historical records.

7.2 Existing Control Plane

Package:

cloudheal-control-plane

Previously configured port: 9000.

The existing implementation includes functionality for:

* Node registration and lookup.
* Heartbeat processing.
* Node health tracking.
* Workload records.
* Scheduling.
* Remote Node Agent communication.
* Execution-result handling.
* Workload reconciliation.
* SQLite persistence.
* Event recording.

The Control Plane belongs to the existing custom orchestration design. Its future responsibilities must be reviewed against the revised CloudHeal architecture.

Some existing Control Plane functionality may be reusable as the foundation for CloudHeal’s management API, event processing, persistence, or self-healing coordination.

7.3 Existing Node Agent

Package:

cloudheal-node-agent

Previously configured port: 8000.

The existing implementation includes:

* Persistent node identity.
* Node registration.
* Heartbeats.
* System information reporting.
* Docker runtime reporting.
* Container execution.
* Container status queries.

Its long-term role is not yet finalized.

Do not delete or rewrite the Node Agent before evaluating whether any functionality remains useful for infrastructure discovery, development tooling, or future adapters.

Ordinary Kubernetes-managed container lifecycle operations should use Kubernetes APIs instead of creating a competing execution mechanism.

7.4 Existing Scheduler and Reconciler

The previous architecture includes a custom scheduler and periodic reconciler.

The scheduler selects nodes and coordinates workload execution through Node Agents.

The reconciler checks workload state and performs recovery-related actions.

These components must be evaluated carefully because Kubernetes already provides standard scheduling and desired-state reconciliation.

Do not automatically invest further effort in a custom scheduler, container-restart engine, or cross-node workload failover mechanism.

Reuse, adapt, retain temporarily, or retire components only after examining the actual implementation and the migration requirements.

7.5 Existing SQLite Persistence

SQLite has been integrated into the existing Control Plane.

The implementation includes node-, workload-, and event-related persistence.

Persistence and event history are partially implemented and have not been fully verified across every lifecycle and restart scenario.

CloudHeal will continue to need persistence for its own responsibilities, including:

* Incidents.
* Diagnostic evidence references.
* Policy decisions.
* Remediation attempts.
* Execution outcomes.
* Verification results.
* Audit history.
* Evaluation metrics.

Do not expand the old custom orchestration persistence extensively until we have established which state belongs to CloudHeal and which state should be managed by Kubernetes.

⸻

8. Existing Infrastructure and Historical Machine Information

The following information is historical and must be reverified before use.

8.1 Mac Development Machine

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

Do not assume any of these addresses are current.

8.2 Windows Development Machine

Property	Historical value
Node ID	fb296fa6-f82d-463f-8850-aef301495d70
Hostname	DESKTOP-G3S6QHM
Tailscale IP	100.127.235.82
Operating system	Windows
Architecture	AMD64
Physical CPU cores	4
Logical CPU cores	8
Reported physical memory	Approximately 8.32 GB
Docker version	29.8.2

Actual current resource availability must be checked before capacity-sensitive experiments.

These details describe one historically recorded Windows machine; they do not represent verified current details for all three Windows laptops.

8.3 Multi-Node Integration Status

The existing custom execution system has already progressed beyond the initial connection stage.

Previously demonstrated behavior includes:

* Windows-to-Mac Control Plane connectivity.
* Registration of the Mac and Windows nodes.
* Node heartbeats.
* Windows workload execution through the existing Node Agent.
* Basic recovery from a stopped Windows container.

This is useful evidence of multi-machine execution in the existing architecture.

It does not establish Kubernetes integration, production-grade failover safety, or correctness under arbitrary network partitions.

Do not restart the Windows integration phase from scratch unless new evidence indicates a regression.

⸻

9. Recent Implementation Changes to Preserve

9.1 Node Availability Detection

Recent changes added node availability tracking to the existing custom Control Plane.

Previously recorded behavior includes:

* A configured heartbeat timeout of 30 seconds.
* Refreshing node status during get_nodes() and get_node() calls.
* Marking nodes unhealthy when the timeout policy is exceeded.
* Recording NODE_BECAME_UNHEALTHY.
* Recording NODE_BECAME_HEALTHY when connectivity recovers.
* Suppressing duplicate transition events based on the most recent recorded event.

These changes must be preserved while reviewing the revised architecture.

9.2 Reconciler Availability Handling

The existing reconciler was updated to handle workloads assigned to unavailable nodes.

Recorded behavior includes:

* Recording WORKLOAD_NODE_UNAVAILABLE.
* Skipping ordinary container-status and recovery checks while the assigned node is unavailable.
* Recording WORKLOAD_NODE_AVAILABLE when the node becomes healthy again.
* Resuming ordinary checks after communication is restored.

The important safety property is that node unavailability is not treated as proof that the workload has terminated.

The existing implementation does not automatically migrate a workload solely because the assigned node becomes unreachable.

Preserve this safety property when designing future remediation.

9.3 Modified Files to Preserve

The latest recorded uncommitted changes include:

M control-plane/src/cloudheal_control_plane/registry.py
M control-plane/src/cloudheal_control_plane/workloads/reconciler.py
M control-plane/tests/test_node_registry.py
M control-plane/tests/test_reconciler.py

These files must not be overwritten or discarded.

The current working tree must be inspected before every meaningful editing session because additional modifications may exist.

Do not reset, delete, or commit changes unless explicitly requested.

⸻

10. Existing Workload Execution and Recovery Evidence

10.1 Historical Recovery Demonstration

A previously recorded workload used ID:

1b5b2f07-169a-47c8-a6c0-b1a0026f821e

The recorded replacement start time was:

2026-10-19T19:11:42.747967761Z

The replacement container reported RestartCount=0.

This demonstrated basic stopped/missing-container recovery in the previous architecture.

It did not demonstrate safe cross-node failover under arbitrary network partitions.

10.2 Historical Execution Demonstration

A workload named event-test was recorded as running on the Mac.

Property	Recorded value
Workload ID	ff02cc16-e20b-43a6-a41c-62fc996dd3b9
Image	nginx:latest
Desired state	RUNNING
Actual state	RUNNING
Assigned node	83a1f6f3-9bbc-4e1f-8566-5080aef7d7ed

This verifies execution at the recorded time only.

10.3 Historical Automated Tests

The latest recorded command was:

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Recorded result:

34 passed in 0.44s

The following command also completed without reported errors:

git diff --check

These are historical results. Rerun relevant checks after subsequent code changes.

⸻

11. Revised Implementation Roadmap

The phases below describe the intended future work. They are not claims that the new architecture has already been implemented.

Phase 1 — Repository and Architecture Validation

Status: Immediate next priority.

Tasks:

1. Inspect the actual repository and working tree.
2. Preserve all uncommitted modifications.
3. Read the existing project specification and context documentation.
4. Map the Control Plane, Node Agent, scheduler, reconciler, database, event system, and tests.
5. Identify capabilities Kubernetes can replace.
6. Identify reusable components for CloudHeal’s self-healing core.
7. Define the core/adapter boundary.
8. Document the intended architecture and migration plan.

Acceptance criteria:

* The current implementation is accurately documented.
* The new architecture explicitly assigns responsibilities.
* Existing changes remain intact.
* The migration plan avoids unnecessary rewrites.
* Existing and planned functionality are clearly distinguished.

Phase 2 — Select and Validate a Local Kubernetes Environment

Status: Not yet established.

Tasks:

1. Evaluate practical Kubernetes options for the Mac and Windows team.
2. Check hardware and memory constraints.
3. Verify networking and teammate access requirements.
4. Select a repeatable development setup.
5. Deploy a test workload.
6. Query its state.
7. Introduce and observe a controlled failure.
8. Document setup and troubleshooting steps.

Acceptance criteria:

* The environment can be recreated.
* A test workload can be deployed and inspected.
* A controlled failure can be observed.
* The team has documented setup instructions.

Phase 3 — Define the Self-Healing Core and Adapter Contract

Status: Planned.

Define infrastructure-independent interfaces for:

* Observations.
* Incidents.
* Diagnostic evidence.
* Remediation recommendations.
* Policy decisions.
* Action execution.
* Verification results.
* Audit records.

Design the first Kubernetes adapter around these interfaces.

Acceptance criteria:

* The core processes a structured incident.
* The adapter retrieves required observations.
* The adapter executes explicitly permitted actions.
* Results have consistent, structured representations.
* Unsupported operations are handled explicitly.

Phase 4 — Implement the Deterministic Self-Healing Workflow

Status: Planned.

Implement:

Observe → Classify → Gather Evidence → Evaluate Policy → Remediate → Verify → Record

Start with a small set of supported failure types and remediation actions.

Acceptance criteria:

* A controlled failure produces a structured incident.
* The core classifies the incident.
* A permitted action passes the policy gate.
* A prohibited action is rejected.
* The approved action is executed through the adapter.
* Recovery is independently verified.
* The complete process is recorded.

Do not introduce unrestricted autonomous AI at this stage.

Phase 5 — Persistence, Audit History, and Recovery Controls

Status: Existing SQLite foundation; completeness requires review.

Persist:

* Incident records.
* Evidence references.
* Policy decisions.
* Remediation attempts.
* Execution outcomes.
* Verification results.
* Timestamps and durations.
* Failure and escalation states.

Implement recovery controls where the underlying infrastructure does not already provide the required behavior.

Possible controls:

* Bounded remediation attempts.
* Backoff.
* Cooldowns.
* Crash-loop recognition.
* Limits on concurrent remediation.
* Capacity checks.
* Escalation when recovery fails.

Acceptance criteria:

* Incident history survives service restarts.
* Related records remain consistent.
* Duplicate events and concurrent actions are handled deliberately.
* Recovery limits prevent uncontrolled repeated actions.
* Failed and inconclusive recovery attempts are recorded.

Do not duplicate Kubernetes’ normal retry and restart mechanisms without a clear reason.

Phase 6 — Experimental Evaluation and Baselines

Status: Planned.

Compare repeatable experiments such as:

1. Kubernetes-native behavior without CloudHeal remediation.
2. CloudHeal observation and alerting only.
3. Deterministic CloudHeal remediation.
4. Alternative deterministic policies.
5. AI-assisted diagnosis compared with deterministic diagnosis, when available.

Measure actual outcomes, including:

* Failure detection time.
* Recovery duration.
* Application downtime.
* Recovery success rate.
* False-positive rate.
* Repeated or unnecessary remediation.
* Rejected unsafe actions.
* Failed and inconclusive attempts.

Acceptance criteria:

* Experiments are reproducible.
* Each trial records its configuration and outcome.
* Metrics use observed timestamps and results.
* Failed trials are retained.
* CloudHeal’s contribution is evaluated against a meaningful baseline.

Phase 7 — Stable Application Access

Status: Architecture decision pending.

Evaluate whether Kubernetes-native networking and existing gateway options are sufficient.

Do not automatically build a custom gateway before evaluating existing capabilities.

If additional CloudHeal routing functionality is justified, define its responsibilities and integration boundary.

Test:

* Application access before failure.
* Access during recovery.
* Access after recovery.
* Unhealthy application handling.
* Stale routing information.
* Active connections and session behavior.

A stable URL does not guarantee uninterrupted connections or preservation of application state.

Phase 8 — AI-Assisted Diagnosis and Constrained Planning

Status: Deferred until the deterministic workflow is reliable.

Potential inputs:

* Application logs.
* Kubernetes events.
* Workload and node status.
* Resource observations.
* Application health checks.
* Incident history.
* Previous remediation attempts.

Potential outputs:

* Likely failure causes.
* Evidence summaries.
* Constrained remediation recommendations.
* Explanations of failed recovery.
* Comparisons of candidate actions and risks.

Every proposed action must pass the deterministic safety gate.

Acceptance criteria:

* Recommendations are recorded with their supporting evidence.
* Policy decisions are auditable.
* Unsupported actions are rejected.
* Recommendations are evaluated against actual outcomes.
* Basic deterministic operation remains available without an AI provider.

Phase 9 — Multi-Provider Support

Status: Future objective.

After the Kubernetes adapter and core contract are stable, evaluate a second infrastructure provider.

AWS is one possible candidate.

Acceptance criteria:

* The core can use a second adapter without spreading provider-specific logic throughout the core.
* Supported capabilities and limitations are documented.
* All provider operations remain subject to the same policy boundary.
* Audit and verification behavior remains consistent.

Supporting Kubernetes does not automatically mean CloudHeal supports every cloud provider.

⸻

12. Resource and Runtime Considerations

The development machines have limited resources.

Always distinguish between:

1. Host physical memory.
2. Memory assigned to Docker Desktop or a Kubernetes VM.
3. Runtime-available memory, where reliably measurable.
4. Workload resource requests and limits.
5. Actual resource consumption.
6. Remaining capacity.

Do not assume host physical memory equals memory available to containers.

Choose a Kubernetes environment that leaves enough resources for development, application workloads, and automated tests.

Avoid introducing an unnecessarily large infrastructure stack.

⸻

13. Development Commands and Working Rules

13.1 Inspect the Repository

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status --short
git diff --check
git diff

Inspect the actual file structure and current code before making changes.

13.2 Run Existing Control Plane Tests

uv run --package cloudheal-control-plane pytest control-plane/tests -q

Latest recorded result:

34 passed in 0.44s

Rerun the relevant tests after code changes.

13.3 Existing Service Commands

The previous custom implementation can be started using:

uv run --package cloudheal-control-plane cloudheal-control-plane

And:

uv run --package cloudheal-node-agent cloudheal-node-agent

Previously configured ports:

* Control Plane: 9000.
* Node Agent: 8000.

Do not launch duplicate processes when the relevant services are already running.

These commands describe the existing architecture. They are not the finalized startup procedure for the future Kubernetes-backed CloudHeal architecture.

13.4 Historical API Endpoints

Previously documented endpoints include:

GET  /health
GET  /nodes
GET  /nodes/{node_id}
POST /nodes/register
POST /nodes/{node_id}/heartbeat
GET  /workloads
GET  /workloads/{workload_id}
POST /workloads
POST /workloads/{workload_id}/schedule

Inspect the actual implementation before relying on any endpoint.

The new self-healing API and Kubernetes adapter have not yet been established as complete.

13.5 Mandatory Development Rules

* Inspect existing code before editing.
* Preserve working code and uncommitted changes.
* Never reset, delete, or commit work unless explicitly requested.
* Prefer small, incremental changes.
* Do not rebuild completed components unnecessarily.
* Do not duplicate Kubernetes functionality without a clear requirement.
* Run automated tests after meaningful changes.
* Verify real infrastructure behavior where appropriate.
* Distinguish implementation, automated tests, and real-world verification.
* Do not claim a feature is complete merely because its tests pass.
* Update repository documentation after verified milestones.
* Keep temporary machine addresses out of shared architecture documentation.
* Do not begin a large rewrite before reviewing the actual implementation.

⸻

14. Documentation and Project Coordination

14.1 Repository Documentation

Previously recorded files include:

* CloudHeal_CONTEXT.md
* README.md
* docs/SPEC-001-cloudheal.md
* docs/current_progress.md

Verify their actual existence and contents before relying on them.

The repository documentation should describe:

* Project objectives.
* Agreed architecture.
* Responsibilities of Kubernetes and CloudHeal.
* Self-healing core and adapter contracts.
* Security boundaries.
* Implementation status.
* Verified test results.
* Known limitations.
* Setup instructions.
* Acceptance criteria.
* Next implementation task.

14.2 Personal Development Notes

Keep machine-specific information separate from shared architecture documentation.

Personal notes may include:

* Local startup commands.
* Machine-specific configuration.
* Temporary IP addresses.
* Debugging observations.
* Experimental results.
* Individual tasks.

14.3 Updating Project Context

After each milestone:

1. Record actual code changes.
2. Record automated test results.
3. Record real-world verification separately.
4. Document limitations and unresolved issues.
5. Update the implementation status.
6. Identify the next concrete task.

Do not describe an intended feature as implemented.

⸻

15. Minimum Defensible Final Scope

The minimum final project should demonstrate:

1. An independently deployable CloudHeal self-healing service.
2. A clear boundary between the self-healing core and infrastructure adapters.
3. A working Kubernetes adapter.
4. Real infrastructure observation and failure classification.
5. A deterministic remediation safety gate.
6. At least one supported remediation action.
7. Independent verification of remediation outcomes.
8. Persistent incident, decision, and action history.
9. Bounded remediation and failure handling.
10. Repeatable experiments with meaningful baselines.
11. Quantitative evaluation of recovery behavior.
12. Clear security and permission boundaries.

Additional capabilities may include:

* AI-assisted diagnosis.
* Constrained AI remediation planning.
* Multi-provider support.
* Advanced incident correlation.
* A dashboard.
* More sophisticated recovery policies.

These features should not delay the first complete, measurable self-healing workflow.

⸻

16. Current Development Position

As of 25 October 2026:

* The existing custom FastAPI Control Plane and Node Agent are implemented.
* Docker workload execution and basic stopped/missing-container recovery have been demonstrated.
* Mac and Windows nodes have been integrated into the existing execution system.
* SQLite persistence and event recording have been introduced but are not fully verified.
* Node availability detection and related event recording have been implemented in the existing system.
* The reconciler avoids treating node unavailability as proof of container termination.
* The latest recorded Control Plane test run passed 34 tests.
* git diff --check passed.
* Four modified files were recorded and must be preserved.
* Kubernetes is the agreed foundation for standard orchestration.
* CloudHeal remains our own private-cloud management and self-healing platform.
* CloudHeal’s primary contribution is higher-level, deterministic self-healing intelligence.
* The Kubernetes adapter will be the first infrastructure adapter.
* AI-assisted diagnosis and constrained planning remain future work.
* Multi-provider support remains a longer-term goal.
* The existing custom scheduler, reconciler, and Node Agent must be evaluated before deciding which components to retain, adapt, or retire.
* The Kubernetes-backed architecture has not yet been implemented.

⸻

17. Next Session — Exact Starting Plan

Step 1: Inspect the Actual Repository

Run:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status --short
git diff --check
git diff

Preserve all existing modifications.

Step 2: Inspect the Existing Architecture

Read the actual versions of:

* CloudHeal_CONTEXT.md
* docs/SPEC-001-cloudheal.md
* docs/current_progress.md
* Control Plane source.
* Node Agent source.
* Database and event implementation.
* Scheduler and reconciler.
* Relevant tests.

Verify the actual repository structure rather than assuming historical paths remain unchanged.

Step 3: Finalize the Kubernetes-Backed Architecture

Explicitly document:

* What Kubernetes owns.
* What CloudHeal owns.
* The self-healing core boundary.
* The Kubernetes adapter responsibilities.
* The security and permission boundaries.
* How remediation outcomes will be verified.
* Which existing components can be reused.
* Which old orchestration responsibilities should be delegated to Kubernetes.

Do not begin a large rewrite before this review.

Step 4: Evaluate the Local Kubernetes Environment

Select a practical development setup for the Mac and Windows team.

Verify that the environment can deploy a test workload, inspect its state, and introduce a controlled failure.

Step 5: Define the Initial Self-Healing Workflow

Design a small, testable workflow:

Observe → Classify → Policy Check → Remediate → Verify → Record

Start with deterministic behavior.

Step 6: Implement Incrementally

Preserve existing code and adapt components where appropriate.

Implement the Kubernetes adapter and self-healing core without duplicating Kubernetes orchestration.

Step 7: Test and Measure

Run automated tests and verify behavior against actual infrastructure.

Record failures, inconclusive outcomes, and limitations.

Step 8: Add AI After the Deterministic Workflow Works

Introduce AI-assisted diagnosis and constrained planning only after the core workflow, policy enforcement, execution, and verification are reliable.

⸻

Guiding Principle

CloudHeal is our own private-cloud management and self-healing platform. Kubernetes provides standard orchestration; CloudHeal provides the independent intelligence, deterministic policies, safe remediation, verification, incident history, and evaluation that we build on top of supported infrastructure interfaces.

Preserve existing work, validate the architecture before changing code, and build the smallest complete self-healing workflow before expanding into AI or multi-provider support.