import argparse
import hashlib
import sys
from pathlib import Path

from PIL import Image, UnidentifiedImageError

CLASSES = [
    "Bread",
    "Dairy product",
    "Dessert",
    "Egg",
    "Fried food",
    "Meat",
    "Noodles-Pasta",
    "Rice",
    "Seafood",
    "Soup",
    "Vegetable-Fruit",
]

SPLITS = ["training", "validation", "evaluation"]

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def image_files(folder: Path):
    return [
        p
        for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("dataset", type=Path)

    parser.add_argument(
        "--min-per-class",
        type=int,
        default=50,
    )

    parser.add_argument(
        "--tau",
        type=float,
        default=0.05,
    )

    args = parser.parse_args()

    dataset = args.dataset

    all_ok = True
    counts = {}

    # 1. Check class folders
    folders_ok = True

    for split in SPLITS:
        split_dir = dataset / split

        if not split_dir.exists():
            folders_ok = False
            continue

        found = {
            p.name
            for p in split_dir.iterdir()
            if p.is_dir()
        }

        if found != set(CLASSES):
            folders_ok = False

    print(
        "PASS class folders"
        if folders_ok
        else "FAIL class folders"
    )

    all_ok &= folders_ok

    # 2. Validate images
    images_ok = True

    for split in SPLITS:
        for class_name in CLASSES:
            folder = dataset / split / class_name

            if not folder.exists():
                continue

            for path in image_files(folder):
                try:
                    with Image.open(path) as img:
                        if img.mode != "RGB":
                            images_ok = False

                        if img.size != (128, 128):
                            images_ok = False

                except (OSError, ValueError, UnidentifiedImageError):
                    images_ok = False

    print(
        "PASS image format"
        if images_ok
        else "FAIL image format"
    )

    all_ok &= images_ok

    # 3. Minimum images per class
    minimum_ok = True

    for split in SPLITS:
        counts[split] = {}

        for class_name in CLASSES:
            folder = dataset / split / class_name

            count = (
                len(image_files(folder))
                if folder.exists()
                else 0
            )

            counts[split][class_name] = count

            if count < args.min_per_class:
                minimum_ok = False

    print(
        "PASS minimum per class"
        if minimum_ok
        else "FAIL minimum per class"
    )

    all_ok &= minimum_ok

    # 4. Duplicate detection across splits
    duplicate_ok = True
    seen = {}

    for split in SPLITS:
        for class_name in CLASSES:
            folder = dataset / split / class_name

            if not folder.exists():
                continue

            for path in image_files(folder):
                file_hash = hashlib.md5(
                    path.read_bytes()
                ).hexdigest()

                if file_hash in seen:
                    previous_split = seen[file_hash]

                    if previous_split != split:
                        duplicate_ok = False
                else:
                    seen[file_hash] = split

    print(
        "PASS no cross-split duplicates"
        if duplicate_ok
        else "FAIL cross-split duplicates"
    )

    all_ok &= duplicate_ok

    # 5. Training vs validation class distribution
    distribution_ok = True

    train_total = sum(counts["training"].values())
    val_total = sum(counts["validation"].values())

    if train_total == 0 or val_total == 0:
        distribution_ok = False
    else:
        for class_name in CLASSES:
            train_share = (
                counts["training"][class_name]
                / train_total
            )

            val_share = (
                counts["validation"][class_name]
                / val_total
            )

            if abs(train_share - val_share) > args.tau:
                distribution_ok = False

    print(
        "PASS class distribution"
        if distribution_ok
        else "FAIL class distribution"
    )

    all_ok &= distribution_ok

    if not all_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()