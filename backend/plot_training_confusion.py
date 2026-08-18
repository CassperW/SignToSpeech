from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import matplotlib
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix

from train_rbf_svm_raw import DEFAULT_DATA_DIR, load_dataset


matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


BACKEND_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BACKEND_DIR / "rbf_svm_1m_raw.joblib"
DEFAULT_OUTPUT_PATH = BACKEND_DIR / "training_confusion_heatmap.png"


def plot_training_confusion(
    data_dir: Path,
    model_path: Path,
    output_path: Path,
) -> None:
    raw_signals, labels, _, _ = load_dataset(data_dir)
    model = joblib.load(model_path)
    if getattr(model, "n_features_in_", None) != raw_signals.shape[1]:
        raise ValueError(
            f"Model expects {getattr(model, 'n_features_in_', None)} features, "
            f"but the data has {raw_signals.shape[1]}"
        )

    predictions = model.predict(raw_signals)
    class_names = model.classes_.tolist()
    matrix = confusion_matrix(
        labels,
        predictions,
        labels=class_names,
        normalize="true",
    )
    accuracy = accuracy_score(labels, predictions)

    figure, axis = plt.subplots(figsize=(12, 10))
    image = axis.imshow(matrix, cmap="YlGn", vmin=0, vmax=1)
    colorbar = figure.colorbar(image, ax=axis, fraction=0.046, pad=0.04)
    colorbar.set_label("Fraction of each true sign")

    axis.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        xlabel="Predicted sign",
        ylabel="True sign",
        title=(
            "Training-set confusion matrix\n"
            f"RBF-SVM on its own training data · accuracy {accuracy:.1%}"
        ),
    )
    plt.setp(axis.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    for row in range(matrix.shape[0]):
        for column in range(matrix.shape[1]):
            value = matrix[row, column]
            axis.text(
                column,
                row,
                f"{value:.0%}" if value else "",
                ha="center",
                va="center",
                color="white" if value > 0.55 else "#17201d",
                fontsize=8,
                fontweight="bold" if row == column else "normal",
            )

    axis.set_ylim(len(class_names) - 0.5, -0.5)
    figure.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(figure)

    print(f"Samples: {len(labels)}")
    print(f"Training-set accuracy: {accuracy:.4f}")
    print("Per-sign training recall:")
    for class_name, recall in zip(class_names, np.diag(matrix)):
        print(f"  {class_name:12s} {recall:.4f}")
    print(f"Saved heatmap to {output_path}")
    print("Warning: this is training-set performance, not field accuracy.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Plot the model's confusion matrix on its own training data"
    )
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    plot_training_confusion(
        arguments.data_dir.resolve(),
        arguments.model_path.resolve(),
        arguments.output.resolve(),
    )
