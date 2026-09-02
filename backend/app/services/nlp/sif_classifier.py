from app.ml.inference.predictor import SIFPrediction
from app.services.nlp.model_registry import get_current_sif_model, get_model_metadata


def classify_sif(text: str) -> SIFPrediction:
    return get_current_sif_model().predict(text)


def model_metadata() -> dict:
    return get_model_metadata()
