import hashlib
import shutil
from pathlib import Path

from PIL import Image, UnidentifiedImageError

# ============================================================
# Configuration
# ============================================================

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100

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

CATEGORIES = {
    str(i): category
    for i, category in enumerate(CLASSES)
}

SPLITS = [
    "training",
    "evaluation",
    "validation",
]


# ============================================================
# Paths
# ============================================================

LAB_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = LAB_ROOT / "data"

RAW_DIR = DATA_DIR / "food11_raw"
PROCESSED_DIR = DATA_DIR / "food11_processed"
MINI_DIR = DATA_DIR / "food11_processed_mini"


# ============================================================
# Duplicate tracking
# ============================================================

# Maps:
#
# image_hash -> split where the image was first seen
#
# Example:
#
# {
#     "abc123...": "training",
#     "def456...": "evaluation",
# }
#
# A repeated image is only rejected if it appears
# in a DIFFERENT split.

SEEN_HASHES = {}


# ============================================================
# Helper functions
# ============================================================

def category_from_filename(filename: str) -> str:
    """
    Extract the Food-11 category from a filename.

    Examples:
        0_123.jpg -> Bread
        5_456.jpg -> Meat
        10_789.jpg -> Vegetable-Fruit
    """

    category_id = filename.split("_")[0]

    return CATEGORIES.get(category_id)


def resize_image(
    img: Image.Image,
    size: int = 128,
) -> Image.Image:
    """
    Convert an image to RGB and resize it to size x size.
    """

    return img.convert("RGB").resize(
        (size, size),
        Image.Resampling.LANCZOS,
    )


def file_hash(path: Path) -> str:
    """
    Return the MD5 hash of a file.

    The hash is used to detect identical image files.
    """

    return hashlib.md5(
        path.read_bytes()
    ).hexdigest()


def prepare_output_directories():
    """
    Remove old processed datasets and recreate empty folders.
    """

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    if MINI_DIR.exists():
        shutil.rmtree(MINI_DIR)

    for split in SPLITS:
        for category in CLASSES:

            (
                PROCESSED_DIR
                / split
                / category
            ).mkdir(
                parents=True,
                exist_ok=True,
            )

            (
                MINI_DIR
                / split
                / category
            ).mkdir(
                parents=True,
                exist_ok=True,
            )


def process_split(split: str):
    """
    Process one split:
    training, evaluation, or validation.

    Identical images are allowed inside the same split,
    but an image already seen in another split is skipped.
    """

    input_split = RAW_DIR / split

    if not input_split.exists():
        print(
            f"ERROR: Split folder does not exist: "
            f"{input_split}"
        )
        return

    mini_counts = {
        category: 0
        for category in CLASSES
    }

    files = sorted(input_split.iterdir())

    processed_count = 0
    cross_split_duplicate_count = 0

    for file_path in files:

        # Skip folders and non-files.
        if not file_path.is_file():
            continue

        category = category_from_filename(
            file_path.name
        )

        # Skip files that do not follow
        # the Food-11 naming convention.
        if category is None:
            print(
                f"Skipping unknown file: "
                f"{file_path.name}"
            )
            continue

        try:
            image_hash = file_hash(
                file_path
            )

            previous_split = SEEN_HASHES.get(
                image_hash
            )

            # Only reject the image if the same content
            # already appeared in a DIFFERENT split.
            if (
                previous_split is not None
                and previous_split != split
            ):
                print(
                    f"Skipping cross-split duplicate: "
                    f"{file_path.name} "
                    f"(already in {previous_split})"
                )

                cross_split_duplicate_count += 1

                continue

            with Image.open(file_path) as image:

                image = resize_image(
                    image
                )

                # --------------------------------------------
                # Full processed dataset
                # --------------------------------------------

                processed_path = (
                    PROCESSED_DIR
                    / split
                    / category
                    / file_path.name
                )

                image.save(
                    processed_path
                )

                # --------------------------------------------
                # Mini processed dataset
                # --------------------------------------------

                if mini_counts[category] < MINI_LIMIT:

                    mini_path = (
                        MINI_DIR
                        / split
                        / category
                        / file_path.name
                    )

                    image.save(
                        mini_path
                    )

                    mini_counts[category] += 1

                # Only store the split for this hash
                # if it has never been seen before.
                if previous_split is None:
                    SEEN_HASHES[image_hash] = split

                processed_count += 1

        except (
            OSError,
            ValueError,
            UnidentifiedImageError,
        ) as error:
            print(
                f"Could not process "
                f"{file_path.name}: {error}"
            )

    print(
        f"{split}: processed "
        f"{processed_count} images"
    )

    print(
        f"{split}: skipped "
        f"{cross_split_duplicate_count} "
        f"cross-split duplicates"
    )


# ============================================================
# Main
# ============================================================

def main():

    global SEEN_HASHES

    print("\nFood-11 Data Preparation")
    print("-------------------------")

    print(f"Raw data: {RAW_DIR}")
    print(f"Processed data: {PROCESSED_DIR}")
    print(f"Mini data: {MINI_DIR}")

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"\nRaw dataset not found at:\n"
            f"{RAW_DIR}\n"
            "\nExpected structure:\n"
            "data/food11_raw/training\n"
            "data/food11_raw/evaluation\n"
            "data/food11_raw/validation"
        )

    print("\nCreating output folders...")

    prepare_output_directories()

    # Reset duplicate tracking at the beginning
    # of every complete preprocessing run.
    SEEN_HASHES = {}

    print("\nProcessing images...\n")

    for split in SPLITS:
        process_split(
            split
        )

    print("\nDone!")

    print("\nCreated:")
    print("data/food11_processed")
    print("data/food11_processed_mini")


if __name__ == "__main__":
    main()