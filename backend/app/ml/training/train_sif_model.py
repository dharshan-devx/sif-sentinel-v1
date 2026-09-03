"""Train a reproducible TF-IDF + logistic-regression baseline from synthetic prototype data."""
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).parents[3]
DATASET = ROOT / "data" / "training" / "safety_reports.csv"
ARTIFACTS = Path(__file__).parents[1] / "artifacts"


def train() -> dict:
    with DATASET.open(encoding="utf-8", newline="") as source:
        records = list(csv.DictReader(source))
    texts = [row["report_text"] for row in records]
    labels = ["SIF" if row["sif_potential"].lower() == "true" else "NON_SIF" for row in records]
    x_train, x_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=2026, stratify=labels)
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, strip_accents="unicode")
    model = LogisticRegression(max_iter=2000, class_weight="balanced", random_state=2026)
    model.fit(vectorizer.fit_transform(x_train), y_train)
    probabilities = model.predict_proba(vectorizer.transform(x_test))[:, list(model.classes_).index("SIF")]
    predicted = model.predict(vectorizer.transform(x_test))
    report = classification_report(y_test, predicted, output_dict=True, zero_division=0)
    metrics = {"classification_report": report, "confusion_matrix": confusion_matrix(y_test, predicted, labels=["NON_SIF", "SIF"]).tolist(), "roc_auc": round(float(roc_auc_score([label == "SIF" for label in y_test], probabilities)), 4), "test_records": len(y_test)}
    (ARTIFACTS / "model").mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "vectorizer").mkdir(parents=True, exist_ok=True)
    joblib.dump(model, ARTIFACTS / "model" / "sif_logreg.joblib")
    joblib.dump(vectorizer, ARTIFACTS / "vectorizer" / "tfidf.joblib")
    
    import hashlib
    dataset_hash = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    
    metadata = {"model_name": "sif-tfidf-logreg", "model_version": "sif-tfidf-logreg-v1", "training_timestamp": datetime.now(UTC).isoformat(), "training_dataset_identifier": "synthetic-safety-reports-v1", "dataset_hash": dataset_hash, "feature_configuration": {"ngram_range": [1, 2], "sublinear_tf": True}, "class_labels": list(model.classes_), "metrics": metrics}
    (ARTIFACTS / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


if __name__ == "__main__":
    result = train()
    print(json.dumps(result["metrics"], indent=2))
