"""Train an advanced Random Forest ensemble with hyperparameter tuning."""
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split, RandomizedSearchCV

ROOT = Path(__file__).parents[2]
DATASET = ROOT / "data" / "processed" / "safety_reports_v1.csv"
ARTIFACTS = ROOT / "artifacts" / "models"


def train() -> dict:
    print(f"Loading dataset from {DATASET}...")
    with DATASET.open(encoding="utf-8", newline="") as source:
        records = list(csv.DictReader(source))
    
    texts = [row["report_text"] for row in records]
    labels = ["SIF" if row["sif_potential"].lower() == "true" else "NON_SIF" for row in records]
    
    x_train, x_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=2026, stratify=labels)
    
    print("Extracting TF-IDF features...")
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.9, sublinear_tf=True, strip_accents="unicode")
    X_train_vec = vectorizer.fit_transform(x_train)
    X_test_vec = vectorizer.transform(x_test)
    
    print("Training Advanced Random Forest Model with Hyperparameter Tuning...")
    base_model = RandomForestClassifier(class_weight="balanced", random_state=2026, n_jobs=-1)
    
    # Define hyperparameter search space
    param_dist = {
        "n_estimators": [100, 200, 300],
        "max_depth": [None, 10, 20, 30],
        "min_samples_split": [2, 5, 10],
        "min_samples_leaf": [1, 2, 4]
    }
    
    # Randomized Search (faster than GridSearch for prototyping)
    search = RandomizedSearchCV(
        estimator=base_model,
        param_distributions=param_dist,
        n_iter=10,
        cv=3,
        scoring="roc_auc",
        random_state=2026,
        n_jobs=-1,
        verbose=1
    )
    
    search.fit(X_train_vec, y_train)
    model = search.best_estimator_
    
    print(f"Best hyperparameters found: {search.best_params_}")
    
    print("Evaluating Model...")
    probabilities = model.predict_proba(X_test_vec)[:, list(model.classes_).index("SIF")]
    predicted = model.predict(X_test_vec)
    report = classification_report(y_test, predicted, output_dict=True, zero_division=0)
    
    metrics = {
        "classification_report": report,
        "confusion_matrix": confusion_matrix(y_test, predicted, labels=["NON_SIF", "SIF"]).tolist(),
        "roc_auc": round(float(roc_auc_score([label == "SIF" for label in y_test], probabilities)), 4),
        "test_records": len(y_test)
    }
    
    (ARTIFACTS / "model").mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "vectorizer").mkdir(parents=True, exist_ok=True)
    
    # Save the advanced model and vectorizer
    joblib.dump(model, ARTIFACTS / "model" / "sif_advanced.joblib")
    joblib.dump(vectorizer, ARTIFACTS / "vectorizer" / "tfidf.joblib")
    
    import hashlib
    dataset_hash = hashlib.sha256(
        DATASET.read_text(encoding="utf-8").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest()
    
    metadata = {
        "model_name": "sif-tfidf-randomforest",
        "model_version": "sif-tfidf-rf-v1",
        "training_timestamp": datetime.now(UTC).isoformat(),
        "training_dataset_identifier": "synthetic-safety-reports-v1",
        "dataset_hash": dataset_hash,
        "scikit_learn_version": sklearn.__version__,
        "feature_configuration": {"ngram_range": [1, 2], "sublinear_tf": True},
        "class_labels": list(model.classes_),
        "best_params": search.best_params_,
        "metrics": metrics
    }
    
    (ARTIFACTS / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print("Training complete and artifacts saved!")
    return metadata


if __name__ == "__main__":
    result = train()
    print(json.dumps(result["metrics"], indent=2))
