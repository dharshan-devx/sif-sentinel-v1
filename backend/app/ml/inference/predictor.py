import json
import threading
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.core.constants import SIFLevel

ARTIFACT_DIR = Path(__file__).parents[1] / "artifacts"


@dataclass(frozen=True)
class SIFPrediction:
    sif_potential: bool
    probability: float
    sif_level: SIFLevel
    model_name: str
    model_version: str


class SIFPredictor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._model = None
        self._vectorizer = None
        self._metadata: dict = {}

    def _load(self) -> None:
        if self._model is not None:
            return
        with self._lock:
            if self._model is not None:
                return
            model_path = ARTIFACT_DIR / "model" / "sif_logreg.joblib"
            vectorizer_path = ARTIFACT_DIR / "vectorizer" / "tfidf.joblib"
            metadata_path = ARTIFACT_DIR / "metadata.json"
            if not all(path.exists() for path in (model_path, vectorizer_path, metadata_path)):
                raise RuntimeError("SIF model artifacts are unavailable; run python -m app.ml.training.train_sif_model")
            self._model = joblib.load(model_path)
            self._vectorizer = joblib.load(vectorizer_path)
            self._metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    def predict(self, text: str) -> SIFPrediction:
        self._load()
        transformed = self._vectorizer.transform([text])
        classes = list(self._model.classes_)
        probability = float(self._model.predict_proba(transformed)[0][classes.index("SIF")])
        return SIFPrediction(probability >= 0.5, round(probability, 4), level_for_probability(probability), self._metadata["model_name"], self._metadata["model_version"])

    def metadata(self) -> dict:
        self._load()
        return self._metadata.copy()


def level_for_probability(probability: float) -> SIFLevel:
    if probability >= 0.75:
        return SIFLevel.HIGH
    if probability >= 0.60:
        return SIFLevel.MEDIUM
    if probability >= 0.55:
        return SIFLevel.LOW
    if probability >= 0.45:
        return SIFLevel.REVIEW
    return SIFLevel.NON_SIF
