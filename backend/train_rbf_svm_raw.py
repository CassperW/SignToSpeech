from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import classification_report
from sklearn.model_selection import GridSearchCV, GroupKFold, cross_val_predict
from sklearn.svm import SVC


DEFAULT_DATA_DIR = Path(__file__).resolve().parent / "data"
DEFAULT_MODEL_PATH = Path(__file__).resolve().with_name("rbf_svm_1m_raw.joblib")
N_RAW_FEATURES = 1025
N_SPLITS = 5
BLOCK_SIZE = 20


def load_dataset(data_dir: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str]]:
    paths = sorted(
        path
        for path in data_dir.glob("*.xlsx")
        if not path.name.startswith("~$")
    )
    if not paths:
        raise FileNotFoundError(f"No Excel files found in {data_dir}")

    parts: list[np.ndarray] = []
    labels: list[str] = []
    groups: list[int] = []

    for path in paths:
        frame = pd.read_excel(path, header=None, engine="openpyxl")
        if frame.shape[1] != N_RAW_FEATURES:
            raise ValueError(
                f"{path.name}: expected {N_RAW_FEATURES} columns, got {frame.shape[1]}"
            )
        try:
            values = frame.to_numpy(dtype=np.float32)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{path.name}: contains non-numeric values") from exc
        if not np.isfinite(values).all():
            raise ValueError(f"{path.name}: contains NaN or infinite values")

        parts.append(values)
        labels.extend([path.stem] * len(values))
        groups.extend(np.arange(len(values)) // BLOCK_SIZE)

    raw_signals = np.vstack(parts)
    unique_groups = np.unique(groups)
    if len(unique_groups) < N_SPLITS:
        raise ValueError(
            f"Need at least {N_SPLITS} row blocks, found {len(unique_groups)}"
        )
    return raw_signals, np.asarray(labels), np.asarray(groups), [p.name for p in paths]


def train(data_dir: Path, model_path: Path) -> None:
    raw_signals, labels, groups, source_files = load_dataset(data_dir)
    print(f"Loaded {len(labels)} samples from {len(source_files)} classes")
    print(f"Model input shape: {raw_signals.shape}; StandardScaler: disabled")

    cross_validation = GroupKFold(n_splits=N_SPLITS)
    search = GridSearchCV(
        SVC(
            kernel="rbf",
            gamma="scale",
            class_weight="balanced",
            cache_size=512,
        ),
        {"C": [0.1, 1, 3, 10, 30, 100]},
        scoring="balanced_accuracy",
        cv=cross_validation,
        n_jobs=1,
        refit=True,
    )
    search.fit(raw_signals, labels, groups=groups)

    best_index = search.best_index_
    fold_scores = np.asarray(
        [
            search.cv_results_[f"split{fold}_test_score"]
            for fold in range(N_SPLITS)
        ]
    )[:, best_index]
    predictions = cross_val_predict(
        search.best_estimator_,
        raw_signals,
        labels,
        groups=groups,
        cv=cross_validation,
        n_jobs=1,
    )

    print(f"Best parameters: {search.best_params_}, gamma='scale'")
    print(f"Block CV scores: {np.round(fold_scores, 4).tolist()}")
    print(f"Mean block CV balanced accuracy: {fold_scores.mean():.4f}")
    print(classification_report(labels, predictions, digits=4, zero_division=0))

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, model_path, compress=3)

    metadata = {
        "model_type": "RBF-SVM",
        "input": "1025 raw board sensor values",
        "raw_feature_count": N_RAW_FEATURES,
        "standard_scaler": False,
        "classes": search.best_estimator_.classes_.tolist(),
        "best_parameters": {"C": search.best_params_["C"], "gamma": "scale"},
        "block_cv_scores": fold_scores.tolist(),
        "block_cv_mean_balanced_accuracy": float(fold_scores.mean()),
        "source_files": source_files,
        "sample_count": int(len(labels)),
        "trained_at_utc": datetime.now(timezone.utc).isoformat(),
        "sklearn_version": sklearn.__version__,
        "validation_note": (
            "Row-block validation uses the current collection only; validate on a new "
            "collection session before treating this score as field accuracy."
        ),
    }
    metadata_path = model_path.with_suffix(".metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved model to {model_path}")
    print(f"Saved metadata to {metadata_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train raw 1025-sensor RBF-SVM")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    train(arguments.data_dir.resolve(), arguments.model_path.resolve())
