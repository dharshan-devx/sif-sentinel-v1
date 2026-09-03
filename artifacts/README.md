# Artifacts

This directory contains generated outputs from the machine learning training pipeline.

- `models/`: Stores exported models, vectorizers, and metadata (`*.joblib`, `*.pkl`, `metadata.json`, etc.) ready to be loaded by the backend inference engine.
- **Do not commit large model artifacts directly** unless explicitly permitted (e.g., small synthetic demo models).
