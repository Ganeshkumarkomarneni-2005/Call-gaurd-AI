"""Data loading utilities for CallGuard AI machine learning pipelines.

Provides standardized loaders for public benchmarks (CLINC150, BANKING77)
and custom CallGuard synthetic and recorded datasets.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Optional, Union

import pandas as pd

logger = logging.getLogger(__name__)


def load_clinc150(split: Optional[str] = None) -> pd.DataFrame:
    """Load the CLINC150 (clinc_oos) dataset.

    Attempts to load via HuggingFace `datasets` library. If unavailable or offline,
    attempts to load from local cache or fallback samples.

    Args:
        split: Optional split name ('train', 'validation', 'test').
               If None, loads and concatenates all splits with a 'split' column.

    Returns:
        pd.DataFrame: Columns ['text', 'intent', 'split'].
    """
    try:
        from datasets import load_dataset

        logger.info("Loading CLINC150 dataset via HuggingFace datasets library...")
        ds = load_dataset("clinc_oos", "plus")
        records = []
        splits_to_load = [split] if split else ["train", "validation", "test"]
        for s in splits_to_load:
            if s in ds:
                split_df = ds[s].to_pandas()
                split_df["split"] = s
                records.append(split_df)
        df = pd.concat(records, ignore_index=True)
        # Rename or ensure 'intent' and 'text' columns
        if "text" in df.columns and "intent" in df.columns:
            return df[["text", "intent", "split"]]
        return df
    except Exception as exc:
        logger.warning(
            "Could not load CLINC150 from HuggingFace (%s). Checking local cache...",
            exc,
        )

    # Check local fallback path
    local_path = Path("ml/datasets/clinc150/clinc150.csv")
    if local_path.exists():
        logger.info("Loaded CLINC150 from local file %s", local_path)
        df = pd.read_csv(local_path)
        if split and "split" in df.columns:
            df = df[df["split"] == split].reset_index(drop=True)
        return df

    # Minimal bootstrap fallback for offline/development environments
    logger.info("Returning bootstrap sample of CLINC150 dataset.")
    sample_data = [
        {"text": "what is my current bank account balance", "intent": "balance", "split": "train"},
        {"text": "check available balance on checking account", "intent": "balance", "split": "train"},
        {"text": "can you tell me if my card was charged yesterday", "intent": "transactions", "split": "train"},
        {"text": "i need to transfer 50 dollars to my savings", "intent": "transfer", "split": "train"},
        {"text": "block my credit card immediately i lost it", "intent": "freeze_account", "split": "train"},
        {"text": "what is the interest rate on personal loans", "intent": "interest_rate", "split": "train"},
        {"text": "how do i change my account password", "intent": "change_password", "split": "validation"},
        {"text": "show my recent deposit history", "intent": "transactions", "split": "validation"},
        {"text": "report unauthorized charges on debit card", "intent": "report_fraud", "split": "test"},
        {"text": "what routing number should i use for wire", "intent": "routing", "split": "test"},
    ]
    df = pd.DataFrame(sample_data)
    if split:
        df = df[df["split"] == split].reset_index(drop=True)
    return df


def load_banking77(split: Optional[str] = None) -> pd.DataFrame:
    """Load the BANKING77 dataset.

    Attempts to load via HuggingFace `datasets` library. If offline or unavailable,
    attempts to load from local cache or fallback samples.

    Args:
        split: Optional split name ('train', 'test').
               If None, loads and concatenates all splits with a 'split' column.

    Returns:
        pd.DataFrame: Columns ['text', 'label', 'split'].
    """
    try:
        from datasets import load_dataset

        logger.info("Loading BANKING77 dataset via HuggingFace datasets...")
        ds = load_dataset("PolyAI/banking77")
        records = []
        splits_to_load = [split] if split else ["train", "test"]
        for s in splits_to_load:
            if s in ds:
                split_df = ds[s].to_pandas()
                # Map numeric label to label name if features exist
                if hasattr(ds[s].features["label"], "int2str"):
                    split_df["label_name"] = split_df["label"].apply(
                        ds[s].features["label"].int2str
                    )
                split_df["split"] = s
                records.append(split_df)
        df = pd.concat(records, ignore_index=True)
        return df
    except Exception as exc:
        logger.warning(
            "Could not load BANKING77 from HuggingFace (%s). Checking local cache...",
            exc,
        )

    local_path = Path("ml/datasets/banking77/banking77.csv")
    if local_path.exists():
        logger.info("Loaded BANKING77 from local file %s", local_path)
        df = pd.read_csv(local_path)
        if split and "split" in df.columns:
            df = df[df["split"] == split].reset_index(drop=True)
        return df

    # Minimal bootstrap fallback
    logger.info("Returning bootstrap sample of BANKING77 dataset.")
    sample_data = [
        {"text": "why is my card payment still pending", "label": "pending_card_payment", "split": "train"},
        {"text": "my card has expired when will new one arrive", "label": "card_arrival", "split": "train"},
        {"text": "how do i activate my newly received card", "label": "activate_my_card", "split": "train"},
        {"text": "there is a charge i do not recognise on my statement", "label": "card_payment_not_recognised", "split": "train"},
        {"text": "can i transfer funds to an international account", "label": "transfer_into_account", "split": "train"},
        {"text": "pin number was entered incorrectly three times", "label": "pin_blocked", "split": "test"},
        {"text": "what are the extra exchange rates for euro payments", "label": "exchange_rate", "split": "test"},
    ]
    df = pd.DataFrame(sample_data)
    if split:
        df = df[df["split"] == split].reset_index(drop=True)
    return df


def load_callguard_custom(
    path: Union[str, Path] = "ml/datasets/callguard/synthetic_conversations.jsonl",
) -> pd.DataFrame:
    """Load the CallGuard custom dataset (synthetic or annotated calls).

    Reads JSONL or CSV formatted conversation files. If the file contains
    nested turn structures, extracts the unified transcript while retaining
    metadata labels (caller_type, intent, risk_level, action, is_recruitment, is_legitimate).

    Args:
        path: File path to the custom dataset.

    Returns:
        pd.DataFrame: Call records with transcripts and annotations.
    """
    file_path = Path(path)
    if not file_path.exists():
        logger.warning("CallGuard custom dataset file not found at %s. Attempting to generate...", file_path)
        try:
            from ml.scripts.synthetic_data_generator import generate_dataset
            file_path.parent.mkdir(parents=True, exist_ok=True)
            generate_dataset(output_path=str(file_path), count_per_scenario=50)
        except Exception as exc:
            logger.error("Failed to generate synthetic data: %s", exc)
            return pd.DataFrame()

    if file_path.suffix == ".jsonl":
        records = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        df = pd.DataFrame(records)
    elif file_path.suffix == ".csv":
        df = pd.read_csv(file_path)
    elif file_path.suffix == ".json":
        df = pd.read_json(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")

    # Ensure full_transcript column exists
    if "full_transcript" not in df.columns and "conversation" in df.columns:
        def build_transcript(turns: list) -> str:
            if isinstance(turns, list):
                return " ".join([t.get("text", "") for t in turns if isinstance(t, dict)])
            return str(turns)
        df["full_transcript"] = df["conversation"].apply(build_transcript)

    # Standardize primary text column
    if "text" not in df.columns and "full_transcript" in df.columns:
        df["text"] = df["full_transcript"]

    logger.info("Loaded CallGuard dataset with %d records from %s", len(df), file_path)
    return df


def merge_datasets(
    dfs: List[pd.DataFrame],
    label_col: str = "intent",
    text_col: str = "text",
) -> pd.DataFrame:
    """Concatenate multiple DataFrames and standardize text/label schema.

    Args:
        dfs: List of DataFrames to merge.
        label_col: Destination column name for labels.
        text_col: Destination column name for text utterances.

    Returns:
        pd.DataFrame: Merged and cleaned DataFrame.
    """
    processed_dfs = []
    for i, df in enumerate(dfs):
        if df is None or df.empty:
            continue
        curr = df.copy()

        # Find text column
        if text_col not in curr.columns:
            candidates = ["full_transcript", "utterance", "query", "sentence"]
            for cand in candidates:
                if cand in curr.columns:
                    curr[text_col] = curr[cand]
                    break

        # Find label column
        if label_col not in curr.columns:
            candidates = ["label", "intent", "category", "target", "label_name"]
            for cand in candidates:
                if cand in curr.columns:
                    curr[label_col] = curr[cand]
                    break

        if text_col in curr.columns and label_col in curr.columns:
            subset = curr[[text_col, label_col]].dropna().copy()
            subset["source_index"] = i
            processed_dfs.append(subset)

    if not processed_dfs:
        return pd.DataFrame(columns=[text_col, label_col, "source_index"])

    merged = pd.concat(processed_dfs, ignore_index=True)
    merged[text_col] = merged[text_col].astype(str).str.strip()
    merged = merged[merged[text_col] != ""]
    logger.info("Merged %d datasets into %d total rows", len(processed_dfs), len(merged))
    return merged
