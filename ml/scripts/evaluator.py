"""Model evaluation and business risk metric utilities for CallGuard AI.

Calculates standard classification statistics (Accuracy, Precision, Recall, F1)
along with mission-critical fraud metrics (False Positive Rate, False Negative Rate,
Missed Fraud, Blocked Legitimate Calls) and visualization helpers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

logger = logging.getLogger(__name__)


def evaluate_classifier(
    model: Any,
    X_test: Any,
    y_test: Sequence[Any],
    class_names: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Evaluate a trained classifier on a test dataset.

    Computes overall accuracy, macro and weighted precision, recall, and F1,
    as well as full classification report and confusion matrix.

    Args:
        model: Trained scikit-learn compatible estimator.
        X_test: Test features (sparse matrix, array, or DataFrame).
        y_test: Ground truth labels.
        class_names: Optional explicit list of class names.

    Returns:
        Dict[str, Any]: Structured evaluation metrics.
    """
    y_pred = model.predict(X_test)
    y_test_arr = np.array(y_test)

    # Determine unique labels
    if class_names is None:
        unique_labels = sorted(list(set(y_test_arr).union(set(y_pred))))
    else:
        unique_labels = class_names

    cm = confusion_matrix(y_test_arr, y_pred, labels=unique_labels)
    report = classification_report(
        y_test_arr,
        y_pred,
        labels=unique_labels,
        target_names=[str(c) for c in unique_labels],
        output_dict=True,
        zero_division=0,
    )

    acc = float(accuracy_score(y_test_arr, y_pred))
    p_macro = float(precision_score(y_test_arr, y_pred, average="macro", zero_division=0))
    r_macro = float(recall_score(y_test_arr, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test_arr, y_pred, average="macro", zero_division=0))
    p_weighted = float(precision_score(y_test_arr, y_pred, average="weighted", zero_division=0))
    r_weighted = float(recall_score(y_test_arr, y_pred, average="weighted", zero_division=0))
    f1_weighted = float(f1_score(y_test_arr, y_pred, average="weighted", zero_division=0))

    results = {
        "accuracy": acc,
        "precision_macro": p_macro,
        "recall_macro": r_macro,
        "f1_macro": f1_macro,
        "precision_weighted": p_weighted,
        "recall_weighted": r_weighted,
        "f1_weighted": f1_weighted,
        "confusion_matrix": cm.tolist(),
        "class_names": [str(c) for c in unique_labels],
        "classification_report": report,
    }

    logger.info(
        "Evaluation results: Acc=%.4f, Macro F1=%.4f, Weighted F1=%.4f",
        acc,
        f1_macro,
        f1_weighted,
    )
    return results


def plot_confusion_matrix(
    cm: Any,
    class_names: List[str],
    title: str = "Confusion Matrix",
    figsize: tuple = (8, 6),
    cmap: str = "Blues",
) -> Any:
    """Render a confusion matrix heatmap using matplotlib and seaborn.

    Args:
        cm: 2D array or nested list confusion matrix.
        class_names: Labels for the matrix axes.
        title: Chart title.
        figsize: Figure width and height.
        cmap: Color map palette.

    Returns:
        matplotlib.figure.Figure: Generated figure object.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, ax = plt.subplots(figsize=figsize)
    cm_arr = np.array(cm)
    sns.heatmap(
        cm_arr,
        annot=True,
        fmt="d",
        cmap=cmap,
        xticklabels=class_names,
        yticklabels=class_names,
        ax=ax,
    )
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Predicted Label", fontsize=11)
    ax.set_ylabel("True Label", fontsize=11)
    plt.xticks(rotation=45, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    return fig


def plot_classification_report(
    report: Dict[str, Any],
    title: str = "Classification Report Metrics",
    figsize: tuple = (10, 6),
) -> Any:
    """Plot per-class precision, recall, and F1 scores from a classification report dictionary.

    Args:
        report: Dict returned by sklearn.metrics.classification_report(output_dict=True).
        title: Chart title.
        figsize: Figure dimensions.

    Returns:
        matplotlib.figure.Figure: Generated figure object.
    """
    import matplotlib.pyplot as plt

    # Filter out summary rows
    excluded = {"accuracy", "macro avg", "weighted avg"}
    class_metrics = {k: v for k, v in report.items() if k not in excluded and isinstance(v, dict)}

    df_report = pd.DataFrame(class_metrics).T[["precision", "recall", "f1-score"]]

    fig, ax = plt.subplots(figsize=figsize)
    df_report.plot(kind="bar", ax=ax, colormap="viridis", width=0.8)
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Class", fontsize=11)
    ax.set_ylabel("Score", fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    plt.xticks(rotation=45, ha="right")
    plt.legend(loc="lower right")
    plt.tight_layout()
    return fig


def calculate_business_metrics(
    y_true: Sequence[Any],
    y_pred: Sequence[Any],
    fraud_class_label: Any = "high_risk",
) -> Dict[str, Any]:
    """Calculate telephony security business risk metrics.

    Focuses on:
    - Missed fraud calls (False Negatives): User was subjected to attack.
    - Legitimate calls blocked (False Positives): Genuine caller blocked, harming business/user experience.

    Args:
        y_true: Ground truth binary or multiclass labels.
        y_pred: Model predictions.
        fraud_class_label: Value identifying the fraud/risk class (e.g. 'high_risk', 1, 'fraud').

    Returns:
        Dict[str, Any]: Business metrics including FPR, FNR, counts, and security ratios.
    """
    y_true_bin = np.array([1 if str(x) == str(fraud_class_label) else 0 for x in y_true])
    y_pred_bin = np.array([1 if str(x) == str(fraud_class_label) else 0 for x in y_pred])

    tp = int(np.sum((y_true_bin == 1) & (y_pred_bin == 1)))
    fp = int(np.sum((y_true_bin == 0) & (y_pred_bin == 1)))
    fn = int(np.sum((y_true_bin == 1) & (y_pred_bin == 0)))
    tn = int(np.sum((y_true_bin == 0) & (y_pred_bin == 0)))

    total_calls = len(y_true)
    total_fraud = int(np.sum(y_true_bin == 1))
    total_legitimate = int(np.sum(y_true_bin == 0))

    false_positive_rate = float(fp / total_legitimate) if total_legitimate > 0 else 0.0
    false_negative_rate = float(fn / total_fraud) if total_fraud > 0 else 0.0
    precision = float(tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    recall = float(tp / (tp + fn)) if (tp + fn) > 0 else 0.0

    return {
        "total_calls": total_calls,
        "total_fraud": total_fraud,
        "total_legitimate": total_legitimate,
        "true_positives": tp,
        "true_negatives": tn,
        "false_positive_rate": false_positive_rate,
        "false_negative_rate": false_negative_rate,
        "missed_fraud_count": fn,
        "legitimate_calls_blocked": fp,
        "fraud_precision": precision,
        "fraud_recall": recall,
    }
