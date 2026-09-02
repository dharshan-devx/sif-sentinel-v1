"""Single access point for the active local SIF model and its saved metadata."""
from app.ml.inference.predictor import SIFPredictor

_current_sif_model = SIFPredictor()


def get_current_sif_model() -> SIFPredictor:
    return _current_sif_model


def get_model_metadata() -> dict:
    return get_current_sif_model().metadata()
