"""Text preprocessing and dataset preparation routines for CallGuard AI.

Includes text cleaning, normalization, deduplication, and stratified train/val/test splitting.
"""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

logger = logging.getLogger(__name__)

# Common English contraction mappings for telephony NLP
CONTRACTIONS = {
    r"\bwon't\b": "will not",
    r"\bcan't\b": "cannot",
    r"\bi'm\b": "i am",
    r"\bi've\b": "i have",
    r"\bi'll\b": "i will",
    r"\bi'd\b": "i would",
    r"\byou're\b": "you are",
    r"\byou've\b": "you have",
    r"\byou'll\b": "you will",
    r"\byou'd\b": "you would",
    r"\bhe's\b": "he is",
    r"\bshe's\b": "she is",
    r"\bit's\b": "it is",
    r"\bwe're\b": "we are",
    r"\bthey're\b": "they are",
    r"\bdon't\b": "do not",
    r"\bdoesn't\b": "does not",
    r"\bdidn't\b": "did not",
    r"\bhaven't\b": "have not",
    r"\bhasn't\b": "has not",
    r"\bhadn't\b": "had not",
    r"\baren't\b": "are not",
    r"\bisn't\b": "is not",
    r"\bwasn't\b": "was not",
    r"\bweren't\b": "were not",
}


def clean_text(text: str) -> str:
    """Clean raw text string.

    Strips whitespace, collapses internal consecutive whitespace,
    normalizes unicode, and removes non-printable characters.

    Args:
        text: Input raw string.

    Returns:
        str: Cleaned text string.
    """
    if text is None:
        return ""
    text = str(text)
    # Normalize unicode to NFKD
    text = unicodedata.normalize("NFKD", text)
    # Remove control characters
    text = "".join(ch for ch in text if unicodedata.category(ch)[0] != "C" or ch in ("\n", "\t"))
    # Remove telephony annotations like [laughter], <whisper>, [applause]
    text = re.sub(r"\[.*?\]|<.*?>", " ", text)
    # Replace multiple whitespaces/tabs/newlines with a single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize(text: str) -> str:
    """Normalize text for consistent NLP model intake.

    Performs lowercasing, contraction expansion, phone/currency tokenization,
    and punctuation simplification.

    Args:
        text: Input text string.

    Returns:
        str: Normalized text string.
    """
    cleaned = clean_text(text).lower()

    # Expand contractions
    for pattern, replacement in CONTRACTIONS.items():
        cleaned = re.sub(pattern, replacement, cleaned)

    # Normalize phone numbers or currency mentions
    cleaned = re.sub(r"\$\s*\d+([.,]\d+)?", " <currency> ", cleaned)
    cleaned = re.sub(r"\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b", " <phonenumber> ", cleaned)
    cleaned = re.sub(r"\b\d{4,8}\b", " <number> ", cleaned)

    # Remove non-alphanumeric except whitespace and common punctuation markers
    cleaned = re.sub(r"[^a-z0-9\s.,?!'<>]", " ", cleaned)
    # Collapse multiple punctuation
    cleaned = re.sub(r"([.,?!]){2,}", r"\1", cleaned)
    # Collapse spaces again
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def remove_duplicates(df: pd.DataFrame, text_col: str = "text") -> pd.DataFrame:
    """Remove exact and case-insensitive duplicate texts from DataFrame.

    Keeps the first occurrence and resets DataFrame index.

    Args:
        df: Input DataFrame.
        text_col: Name of column containing text.

    Returns:
        pd.DataFrame: Deduplicated DataFrame.
    """
    if text_col not in df.columns:
        raise ValueError(f"Column '{text_col}' not found in DataFrame.")

    initial_len = len(df)
    # Create temporary normalized key for comparison
    temp_key = "__normalized_text_key__"
    df = df.copy()
    df[temp_key] = df[text_col].astype(str).str.strip().str.lower()
    deduped = df.drop_duplicates(subset=[temp_key], keep="first").drop(columns=[temp_key])
    deduped = deduped.reset_index(drop=True)
    logger.info("Deduplication: removed %d duplicates (%d -> %d)", initial_len - len(deduped), initial_len, len(deduped))
    return deduped


def stratified_split(
    df: pd.DataFrame,
    label_col: str = "label",
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split DataFrame into train, validation, and test sets with stratification.

    Ensures balanced class distributions across all three splits. If any class
    has insufficient instances for stratified splitting (< 2 samples),
    falls back to non-stratified random split with a logged warning.

    Args:
        df: Input DataFrame.
        label_col: Target column name for stratification.
        test_size: Proportion of dataset to include in test split (e.g. 0.2).
        val_size: Proportion of dataset to include in validation split (e.g. 0.1).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]: (train_df, val_df, test_df)
    """
    if label_col not in df.columns:
        raise ValueError(f"Column '{label_col}' not found in DataFrame.")

    counts = df[label_col].value_counts()
    min_samples = counts.min()
    use_stratify = min_samples >= 2

    if not use_stratify:
        logger.warning(
            "Some classes have fewer than 2 samples (min count: %d). Proceeding with unstratified split.",
            min_samples,
        )

    # 1. Split out test set
    train_val_df, test_df = train_test_split(
        df,
        test_size=test_size,
        random_state=random_state,
        stratify=df[label_col] if use_stratify else None,
    )

    # 2. Split train_val into train and validation
    if val_size > 0:
        adjusted_val_size = val_size / (1.0 - test_size)
        train_counts = train_val_df[label_col].value_counts()
        train_stratify = train_val_df[label_col] if (train_counts.min() >= 2 and use_stratify) else None

        train_df, val_df = train_test_split(
            train_val_df,
            test_size=adjusted_val_size,
            random_state=random_state,
            stratify=train_stratify,
        )
    else:
        train_df = train_val_df
        val_df = pd.DataFrame(columns=df.columns)

    logger.info(
        "Dataset split complete: train=%d, val=%d, test=%d",
        len(train_df),
        len(val_df),
        len(test_df),
    )
    return (
        train_df.reset_index(drop=True),
        val_df.reset_index(drop=True),
        test_df.reset_index(drop=True),
    )
