# SIF SENTINEL

SIF SENTINEL is an advanced intelligence platform for Severe Incident and Fatality (SIF) precursor detection, risk scoring, and intervention recommendation.

## Architecture
The system consists of:
- **Frontend:** A Next.js UI (see `frontend/`)
- **Backend:** A FastAPI Modular Monolith (see `backend/`)
- **Intelligence Engines:** Deterministic NLP, Risk, and Intervention engines powered by trained models.

## Repository Structure
Please refer to [docs/architecture/REPOSITORY_STRUCTURE.md](docs/architecture/REPOSITORY_STRUCTURE.md) for the exact boundary definitions.
- `backend/` - Application Runtime
- `frontend/` - UI
- `ml/` - ML Research and Training
- `data/` - Datasets
- `artifacts/` - Generated models
- `docs/` - Documentation
- `scripts/` - Automation and utilities

## Local Development
For backend setup, testing, and execution, see [backend/README.md](backend/README.md).
