# Repository Architecture and Structure

## Overview
SIF SENTINEL is organized into a modular monolith with clear boundaries for distinct development lifecycles.

### Layers
- **Presentation:** UI/Web tier.
- **Application/API:** Core orchestration and HTTP endpoints.
- **Domain Intelligence:** Business rules and specialized analytical engines.
- **ML Inference:** Execution of trained models within the backend.
- **Persistence:** Relational databases and object storage.

## Directory Boundaries

### `frontend/`
- **Purpose:** Next.js application UI.
- **Expectation:** Consumes backend APIs only. Must not couple to Python code or access the DB.

### `backend/`
- **Purpose:** FastAPI modular monolith running the application logic and ML inference.
- **Expectation:** Should not contain ML training code, notebooks, or overarching documentation. It runs the system.

### `ml/`
- **Purpose:** Machine learning research, experiments, training, and pipelines.
- **Expectation:** A sandbox for data scientists to use Colab/Jupyter. Models generated here are exported.

### `artifacts/`
- **Purpose:** Generated artifacts (e.g. models, vectorizers) from the `ml/` pipeline.
- **Expectation:** Models here are loaded by the `backend/` inference layer.

### `data/`
- **Purpose:** Lifecycle management for datasets (raw -> interim -> processed).
- **Expectation:** Do not commit large datasets. Only synthetic or down-sampled demo data should be tracked.

### `docs/`
- **Purpose:** System architecture, intelligence documentation, and demo scripts.
- **Expectation:** A central knowledge base for the entire project.

### `scripts/`
- **Purpose:** Shared tooling for setups, database seeds, and environments.
- **Expectation:** Cross-cutting developer experience utilities.
