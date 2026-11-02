☁️ CloudHeal

Intelligent Private Cloud Management & Self-Healing Infrastructure Platform

<p align="center">
  <strong>Monitor. Detect. Recover. Verify.</strong>
  <br/>
  Building a resilient private cloud with Kubernetes-native orchestration and intelligent infrastructure management.
</p>

⸻

🚀 Overview

CloudHeal is a cloud-agnostic private-cloud management and self-healing platform designed to monitor infrastructure, detect failures, coordinate recovery, and improve workload reliability.

Built around Kubernetes, CloudHeal adds an infrastructure intelligence and recovery coordination layer on top of standard container orchestration.

Instead of reinventing Kubernetes, CloudHeal works alongside it:

* Kubernetes handles container scheduling, workload lifecycle, and orchestration.
* CloudHeal monitors infrastructure and workload health.
* CloudHeal detects and classifies infrastructure incidents.
* Its recovery system is designed to apply deterministic safety policies before coordinating recovery.
* Recovery outcomes can be independently verified.

The long-term goal is to make private-cloud infrastructure more observable, resilient, and easier to manage.

🎯 Why CloudHeal?

Infrastructure failures can happen for many reasons:

* Worker nodes going offline.
* Network connectivity interruptions.
* Unhealthy workloads.
* Deployment availability problems.
* Infrastructure resource exhaustion.

Traditional orchestration can handle many workload-level failures, but infrastructure operators also need visibility into what happened, why it happened, and whether recovery actually succeeded.

CloudHeal aims to bridge that gap through infrastructure monitoring, incident management, and controlled recovery coordination.

🏗️ Architecture

CloudHeal follows a modular architecture with three major components.

1. CloudHeal Control Plane

The central management and coordination layer.

Responsibilities:

* Node registration and identity validation.
* Heartbeat monitoring.
* Infrastructure health monitoring.
* Kubernetes workload discovery.
* Incident detection and classification.
* Incident persistence.
* Recovery policy and safety evaluation.
* Recovery coordination.
* Post-recovery verification.

2. CloudHeal Node Agent

A lightweight agent designed to run on infrastructure hosts.

Responsibilities:

* Host registration.
* Periodic heartbeats.
* Host identity reporting.
* CPU and memory monitoring.
* Disk and operating-system information.
* Runtime and network information.

3. Kubernetes / K3s Infrastructure

Kubernetes provides the underlying orchestration capabilities.

Responsibilities:

* Container lifecycle management.
* Pod scheduling.
* Deployment reconciliation.
* Replica management.
* Service networking.
* Workload rescheduling.
* Node health and lifecycle management.

Architecture principle: Kubernetes remains the authoritative orchestration system. CloudHeal adds monitoring, incident intelligence, and recovery coordination.

🔄 How CloudHeal Works

         Infrastructure Hosts
                  |
                  v
          CloudHeal Node Agents
                  |
             Heartbeats
                  |
                  v
          CloudHeal Control Plane
                  |
          Health Monitoring
                  |
                  v
           Incident Detection
                  |
                  v
          Incident Classification
                  |
                  v
           Safety / Policy Gate
                  |
                  v
         Recovery Coordination
                  |
                  v
          Kubernetes / Provider
                  |
                  v
          Recovery Verification

The recovery architecture is designed around deterministic safety controls. AI-assisted diagnosis and planning are planned as optional capabilities, not prerequisites for reliable operation.

🧪 Live Infrastructure Demonstration

CloudHeal is being developed and tested using a private multi-laptop K3s cluster connected through Tailscale.

Test Environment

Machine	Role	Environment
MacBook	K3s control plane and CloudHeal Control Plane	Ubuntu Multipass
Windows Laptop 1	Kubernetes worker	Ubuntu WSL2
Windows Laptop 2	Kubernetes worker	Ubuntu WSL2

Workload Failover Test

A video-streaming website is deployed inside the private Kubernetes cluster.

The failover demonstration follows this sequence:

1. Deploy the website on a preferred worker.
2. Verify that the website is accessible over the private network.
3. Stop the worker’s K3s Agent to simulate worker failure.
4. Kubernetes detects the node failure.
5. The Deployment becomes eligible for scheduling on another available worker.
6. Kubernetes creates a replacement Pod on the Mac worker.
7. Verify that the website remains accessible.
8. Restart the disconnected worker.
9. Verify that Kubernetes can schedule the workload back onto the preferred worker.

Important: Kubernetes performs the actual Pod rescheduling. CloudHeal independently monitors workload health and detects incidents. Automatic CloudHeal recovery remains disabled during this demonstration.

This test demonstrates Kubernetes-native workload resilience alongside CloudHeal’s monitoring capabilities.

🛠️ Technology Stack

Category	Technologies
Backend	Python
API Framework	FastAPI / Starlette
Infrastructure Orchestration	Kubernetes, K3s
Container Runtime	containerd
Infrastructure Agents	Python
Networking	Tailscale
Testing	pytest
Package Management	uv
Version Control	Git, GitHub

The stack reflects the technologies used or integrated in the current development environment.

🛡️ Design Principles

CloudHeal is being developed with the following principles:

1. Kubernetes-Native

Use Kubernetes APIs and reconciliation instead of implementing a competing orchestration engine.

2. Cloud-Agnostic

Keep infrastructure integrations modular so the platform can support different private-cloud environments.

3. Safety First

Recovery actions must pass deterministic policy and safety checks.

4. Observable Infrastructure

Maintain visibility into nodes, workloads, incidents, and recovery outcomes.

5. Independent Recovery Verification

A recovery action is not considered successful merely because it was initiated. The resulting infrastructure and workload state must be checked.

6. AI as an Optional Intelligence Layer

AI may assist with diagnosis and recovery planning, but critical infrastructure decisions remain controlled by deterministic safeguards.

🗺️ Development Roadmap

CloudHeal is actively under development.

Phase	Focus	Status
Phase 1	Core project foundation	Completed
Phase 2	Control Plane and Node Agent foundations	Completed
Phase 3	Repeatability and testing	Completed
Phase 4	Windows worker integration	Functionally completed
Phase 5	Multi-laptop private-cloud integration	In progress
Phase 6	Kubernetes RBAC and access control	Planned
Phase 7	Recovery safety and policy enforcement	Planned
Phase 8	Operational reliability and verification	Planned
Future	AI-assisted incident diagnosis and recovery planning	Planned

Roadmap statuses will evolve as implementation and validation progress.

🔐 Safety & Reliability

CloudHeal is designed with infrastructure safety in mind.

* Automatic recovery is disabled by default.
* Recovery actions require explicit safety evaluation.
* Kubernetes remains responsible for standard workload reconciliation.
* AI is not required for core infrastructure operation.
* Recovery results must be independently verified.
* Infrastructure changes should be auditable.

💻 Getting Started

CloudHeal is currently an active development project.

To explore the codebase:

git clone https://github.com/anikettt-cd/CloudHeal.git
cd CloudHeal

Install the Python environment using uv:

uv sync

Run the project tests:

uv run pytest

Individual workspace packages and services may have their own execution commands and environment requirements.

Note: A complete standalone deployment guide is still part of the project’s ongoing development.

🔮 Future Vision

The long-term vision for CloudHeal is to evolve into an intelligent private-cloud operations platform featuring:

* Advanced infrastructure observability.
* Automated incident correlation.
* Policy-driven infrastructure recovery.
* Node lifecycle management.
* Workload protection and availability management.
* Provider-specific infrastructure adapters.
* AI-assisted incident diagnosis.
* Intelligent recovery planning.
* Recovery audit trails and verification.

The objective is not simply to restart failed workloads, but to build infrastructure that can understand failures, coordinate safe recovery, and verify that services return to a healthy state.

👨‍💻 Author

Aniket Saini

Information Technology Engineering Student | Backend & Applied AI Engineering

* GitHub: @anikettt-cd
* Project: CloudHeal

⸻

<p align="center">
  <strong>CloudHeal — Building Infrastructure That Can Recover.</strong>
  <br/>
  <sub>Designed for resilience. Built around Kubernetes. Evolving toward intelligent infrastructure operations.</sub>
</p>
