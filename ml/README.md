# Machine Learning Research

This directory contains research, training pipelines, and experiments for SIF SENTINEL.

## Boundaries
- **Research vs Inference:** This `ml/` directory is strictly for research, dataset generation, and model training (e.g. Jupyter notebooks, pipelines).
- **Runtime Inference:** The backend application's runtime inference logic remains in `backend/app/ml/`.
- **Artifacts:** Generated models from training (joblib, ONNX, etc.) must be saved to the top-level `artifacts/models/` directory, NOT here.
