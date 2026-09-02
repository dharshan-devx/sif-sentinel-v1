from app.ml.inference.predictor import SIFPrediction, SIFPredictor

_predictor = SIFPredictor()


def classify_sif(text: str) -> SIFPrediction:
    return _predictor.predict(text)


def model_metadata() -> dict:
    return _predictor.metadata()
