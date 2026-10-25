CloudHeal — Development Phases & Roadmap

1. Project Vision

CloudHeal is an independently deployable, cloud-agnostic private-cloud management and self-healing platform.

The initial environment consists of three Windows laptops and one MacBook Air connected through a private network. The platform will use Kubernetes for standard container orchestration and provide its own management interface, infrastructure-independent self-healing capabilities, incident history, and operational intelligence.

CloudHeal is not intended to reimplement Kubernetes. Kubernetes will provide the underlying orchestration capabilities, while CloudHeal will build higher-level cloud management and self-healing functionality on top.

The long-term objective is to create a platform that can manage supported infrastructure across private environments and, eventually, other compatible infrastructure providers.

Core Principles

* Build a functioning private cloud before expanding self-healing features.
* Use Kubernetes for standard container orchestration and workload lifecycle management.
* Build CloudHeal as an independently deployable platform with its own APIs, configuration, policies, and operational records.
* Keep the self-healing engine deterministic, auditable, and safe.
* Use AI for diagnosis and planning only after the deterministic recovery workflow is operational.
* Preserve existing working code and migrate responsibilities incrementally.
* Validate features through real infrastructure tests and measurable results.

⸻

Phase 1 — Architecture and Infrastructure Foundation

Goal: Establish a technically feasible architecture and prepare the development environment.

Tasks

* Review the existing repository, implementation, and architecture documents.
* Identify existing functionality that can be reused.
* Define the boundary between Kubernetes orchestration and CloudHeal platform responsibilities.
* Evaluate Kubernetes distributions suitable for the team’s hardware and operating systems.
* Determine how Windows machines will participate in the cluster, including any required Linux environments or virtual machines.
* Validate private-network connectivity between the MacBook and Windows machines.
* Define the initial cluster topology and access requirements.
* Document configuration, credentials, and operational assumptions.

Deliverables

* Finalized initial architecture.
* Documented Kubernetes distribution and installation strategy.
* Verified connectivity between participating machines.
* Documented infrastructure prerequisites and limitations.

Completion Criteria

The team has a tested, reproducible plan for creating the initial multi-node Kubernetes environment.

⸻

Phase 2 — Build the Private Cloud Infrastructure

Goal: Establish a functioning Kubernetes environment across the team’s machines.

Tasks

1. Prepare the required Linux execution environments and Kubernetes prerequisites.
2. Initialize the Kubernetes cluster.
3. Connect the first additional worker node.
4. Verify node registration, readiness, and resource reporting.
5. Expand the cluster to the remaining supported machines.
6. Configure and validate cluster networking.
7. Verify workload scheduling and container lifecycle behavior.
8. Test node unavailability and observe Kubernetes recovery behavior.
9. Document storage, networking, and workload-placement limitations.

Deliverables

* Working Kubernetes cluster.
* Multiple verified nodes.
* Working container scheduling and lifecycle management.
* Documented network and resource configuration.
* Repeatable cluster setup instructions.

Completion Criteria

* All intended participating nodes can join the cluster using the selected architecture.
* Nodes report their expected readiness and capacity.
* Applications can be deployed and scheduled.
* Standard Kubernetes recovery behavior has been tested.
* Known limitations are documented.

Important: The cluster must be tested on the actual team hardware. Windows nodes may require Linux environments or virtual machines, depending on the selected configuration.

⸻

Phase 3 — Workload Deployment, Networking, and Access

Goal: Demonstrate that the private cloud can run and expose real applications.

Tasks

* Deploy an initial application, such as NGINX.
* Manage applications through Kubernetes Deployments.
* Inspect Pods, ReplicaSets, and Deployment status.
* Update container images.
* Scale application replicas.
* Expose applications through Kubernetes Services.
* Establish a suitable mechanism for accessing applications from outside the cluster.
* Verify communication between workloads and Services.
* Test Pod replacement and application availability.
* Investigate storage requirements for workloads that need persistent data.

Deliverables

* Running application workloads.
* Working application networking.
* Documented application access endpoints.
* Tested deployment, update, scaling, and inspection procedures.

Completion Criteria

A user can deploy an application to the private cloud, access it through a documented endpoint, and verify its state using Kubernetes.

⸻

Phase 4 — CloudHeal Platform and Kubernetes Integration

Goal: Build our own cloud-management layer on top of Kubernetes.

Tasks

* Review the existing FastAPI Control Plane, Node Agent, custom scheduler, and Kubernetes adapter.
* Identify responsibilities that Kubernetes will replace.
* Preserve useful functionality while avoiding competing orchestration implementations.
* Define CloudHeal’s platform API and configuration model.
* Integrate the platform with the Kubernetes API.
* Implement infrastructure and node-status inspection.
* Implement workload listing and inspection.
* Add application deployment, update, scaling, and lifecycle operations.
* Record relevant operations and failures.
* Establish authentication and authorization requirements.
* Document how CloudHeal connects to and manages the cluster.

Deliverables

* CloudHeal management API.
* Kubernetes-backed workload management.
* Infrastructure and workload inspection.
* Persistent operational records.
* Documented platform configuration and deployment procedures.

Completion Criteria

Users can perform the agreed workload-management operations through CloudHeal’s own API without manually executing Kubernetes commands for every operation.

Kubernetes remains responsible for standard orchestration.

⸻

Phase 5 — Incident Detection and Classification

Goal: Detect and classify infrastructure and application incidents using reliable evidence.

Tasks

* Define incident types and classification rules.
* Collect relevant infrastructure and workload health information.
* Detect degraded Deployments and unhealthy Pods.
* Track desired, ready, and available replicas.
* Persist incidents and their evidence.
* Implement incident lifecycle management.
* Record detection timestamps and state transitions.
* Prevent duplicate open incidents for the same resource.
* Distinguish current resource health from the resolution state of an incident.
* Test detection behavior under normal and degraded conditions.

Deliverables

* Deterministic incident detector.
* Persistent incident history.
* Evidence-based incident classifications.
* Auditable incident lifecycle.
* Automated incident detection tests.

Completion Criteria

CloudHeal detects supported failure conditions, records the relevant evidence, and tracks incidents accurately without incorrectly declaring unresolved incidents resolved.

⸻

Phase 6 — Safe Self-Healing Engine

Goal: Implement a complete recovery workflow with deterministic safety controls and independent verification.

Tasks

* Define supported recovery actions.
* Implement recovery-policy evaluation.
* Validate incident state and recovery eligibility.
* Prevent duplicate active recovery attempts.
* Persist recovery attempts and their outcomes.
* Implement a recovery executor that uses the appropriate infrastructure adapter.
* Handle execution failures, timeouts, and uncertain outcomes.
* Independently inspect the resulting infrastructure state.
* Verify recovery against explicit success criteria.
* Resolve incidents only when resolution conditions are satisfied.
* Implement recovery reconciliation for interrupted or unresolved attempts.
* Record decisions, actions, verification evidence, and outcomes.
* Test concurrent requests, repeated failures, and recovery conflicts.

Deliverables

* Deterministic recovery policy.
* Safe recovery coordinator.
* Recovery executor.
* Independent outcome verification.
* Persistent recovery history.
* Recovery reconciliation and failure handling.

Completion Criteria

CloudHeal can detect a supported incident, evaluate whether recovery is permitted, execute an approved action, independently verify the outcome, and resolve or retain the incident according to the verified result.

Kubernetes continues to handle ordinary container restarts and standard orchestration. CloudHeal coordinates higher-level recovery actions that require its own policies and verification.

⸻

Phase 7 — Multi-Node Failure Testing and Recovery Safety

Goal: Demonstrate CloudHeal’s behavior under realistic infrastructure and application failures.

Tasks

* Test container and Pod failures.
* Test application readiness failures.
* Test Deployment degradation.
* Test worker-node unavailability.
* Test temporary network disconnections.
* Test insufficient resources and placement constraints.
* Test failed remediation and uncertain execution outcomes.
* Prevent duplicate recovery execution.
* Evaluate recovery behavior during repeated or concurrent incidents.
* Document interactions between Kubernetes recovery and CloudHeal remediation.
* Identify scenarios that require additional fencing, leases, or execution coordination.

Deliverables

* Reproducible failure scenarios.
* Automated integration tests where practical.
* Recovery evidence and incident timelines.
* Documented failure-handling limitations.
* Safety-validation results.

Completion Criteria

Supported failure scenarios produce predictable, auditable behavior. CloudHeal does not claim successful recovery without verification, and uncertain outcomes are handled conservatively.

⸻

Phase 8 — Observability, Metrics, and Evaluation

Goal: Measure the reliability and effectiveness of the private cloud and self-healing system.

Tasks

* Track node and workload health.
* Record incident detection time.
* Record recovery initiation and completion times.
* Measure service disruption during recovery.
* Track successful, failed, and uncertain recovery attempts.
* Track policy rejections and unsafe actions prevented.
* Evaluate duplicate recovery attempts and recovery conflicts.
* Record infrastructure resource utilization.
* Establish repeatable baseline experiments.
* Compare baseline orchestration behavior with CloudHeal-assisted recovery where meaningful.

Deliverables

* Operational metrics.
* Incident and recovery reports.
* Reproducible evaluation scenarios.
* Documented results and limitations.

Completion Criteria

CloudHeal’s behavior can be evaluated using recorded evidence and measurable outcomes rather than demonstrations alone.

⸻

Phase 9 — AI-Assisted Operational Intelligence

Goal: Add AI-assisted diagnosis and recovery planning without compromising deterministic safety.

Tasks

* Collect and structure incident evidence.
* Build a searchable incident knowledge base.
* Retrieve relevant historical incidents and recovery outcomes.
* Integrate an LLM for evidence-based diagnosis.
* Generate proposed recovery plans.
* Add constrained tool calling where appropriate.
* Evaluate LangGraph or a similar orchestration framework if it provides a concrete benefit.
* Require deterministic policy approval before executing proposed actions.
* Log AI recommendations and the decisions made about them.
* Evaluate diagnostic usefulness and failure modes.
* Ensure deterministic recovery remains available when AI services are unavailable.

Deliverables

* Evidence-grounded incident diagnosis.
* AI-assisted recovery recommendations.
* Constrained operational tools.
* Auditable AI-assisted decisions.
* Evaluation of accuracy, usefulness, and safety.

Completion Criteria

AI improves diagnosis or planning in measured scenarios while remaining subject to CloudHeal’s deterministic safety controls.

AI is not required for core infrastructure operation or basic recovery.

⸻

Phase 10 — Independent Deployment and Final Demonstration

Goal: Package CloudHeal as a reproducible platform and demonstrate its complete workflow.

Tasks

* Define the deployment and configuration model.
* Package the CloudHeal platform and its dependencies.
* Document Kubernetes prerequisites and supported environments.
* Configure authentication and permissions.
* Document installation, startup, upgrades, and troubleshooting.
* Verify persistence across restarts.
* Prepare repeatable end-to-end demonstrations.
* Record baseline and recovery metrics.
* Document architecture, interfaces, security considerations, and limitations.

Final Demonstration

The demonstration should show:

1. A working private Kubernetes cluster.
2. CloudHeal managing the cluster through its own API.
3. An application deployed and accessible through the platform.
4. A genuine application or infrastructure failure.
5. CloudHeal detecting and classifying the incident.
6. A deterministic policy approving or rejecting a recovery action.
7. Safe execution of an approved action.
8. Independent verification of the result.
9. Correct incident and recovery history.
10. Measurable recovery and availability results.
11. AI-assisted diagnosis, if implemented and evaluated.

Completion Criteria

CloudHeal can be deployed using documented procedures and demonstrates private-cloud management and safe self-healing on the supported infrastructure.

⸻

Implementation Priorities

The immediate priorities are:

1. Finalize the Kubernetes infrastructure design.
2. Establish and validate the initial multi-node cluster.
3. Demonstrate application deployment, networking, and access.
4. Integrate CloudHeal’s management API with Kubernetes.
5. Complete the deterministic self-healing workflow.
6. Evaluate failure scenarios and recovery metrics.
7. Add AI-assisted operational intelligence.
8. Package and demonstrate the complete platform.

Development Rules

* Inspect existing code before modifying it.
* Preserve existing user changes and working functionality.
* Avoid duplicating Kubernetes orchestration capabilities.
* Make incremental changes with focused tests.
* Validate infrastructure behavior on real machines.
* Distinguish implemented features from planned capabilities.
* Do not treat passing unit tests as proof of end-to-end functionality.
* Keep recovery decisions deterministic and auditable.
* Never claim successful recovery without independent verification.
* Document limitations rather than hiding them.

Definition of Success

CloudHeal succeeds when it provides a reproducible private-cloud management platform, runs real workloads across supported infrastructure, exposes its own management interface, detects and responds safely to supported failures, verifies recovery independently, and demonstrates its reliability through measurable evidence.

AI-assisted intelligence extends this foundation; it does not replace it.