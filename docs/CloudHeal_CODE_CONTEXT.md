# CloudHeal Code Context & Workflow

Last updated: 2026-10-10

## Purpose of this file

This file is the reusable engineering context for CloudHeal. Share or
attach it in a new ChatGPT conversation so the assistant can continue
from the current architecture and implementation state without
repeatedly asking for the same source files.

**Important maintenance rule:** Update this file whenever architecture,
file responsibilities, commands, implementation status, or the next
milestone changes. Distinguish code that is verified in the repository
from code that has only been proposed.

------------------------------------------------------------------------

## 1. Project goal

CloudHeal is a student-built, small cloud platform that runs workloads
across a few laptops connected through a private network. It is being
built bottom-up:

1.  Laptop/node infrastructure
2.  Node Agent and node registration/heartbeats
3.  Private networking and node reachability
4.  Workload model and lifecycle
5.  Scheduling and remote execution
6.  Runtime status/reconciliation
7.  Later: monitoring, fault detection, recovery/self-healing,
    dashboard, and application workloads

Initial target is a free/local demo while participating laptops are
powered on, not a 24/7 production cloud. Do not introduce Kubernetes or
production-scale complexity prematurely.

## 2. User's engineering preferences

-   Explain the architecture and purpose before suggesting code changes.
-   Implement incrementally and verify each milestone before moving on.
-   Preserve working components; avoid unnecessary rewrites.
-   Give practical, implementation-first explanations rather than long
    theory.
-   Be clear about what is implemented, what has been tested, and what
    remains unverified.
-   Inspect the current code before proposing changes when the source is
    available.
-   Update this context file after meaningful architecture or progress
    changes.

## 3. Repository and environment

Repository root: `/Users/aniketsaini/Desktop/CloudHeal`

Python environment uses `uv`. The root workspace currently includes the
Node Agent package; Control Plane is a separate workspace package.

Key commands from repository root:

``` bash
# Control Plane
uv run --package cloudheal-control-plane cloudheal-control-plane

# Node Agent
uv run --package cloudheal-node-agent cloudheal-node-agent

# Compile/check Control Plane Python files
uv run --package cloudheal-control-plane python -m compileall \
  control-plane/src/cloudheal_control_plane

# Show source files
find control-plane -type f -name "*.py" -not -path "*/__pycache__/*"
find infrastructure/node-agent -type f -name "*.py" -not -path "*/__pycache__/*"
```

Ports: - Control Plane: `9000` - Node Agent: `8000`

Control Plane API docs when it is running locally:
`http://127.0.0.1:9000/docs`

## 4. Current architecture

``` text
                      Control Plane (:9000)
                   +---------------------------+
                   | Node registry             |
                   | Workload registry         |
                   | Workload service          |
                   | Workload scheduler        |
                   | HTTP API                  |
                   +-------------+-------------+
                                 |
                       intended HTTP dispatch
                                 |
                                 v
                       Node Agent (:8000)
                   +---------------------------+
                   | Node identity             |
                   | Registration/heartbeat    |
                   | System information         |
                   | Container API             |
                   | Docker runtime             |
                   +-------------+-------------+
                                 |
                                 v
                              Docker
                         workload container
```

The intended end-to-end lifecycle is:

``` text
POST /workloads
      |
      v
PENDING
      |
POST /workloads/{id}/schedule
      |
      v
Scheduler selects a healthy node
and records node_id
      |
      v
SCHEDULED
      |
      |  This dispatch connection is the current implementation gap
      v
Control Plane POSTs workload to Node Agent /containers
      |
      v
Node Agent invokes Docker and inspects the container
      |
      v
Node Agent confirms RUNNING
      |
      v
Control Plane stores actual_state = RUNNING
```

On a dispatch/runtime error, the Control Plane should record `FAILED`,
not falsely report `RUNNING`.

## 5. Node Agent: files and responsibilities

Package path: `infrastructure/node-agent/src/cloudheal_node_agent/`

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `api.py`                            FastAPI endpoints, lifespan
                                      startup, registration and heartbeat
                                      startup, `POST /containers`

  `identity.py`                       Persistent node UUID stored at
                                      `~/.cloudheal/node_id`

  `network.py`                        Determines local network IP

  `system.py`                         System information using `psutil`

  `registration.py`                   Registers this node with Control
                                      Plane

  `heartbeat.py`                      Periodic heartbeat loop

  `models.py`                         Node-related request/response
                                      models

  `runtime.py`                        Docker container creation and
                                      verification

  `workload_models.py`                Validation model for container
                                      execution request

  `main.py`                           Starts the Node Agent application
  -----------------------------------------------------------------------

### Current Node Agent behavior

`api.py` imports and calls `run_container()` from `runtime.py` in the
`POST /containers` endpoint. The request model fields are:

``` python
class ContainerRunRequest(BaseModel):
    workload_id: UUID
    image: str = Field(min_length=1, max_length=255)
    cpu_limit: float = Field(gt=0, le=8)
    memory_limit_mb: int = Field(gt=0, le=2048)
```

`runtime.py` currently:

1.  Names containers `cloudheal-{workload_id}`.
2.  Runs `docker container inspect` to check whether that named
    container exists.
3.  If it exists and is running, returns its ID and `status: RUNNING`.
4.  If it exists but is stopped, raises `ContainerExecutionError` (does
    not restart it yet).
5.  Otherwise runs
    `docker run --detach --name ... --cpus ... --memory ... <image>`.
6.  Inspects the created container and verifies that Docker reports it
    as running.
7.  Returns `workload_id`, `container_id`, `container_name`, and
    `status: RUNNING`.

The Node Agent API catches `ContainerExecutionError` and responds with
HTTP 409.

### Important configuration detail

At the last inspected version, Node Agent `api.py` contains:

``` python
CONTROL_PLANE_URL = "http://100.90.104.13:9000"
```

This is the Control Plane's configured Tailscale IP at that time. Verify
it if networking changes. Do not assume it is still correct without
checking.

Node Agent listens on port 8000. The Control Plane has previously shown
a registered node address of `192.168.0.6`; this is a LAN address and
may not be reachable outside that LAN. Cross-laptop dispatch should use
a reachable address on the chosen private network. Networking/address
advertisement remains an item to verify.

The inspected `api.py` had a duplicate `from fastapi import FastAPI`
import. It is harmless but can be cleaned up when touching that file.

## 6. Control Plane: files and responsibilities

Package path: `control-plane/src/cloudheal_control_plane/`

  -----------------------------------------------------------------------
  File                                Responsibility
  ----------------------------------- -----------------------------------
  `main.py`                           Starts the Control Plane
                                      application

  `api.py`                            FastAPI endpoints and shared
                                      in-memory workload objects

  `registry.py`                       In-memory node registry and node
                                      heartbeat updates

  `workloads/models.py`               Desired state, actual state, create
                                      request, workload record

  `workloads/registry.py`             In-memory workload storage

  `workloads/service.py`              Workload CRUD/service layer

  `workloads/scheduler.py`            Chooses the first healthy node and
                                      marks workload `SCHEDULED`

  `workloads/dispatcher.py`           **Not confirmed as created yet.**
                                      Proposed next component for sending
                                      workload requests to Node Agents.
  -----------------------------------------------------------------------

### Node registry

`NodeRecord` fields: - `node_id: str` - `hostname: str` -
`address: str` - `status: str = "healthy"` -
`last_seen: datetime | None`

The registry is an in-memory dictionary. Functions include
`register_node`, `get_nodes`, `get_node`, and `heartbeat_node`.

### Workload state model

`DesiredState`: - `RUNNING` - `STOPPED`

`WorkloadState`: - `PENDING` - `SCHEDULED` - `RUNNING` - `FAILED` -
`STOPPED`

`WorkloadCreate` accepts `name`, `image`, `desired_state` (default
`RUNNING`), `cpu_limit` (default `1.0`, greater than zero), and
`memory_limit_mb` (default `256`, greater than zero).

`WorkloadRecord` includes: - `workload_id` (UUID) - `name`, `image` -
`desired_state`, `actual_state` - `node_id` (optional UUID) -
`cpu_limit`, `memory_limit_mb` - `created_at`, `updated_at`

### Scheduler behavior

Current `workloads/scheduler.py`:

-   Retrieves the workload by UUID.
-   Requires `actual_state == PENDING`.
-   Requires desired state `RUNNING`.
-   Gets registered nodes and filters those whose status lowercases to
    `healthy`.
-   Selects the first healthy node (simple initial policy).
-   Sets `workload.node_id` to selected node UUID.
-   Sets `actual_state = SCHEDULED` and updates timestamp.
-   Stores and returns the workload through `WorkloadService`.

**The scheduler currently does not contact the Node Agent.** It only
assigns a node and marks the workload `SCHEDULED`.

### Current Control Plane API routes

-   `GET /health`
-   `POST /nodes/register`
-   `GET /nodes`
-   `GET /nodes/{node_id}`
-   `POST /nodes/{node_id}/heartbeat`
-   `POST /workloads`
-   `GET /workloads`
-   `GET /workloads/{workload_id}`
-   `POST /workloads/{workload_id}/schedule`

The scheduling endpoint currently invokes
`workload_scheduler.schedule(workload_id)` and handles `LookupError` as
404 and `SchedulingError` as 409. The dispatcher call and lifecycle
update after scheduling are not yet present in the last confirmed
source.

### Control Plane dependencies

Last inspected `control-plane/pyproject.toml` dependencies:

``` toml
dependencies = [
    "fastapi>=0.142.2",
    "uvicorn>=0.54.0",
    "pydantic>=2.13.5",
]
```

`httpx` was **not** listed at the time of inspection. Add it using:

``` bash
uv add --package cloudheal-control-plane httpx
```

Do not assume this command or dispatcher implementation has been run
successfully until verified.

## 7. Recent observed state and tests

Observed in earlier terminal/API output: - Control Plane runs on port
9000. - Node Agent runs on port 8000. - Node Agent registers with
Control Plane and heartbeats. - Registered Mac node has previously
appeared with hostname `Anikets-MacBook-Air.local`, address
`192.168.0.6`, and status `healthy`. - A workload such as
`test-workload` with image `nginx:latest`, CPU 1 and memory 256 MB was
created and scheduled. - The example workload response showed
`actual_state: SCHEDULED` and a selected `node_id`. - Node Agent's
`POST /containers` endpoint was observed returning HTTP 201 in its
access log, but that log alone does not prove the Control Plane
dispatched the workload or that the whole workflow succeeded. - Node
Agent's `runtime.py` contains Docker start-and-inspect logic, but do not
claim the full Control Plane → Node Agent → Docker workflow has been
verified end to end unless freshly tested.

Both node and workload registries are currently in memory; restarting
the relevant process clears its registry data.

## 8. Immediate next milestone: end-to-end dispatch

**Status: planned, not confirmed implemented.**

1.  Add `httpx` to the Control Plane package using `uv`.
2.  Create
    `control-plane/src/cloudheal_control_plane/workloads/dispatcher.py`.
3.  Dispatcher takes a `WorkloadRecord` and selected `NodeRecord`,
    constructs `http://{node.address}:8000/containers`, and sends JSON
    fields:
    -   `workload_id`
    -   `image`
    -   `cpu_limit`
    -   `memory_limit_mb`
4.  Use a timeout slightly greater than the Node Agent Docker run
    timeout (Docker call currently has a 300-second timeout).
5.  Validate HTTP status, response JSON, matching workload ID, and
    `status == "RUNNING"`.
6.  Integrate dispatch into the existing schedule API without rewriting
    the scheduler.
7.  On success, set and persist `actual_state = RUNNING`.
8.  On dispatch/execution failure, set and persist
    `actual_state = FAILED`, and return an appropriate HTTP error.
9.  Compile the package and test first on one machine, then test across
    the private network.
10. Verify independently with `docker ps` and `docker inspect`.

### Important edge case for later

If Docker starts the container but the Node Agent's response is lost,
the Control Plane might mark the workload `FAILED` while the container
is actually running. Future reconciliation/retry logic should resolve
this. Do not overbuild this before the basic workflow works.

### First test payload

Create via `POST /workloads`:

``` json
{
  "name": "nginx-test",
  "image": "nginx:latest",
  "desired_state": "RUNNING",
  "cpu_limit": 1,
  "memory_limit_mb": 256
}
```

Copy the returned workload UUID and call
`POST /workloads/{workload_id}/schedule`.

Expected success: - Response workload `actual_state` is `RUNNING`. -
Node Agent returns the matching workload ID, container ID/name, and
`status: RUNNING`. - `docker ps --filter "name=cloudheal-"` shows the
container.

## 9. Collaboration protocol for future ChatGPT sessions

At the start of a CloudHeal session, read this file first. Then:

1.  Ask the user for only the latest status or exact error, not for all
    code already described here.
2.  If a file has changed since this snapshot, ask for that file or have
    the user provide current output before modifying it.
3.  Keep the existing architecture unless a concrete reason justifies
    changing it.
4.  After a milestone, update the status sections in this file and keep
    the "implemented vs planned" distinction accurate.
5.  Do not state that tests passed unless the user has supplied
    successful output or the test was actually run.
