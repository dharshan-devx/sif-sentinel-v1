# Artifacts

This directory contains generated outputs from the machine learning training pipeline.

- `models/`: Stores exported models, vectorizers, and metadata (`*.joblib`, `*.pkl`, `metadata.json`, etc.) ready to be loaded by the backend inference engine.
- **Do not commit large model artifacts directly** unless explicitly permitted (e.g., small synthetic demo models).

## Runtime catalog

The backend default is the paired `models/v2/model/sif_model.joblib` and
`models/v2/vectorizer/tfidf.joblib` artifact set. They must be loaded together;
the root-level legacy files are retained for provenance and are not the default
runtime pair.

`models/v4b_transformer/` contains tokenizer/configuration and evaluation
metadata only. Its metadata explicitly marks it as unavailable at runtime
because trained weights are not in this repository. Do not configure
`SIF_MODEL_BACKEND=v4b_transformer` until versioned weights and the optional
PyTorch/Transformers runtime dependencies have been provisioned.
