
import argparse
import math
import os

import mlflow
from mlflow import MlflowClient

# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "food11"
METRIC_NAME = "test_accuracy"

# Number of images in our evaluation split
TEST_SET_SIZE = 1096

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "http://127.0.0.1:5000",
)


# ============================================================
# Helpers
# ============================================================

def get_accuracy(client, model_version):
    """Read the test accuracy of a registered model version."""

    if not model_version.run_id:
        raise ValueError(
            f"Version {model_version.version} has no associated run ID."
        )

    run = client.get_run(model_version.run_id)
    metrics = run.data.metrics

    if METRIC_NAME not in metrics:
        raise ValueError(
            f"Missing {METRIC_NAME} for version "
            f"{model_version.version} (run {model_version.run_id})"
        )

    accuracy = float(metrics[METRIC_NAME])

    if not 0.0 <= accuracy <= 1.0:
        raise ValueError("Accuracy must be between 0 and 1.")

    return accuracy


# ============================================================
# Promotion gate
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Promote a Food-11 model using a quality gate."
    )

    parser.add_argument(
        "--version",
        type=int,
        required=True,
        help="Candidate model version number",
    )

    parser.add_argument(
        "--n",
        type=int,
        default=TEST_SET_SIZE,
        help="Evaluation dataset size",
    )

    args = parser.parse_args()

    if args.n <= 0:
        parser.error("--n must be greater than zero")

    # Connect to MLflow
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    client = MlflowClient()

    print(f"\nMLflow server: {MLFLOW_TRACKING_URI}")
    print(f"Registered model: {MODEL_NAME}")

    # Get candidate
    candidate = client.get_model_version(
        MODEL_NAME,
        str(args.version),
    )

    # Get current champion
    champion = client.get_model_version_by_alias(
        MODEL_NAME,
        "champion",
    )

    if str(candidate.version) == str(champion.version):
        raise ValueError(
            "Candidate is already the champion. "
            "Choose a different version."
        )

    # Retrieve accuracies from the runs
    candidate_acc = get_accuracy(client, candidate)
    champion_acc = get_accuracy(client, champion)

    # Compute standard error
    se = math.sqrt(
        champion_acc * (1.0 - champion_acc) / args.n
    )

    margin = 2.0 * se
    threshold = champion_acc + margin

    # Apply quality gate
    if candidate_acc >= threshold:
        decision = "PROMOTED_TO_CHAMPION"
        assigned_alias = "champion"

        client.set_registered_model_alias(
            MODEL_NAME,
            "champion",
            str(candidate.version),
        )
    else:
        decision = "KEPT_AS_CHALLENGER"
        assigned_alias = "challenger"

        client.set_registered_model_alias(
            MODEL_NAME,
            "challenger",
            str(candidate.version),
        )

    # Save decision and numerical evidence as model-version tags
    tags = {
        "promotion_decision": decision,
        "candidate_test_accuracy": str(candidate_acc),
        "champion_test_accuracy": str(champion_acc),
        "champion_version_compared": str(champion.version),
        "standard_error": str(se),
        "two_standard_errors": str(margin),
        "promotion_threshold": str(threshold),
        "test_set_size": str(args.n),
    }

    for key, value in tags.items():
        client.set_model_version_tag(
            MODEL_NAME,
            str(candidate.version),
            key,
            value,
        )

    # Print report
    print("\n========== PROMOTION REPORT ==========")
    print(f"Candidate version: {candidate.version}")
    print(f"Champion version: {champion.version}")
    print(f"Test-set size: {args.n}")
    print(f"Candidate accuracy: {candidate_acc:.6f}")
    print(f"Champion accuracy: {champion_acc:.6f}")
    print(f"Standard error: {se:.6f}")
    print(f"2 x SE: {margin:.6f}")
    print(f"Required accuracy: {threshold:.6f}")
    print(f"Decision: {decision}")
    print(f"Assigned alias: {assigned_alias}")
    print("Model-version tags saved successfully")
    print("======================================\n")


if __name__ == "__main__":
    main()
