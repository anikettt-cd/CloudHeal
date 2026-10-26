✅ The CloudHeal Control Plane is responding correctly.

Your output confirms:

* API title: CloudHeal Control Plane
* Version: 0.1.0
* Registered routes: 12
* API availability: Confirmed

Mac validation summary

We’ve now verified the main CloudHeal workflow on your Mac:

1. K3s integration — CloudHeal reads real Kubernetes state.
2. Application monitoring — The background monitor checks configured deployments.
3. Incident detection — It detected an unhealthy pod and recorded incident #6.
4. Recovery execution — Recovery attempt #1 succeeded.
5. Recovery verification — CloudHeal confirmed that the deployment was healthy after recovery.
6. Incident resolution and history — Resolved incidents, evidence, and recovery records persist.
7. Service availability — The Control Plane API remains accessible.

Automatic recovery — Verified

The complete automatic recovery workflow has now been demonstrated against the local K3s test deployment.

During the live test:

1. CloudHeal detected a degraded deployment and persisted incident #7.
2. The background monitor initiated recovery with the automatic trigger.
3. CloudHeal requested a deployment rollout restart.
4. The recovery executor independently checked deployment health.
5. All three desired replicas returned to Ready and Available status.
6. Recovery attempt #2 was persisted as SUCCEEDED, and incident #7 was marked RESOLVED.

The test deployment, cloudheal-recovery-demo, returned to 3/3 ready replicas. The protected cloudheal-demo deployment remained healthy at 1/1.

Current result: The automatic detect → recover → verify → resolve workflow is verified in the local Mac/K3s environment.

Still outstanding: Multi-laptop worker integration, broader failure-mode testing, and validation of the private cloud across the Tailscale network. Local validation does not establish production readiness.
