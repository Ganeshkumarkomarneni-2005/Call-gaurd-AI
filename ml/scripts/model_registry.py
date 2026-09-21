"""Model registry for CallGuard AI machine learning artifacts.

Provides functions to serialize, version, load models, and maintain
structured model card metadata for downstream backend consumption.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

import joblib

logger = logging.getLogger(__name__)


def save_model(
    model: Any,
    name: str,
    version: str,
    metadata: Optional[Dict[str, Any]] = None,
    path: Union[str, Path] = "ml/models",
) -> str:
    """Serialize and save a trained model and companion model card metadata.

    Artifacts saved:
    - `{path}/{name}_v{version}.joblib` (serialized model artifact)
    - `{path}/{name}_v{version}.json` (model card metadata)

    Args:
        model: Trained scikit-learn or PyTorch model object.
        name: Unique model identifier (e.g. 'intent_classifier', 'fraud_detector').
        version: Semantic version string (e.g. '1.0.0').
        metadata: Model card dictionary detailing metrics, features, hyperparameters, limitations.
        path: Target directory path.

    Returns:
        str: Path to saved model artifact.
    """
    out_dir = Path(path)
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_version = version.lstrip("v")
    base_stem = f"{name}_v{clean_version}"
    model_file = out_dir / f"{base_stem}.joblib"
    meta_file = out_dir / f"{base_stem}.json"

    # Persist model
    joblib.dump(model, model_file)
    logger.info("Saved model artifact to %s", model_file)

    # Prepare model card metadata
    meta_payload = {
        "model_name": name,
        "version": clean_version,
        "saved_at": datetime.now(timezone.utc).isoformat(),
        "model_file": str(model_file.name),
        "framework": "scikit-learn",
        "description": f"CallGuard AI model for {name}",
    }
    if metadata:
        meta_payload.update(metadata)

    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(meta_payload, f, indent=2)
    logger.info("Saved model card metadata to %s", meta_file)

    return str(model_file)


def load_model(
    name: str,
    version: str,
    path: Union[str, Path] = "ml/models",
) -> Any:
    """Load a serialized model from the registry.

    Args:
        name: Model identifier name.
        version: Version string.
        path: Registry base directory.

    Returns:
        Any: Loaded model object.
    """
    clean_version = version.lstrip("v")
    model_file = Path(path) / f"{name}_v{clean_version}.joblib"
    if not model_file.exists():
        raise FileNotFoundError(f"Model artifact not found at {model_file}")

    model = joblib.load(model_file)
    logger.info("Loaded model %s (v%s) from %s", name, clean_version, model_file)
    return model


def get_model_card(
    name: str,
    version: str,
    path: Union[str, Path] = "ml/models",
) -> Dict[str, Any]:
    """Retrieve the model card metadata JSON for a registered model.

    Args:
        name: Model identifier name.
        version: Version string.
        path: Registry base directory.

    Returns:
        Dict[str, Any]: Parsed model card metadata.
    """
    clean_version = version.lstrip("v")
    meta_file = Path(path) / f"{name}_v{clean_version}.json"
    if not meta_file.exists():
        raise FileNotFoundError(f"Model card metadata not found at {meta_file}")

    with open(meta_file, "r", encoding="utf-8") as f:
        card = json.load(f)
    return card
