import argparse
from pathlib import Path

import mlflow
import mlflow.pytorch
import torch
from torch import nn
from torch.optim import Adam
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------

LAB_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = LAB_ROOT / "data"


# ---------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--dataset",
        choices=["processed", "mini"],
        default="mini"
    )

    parser.add_argument(
        "--epochs",
        type=int,
        default=5
    )

    parser.add_argument(
        "--lr",
        type=float,
        default=0.001
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=32
    )

    return parser.parse_args()


# ---------------------------------------------------------
# Device
# ---------------------------------------------------------

def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")

    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")

    return torch.device("cpu")


# ---------------------------------------------------------
# Datasets and DataLoaders
# ---------------------------------------------------------

def create_dataloaders(dataset_name, batch_size):

    if dataset_name == "mini":
        dataset_dir = DATA_ROOT / "food11_processed_mini"
    else:
        dataset_dir = DATA_ROOT / "food11_processed"

    transform = transforms.Compose([
        transforms.ToTensor(),

        # ImageNet normalization used by pretrained ResNet18
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])

    train_dataset = datasets.ImageFolder(
        dataset_dir / "training",
        transform=transform
    )

    val_dataset = datasets.ImageFolder(
        dataset_dir / "validation",
        transform=transform
    )

    test_dataset = datasets.ImageFolder(
        dataset_dir / "evaluation",
        transform=transform
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False
    )

    return train_loader, val_loader, test_loader


# ---------------------------------------------------------
# Train one epoch
# ---------------------------------------------------------

def train_one_epoch(model, loader, criterion, optimizer, device):

    model.train()

    total_loss = 0.0

    for images, labels in loader:

        images = images.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        outputs = model(images)

        loss = criterion(outputs, labels)

        loss.backward()

        optimizer.step()

        total_loss += loss.item() * images.size(0)

    average_loss = total_loss / len(loader.dataset)

    return average_loss


# ---------------------------------------------------------
# Validation
# ---------------------------------------------------------

def evaluate(model, loader, criterion, device):

    model.eval()

    total_loss = 0.0
    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            loss = criterion(outputs, labels)

            total_loss += loss.item() * images.size(0)

            predictions = outputs.argmax(dim=1)

            correct += (predictions == labels).sum().item()

            total += labels.size(0)

    average_loss = total_loss / len(loader.dataset)

    accuracy = correct / total

    return average_loss, accuracy


# ---------------------------------------------------------
# Test accuracy
# ---------------------------------------------------------

def test_accuracy(model, loader, device):

    model.eval()

    correct = 0
    total = 0

    with torch.no_grad():

        for images, labels in loader:

            images = images.to(device)
            labels = labels.to(device)

            outputs = model(images)

            predictions = outputs.argmax(dim=1)

            correct += (predictions == labels).sum().item()

            total += labels.size(0)

    accuracy = correct / total

    return accuracy


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    args = parse_args()

    device = get_device()

    print(f"Using device: {device}")
    print(f"Dataset: {args.dataset}")
    print(f"Epochs: {args.epochs}")
    print(f"Learning rate: {args.lr}")
    print(f"Batch size: {args.batch_size}")

    # -----------------------------------------------------
    # MLflow configuration
    # -----------------------------------------------------

    mlflow.set_tracking_uri(
        "http://127.0.0.1:5000"
    )

    mlflow.set_experiment(
        "food11"
    )

    # -----------------------------------------------------
    # Load data
    # -----------------------------------------------------

    train_loader, val_loader, test_loader = create_dataloaders(
        args.dataset,
        args.batch_size
    )

    # -----------------------------------------------------
    # Build pretrained ResNet18
    # -----------------------------------------------------

    weights = ResNet18_Weights.DEFAULT

    model = resnet18(
        weights=weights
    )

    # ResNet18 normally outputs 1000 classes.
    # Food-11 has 11 classes.
    model.fc = nn.Linear(
        model.fc.in_features,
        11
    )

    model = model.to(device)

    criterion = nn.CrossEntropyLoss()

    optimizer = Adam(
        model.parameters(),
        lr=args.lr
    )

    # -----------------------------------------------------
    # Start MLflow run
    # -----------------------------------------------------

    with mlflow.start_run():

        # -------------------------------------------------
        # Log hyperparameters
        # -------------------------------------------------

        mlflow.log_params({
            "dataset": args.dataset,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "model": "resnet18",
            "num_classes": 11
        })

        # -------------------------------------------------
        # Training loop
        # -------------------------------------------------

        for epoch in range(args.epochs):

            train_loss = train_one_epoch(
                model,
                train_loader,
                criterion,
                optimizer,
                device
            )

            val_loss, val_accuracy = evaluate(
                model,
                val_loader,
                criterion,
                device
            )

            print(
                f"Epoch {epoch + 1}/{args.epochs} | "
                f"Train Loss: {train_loss:.4f} | "
                f"Val Loss: {val_loss:.4f} | "
                f"Val Accuracy: {val_accuracy:.4f}"
            )

            # Log metrics for each epoch
            mlflow.log_metric(
                "train_loss",
                train_loss,
                step=epoch
            )

            mlflow.log_metric(
                "val_loss",
                val_loss,
                step=epoch
            )

            mlflow.log_metric(
                "val_accuracy",
                val_accuracy,
                step=epoch
            )

        # -------------------------------------------------
        # Final test evaluation
        # -------------------------------------------------

        final_test_accuracy = test_accuracy(
            model,
            test_loader,
            device
        )

        print(
            f"Final Test Accuracy: "
            f"{final_test_accuracy:.4f}"
        )

        mlflow.log_metric(
            "test_accuracy",
            final_test_accuracy
        )

        # -------------------------------------------------
        # Log trained model
        # -------------------------------------------------

        # Move model to CPU before saving for portability
        model = model.to("cpu")

        mlflow.pytorch.log_model(
            model,
            name="model",
            serialization_format="pickle"
        )


if __name__ == "__main__":
    main()