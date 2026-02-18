# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

keip (Kubernetes Enterprise Integration Patterns) is a Kubernetes operator that deploys Spring Integration routes as Kubernetes resources. It uses Metacontroller to watch `IntegrationRoute` custom resources, calls a Python webhook to generate Deployment/Service manifests, and manages the lifecycle of Spring Boot integration containers.

## Repository Structure

Three independently versioned artifacts in a monorepo:

- **`webapp/`** — Python (3.11) webhook server (Starlette/Uvicorn) that handles Metacontroller sync requests and generates Kubernetes child resources. This is where most active development happens.
- **`operator/`** — Kubernetes manifests (CRD, CompositeController, RBAC) deployed via kustomize.
- **`minimal-app/`** — Default Java 21 Spring Boot container that runs the integration routes.

A root `Makefile` provides aggregate targets that delegate to sub-projects.

**Python 3.11 required** — the webapp uses `logging.getLevelNamesMapping()` (3.11+) and `datetime.fromisoformat()` with `"Z"` suffix (3.11+). On systems without `python3.11` as default, set `HOST_PYTHON=python3.11 make venv`.

## Build & Development Commands

### Webapp (Python) — `webapp/`

```bash
make venv                  # Create virtualenv and install deps (requires python3.11)
make test                  # Run pytest with coverage
make lint                  # Run ruff linter
make format                # Run black formatter
make precommit             # Run test + format + lint (use before committing)
make start-dev-server      # Start uvicorn on :7080 with --reload
```

Run a single test or test file:
```bash
EXTRA_PYTEST_ARGS="-k test_function_name" make test
EXTRA_PYTEST_ARGS="core/test/test_sync.py" make test
EXTRA_PYTEST_ARGS="-vv --log-cli-level=DEBUG" make test  # verbose with debug logging
```

### Operator (K8s Manifests) — `operator/`

```bash
make deploy                # Deploy all operator components via top-level kustomization
make undeploy              # Remove all operator components
make prep-release          # Generate install.yaml and per-component manifests to ./output/
```

Users can also install without cloning: `kubectl apply -f <release-url>/install.yaml` or `kubectl apply -k 'https://github.com/codice/keip/operator?ref=<tag>'`.

### Minimal App (Java) — `minimal-app/`

```bash
mvn clean install          # Build JAR and Docker image (uses Jib)
mvn verify                 # Run tests without install
```

### Root Makefile (delegates to sub-projects)

```bash
make test-webapp           # Run webapp tests
make lint-webapp           # Lint webapp
make precommit-webapp      # Full precommit check
make deploy-operator       # Deploy operator to cluster
make build-minimal-app     # Build Java app
```

## Architecture

```
IntegrationRoute CR  →  Metacontroller  →  Webhook (Python)  →  Deployment + Service
     (user)            (watches CRDs)      (sync.py logic)      (child resources)
```

1. User creates an `IntegrationRoute` resource (`keip.codice.org/v1alpha1`, shortname: `ir`)
2. Metacontroller (v4.11.6) detects it via CompositeController
3. Metacontroller POSTs to the webhook at `/webhook/sync`
4. `core/sync.py` generates a Deployment spec (mounting the route XML from a ConfigMap) and an actuator Service
5. Metacontroller applies the generated child resources

### Webapp Code Layout

- **`app.py`** — Starlette app entrypoint, CORS config, route and addon registration
- **`config.py`** — Env var config (`DEBUG`, `CORS_ALLOWED_ORIGINS`, `INTEGRATION_IMAGE`)
- **`models.py`** — Pydantic models for request/response validation
- **`core/sync.py`** — Core sync logic. `VolumeConfig` class handles volume/mount generation. Key functions: `_new_deployment()`, `_new_actuator_service()`, `_compute_status()`, `_gen_children()`
- **`logconf.py`** — Logging config; reads `LOG_LEVEL` env var via `get_log_level_from_env()` (uses `logging.getLevelNamesMapping()`, Python 3.11+)
- **`core/k8s_client.py`** — Kubernetes API client wrappers (used by deploy route)
- **`routes/webhook.py`** — Core Metacontroller webhook endpoint (`build_webhook()` factory)
- **`routes/deploy.py`** — `/route` endpoint for direct deployment via K8s API
- **`addons/certmanager/`** — Optional cert-manager TLS integration addon (registered in `app.py`)

### Operator Manifest Layout

- **`kustomization.yaml`** — Top-level kustomization (references metacontroller, crd, controller)
- **`controller/composite-controller.yaml`** — Metacontroller CompositeController definition
- **`controller/namespace.yaml`** — keip namespace
- **`controller/webhook-deployment.yaml`** — Webhook Deployment + Service
- **`controller/core-privileges.yaml`** — RBAC (ServiceAccounts, Roles, ClusterRoles)
- **`controller/keip-controller-props.yaml`** — ConfigMap with default integration image
- **`crd/crd.yaml`** — IntegrationRoute CRD definition

## Key Environment Variables (Webapp)

| Variable | Default | Source | Purpose |
|---|---|---|---|
| `INTEGRATION_IMAGE` | `keip-integration` | `config.py` | Container image for integration routes |
| `CORS_ALLOWED_ORIGINS` | `""` | `config.py` | Comma-separated allowed origins |
| `DEBUG` | `false` | `config.py` | Starlette debug mode |
| `LOG_LEVEL` | `INFO` | `logconf.py` | Python logging level (requires Python 3.11+) |

## Testing

Tests live adjacent to source in `test/` subdirectories with shared utilities in `webapp/conftest.py`:
- `webapp/core/test/` — sync, status, k8s_client tests
- `webapp/routes/test/` — deploy, webhook, CORS, webapp integration tests
- `webapp/addons/certmanager/test/` — cert-manager addon tests

Uses pytest, httpx (for async HTTP testing), pytest-mock. Coverage is tracked via `coverage` to `.test_coverage/`.

## CI/CD

GitHub Actions workflows in `.github/workflows/`:
- **`webapp.yml`** — verify-versions → test → lint → build (PR) / release (main). Builds linux/amd64 + arm64.
- **`operator.yml`** — verify-versions → kustomize build (PR) / release (main)
- **`minimal-app.yml`** — verify-versions → Maven verify (PR) / release (main). Java 21.

## Conventions

- Python code formatted with **black**, linted with **ruff**
- Webapp uses **Starlette** (not Flask/FastAPI) as the ASGI framework with **Pydantic** for validation
- Kubernetes manifests managed with **kustomize** (no Helm)
- Container images published to `ghcr.io/codice`
- Operator namespace: `keip`, metacontroller namespace: `metacontroller`
