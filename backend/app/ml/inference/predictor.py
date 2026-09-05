import json
import os
import sys
import threading
from dataclasses import dataclass
from pathlib import Path

import joblib

from app.core.config import get_settings
from app.core.constants import SIFLevel
from app.services.nlp.preprocessing import preprocess_text

# Ensure custom unpickling classes can be resolved regardless of entrypoint
try:
    from ml.training.train_transformer_v4b import (
        TransformerClassifierWrapper,
        TransformerHybridPipeline,
    )

    main_mod = sys.modules.get("__main__")
    if main_mod is not None:
        if not hasattr(main_mod, "TransformerHybridPipeline"):
            main_mod.TransformerHybridPipeline = TransformerHybridPipeline
        if not hasattr(main_mod, "TransformerClassifierWrapper"):
            main_mod.TransformerClassifierWrapper = TransformerClassifierWrapper
except Exception:
    pass

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
    def __init__(self, version: str | None = None) -> None:
        self._lock = threading.Lock()
        self._model = None
        self._vectorizer = None
        self._metadata: dict = {}
        self._sif_index = 0
        self._threshold = 0.50
        self._version = version

    def _load(self) -> None:
        configured_version = os.environ.get("SIF_MODEL_BACKEND") or os.environ.get("SIF_MODEL_VERSION")
        if not configured_version:
            try:
                settings = get_settings()
                configured_version = getattr(settings, "sif_model_backend", None) or settings.sif_model_version
            except Exception:
                configured_version = "v2"

        version_to_use = str(self._version or configured_version).lower()
        if self._model is not None and getattr(self, "_loaded_version", None) == version_to_use:
            return

        with self._lock:
            if self._model is not None and getattr(self, "_loaded_version", None) == version_to_use:
                return
            self._is_v1 = version_to_use in {"v1", "baseline_v1", "sif-tfidf-logreg-v1"}
            self._is_v2 = version_to_use in {"v2", "sif-tfidf-logreg-v2"}
            self._is_hybrid = version_to_use in {"hybrid", "v4_hybrid", "sif-hybrid-v1"}
            self._is_semantic = version_to_use in {"semantic", "v4_semantic", "sif-semantic-v1"}
            self._is_transformer = version_to_use in {"transformer", "v4b", "v4b_transformer", "sif-transformer-v4b", "sif-transformer-distilbert-v1"}
            self._is_transformer_hybrid = version_to_use in {"v4b_hybrid", "transformer_hybrid", "sif-transformer-hybrid-v1"}

            if self._is_v1:
                base_dir = ARTIFACT_DIR / "baseline_v1"
                model_path = base_dir / "model" / "sif_logreg.joblib"
                vectorizer_path = base_dir / "vectorizer" / "tfidf.joblib"
            elif self._is_v2:
                base_dir = ARTIFACT_DIR / "v2"
                model_path = base_dir / "model" / "sif_model.joblib"
                vectorizer_path = base_dir / "vectorizer" / "tfidf.joblib"
            elif self._is_transformer and (ARTIFACT_DIR / "v4b_transformer" / "config.json").exists():
                base_dir = ARTIFACT_DIR / "v4b_transformer"
                if not any((base_dir / name).exists() for name in ("model.safetensors", "pytorch_model.bin")):
                    raise RuntimeError(
                        "SIF transformer weights are unavailable; v4b_transformer is a research export, not a runtime artifact."
                    )
                try:
                    from transformers import AutoModelForSequenceClassification, AutoTokenizer
                except ImportError as exc:
                    raise RuntimeError(
                        "SIF transformer runtime requires the optional transformers and torch dependencies."
                    ) from exc
                self._tokenizer = AutoTokenizer.from_pretrained(str(base_dir))
                self._model = AutoModelForSequenceClassification.from_pretrained(str(base_dir))
                self._model.eval()
                vectorizer_path = ARTIFACT_DIR / "vectorizer" / "tfidf.joblib"
                self._vectorizer = joblib.load(vectorizer_path) if vectorizer_path.exists() else None
                metadata_path = base_dir / "metadata.json"
                threshold_path = base_dir / "threshold.json"
                self._metadata = json.loads(metadata_path.read_text(encoding="utf-8")) if metadata_path.exists() else {}
                self._sif_index = 1
                self._loaded_version = version_to_use
                self._threshold = 0.50
                if threshold_path.exists():
                    try:
                        th_data = json.loads(threshold_path.read_text(encoding="utf-8"))
                        self._threshold = float(th_data.get("selected_threshold", 0.50))
                    except Exception:
                        pass
                return
            elif self._is_transformer_hybrid and (ARTIFACT_DIR / "v4b_hybrid" / "sif_transformer_hybrid_model.joblib").exists():
                base_dir = ARTIFACT_DIR / "v4b_hybrid"
                model_path = base_dir / "sif_transformer_hybrid_model.joblib"
                vectorizer_path = ARTIFACT_DIR / "vectorizer" / "tfidf.joblib"
            elif self._is_hybrid and (ARTIFACT_DIR / "v4_hybrid" / "sif_hybrid_model.joblib").exists():
                base_dir = ARTIFACT_DIR / "v4_hybrid"
                model_path = base_dir / "sif_hybrid_model.joblib"
                vectorizer_path = ARTIFACT_DIR / "vectorizer" / "tfidf.joblib"
            elif self._is_semantic and (ARTIFACT_DIR / "v4_semantic" / "sif_semantic_model.joblib").exists():
                base_dir = ARTIFACT_DIR / "v4_semantic"
                model_path = base_dir / "sif_semantic_model.joblib"
                vectorizer_path = ARTIFACT_DIR / "vectorizer" / "tfidf.joblib"
            else:
                base_dir = ARTIFACT_DIR
                model_path = base_dir / "model" / "sif_logreg.joblib"
                vectorizer_path = base_dir / "vectorizer" / "tfidf.joblib"

            metadata_path = base_dir / "metadata.json"
            threshold_path = base_dir / "threshold.json"

            if not all(path.exists() for path in (model_path, metadata_path)):
                raise RuntimeError(
                    "SIF model artifacts are unavailable; run python ml/training/train_sif_model_v2.py from the repository root"
                )
            self._model = joblib.load(model_path)
            self._vectorizer = joblib.load(vectorizer_path) if vectorizer_path.exists() else None
            self._metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            if hasattr(self._model, "classes_") and "SIF" in list(self._model.classes_):
                self._sif_index = list(self._model.classes_).index("SIF")
            else:
                self._sif_index = 1
            self._loaded_version = version_to_use

        if threshold_path.exists():
            try:
                th_data = json.loads(threshold_path.read_text(encoding="utf-8"))
                self._threshold = float(th_data.get("selected_threshold", 0.50))
            except Exception:
                self._threshold = float(self._metadata.get("operating_threshold", 0.50))
        else:
            self._threshold = float(self._metadata.get("operating_threshold", 0.50))

    def predict(self, text: str) -> SIFPrediction:
        self._load()
        if getattr(self, "_is_transformer", False):
            import torch
            norm = preprocess_text(text).normalized_text
            inputs = self._tokenizer(norm, return_tensors="pt", truncation=True, max_length=64)
            with torch.no_grad():
                logits = self._model(**inputs).logits
                probability = float(torch.softmax(logits, dim=-1)[0, 1].item())
            transformed = self._vectorizer.transform([norm]) if self._vectorizer else None
        elif getattr(self, "_is_transformer_hybrid", False):
            norm = preprocess_text(text).normalized_text
            probability = float(self._model.predict_proba([text])[0, 1])
            transformed = self._vectorizer.transform([norm]) if self._vectorizer else None
        elif getattr(self, "_is_v1", False):
            transformed = self._vectorizer.transform([text])
            probability = float(self._model.predict_proba(transformed)[0][self._sif_index])
        elif getattr(self, "_is_hybrid", False) or getattr(self, "_is_semantic", False):
            normalized = preprocess_text(text).normalized_text
            probability = float(self._model.predict_proba([normalized])[0][1])
            transformed = self._vectorizer.transform([normalized]) if self._vectorizer else None
        else:
            normalized = preprocess_text(text).normalized_text
            transformed = self._vectorizer.transform([normalized])
            probability = float(self._model.predict_proba(transformed)[0][self._sif_index])

        # Extract predictive terms
        top_terms: list[str] = []
        if transformed is not None and self._vectorizer is not None and hasattr(self._model, "coef_"):
            feature_names = self._vectorizer.get_feature_names_out()
            coefficients = (
                self._model.coef_[0]
                if self._model.classes_.shape[0] == 2
                else self._model.coef_[self._sif_index]
            )
            non_zero_indices = transformed.nonzero()[1]
            contributions = [
                (feature_names[i], transformed[0, i] * coefficients[i])
                for i in non_zero_indices
            ]
            top_terms = [
                term
                for term, contrib in sorted(contributions, key=lambda x: x[1], reverse=True)
                if contrib > 0
            ][:3]
        elif self._vectorizer is not None and transformed is not None:
            feature_names = self._vectorizer.get_feature_names_out()
            non_zero_indices = transformed.nonzero()[1]
            top_terms = [feature_names[i] for i in non_zero_indices[:3]]

        is_sif = probability >= self._threshold

        return SIFPrediction(
            is_sif,
            round(probability, 4),
            level_for_probability(probability),
            self._metadata.get("model_name", "sif-classifier"),
            self._metadata.get("model_version", str(self._loaded_version)),
            top_terms,
        )

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
