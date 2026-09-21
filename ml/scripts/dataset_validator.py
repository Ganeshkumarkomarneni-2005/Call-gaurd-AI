"""Dataset quality validation and integrity testing for CallGuard AI.

Checks data schemas, class distributions, null values, and train/test leakage.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Set

import pandas as pd

logger = logging.getLogger(__name__)

# Canonical enum values aligned with backend/schemas/analysis.py and database models
VALID_CALLER_TYPES: Set[str] = {"human", "ai", "robocall", "unknown"}
VALID_RISK_LEVELS: Set[str] = {"low", "medium", "high", "critical"}
VALID_ACTIONS: Set[str] = {"continue_ai", "transfer_human", "block", "end_call"}
REQUIRED_COLUMNS: List[str] = ["id", "caller_type", "intent", "risk_level", "action"]


def validate_callguard_schema(df: pd.DataFrame) -> List[str]:
    """Validate that a CallGuard dataset conforms to the expected schema and constraints.

    Checks:
    - Presence of required columns
    - Presence of text column (full_transcript, text, or conversation)
    - Value domains for caller_type, risk_level, and action enums
    - Null or empty field violations

    Args:
        df: Input DataFrame to validate.

    Returns:
        List[str]: List of validation error messages. Empty if valid.
    """
    errors: List[str] = []

    if df is None or df.empty:
        return ["DataFrame is empty or None."]

    # Column presence
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            errors.append(f"Missing required column: '{col}'")

    if not any(c in df.columns for c in ("full_transcript", "text", "conversation")):
        errors.append("Dataset must contain at least one text column ('full_transcript', 'text', or 'conversation')")

    # If critical columns missing, return early to prevent KeyError
    if errors:
        return errors

    # Check nulls
    for col in REQUIRED_COLUMNS:
        null_count = df[col].isnull().sum()
        if null_count > 0:
            errors.append(f"Column '{col}' has {null_count} null values.")

    # Validate caller_type
    invalid_caller_types = set(df["caller_type"].dropna().unique()) - VALID_CALLER_TYPES
    if invalid_caller_types:
        errors.append(
            f"Invalid caller_type values detected: {invalid_caller_types}. Allowed: {VALID_CALLER_TYPES}"
        )

    # Validate risk_level
    invalid_risk_levels = set(df["risk_level"].dropna().unique()) - VALID_RISK_LEVELS
    if invalid_risk_levels:
        errors.append(
            f"Invalid risk_level values detected: {invalid_risk_levels}. Allowed: {VALID_RISK_LEVELS}"
        )

    # Validate action
    invalid_actions = set(df["action"].dropna().unique()) - VALID_ACTIONS
    if invalid_actions:
        errors.append(
            f"Invalid action values detected: {invalid_actions}. Allowed: {VALID_ACTIONS}"
        )

    # Validate non-empty transcripts
    text_col = "full_transcript" if "full_transcript" in df.columns else ("text" if "text" in df.columns else None)
    if text_col:
        empty_texts = (df[text_col].astype(str).str.strip() == "").sum()
        if empty_texts > 0:
            errors.append(f"Column '{text_col}' contains {empty_texts} empty string rows.")

    if not errors:
        logger.info("CallGuard schema validation succeeded with 0 errors across %d rows.", len(df))
    else:
        logger.warning("CallGuard schema validation failed with %d errors.", len(errors))

    return errors


def check_class_balance(df: pd.DataFrame, label_col: str) -> Dict[str, Any]:
    """Analyze class distribution, percentages, and imbalance ratio.

    Args:
        df: Input DataFrame.
        label_col: Name of the class label column.

    Returns:
        Dict[str, Any]: Summary dictionary containing counts, percentages,
                        min count, max count, and imbalance ratio.
    """
    if label_col not in df.columns:
        raise ValueError(f"Column '{label_col}' not found in DataFrame.")

    counts = df[label_col].value_counts().to_dict()
    total = len(df)
    percentages = {k: float(v / total) for k, v in counts.items()} if total > 0 else {}

    min_count = min(counts.values()) if counts else 0
    max_count = max(counts.values()) if counts else 0
    imbalance_ratio = float(max_count / min_count) if min_count > 0 else 0.0

    return {
        "label_column": label_col,
        "total_samples": total,
        "unique_classes": len(counts),
        "counts": counts,
        "percentages": percentages,
        "min_class_count": min_count,
        "max_class_count": max_count,
        "imbalance_ratio": round(imbalance_ratio, 3),
        "is_severely_imbalanced": imbalance_ratio > 5.0,
    }


def check_for_leakage(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    text_col: str = "full_transcript",
) -> int:
    """Detect data leakage between train and test splits by finding exact/normalized text overlaps.

    Args:
        train_df: Training DataFrame.
        test_df: Testing DataFrame.
        text_col: Column containing text transcripts.

    Returns:
        int: Number of leaked (overlapping) samples found in the test set.
    """
    # Fallback to 'text' if specified text_col is missing
    actual_train_col = text_col if text_col in train_df.columns else "text"
    actual_test_col = text_col if text_col in test_df.columns else "text"

    if actual_train_col not in train_df.columns or actual_test_col not in test_df.columns:
        logger.warning("Could not find text column for leakage check.")
        return 0

    def _normalize_for_leak_check(text: Any) -> str:
        s = str(text).lower().strip()
        return re.sub(r"\s+", " ", s)

    train_set: Set[str] = set(train_df[actual_train_col].dropna().apply(_normalize_for_leak_check))
    test_texts = test_df[actual_test_col].dropna().apply(_normalize_for_leak_check)

    leaked_count = sum(1 for t in test_texts if t in train_set)

    if leaked_count > 0:
        logger.warning(
            "DATA LEAKAGE DETECTED: %d test examples (%0.2f%%) exist in training set!",
            leaked_count,
            (leaked_count / len(test_df)) * 100 if len(test_df) > 0 else 0,
        )
    else:
        logger.info("Leakage check passed: 0 overlapping samples detected between train and test splits.")

    return leaked_count
