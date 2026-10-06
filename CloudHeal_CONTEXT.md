# CloudHeal Project Context

## Current project
CloudHeal is a self-healing infrastructure / service-reliability project. The goal is to build a system that can observe a customer service, detect failures, investigate them, take a recovery action, and verify that the service recovered.

Core lifecycle:

Customer Service (Shop API)
        ↓
Observe / Monitor
        ↓
Detector
        ↓
Diagnosis / Decision
        ↓
Executor
        ↓
Verifier
        ↓
Recovered / confirmed

The Shop API is the demo customer workload. The complexity should primarily live in CloudHeal, not in the demo API.

## Development preferences
- Implementation-first teaching.
- Explain important code, libraries, APIs, architecture, and data flow before or alongside implementation.
- Do not turn this into a generic FastAPI tutorial.
- Avoid unnecessary theory and unnecessary toy experiments.
- Move step-by-step and test each stage before progressing.
- Keep the Shop API deliberately small; it exists to give CloudHeal a realistic service to observe and break.
- Do not lose the existing project structure or recreate the workspace from scratch.

## Current root structure

CloudHeal/
├── README.md
├── demo-services/
│   └── shop-api/
│       ├── README.md
│       ├── pyproject.toml
│       └── src/
│           └── shop_api/
│               ├── __init__.py
│               └── main.py
├── docker-compose.yml
├── docs/
│   └── SPEC-001-cloudheal.md
├── monitoring/
│   ├── grafana/
│   └── prometheus/
├── pyproject.toml
├── services/
│   ├── cloudheal-api/
│   ├── detector/
│   ├── executor/
│   ├── fault-injector/
│   └── verifier/
└── uv.lock

Important: monitoring/ directories exist but currently contain no files, and docker-compose.yml is currently empty.

## uv workspace
CloudHeal uses a uv workspace.

There is ONE root lockfile:
    CloudHeal/uv.lock

Do NOT create separate uv.lock files inside individual services.

The intended root workspace configuration is:

[tool.uv.workspace]
members = [
    "services/*",
    "demo-services/*",
]

Each independent service should have its own pyproject.toml while uv manages the workspace with the root lockfile.

The root project currently originated from uv init and has FastAPI/Uvicorn dependencies and a project script. Do not blindly redesign/remove the root project configuration unless that becomes necessary.

## Shop API purpose
Shop API is the first real customer/demo service that CloudHeal will eventually break, detect, recover, and verify.

The API is intentionally simple. We are NOT building a complete e-commerce system.

Current endpoints:
- GET /health
- GET /products
- GET /products/{product_id}

## Shop API dependencies

demo-services/shop-api/pyproject.toml currently contains:

[project]
name = "shop-api"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
authors = [
    { name = "anikettt-cd", email = "sainianiket751@gmail.com" }
]
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.142.2",
    "uvicorn>=0.54.0",
]

[project.scripts]
shop-api = "shop_api:main"

[build-system]
requires = ["uv_build>=0.12.23,<0.13.0"]
build-backend = "uv_build"

FastAPI and Uvicorn were added using:
    uv add --package shop-api fastapi uvicorn

## Current Shop API implementation

demo-services/shop-api/src/shop_api/main.py:

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Shop API")


products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 75000,
    },
    {
        "id": 2,
        "name": "Keyboard",
        "price": 2500,
    },
    {
        "id": 3,
        "name": "Mouse",
        "price": 1200,
    },
]


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found",
    )

## Shop API behavior already verified

The API is run from the CloudHeal root with:

    uv run --package shop-api uvicorn shop_api.main:app --reload

Health test completed successfully:

    curl http://127.0.0.1:8000/health

Response:

    {"status":"healthy"}

The /products endpoint was implemented and tested.

The /products/{product_id} endpoint was implemented and the following tests were completed:
- Existing product IDs return the product.
- A non-existent product returns HTTP 404.
- Invalid path parameters are handled by FastAPI validation.

The Shop API feature set is now considered COMPLETE for the current phase.

## Important architecture distinction
/health currently means the Shop API process is alive and can respond to HTTP requests. It is not intended to prove every dependency is healthy.

A missing product returning 404 is normal application behavior, not a service failure.

This distinction will matter when CloudHeal starts detecting real service failures.

## What should happen next

STOP adding normal Shop API features.

The next phase is the actual CloudHeal functionality:

1. Introduce controlled faults into the Shop API / demo environment.
2. Observe the service and collect signals.
3. Build the Detector.
4. Determine whether an observed problem is an actual service fault.
5. Build the Executor to take a recovery action.
6. Build the Verifier to confirm recovery.
7. Later integrate Prometheus/Grafana and other monitoring infrastructure as appropriate.

Expected high-level flow:

Normal Shop API
    ↓
Controlled fault injection
    ↓
Service degradation/failure
    ↓
CloudHeal observes it
    ↓
Detector identifies abnormal/fault state
    ↓
Executor performs recovery
    ↓
Verifier checks the Shop API
    ↓
Recovery confirmed

## Current state summary
- uv workspace: set up
- root uv.lock: present
- shop-api workspace member: present
- FastAPI dependency: installed
- Uvicorn dependency: installed
- Shop API /health: DONE and verified
- Shop API /products: DONE and verified
- Shop API /products/{product_id}: DONE and verified
- Shop API feature work: STOP HERE
- monitoring config: NOT implemented yet
- docker-compose: currently empty
- next focus: CloudHeal failure injection → detection → recovery → verification

## Key project principle
The Shop API is the workload.
CloudHeal is the product.

Do not spend time turning Shop API into a large application. Build enough realistic behavior to give CloudHeal something meaningful to observe and fail, then focus development effort on the self-healing system.
