"""Feature engineering utilities for telephony call classification and fraud detection.

Provides TF-IDF vectorization and linguistic/stylistic feature extraction.
"""

from __future__ import annotations

import re
from typing import Any, List, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

# Lexicons for fraud, urgency, and monetary signals
URGENCY_KEYWORDS = {
    "urgent",
    "urgently",
    "immediately",
    "expire",
    "expired",
    "expiring",
    "suspended",
    "suspension",
    "alert",
    "warning",
    "action required",
    "final notice",
    "asap",
    "promptly",
    "within 24 hours",
    "lawsuit",
    "warrant",
    "arrest",
    "penalty",
    "terminate",
    "critical",
    "freeze",
    "frozen",
    "cancel",
    "cancelled",
    "limited time",
}

MONETARY_KEYWORDS = {
    "fee",
    "fees",
    "dollar",
    "dollars",
    "payment",
    "payments",
    "credit card",
    "debit card",
    "deposit",
    "bank",
    "banking",
    "transfer",
    "gift card",
    "wire",
    "crypto",
    "bitcoin",
    "cash",
    "refund",
    "charge",
    "invoice",
    "balance",
    "money",
    "account number",
    "routing number",
    "otp",
    "pin",
    "cvv",
}


def build_tfidf_features(
    train_texts: Sequence[str],
    test_texts: Sequence[str],
    max_features: int = 10000,
    ngram_range: Tuple[int, int] = (1, 2),
    sublinear_tf: bool = True,
) -> Tuple[Any, Any, TfidfVectorizer]:
    """Build and fit TF-IDF vectorizer on training texts, then transform test texts.

    Args:
        train_texts: Training corpus strings.
        test_texts: Test corpus strings.
        max_features: Maximum vocabulary size.
        ngram_range: N-gram lower and upper boundary.
        sublinear_tf: Apply sublinear tf scaling (1 + log(tf)).

    Returns:
        Tuple[scipy.sparse.csr_matrix, scipy.sparse.csr_matrix, TfidfVectorizer]:
            (X_train, X_test, vectorizer)
    """
    vectorizer = TfidfVectorizer(
        max_features=max_features,
        ngram_range=ngram_range,
        sublinear_tf=sublinear_tf,
        strip_accents="unicode",
        lowercase=True,
    )
    X_train = vectorizer.fit_transform(train_texts)
    X_test = vectorizer.transform(test_texts)
    return X_train, X_test, vectorizer


def extract_linguistic_features(texts: Sequence[str]) -> pd.DataFrame:
    """Extract linguistic, stylistic, and risk marker features from call transcripts.

    Features computed per transcript:
    - `word_count`: total words
    - `avg_word_length`: mean characters per word
    - `sentence_count`: estimated sentence count based on terminators (. ! ? \n)
    - `exclamation_count`: occurrences of '!'
    - `question_count`: occurrences of '?'
    - `caps_ratio`: uppercase characters divided by total length
    - `urgency_word_count`: occurrences of urgent pressure phrases
    - `monetary_keyword_count`: occurrences of financial/transactional terms

    Args:
        texts: Sequence of transcript strings.

    Returns:
        pd.DataFrame: Engineered feature matrix with 8 columns.
    """
    records = []

    for raw_text in texts:
        text = str(raw_text) if raw_text is not None else ""
        text_len = len(text)
        words = re.findall(r"\b\w+\b", text.lower())
        word_count = len(words)

        # Average word length
        avg_word_length = (
            float(sum(len(w) for w in words) / word_count) if word_count > 0 else 0.0
        )

        # Sentence count estimation
        sentences = re.split(r"[.!?\n]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]
        sentence_count = max(1, len(sentences))

        # Punctuation counts
        exclamation_count = text.count("!")
        question_count = text.count("?")

        # Caps ratio (measuring shouting or robotic uppercase headers)
        caps_count = sum(1 for c in text if c.isupper())
        caps_ratio = float(caps_count / text_len) if text_len > 0 else 0.0

        # Lexicon matching
        lower_text = text.lower()
        urgency_count = 0
        for phrase in URGENCY_KEYWORDS:
            if " " in phrase:
                urgency_count += lower_text.count(phrase)
            else:
                urgency_count += sum(1 for w in words if w == phrase)

        monetary_count = 0
        for phrase in MONETARY_KEYWORDS:
            if " " in phrase:
                monetary_count += lower_text.count(phrase)
            else:
                monetary_count += sum(1 for w in words if w == phrase)

        records.append(
            {
                "word_count": word_count,
                "avg_word_length": avg_word_length,
                "sentence_count": sentence_count,
                "exclamation_count": exclamation_count,
                "question_count": question_count,
                "caps_ratio": caps_ratio,
                "urgency_word_count": urgency_count,
                "monetary_keyword_count": monetary_count,
            }
        )

    return pd.DataFrame(records)
