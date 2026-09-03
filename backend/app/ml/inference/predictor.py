import json
import threading
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.core.constants import SIFLevel

ARTIFACT_DIR = Path(__file__).parents[4] / "artifacts" / "models"


@dataclass(frozen=True)
class SIFPrediction:
    sif_potential: bool
    probability: float
    sif_level: SIFLevel
    model_name: str
    model_version: str
    predictive_terms: list[str]


class SIFPredictor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._model = None
        self._vectorizer = None
        self._metadata: dict = {}
        self._sif_index = 0

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
                raise RuntimeError("SIF model artifacts are unavailable; run python ml/training/train_sif_model.py from the repository root")
            self._model = joblib.load(model_path)
            self._vectorizer = joblib.load(vectorizer_path)
            self._metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self._sif_index = list(self._model.classes_).index("SIF")

    def predict(self, text: str) -> SIFPrediction:
        self._load()
        transformed = self._vectorizer.transform([text])
        probability = float(self._model.predict_proba(transformed)[0][self._sif_index])
        
        # Extract feature importance (words that drove the SIF prediction)
        feature_names = self._vectorizer.get_feature_names_out()
        coefficients = self._model.coef_[0] if self._model.classes_.shape[0] == 2 else self._model.coef_[self._sif_index]
        
        # Multiply non-zero TF-IDF values by model coefficients
        non_zero_indices = transformed.nonzero()[1]
        contributions = [(feature_names[i], transformed[0, i] * coefficients[i]) for i in non_zero_indices]
        
        # Top 3 terms that pushed the model toward SIF
        top_terms = [term for term, contrib in sorted(contributions, key=lambda x: x[1], reverse=True) if contrib > 0][:3]
        
        return SIFPrediction(probability >= 0.5, round(probability, 4), level_for_probability(probability), self._metadata["model_name"], self._metadata["model_version"], top_terms)

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
