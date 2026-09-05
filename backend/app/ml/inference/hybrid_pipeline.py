"""
Semantic & Calibrated Hybrid Classifier Pipelines for SIF Sentinel Phase 4.
"""
from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier

from app.services.nlp.preprocessing import preprocess_text


class SemanticClassifierPipeline:
    """
    Model B: Semantic Subword Neural Classifier (sif-semantic-v1).
    Combines subword n-gram character vectorization with MLP Deep Neural Network.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 3), analyzer="char_wb", min_df=2, max_df=0.98, sublinear_tf=True
        )
        self.model = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            activation="relu",
            solver="adam",
            alpha=1e-4,
            max_iter=300,
            early_stopping=True,
            validation_fraction=0.1,
            random_state=2026,
        )

    def fit(self, texts: list[str], y: list[int]):
        X_vec = self.vectorizer.fit_transform(texts)
        y_arr = np.array(y)
        self.model.fit(X_vec, y_arr)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        X_vec = self.vectorizer.transform(texts)
        return self.model.predict_proba(X_vec)


class HybridClassifierPipeline:
    """
    Model C: Calibrated Hybrid Classifier (sif-hybrid-v1).
    Fuses Classical TF-IDF probability + Semantic Transformer probability + Phase 2 NLP evidence scores.
    """
    def __init__(self, baseline_model: Any, baseline_vec: Any, semantic_pipeline: SemanticClassifierPipeline):
        self.baseline_model = baseline_model
        self.baseline_vec = baseline_vec
        self.semantic_pipeline = semantic_pipeline
        self.meta_classifier = LogisticRegression(C=1.0, class_weight="balanced", random_state=2026)

    def extract_nlp_signal(self, text: str) -> list[float]:
        """Extract valid NLP domain evidence signals prior to classification."""
        norm = preprocess_text(text).normalized_text
        has_without = 1.0 if "without" in norm or "lacking" in norm else 0.0
        has_confined = 1.0 if any(w in norm for w in ["confined", "vessel", "tank"]) else 0.0
        has_loto = 1.0 if any(w in norm for w in ["loto", "isolation", "lockout", "unisolated"]) else 0.0
        has_height = 1.0 if any(w in norm for w in ["height", "harness", "scaffold", "ladder"]) else 0.0
        has_gas = 1.0 if any(w in norm for w in ["gas", "lethal", "atmospheric", "lel"]) else 0.0
        has_load = 1.0 if any(w in norm for w in ["load", "crane", "rigging", "suspended"]) else 0.0
        return [has_without, has_confined, has_loto, has_height, has_gas, has_load]

    def _extract_fusion_features(self, texts: list[str]) -> np.ndarray:
        # Baseline probability
        X_base = self.baseline_vec.transform(texts)
        sif_idx_base = list(self.baseline_model.classes_).index("SIF") if "SIF" in self.baseline_model.classes_ else 1
        p_base = self.baseline_model.predict_proba(X_base)[:, sif_idx_base]

        # Semantic probability
        p_sem = self.semantic_pipeline.predict_proba(texts)[:, 1]

        # NLP signals
        nlp_feats = np.array([self.extract_nlp_signal(t) for t in texts])

        return np.column_stack([p_base, p_sem, nlp_feats])

    def fit(self, texts: list[str], y: list[int]):
        X_fusion = self._extract_fusion_features(texts)
        self.meta_classifier.fit(X_fusion, y)

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        X_fusion = self._extract_fusion_features(texts)
        probs_sif = self.meta_classifier.predict_proba(X_fusion)[:, 1]
        probs_non_sif = 1.0 - probs_sif
        return np.column_stack([probs_non_sif, probs_sif])
