# CallGuard AI — ML Evaluation Framework

**Version:** 1.0  
**Status:** NOT_YET_EVALUATED — awaiting Colab notebook execution  
**Last Updated:** 2026-09-21

---

> [!IMPORTANT]
> All metric values in this document are PLACEHOLDERS.
> They are marked `NOT_YET_EVALUATED`.
> Results will be filled in after executing the Google Colab notebooks.
> **Never fabricate ML results.**

---

## 1. Evaluation Methodology

### 1.1 Data Splits

All models are trained and evaluated using a stratified 80/10/10 split:

| Split | Purpose | Percentage |
|-------|---------|-----------|
| Train | Model training | 80% |
| Validation | Hyperparameter tuning, early stopping | 10% |
| Test (held-out) | Final evaluation — used ONCE | 10% |

> [!CAUTION]
> The test split must not be used during training or model selection.
> Only evaluate on test data ONCE, in notebook `09_final_evaluation.ipynb`.

### 1.2 Metrics Reported

For every classifier:
- **Accuracy** — overall correct predictions / total
- **Precision (per class + macro avg)** — TP / (TP + FP)
- **Recall (per class + macro avg)** — TP / (TP + FN)
- **F1-score (per class + macro avg)** — harmonic mean of precision and recall
- **Confusion Matrix** — actual vs predicted grid
- **Classification Report** — per-class breakdown

For fraud/risk models additionally:
- **False Positive Rate** — legitimate calls incorrectly flagged as fraud
- **False Negative Rate** — fraud calls missed
- **Precision-Recall Curve** — threshold analysis
- **ROC-AUC** — discrimination ability

For caller type detection:
- **One-vs-Rest ROC-AUC** per class

### 1.3 Business Metrics

Standard accuracy metrics are insufficient. Report:

| Business Metric | Definition | Priority |
|----------------|------------|----------|
| Missed Fraud (FNR) | Fraud calls not detected | CRITICAL — minimize |
| False Alarms (FPR) | Legitimate calls blocked | HIGH — minimize |
| Missed Recruitment | Legitimate recruitment calls rejected | HIGH — minimize |
| Incorrect Transfer | Calls transferred unnecessarily | MEDIUM |
| Incorrect Termination | Legitimate calls ended | HIGH — minimize |

---

## 2. Models to Evaluate

### 2.1 Intent Classifier

**File:** `ml/models/intent_classifier_v1.*`  
**Notebook:** `03_intent_classification.ipynb`  
**Classes:** RECRUITMENT, PROMOTIONAL, FRAUD, CUSTOMER_SERVICE, DELIVERY, PERSONAL, OTHER, UNKNOWN

#### Baseline Models

| Model | Accuracy | Macro F1 | Status |
|-------|----------|----------|--------|
| TF-IDF + Logistic Regression | NOT_YET_EVALUATED | NOT_YET_EVALUATED | NOT_TRAINED |
| TF-IDF + Linear SVM | NOT_YET_EVALUATED | NOT_YET_EVALUATED | NOT_TRAINED |
| DistilBERT (fine-tuned) | NOT_YET_EVALUATED | NOT_YET_EVALUATED | NOT_TRAINED |

#### Per-Class F1 (Logistic Regression — to be filled)

| Class | Precision | Recall | F1 |
|-------|-----------|--------|-----|
| RECRUITMENT | — | — | — |
| PROMOTIONAL | — | — | — |
| FRAUD | — | — | — |
| CUSTOMER_SERVICE | — | — | — |
| DELIVERY | — | — | — |
| PERSONAL | — | — | — |
| OTHER | — | — | — |
| UNKNOWN | — | — | — |

---

### 2.2 Recruitment Detector

**File:** `ml/models/recruitment_detector_v1.*`  
**Notebook:** `04_recruitment_detection.ipynb`

#### Stage 1: Recruitment vs Non-Recruitment

| Model | Accuracy | Recall | Precision | F1 | Status |
|-------|----------|--------|-----------|-----|--------|
| TF-IDF + LR | — | — | — | — | NOT_TRAINED |

> Focus metric: **Recall** — missing a recruitment call is costly.

#### Stage 2: Legitimate vs Fraudulent Recruitment

| Model | Accuracy | Fraud Recall | Fraud Precision | Status |
|-------|----------|-------------|-----------------|--------|
| TF-IDF + LR | — | — | — | NOT_TRAINED |

> Focus metric: **Fraud Recall** — missing a recruitment scam is CRITICAL.

---

### 2.3 Fraud Risk Model

**File:** `ml/models/fraud_risk_model_v1.*`  
**Notebook:** `05_fraud_risk_model.ipynb`

| Model | AUC-ROC | FPR | FNR | Status |
|-------|---------|-----|-----|--------|
| TF-IDF + LR | — | — | — | NOT_TRAINED |

#### Risk Score Distribution (to be filled after training)

| Risk Level | Count | % of Test Set |
|------------|-------|---------------|
| LOW | — | — |
| MEDIUM | — | — |
| HIGH | — | — |
| CRITICAL | — | — |

#### Error Analysis

| Error Type | Count | % | Impact |
|-----------|-------|---|--------|
| Missed fraud (FN) | — | — | CRITICAL |
| False fraud alert (FP) | — | — | HIGH |
| Risk level underestimated | — | — | HIGH |
| Risk level overestimated | — | — | MEDIUM |

---

### 2.4 Caller Type Detector

**File:** `ml/models/caller_type_model_v1.*`  
**Notebook:** `06_caller_type_experiment.ipynb`  
**Classes:** HUMAN, AI, ROBOCALL, UNKNOWN

| Model | Accuracy | Macro F1 | AUC-ROC (OvR) | Status |
|-------|----------|----------|----------------|--------|
| Linguistic features + LR | — | — | — | NOT_TRAINED |

> [!WARNING]
> Caller type detection is inherently limited.
> AI vs Human distinction based on text features alone has significant limitations:
> - Sophisticated AI callers may appear human
> - Natural human speakers may use scripted language
> - Audio features (prosody, timing) are NOT captured in the current dataset
> This model is a SUPPORTING SIGNAL, not the primary safety classifier.

---

## 3. Model Comparison Summary (to be filled)

| Task | Best Model | Accuracy | F1 | Latency (ms) |
|------|-----------|----------|----|-------------|
| Intent classification | — | — | — | — |
| Recruitment detection | — | — | — | — |
| Fraud risk | — | — | — | — |
| Caller type | — | — | — | — |

---

## 4. Latency Requirements

| Operation | Target (p95) | Measured | Status |
|-----------|-------------|----------|--------|
| Intent classification | < 50ms (classical) | — | NOT_MEASURED |
| Fraud detection | < 50ms (classical) | — | NOT_MEASURED |
| Risk assessment | < 100ms | — | NOT_MEASURED |
| Decision agent | < 50ms | — | NOT_MEASURED |
| Full pipeline | < 500ms | — | NOT_MEASURED |

---

## 5. Model Versioning

Every trained model artifact must include a model card JSON:

```json
{
  "model_name": "intent_classifier",
  "version": "v1",
  "type": "TF-IDF + Logistic Regression",
  "dataset": "callguard_custom_v1 + clinc150",
  "dataset_version": "1.0-synthetic",
  "training_date": "NOT_YET_TRAINED",
  "features": ["tfidf_10000", "linguistic_8"],
  "hyperparameters": {
    "C": "NOT_YET_TUNED",
    "max_features": 10000,
    "ngram_range": "(1, 2)"
  },
  "metrics": {
    "accuracy": "NOT_YET_EVALUATED",
    "macro_f1": "NOT_YET_EVALUATED"
  },
  "limitations": [
    "Synthetic training data only",
    "English language only",
    "May underperform on regional accents or code-switching",
    "Not validated on real telephone calls"
  ]
}
```

---

## 6. Model Export Paths

After training in Colab, export to:

```
ml/models/
├── intent_classifier_v1.pkl
├── intent_classifier_v1_metadata.json
├── recruitment_detector_v1.pkl
├── recruitment_detector_v1_metadata.json
├── fraud_risk_model_v1.pkl
├── fraud_risk_model_v1_metadata.json
├── caller_type_model_v1.pkl
└── caller_type_model_v1_metadata.json
```

Backend integration path: `backend/agents/` agents load models at startup if available.

---

## 7. How to Run Evaluation

### Step 1: Open Google Colab
```
https://colab.research.google.com/
```

### Step 2: Upload notebooks
Upload from `ml/notebooks/` in order: 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10

### Step 3: Run notebooks in sequence
- Start with `01_data_understanding.ipynb`
- Each notebook depends on outputs from previous ones

### Step 4: Record results
After `09_final_evaluation.ipynb` completes:
- Copy ALL metrics into this document
- Save confusion matrix images
- Record latency measurements

### Step 5: Export models
Run `10_model_export.ipynb` to export trained artifacts.

### Step 6: Download and integrate
Download exported `.pkl` files and place in `ml/models/`.

---

## 8. Known Limitations

1. **Synthetic training data** — models trained on synthetic conversations may not generalize to real calls
2. **English only** — no support for Hindi, regional Indian languages
3. **No audio features** — caller type detection uses text only; real deployment should include prosody and timing features
4. **No real-world validation** — all evaluation is on synthetic test data until real call data is obtained
5. **Small dataset** — 1,100 synthetic examples is sufficient for proof-of-concept; production requires more data
6. **Class imbalance** — fraud examples may be over-represented relative to real-world distribution
