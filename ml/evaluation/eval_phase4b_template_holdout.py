"""
Phase 4B: Diagnostic Template-Held-Out Evaluation.
Evaluates semantic generalization across unseen template families:
- Model A: Phase 3 TF-IDF Baseline (Diagnostic retrain on Template-Train)
- Model B: Phase 4A Subword MLP (Diagnostic retrain on Template-Train)
- Model C: Phase 4B Genuine Transformer DistilBERT (Diagnostic retrain on Template-Train)

Zero template family leakage between Train and Evaluation splits.
"""
from __future__ import annotations

import csv
import json
import os
import random
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, precision_recall_curve, auc

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Path setup
ROOT = Path(__file__).parents[2]
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.nlp.preprocessing import preprocess_text
from ml.data.dataset import normalize_binary_target
from ml.evaluation.metrics import calculate_safety_metrics
from ml.training.train_semantic_model_v4 import SemanticClassifierPipeline

PRIMARY_DATASET_PATH = ROOT / "data" / "raw" / "safety_reports.csv"
OUTPUT_PATH = ROOT / "artifacts" / "phase4b_template_holdout_results.json"
MODEL_CHECKPOINT = "distilbert-base-uncased"
RANDOM_SEED = 2026


class DiagnosticDataset(Dataset):
    def __init__(self, encodings: dict[str, torch.Tensor], labels: list[int]):
        self.encodings = encodings
        self.labels = labels

    def __len__(self) -> int:
        return len(self.labels)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {key: val[idx] for key, val in self.encodings.items()}
        item["labels"] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item


def run_template_holdout_benchmark():
    print("=" * 80)
    print("RUNNING DIAGNOSTIC TEMPLATE-HELD-OUT BENCHMARK")
    print("=" * 80)

    records = list(csv.DictReader(open(PRIMARY_DATASET_PATH, encoding="utf-8")))

    # 1. Group by template family (4-word normalized prefix)
    family_map = defaultdict(list)
    for r in records:
        norm = preprocess_text(r["report_text"]).normalized_text
        norm_sk = re.sub(r'\b\d+(\.\d+)?\b', '[NUM]', norm)
        words = norm_sk.split()
        prefix = " ".join(words[:4]) if len(words) >= 4 else norm_sk
        family_map[prefix].append(r)

    families = list(family_map.keys())
    random.seed(RANDOM_SEED)
    random.shuffle(families)

    total_records = len(records)
    target_test_count = int(total_records * 0.20)  # 20% held out

    holdout_families = []
    train_families = []
    curr_holdout = 0

    for f in families:
        f_count = len(family_map[f])
        if curr_holdout + f_count <= target_test_count or not holdout_families:
            holdout_families.append(f)
            curr_holdout += f_count
        else:
            train_families.append(f)

    train_recs = [r for f in train_families for r in family_map[f]]
    holdout_recs = [r for f in holdout_families for r in family_map[f]]

    print(f"Total Families: {len(families)} | Train Families: {len(train_families)} ({len(train_recs)} records) | Holdout Families: {len(holdout_families)} ({len(holdout_recs)} records)")

    train_texts = [r["report_text"] for r in train_recs]
    y_train = [normalize_binary_target(r["sif_potential"]) for r in train_recs]

    holdout_texts = [r["report_text"] for r in holdout_recs]
    y_holdout = [normalize_binary_target(r["sif_potential"]) for r in holdout_recs]

    norm_train = [preprocess_text(t).normalized_text for t in train_texts]
    norm_holdout = [preprocess_text(t).normalized_text for t in holdout_texts]

    # --- 1. MODEL A: DIAGNOSTIC TF-IDF BASELINE ---
    print("\n[1/3] Training Diagnostic Model A (TF-IDF + Logistic Regression)...")
    vec_a = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_df=0.95, sublinear_tf=True)
    X_train_a = vec_a.fit_transform(norm_train)
    X_holdout_a = vec_a.transform(norm_holdout)

    clf_a = LogisticRegression(C=1.0, class_weight="balanced", random_state=RANDOM_SEED)
    clf_a.fit(X_train_a, y_train)

    sif_idx_a = list(clf_a.classes_).index(1) if 1 in clf_a.classes_ else 1
    probs_a = clf_a.predict_proba(X_holdout_a)[:, sif_idx_a]
    preds_a = (probs_a >= 0.50).astype(int)
    metrics_a = calculate_safety_metrics(y_holdout, preds_a, probs_a)

    # --- 2. MODEL B: DIAGNOSTIC SUBWORD MLP ---
    print("\n[2/3] Training Diagnostic Model B (Subword Char-TFIDF + MLP)...")
    clf_b = SemanticClassifierPipeline()
    clf_b.fit(norm_train, y_train)

    probs_b = clf_b.predict_proba(norm_holdout)[:, 1]
    preds_b = (probs_b >= 0.50).astype(int)
    metrics_b = calculate_safety_metrics(y_holdout, preds_b, probs_b)

    # --- 3. MODEL C: DIAGNOSTIC TRANSFORMER (DistilBERT) ---
    print("\n[3/3] Training Diagnostic Model C (Genuine DistilBERT on Template-Train)...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)
    model_c = AutoModelForSequenceClassification.from_pretrained(MODEL_CHECKPOINT, num_labels=2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_c.to(device)

    torch.set_num_threads(min(os.cpu_count() or 4, 16))
    enc_train = tokenizer(norm_train, truncation=True, padding=True, max_length=64, return_tensors="pt")
    enc_holdout = tokenizer(norm_holdout, truncation=True, padding=True, max_length=64, return_tensors="pt")

    ds_train = DiagnosticDataset(enc_train, y_train)
    loader_train = DataLoader(ds_train, batch_size=64, shuffle=True)

    optimizer = torch.optim.AdamW(model_c.parameters(), lr=3e-5, weight_decay=0.01)
    model_c.train()
    for epoch in range(1, 3):  # 2 fast diagnostic epochs
        total_loss = 0.0
        for b in loader_train:
            optimizer.zero_grad()
            i_ids = b["input_ids"].to(device)
            a_mask = b["attention_mask"].to(device)
            lbls = b["labels"].to(device)

            out = model_c(input_ids=i_ids, attention_mask=a_mask, labels=lbls)
            loss = out.loss
            loss.backward()
            optimizer.step()
            total_loss += loss.item() * len(lbls)
        print(f"  Epoch {epoch}/2 - Loss: {total_loss / len(ds_train):.4f}", flush=True)

    # Evaluate Model C on Holdout
    model_c.eval()
    ds_holdout = DiagnosticDataset(enc_holdout, y_holdout)
    loader_holdout = DataLoader(ds_holdout, batch_size=32, shuffle=False)

    probs_c_list = []
    with torch.no_grad():
        for b in loader_holdout:
            i_ids = b["input_ids"].to(device)
            a_mask = b["attention_mask"].to(device)
            out = model_c(input_ids=i_ids, attention_mask=a_mask)
            p = torch.softmax(out.logits, dim=-1).cpu().numpy()
            probs_c_list.extend(p[:, 1])

    probs_c = np.array(probs_c_list)
    preds_c = (probs_c >= 0.50).astype(int)
    metrics_c = calculate_safety_metrics(y_holdout, preds_c, probs_c)

    print("\n" + "=" * 95)
    print("TEMPLATE-HELD-OUT DIAGNOSTIC GENERALIZATION RESULTS")
    print("=" * 95)
    print(f"{'Model':<30} | {'Accuracy':<8} | {'Precision':<9} | {'Recall':<8} | {'F1':<7} | {'ROC-AUC':<8} | {'FNR':<7}")
    print("-" * 95)
    print(f"{'Model A (TF-IDF Baseline)':<30} | {metrics_a['accuracy']*100:.2f}%  | {metrics_a['sif_precision']*100:.2f}%   | {metrics_a['sif_recall']*100:.2f}% | {metrics_a['sif_f1']:.4f}  | {metrics_a['roc_auc']:.4f}   | {metrics_a['false_negative_rate']*100:.2f}%")
    print(f"{'Model B (Subword MLP)':<30} | {metrics_b['accuracy']*100:.2f}%  | {metrics_b['sif_precision']*100:.2f}%   | {metrics_b['sif_recall']*100:.2f}% | {metrics_b['sif_f1']:.4f}  | {metrics_b['roc_auc']:.4f}   | {metrics_b['false_negative_rate']*100:.2f}%")
    print(f"{'Model C (Genuine Transformer)':<30} | {metrics_c['accuracy']*100:.2f}%  | {metrics_c['sif_precision']*100:.2f}%   | {metrics_c['sif_recall']*100:.2f}% | {metrics_c['sif_f1']:.4f}  | {metrics_c['roc_auc']:.4f}   | {metrics_c['false_negative_rate']*100:.2f}%")
    print("=" * 95)

    results = {
        "train_records": len(train_recs),
        "holdout_records": len(holdout_recs),
        "train_families": len(train_families),
        "holdout_families": len(holdout_families),
        "model_a_metrics": metrics_a,
        "model_b_metrics": metrics_b,
        "model_c_metrics": metrics_c,
    }

    OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nDiagnostic results saved to: {OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    run_template_holdout_benchmark()
