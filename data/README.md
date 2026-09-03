# Data Lifecycle

This directory stores datasets for SIF SENTINEL.

## Structure
- `raw/`: Original source datasets. Never modify these in place.
- `interim/`: Temporary/transformed datasets used during processing.
- `processed/`: Cleaned datasets ready for training/evaluation.
- `external/`: Third-party datasets.
- `samples/`: Small datasets suitable for tests, development, demos, and CI.

## Large Dataset Policy
- **Do not commit large datasets directly to the repository.**
- Use approved object storage, Git LFS, or another controlled data distribution mechanism when dataset size exceeds repository limits.
- The datasets currently in this repository are synthetic or down-sampled for demonstration purposes.
