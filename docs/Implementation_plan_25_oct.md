We should plan CloudHeal based on what we have already implemented, what Kubernetes can replace, and what we need to build ourselves to make the project genuinely intelligent and measurable.

The most important decision is that we should not start implementing Kubernetes integration immediately without reviewing the existing code. We already have a working foundation: a FastAPI Control Plane, Node Agents, distributed execution across Mac and Windows, a scheduler, a reconciler, SQLite persistence, event recording, and tests.

We will preserve that work and migrate incrementally.

Below is the implementation roadmap I recommend for CloudHeal, from our current state through the final demonstration.

CloudHeal — Detailed Implementation Roadmap

1. Our final target architecture

CloudHeal will have four major logical components.

Component	Responsibility	Build or reuse?
Private infrastructure	Provides the machines and resources that run applications	Use our Mac and Windows machines initially
Infrastructure and orchestration	Runs workloads, schedules containers, maintains desired state	Use Kubernetes for standard orchestration
CloudHeal self-healing core	Detects, classifies, evaluates, coordinates, and verifies recovery	Build ourselves
AI-assisted intelligence	Diagnoses incidents and recommends constrained remediation plans	Build after deterministic recovery works

An infrastructure adapter connects the CloudHeal core to the target environment.

For the first implementation:

CloudHeal Core → Kubernetes Adapter → Kubernetes API → Application Workloads

Later, we can introduce additional adapters without redesigning the entire self-healing engine.

One important distinction: Kubernetes gives us orchestration, not automatically a complete cloud provider. We should build only the infrastructure management capabilities required for our demonstration and expand them when the project needs them.

⸻

2. What we have already built

Before defining the phases, let’s establish our starting point.

Existing component	Current recorded status	Planned direction
FastAPI Control Plane	Implemented	Preserve useful management and coordination functionality
Node Agent	Implemented	Evaluate its role after Kubernetes integration
Node registration	Implemented	Determine whether it remains necessary for Kubernetes-managed environments
Heartbeats	Implemented	Preserve useful monitoring concepts; avoid duplicating Kubernetes node health
Node availability detection	Implemented and tested previously	Retain where relevant; avoid treating disconnection as workload termination
Custom scheduler	Implemented	Delegate Kubernetes workload scheduling to Kubernetes
Custom reconciler	Implemented	Evaluate which responsibilities remain CloudHeal’s
Docker workload execution	Implemented	Use Kubernetes APIs for Kubernetes-managed workloads
SQLite persistence	Partially implemented	Adapt and expand for incidents, decisions, actions, and audit history
Event recording	Partially implemented	Evolve into structured incident and remediation history
Basic recovery	Demonstrated	Replace duplicate orchestration recovery with Kubernetes where appropriate
Windows-to-Mac execution	Demonstrated	Preserve as existing multi-machine integration evidence
Kubernetes adapter	Not implemented	Build
Infrastructure-independent self-healing core	Not yet established as a complete implementation	Build
Deterministic policy engine	Not yet established as a complete implementation	Build
Independent remediation verification	Not yet established in the new architecture	Build
AI diagnosis and planning	Future work	Build after deterministic recovery
Multi-provider support	Future work	Add after the first adapter is stable

The latest recorded Control Plane test result was 34 passing tests in 0.44 seconds. That result is historical and should be reverified when we begin.

What we should not do

We should not immediately delete the scheduler, reconciler, Node Agent, or database implementation.

Instead, we will identify which functionality can be reused and which functionality Kubernetes makes unnecessary.

⸻

Phase 1 — Repository Audit and Architecture Finalization

Priority: Immediate
Purpose: Understand the existing implementation before modifying it.

Step 1.1 — Inspect the working tree

On your Mac, run:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status --short
git diff --check
git diff

We need to know exactly which files have uncommitted changes.

Preserve all existing modifications. Do not reset or overwrite them.

Step 1.2 — Inspect the repository structure

Run:

find . -maxdepth 3 -type f | sort

Exclude generated directories such as .git, .venv, and cache directories if the output becomes too large.

Inspect the current versions of:

* CloudHeal_CONTEXT.md
* README.md
* docs/SPEC-001-cloudheal.md
* docs/current_progress.md
* Control Plane source.
* Node Agent source.
* Database implementation.
* Event recording.
* Scheduler.
* Reconciler.
* Existing tests.

Step 1.3 — Map existing functionality

Create a component inventory.

For every significant module, document:

1. What it does.
2. What state it owns.
3. Which other modules it depends on.
4. Whether Kubernetes already provides the same functionality.
5. Whether CloudHeal still needs that responsibility.
6. Whether the code should be retained, adapted, or retired.

For example:

Existing functionality	Decision
Custom container scheduling	Delegate standard scheduling to Kubernetes
Node registration	Reevaluate based on the adapter and target infrastructure
Workload desired-state tracking	Use Kubernetes state for Kubernetes-managed workloads
Incident event recording	Retain and adapt
Custom health-state transitions	Reevaluate against Kubernetes observations
Higher-level recovery policy	Build into CloudHeal
Basic container restart logic	Avoid duplicating Kubernetes behavior

Step 1.4 — Finalize the architecture document

Document three boundaries:

CloudHeal core: incidents, evidence, policy decisions, remediation coordination, verification, audit history, and metrics.

Infrastructure adapters: Kubernetes first, with future adapters for other providers.

Infrastructure: Kubernetes and the underlying environment that actually execute and manage workloads.

Deliverables

* Accurate repository inventory.
* Existing-component migration table.
* Updated architecture documentation.
* Explicit list of responsibilities assigned to Kubernetes and CloudHeal.
* No unnecessary code changes.

Acceptance criteria

We understand what exists, what works, what is incomplete, and what must change before beginning the migration.

⸻

Phase 2 — Establish the Local Kubernetes Environment

Priority: High
Purpose: Provide the infrastructure that CloudHeal will manage.

We should select a suitable Kubernetes setup for the actual Mac and Windows machines rather than assuming that every machine can join the same cluster without limitations.

Step 2.1 — Evaluate the available options

Evaluate practical options such as:

* A local single-machine Kubernetes environment for initial development.
* A lightweight local cluster.
* A multi-machine Kubernetes cluster if the hardware, operating systems, and networking make it practical.

The choice should account for memory, compatibility, maintenance, and reproducibility.

We do not need a large production-grade cluster to demonstrate the core self-healing workflow.

Step 2.2 — Establish the initial environment

Once the setup is selected:

1. Install or configure the required Kubernetes environment.
2. Verify cluster connectivity.
3. Inspect available nodes.
4. Deploy a basic application.
5. Inspect the workload and pod status.
6. Access the application.
7. Introduce a controlled failure.
8. Observe Kubernetes’ native behavior.

Start with a simple workload such as NGINX.

Step 2.3 — Record Kubernetes-native behavior

This is important for our eventual evaluation.

For example, deliberately terminate a disposable pod and measure how Kubernetes responds without CloudHeal remediation.

We need to understand what Kubernetes already handles automatically.

Deliverables

* Documented local Kubernetes setup.
* Repeatable workload deployment procedure.
* Verified access to Kubernetes state.
* A controlled failure scenario.
* Initial evidence of Kubernetes-native recovery behavior.

Acceptance criteria

We can reliably deploy, inspect, and deliberately fail a test workload.

Important: Do not build CloudHeal’s recovery engine yet. First establish the environment and understand the behavior it already provides.

⸻

Phase 3 — Define CloudHeal’s Data Models and Adapter Contract

Priority: High
Purpose: Prevent the core from becoming tightly coupled to Kubernetes.

This is where we establish the interfaces that future components will use.

Step 3.1 — Define the core data models

Start with a small set of structured models.

Model	Purpose
Observation	Represents something observed in infrastructure
Incident	Represents a detected failure or abnormal condition
DiagnosticEvidence	Holds evidence supporting a diagnosis
RemediationPlan	Describes a proposed recovery action
PolicyDecision	Records whether an action is permitted
RemediationAttempt	Tracks execution of an approved action
VerificationResult	Records whether the intended outcome occurred
AuditEvent	Records important lifecycle and decision events

Each model should have a clear purpose.

Avoid creating unnecessary abstractions before we have a real use for them.

Step 3.2 — Define infrastructure-independent interfaces

The core should not need to know how Kubernetes represents every resource.

Conceptually, we need operations for:

Observe infrastructure
Retrieve diagnostic evidence
Inspect target state
Execute a supported action
Verify the outcome

These are conceptual responsibilities, not final method names.

We will define the actual interface after inspecting the repository and identifying the minimum operations required by our first workflow.

Step 3.3 — Define action outcomes

An adapter must distinguish between:

* Action rejected.
* Request accepted.
* Execution in progress.
* Execution completed.
* Outcome verified.
* Execution failed.
* Outcome unknown.

A successful HTTP response is not proof that recovery succeeded.

Step 3.4 — Define capability reporting

Not all infrastructure providers support the same operations.

An adapter should report what it supports and reject unsupported requests explicitly.

For example, a Kubernetes adapter may support restarting a workload through a specific operation, while another adapter may expose a different mechanism.

Deliverables

* Initial domain models.
* Adapter interface.
* Structured action-result model.
* Capability definitions.
* Unit tests for the core contracts.

Acceptance criteria

The core can represent an incident and a proposed action without depending on Kubernetes-specific types.

⸻

Phase 4 — Build the Kubernetes Adapter

Priority: High
Purpose: Allow CloudHeal to observe and interact with real infrastructure.

This is our first actual infrastructure integration.

Step 4.1 — Connect to the Kubernetes API

Implement the adapter using the Kubernetes API and an appropriate client library.

Use configured credentials and least-privilege permissions.

Do not grant unrestricted cluster-admin permissions by default.

Step 4.2 — Implement observations

Start with the minimum information needed for the first recovery scenario:

* Workload and pod status.
* Readiness and health information.
* Relevant Kubernetes events.
* Restart counts and failure information.
* Node conditions where relevant.
* Selected logs or diagnostic evidence.

Avoid collecting every possible metric immediately.

Step 4.3 — Implement supported actions

Initially, support a small set of explicit operations.

Examples include:

* Inspect a workload.
* Read relevant logs.
* Restart or recreate a supported workload through an appropriate Kubernetes API operation when policy permits.

The exact action set must be chosen according to the failure scenario and the desired distinction between CloudHeal and Kubernetes-native behavior.

Do not directly manipulate containers through Docker when Kubernetes manages them.

Step 4.4 — Verify adapter behavior

Test:

* Successful observations.
* Missing resources.
* Insufficient permissions.
* Kubernetes API timeouts.
* Unsupported operations.
* Ambiguous execution outcomes.

Deliverables

* Working Kubernetes adapter.
* Read-only observation support.
* Limited, explicit remediation operations.
* Structured errors and action results.
* Automated tests, including failure cases.

Acceptance criteria

CloudHeal can retrieve actual Kubernetes state and request supported actions through the adapter.

At this point, we have infrastructure connectivity, but not yet a complete self-healing engine.

⸻

Phase 5 — Implement the Deterministic Self-Healing Core

Priority: Critical
Purpose: Build CloudHeal’s main contribution.

This is the most important phase of the project.

The core should work without AI.

Step 5.1 — Implement observation processing

Receive observations from the adapter and normalize them into CloudHeal’s domain models.

For example:

Observed:
A workload repeatedly fails to become ready.
Normalized observation:
WORKLOAD_NOT_READY
Evidence:
Workload status, events, restart information, relevant logs.

This is an illustrative example, not a prescribed final incident taxonomy.

Step 5.2 — Implement failure classification

Start with a small number of deterministic failure types.

Possible examples:

* Workload unavailable.
* Repeated container crashes.
* Readiness failure.
* Resource pressure.
* Infrastructure dependency failure.

Only implement classifications that can be supported by evidence available through the initial adapter.

Step 5.3 — Implement incident correlation

Avoid treating every observation as an unrelated incident.

For example, multiple failed pods caused by one underlying dependency may belong to the same incident.

Begin with simple, explainable correlation rules.

Advanced correlation can come later.

Step 5.4 — Implement the policy engine

Create explicit rules governing which actions are permitted.

Examples:

* A recovery action is allowed for a recognized failure type.
* An unsupported action is rejected.
* An invalid target is rejected.
* A retry limit prevents repeated actions.
* An active cooldown blocks another attempt.
* A high-risk action requires approval.

Every decision should include a reason.

Step 5.5 — Implement remediation coordination

The core should:

1. Select an eligible remediation plan.
2. Evaluate it against policy.
3. Record the decision.
4. Request execution through the adapter.
5. Track the execution result.
6. Trigger verification.
7. Record the final outcome.

The core should not become a second Kubernetes scheduler or container lifecycle manager.

Step 5.6 — Implement independent verification

Verification must evaluate actual observations after remediation.

For example, if the intended result is that an application becomes available, inspect workload readiness and an appropriate application health check.

Do not treat an accepted request or a successful API call as proof of recovery.

Deliverables

* Deterministic incident classification.
* Policy engine.
* Remediation coordination.
* Independent verification.
* Unit and integration tests.

Acceptance criteria

A controlled failure can pass through classification, policy evaluation, permitted remediation, verification, and a recorded result.

This is the first major CloudHeal milestone.

⸻

Phase 6 — Persistence, Incident History, and Recovery Controls

Priority: High
Purpose: Make the system auditable, restart-safe, and resistant to uncontrolled recovery loops.

We already have SQLite persistence and event recording in the old architecture. We should inspect and reuse suitable pieces rather than starting from scratch.

Step 6.1 — Define CloudHeal’s persistent records

Persist at least:

* Incidents.
* Evidence references.
* Policy decisions.
* Remediation attempts.
* Execution results.
* Verification results.
* Important timestamps.
* Failure and escalation states.

Avoid duplicating Kubernetes’ complete resource state in the CloudHeal database unless there is a specific need.

Step 6.2 — Ensure consistent lifecycle recording

Related records should be written consistently.

For example, an approved remediation must not be recorded as successful before its outcome is verified.

Consider transaction boundaries and recovery after process restarts.

Step 6.3 — Add bounded recovery behavior

Where not already provided by the underlying infrastructure or the core policy, implement:

* Maximum attempts.
* Cooldowns.
* Backoff.
* Concurrent remediation limits.
* Duplicate-action prevention.
* Crash-loop recognition.
* Escalation when recovery repeatedly fails.

These controls should govern CloudHeal’s higher-level actions rather than blindly duplicating Kubernetes’ ordinary restart logic.

Step 6.4 — Handle uncertain outcomes

Suppose CloudHeal requests an action and then loses connectivity.

The action might have completed even though CloudHeal never received the response.

CloudHeal should inspect the current infrastructure state before retrying an operation whose outcome is uncertain.

Deliverables

* Persistent incident and action history.
* Restart-safe processing.
* Recovery limits.
* Duplicate-action protection.
* Tests for failure and uncertain outcomes.

Acceptance criteria

Incident history survives a CloudHeal restart, and repeated failures cannot trigger uncontrolled recovery loops.

⸻

Phase 7 — End-to-End Integration and First Demonstration

Priority: Critical
Purpose: Prove that all the components work together.

Now we combine the infrastructure adapter, deterministic core, policies, persistence, and verification.

Step 7.1 — Prepare the application

Deploy a disposable test application to the Kubernetes environment.

Confirm normal operation before introducing a failure.

Step 7.2 — Introduce a controlled failure

Choose a failure that produces clear, observable evidence.

Possible initial scenarios include:

* An application process exits.
* A test workload becomes unavailable.
* A readiness check fails.
* A disposable workload enters a repeated crash state.

Choose a scenario in which CloudHeal’s behavior can be distinguished from Kubernetes’ normal behavior.

Step 7.3 — Execute the self-healing workflow

Demonstrate:

1. Failure observed.
2. Incident classified.
3. Evidence collected.
4. Remediation candidate selected.
5. Policy decision recorded.
6. Approved action executed.
7. Recovery verified.
8. Incident history updated.

Step 7.4 — Demonstrate a rejected action

Submit a remediation request that violates a deterministic policy.

Show that CloudHeal rejects it and records the reason without executing it.

Step 7.5 — Test unsuccessful recovery

Introduce a failure for which the selected action cannot solve the problem.

Demonstrate that CloudHeal:

* Detects unsuccessful recovery.
* Records the failed or inconclusive outcome.
* Applies its recovery limits.
* Avoids endless retries.
* Escalates or reports the unresolved incident.

Deliverables

* One complete end-to-end demonstration.
* A successful remediation scenario.
* A rejected-action scenario.
* An unsuccessful-recovery scenario.
* Recorded evidence and results.

Acceptance criteria

We can demonstrate actual behavior from infrastructure failure through final verification, not merely simulated decisions.

⸻

Phase 8 — Evaluation and Experimental Baselines

Priority: High
Purpose: Demonstrate what CloudHeal adds beyond Kubernetes.

This phase is important for the project’s technical credibility.

We need to show that CloudHeal contributes measurable value rather than simply invoking an existing Kubernetes operation.

Step 8.1 — Establish baselines

Compare at least:

Experiment	Purpose
Kubernetes only	Measure native orchestration behavior
CloudHeal observation only	Measure detection and classification
CloudHeal deterministic remediation	Measure the effect of the self-healing policy and workflow
Different policy configurations	Evaluate recovery controls and trade-offs
AI-assisted diagnosis, later	Compare AI recommendations against deterministic analysis

Step 8.2 — Measure meaningful metrics

Collect:

* Detection latency.
* Time from incident detection to remediation request.
* Time from remediation request to execution result.
* Time until recovery is independently verified.
* Total application downtime.
* Recovery success rate.
* False-positive rate.
* Failed remediation count.
* Duplicate or unnecessary action count.
* Unsafe actions rejected.
* Escalation frequency.

Use actual timestamps and observed results.

Step 8.3 — Repeat experiments

Run multiple trials using the same documented setup.

Retain unsuccessful and inconclusive trials.

Compare results under consistent conditions and explain differences in behavior.

Deliverables

* Reproducible test scenarios.
* Experiment records.
* Metric calculations.
* Baseline comparison.
* Results suitable for the final report and demonstration.

Acceptance criteria

We can explain quantitatively what CloudHeal adds beyond Kubernetes-native behavior.

⸻

Phase 9 — Stable Application Access and Networking

Priority: Medium
Purpose: Make applications accessible in a useful way during normal operation and recovery.

Do not build a custom gateway automatically.

First evaluate the networking and service capabilities already provided by the selected Kubernetes environment.

Determine whether the demonstration requires:

* A stable application URL.
* External access.
* Routing to healthy replicas.
* Health-aware endpoint selection.
* Additional private-network integration.

If existing Kubernetes networking or a suitable ingress/gateway component meets the requirements, use it.

Build custom functionality only where a justified gap remains.

Acceptance criteria

The application is accessible through the intended endpoint, and its behavior during failure and recovery has been tested.

A stable URL must not be presented as proof of uninterrupted connections or preserved application state.

⸻

Phase 10 — AI-Assisted Diagnosis

Priority: After deterministic self-healing works
Purpose: Introduce intelligent diagnosis without compromising safety.

This is where we start adding AI capabilities.

Step 10.1 — Build the diagnostic context

Provide the AI component with relevant, bounded evidence:

* Incident classification.
* Workload status.
* Kubernetes events.
* Selected logs.
* Resource observations.
* Application health results.
* Previous incident summaries.
* Previous remediation outcomes.

Avoid sending unrestricted infrastructure access or unnecessary information.

Step 10.2 — Generate structured diagnoses

The AI should return structured output such as:

* Likely cause.
* Supporting evidence.
* Alternative explanations.
* Confidence or uncertainty.
* Recommended diagnostic step.
* Candidate remediation from an explicitly supported action set.

The exact schema should be defined and validated.

Step 10.3 — Evaluate diagnosis quality

Compare AI-generated diagnoses against:

* Known failure scenarios.
* Available diagnostic evidence.
* Deterministic classifications.
* Observed remediation outcomes.

Measure correctness and uncertainty instead of assuming that a fluent explanation is accurate.

Acceptance criteria

The AI can assist diagnosis, and its recommendations can be evaluated against real evidence.

The basic deterministic system must still work if the AI API is unavailable.

⸻

Phase 11 — Constrained AI Remediation Planning

Priority: After AI diagnosis is evaluated

This phase extends AI from diagnosis into planning.

The AI may compare candidate actions, but it does not execute unrestricted operations.

The flow is:

Incident Evidence → AI Recommendation → Deterministic Policy Check → Approved Adapter Action → Verification

Step 11.1 — Define the permitted action space

Examples might include:

* Inspect a workload.
* Retrieve additional permitted logs.
* Request a supported recovery operation.
* Recommend scaling within configured limits.
* Escalate an unresolved incident.

Each action must have a defined schema, target, and permission boundary.

Step 11.2 — Enforce deterministic authorization

The policy engine checks the recommendation against:

* Supported actions.
* Target validity.
* Permissions.
* Recovery limits.
* Cooldowns.
* Resource constraints.
* Approval requirements.
* Provider capabilities.
* Verification conditions.

The model cannot modify the policy engine or bypass these checks.

Step 11.3 — Evaluate AI-assisted planning

Compare the AI’s recommendations against a deterministic baseline.

Record:

* Whether the recommendation was supported by evidence.
* Whether policy accepted it.
* Whether the action succeeded.
* Whether the intended outcome was verified.
* Whether the recommendation caused unnecessary or ineffective action.

Acceptance criteria

AI can recommend actions safely within the supported action space, with every decision and outcome recorded.

⸻

Phase 12 — Second Infrastructure Provider

Priority: Later
Purpose: Validate that CloudHeal is genuinely adaptable across environments.

Once the Kubernetes adapter and core interface are stable, select a second provider based on the project’s actual requirements.

AWS is one possible candidate.

Step 12.1 — Identify the supported capabilities

Document what the second provider can observe and which actions it can perform.

Do not assume its resource model or permissions match Kubernetes.

Step 12.2 — Implement the second adapter

Reuse the existing core and policy engine.

Provider-specific behavior should remain inside the adapter wherever practical.

Step 12.3 — Run the same core workflow

Test observation, incident processing, policy enforcement, remediation, verification, and audit history against the second environment.

Acceptance criteria

The second adapter works without requiring provider-specific logic to spread throughout the self-healing core.

This phase is a future goal, not a prerequisite for the first successful CloudHeal demonstration.

⸻

3. Overall Roadmap at a Glance

Phase	Main objective	Priority
1	Audit repository and finalize architecture	Immediate
2	Establish local Kubernetes environment	High
3	Define core models and adapter contract	High
4	Implement Kubernetes adapter	High
5	Build deterministic self-healing core	Critical
6	Persistence, audit, and recovery controls	High
7	Complete end-to-end demonstration	Critical
8	Evaluation and experimental baselines	High
9	Stable application access and networking	Medium
10	AI-assisted diagnosis	Later
11	Constrained AI remediation planning	Later
12	Second infrastructure provider	Later

Dependency rule: Phases 1–4 establish the architecture and infrastructure foundation. Phases 5–7 deliver the first complete self-healing workflow. Phase 8 proves its value. Phases 10–12 expand its intelligence and portability.

Some work can proceed in parallel once its dependencies are stable, but we should not begin advanced AI planning before deterministic remediation and verification are reliable.

⸻

4. What We Should Do First: The Next Three Working Sessions

Rather than trying to implement the entire roadmap immediately, I recommend the following concrete sequence.

Session 1 — Audit the Existing Repository

Run:

cd ~/Desktop/CloudHeal
source .venv/bin/activate
git status --short
git diff --check
git diff

Then inspect the project documentation, Control Plane, Node Agent, database, scheduler, reconciler, and tests.

Goal: Produce an accurate migration map without changing working code unnecessarily.

Session 2 — Validate Kubernetes Locally

Select the simplest practical Kubernetes environment for the team’s machines.

Deploy a disposable application, inspect its state, and observe how Kubernetes responds to a controlled failure.

Goal: Establish the infrastructure foundation and understand what Kubernetes already handles.

Session 3 — Design the First Self-Healing Workflow

Choose one failure scenario and define:

* What CloudHeal observes.
* How it classifies the failure.
* What evidence it needs.
* Which remediation action is permitted.
* Which policy would reject an unsafe action.
* How recovery will be verified.
* Which records and metrics must be persisted.

Goal: Produce a small, testable design that maps directly to the existing codebase and the Kubernetes adapter.

After that, we can implement the first vertical slice incrementally.

⸻

5. Final Demonstration We Are Working Toward

The final demonstration should look like this:

1. CloudHeal connects to the configured infrastructure.
2. An application is deployed and confirmed healthy.
3. We introduce a controlled failure.
4. CloudHeal observes and classifies the incident.
5. It gathers diagnostic evidence.
6. Its deterministic engine evaluates candidate remediation actions.
7. An unsafe action is rejected when appropriate.
8. A permitted action is executed through the infrastructure adapter.
9. CloudHeal verifies actual recovery.
10. The incident, evidence, decision, action, and result are persisted.
11. We report measured recovery performance against a baseline.
12. AI-assisted diagnosis and constrained planning are demonstrated when mature enough.

This gives us a defensible engineering project: established orchestration underneath, our own self-healing logic above it, and measured evidence that the system behaves as intended.

My recommendation

Our next step is Phase 1: inspect the actual repository and map the existing code to the revised architecture.

Do not install Kubernetes, delete old components, or begin a large rewrite before we know what is already in the repository and how best to reuse it.

We will work phase by phase, preserve existing functionality, run tests after meaningful changes, verify actual infrastructure behavior, and update the project context after each confirmed milestone.


We need to change how we approach CloudHeal now. We have a maximum of 1–2 months, so we need to build a working, measurable project—not spend weeks designing infrastructure or implementing features Kubernetes already provides.

My recommendation: target 4 weeks for a strong, working MVP and allow up to 8 weeks for the complete project with evaluation and AI-assisted remediation. We should prioritize a successful end-to-end demonstration over a large feature list.

1. The one-month vs. two-month target

Area	1-month MVP	2-month target
Private infrastructure	Kubernetes running on our available machines	More reliable multi-node setup
Infrastructure integration	Kubernetes adapter	Kubernetes adapter plus a second provider if feasible
Self-healing	Deterministic detection, policies, remediation and verification	Better failure classification, correlation and recovery controls
Persistence	Durable incident and action history	Restart-safe recovery and stronger auditability
AI	Bounded incident diagnosis	Constrained AI remediation planning
Evaluation	Repeatable failure experiments and metrics	Baselines, comparisons and repeated trials
Demo	Real application failure and recovery	Polished end-to-end demonstration and results

Important: We should not promise that every feature will be production-ready in two months. The priority is to make the core system genuinely work and demonstrate its value.

⸻

2. Our accelerated implementation roadmap

Week 1 — Audit CloudHeal and establish Kubernetes

Goal: Have a working Kubernetes environment and understand exactly what to reuse from our existing code.

Step 1: Audit the existing repository

We have already built:

* FastAPI Control Plane.
* Node Agent and node registration/heartbeats.
* Docker-based workload execution.
* Workload scheduling and reconciliation.
* SQLite persistence and event recording.
* Node availability detection and recovery-related logic.
* An existing automated test suite.

We must preserve this work while identifying which responsibilities should move to Kubernetes.

We will inspect the actual code and classify each component as:

* Reuse.
* Adapt into CloudHeal’s self-healing system.
* Replace with Kubernetes functionality.
* Defer until later.

We will not rewrite everything from scratch.

Step 2: Establish a Kubernetes environment

We need a practical environment for our Mac and three Windows laptops.

We will evaluate the available hardware, memory, networking, and operating systems before choosing the setup. We should begin with the smallest reliable Kubernetes environment that supports our first experiments, then expand to multiple machines.

We will deploy a sample application and verify:

* Kubernetes can run the application.
* Application health can be inspected.
* Pod failures and restarts can be observed.
* Kubernetes’ native recovery behavior can be demonstrated.

Week 1 acceptance criteria

* Existing CloudHeal changes are preserved.
* Kubernetes runs a test application.
* We can deliberately cause a failure and observe what Kubernetes does.
* We understand which responsibilities belong to Kubernetes and which belong to CloudHeal.

Time limit: Aim to finish this phase within 5–7 days. Do not spend the entire first week debating Kubernetes distributions.

⸻

Week 2 — Build CloudHeal’s deterministic self-healing engine

Goal: CloudHeal detects a real problem, makes a policy decision, takes a permitted action, and verifies the result.

This is the most important part of the project.

Step 1: Connect CloudHeal to Kubernetes

Build a Kubernetes adapter that allows CloudHeal to inspect:

* Pod and workload status.
* Readiness and health information.
* Restart counts.
* Kubernetes events.
* Relevant logs.
* Node conditions.

CloudHeal should use Kubernetes APIs for Kubernetes-managed workloads rather than manipulating their containers directly through Docker.

Step 2: Implement deterministic failure classification

Start with three failure scenarios:

1. Application unavailable: The application is not healthy or ready.
2. Repeated crashes: The workload repeatedly restarts or fails.
3. Node unavailable: Kubernetes reports that a node is unhealthy or unavailable.

Each classification must be supported by actual observations. We should not classify a failure from an AI guess or a single ambiguous signal.

Step 3: Implement the policy engine

For every incident, CloudHeal should determine:

* What happened?
* What evidence supports the classification?
* Is remediation necessary?
* Which actions are permitted?
* Is the target valid?
* Have retry limits or cooldowns been exceeded?
* Should the incident be escalated instead?

The decision must include a reason that we can inspect and demonstrate.

Step 4: Execute and verify remediation

CloudHeal should execute a supported action through the Kubernetes adapter, then independently inspect the actual infrastructure state.

An API returning success is not sufficient evidence that recovery succeeded.

Week 2 acceptance criteria

We can demonstrate this complete sequence:

Real failure → Detection → Classification → Policy decision → Remediation → Independent verification → Recorded result

The workflow must function without an AI API.

⸻

Week 3 — Persistence, safety and measurable results

Goal: Make the self-healing engine reliable enough to survive real experiments.

Step 1: Complete incident persistence

Extend our existing SQLite implementation rather than introducing another database unnecessarily.

Persist:

* Incident details.
* Diagnostic evidence or references to it.
* Classification and confidence where applicable.
* Policy decisions and reasons.
* Remediation attempts.
* Execution outcomes.
* Verification results.
* Timestamps and failure details.

We must also verify that records remain consistent when the Control Plane restarts.

Step 2: Add recovery safety controls

Implement:

* Bounded retries.
* Cooldowns and backoff.
* Duplicate-remediation prevention.
* Concurrent action limits.
* Crash-loop recognition.
* Escalation when remediation fails.
* Handling of uncertain execution outcomes.

Critical distinction: If a node becomes unreachable, we cannot automatically assume its workload has stopped. We must inspect the state and apply an appropriate safety policy before attempting potentially conflicting recovery.

Kubernetes continues to handle its ordinary orchestration responsibilities. CloudHeal adds higher-level diagnosis, coordination, safety and verification.

Step 3: Establish a measurable baseline

Run the same failure scenarios under at least two configurations:

Configuration	Purpose
Kubernetes alone	Establish native recovery behavior
Kubernetes + CloudHeal	Measure the additional value of CloudHeal

Measure:

* Failure detection time.
* Recovery time.
* Application downtime.
* Successful recovery rate.
* False-positive incidents.
* Unnecessary or duplicate remediation actions.
* Unsafe actions blocked.
* Escalations after failed recovery.

We should retain failed experiments as well as successful ones.

Week 3 acceptance criteria

We have a repeatable experiment, durable incident history, safety limits, and actual measurements showing what CloudHeal adds beyond Kubernetes.

⸻

Week 4 — AI-assisted diagnosis and final demonstration

Goal: Deliver the first complete project version.

Step 1: Add AI diagnosis

Only after deterministic detection and remediation work should we add an LLM.

Give it structured, bounded evidence such as:

* Incident classification.
* Workload status.
* Relevant Kubernetes events.
* Selected logs.
* Resource information.
* Previous incident outcomes.

The model should return a structured diagnosis containing:

* Likely cause.
* Supporting evidence.
* Alternative explanations.
* Confidence or uncertainty.
* Recommended diagnostic steps.
* Candidate remediation from a fixed set of supported actions.

The model must not have unrestricted shell access, direct unrestricted Docker access, or authority to bypass the policy engine.

If the AI service is unavailable, deterministic CloudHeal must continue working.

Step 2: Build the demonstration

Our final demonstration should follow a simple, convincing sequence:

1. Deploy an application into our private infrastructure.
2. Show that it is healthy.
3. Introduce a controlled failure.
4. Show CloudHeal detecting the problem.
5. Display the evidence and deterministic policy decision.
6. Execute a permitted recovery action.
7. Verify the application’s actual health.
8. Show the incident and action history.
9. Display the recovery metrics.
10. Demonstrate a failure that is safely blocked or escalated.

The UI should support this workflow, not become a separate project that delays it.

Week 4 acceptance criteria

A working end-to-end demo, automated tests, measurable results, setup instructions, and a clear architecture explanation.

This is our one-month deliverable.

⸻

3. What we will build during weeks 5–8

If we use the full two months, we will improve the system rather than expand in every direction simultaneously.

Period	Priority	Deliverable
Week 5	Multi-node reliability	Test node failures, connectivity loss, resource constraints and recovery behavior across the available machines.
Week 6	AI-assisted remediation planning	Let AI propose actions from a fixed schema; enforce deterministic authorization and safety checks.
Week 7	Second infrastructure adapter	Integrate another provider, potentially AWS, if the Kubernetes workflow is stable.
Week 8	Final evaluation and hardening	Repeat experiments, compare baselines, fix defects, document limitations and polish the demo.

The second provider is conditional. If our Kubernetes integration or self-healing workflow remains unreliable, we should use that time to improve the core instead.

Likewise, a stable application URL and advanced networking are important only after the core recovery workflow works.

⸻

4. Our technology boundaries

To avoid wasting time, these are our working decisions.

Component	Responsibility
Kubernetes	Scheduling, container lifecycle, ordinary restarts, rescheduling and standard workload orchestration
CloudHeal Control Plane	Incident management, evidence collection, deterministic classification, policies, remediation coordination and audit history
CloudHeal infrastructure adapter	Communicating with Kubernetes through its APIs
CloudHeal verification	Checking whether the intended recovery actually succeeded
AI diagnosis agent	Analysing evidence and proposing explanations
AI planning agent	Later, proposing constrained remediation actions
Deterministic safety engine	Authorizing or rejecting actions regardless of AI recommendations
Private infrastructure	Our available Mac and Windows machines, subject to the selected Kubernetes setup

We will retain useful existing FastAPI, Python and SQLite code where appropriate. We will not maintain a second general-purpose scheduler and container orchestrator unless a demonstrated requirement justifies it.

⸻

5. Rules for finishing within two months

I want us to follow five rules.

1. One working vertical slice at a time. Every major feature must connect to an actual infrastructure workflow.
2. No premature AI. First make deterministic recovery work; then add AI diagnosis and constrained planning.
3. No unnecessary infrastructure. Avoid adding databases, orchestration systems or services without a clear need.
4. Test every milestone. Distinguish unit tests, integration tests and verified real-machine behavior.
5. Keep the scope flexible. If something threatens the deadline, reduce optional features—not the core reliability and evaluation work.

The essential deliverable is not the number of agents, endpoints or dashboards. It is a system that detects failures, makes explainable decisions, safely executes recovery, verifies the outcome, and proves its value through experiments.

⸻

6. Let’s start now: Phase 1 audit

Before changing the architecture, we need to inspect the repository’s current state, including your latest changes. I do not want to give you commands that overwrite existing work or assume files have not changed.

Open Terminal on your Mac and run:

cd ~/Desktop/CloudHeal
git status --short
git diff --check
uv run --package cloudheal-control-plane pytest control-plane/tests -q

These commands show the working-tree changes, check for whitespace errors, and run the Control Plane tests. If the tests fail, don’t modify anything yet; we will inspect the failures.

Then run:

find . -maxdepth 3 -type f \
  -not -path './.git/*' \
  -not -path './.venv/*' \
  -not -path './**/__pycache__/*' \
  | sort | head -200

This gives us a manageable view of the project structure.

Send me the output of these commands first.

Our next step will be to map the existing implementation against the new architecture and decide exactly what stays, what changes, and what Kubernetes replaces.

The target is a working MVP in four weeks, with eight weeks as our maximum—not eight weeks of preparation followed by implementation.
