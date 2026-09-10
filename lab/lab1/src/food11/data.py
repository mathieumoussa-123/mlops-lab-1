from pathlib import Path
from PIL import Image
import shutil


# ============================================================
# Configuration
# ============================================================

IMAGE_SIZE = (128, 128)
MINI_LIMIT = 100

CATEGORIES = {
    "0": "Bread",
    "1": "Dairy product",
    "2": "Dessert",
    "3": "Egg",
    "4": "Fried food",
    "5": "Meat",
    "6": "Noodles-Pasta",
    "7": "Rice",
    "8": "Seafood",
    "9": "Soup",
    "10": "Vegetable-Fruit",
}

SPLITS = ["training", "evaluation", "validation"]


# ============================================================
# Paths
# ============================================================

# data.py is located at:
# lab/lab1/src/food11/data.py
#
# parents[2] therefore gives:
# lab/lab1/

LAB_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = LAB_ROOT / "data"

RAW_DIR = DATA_DIR / "food11_raw"
PROCESSED_DIR = DATA_DIR / "food11_processed"
MINI_DIR = DATA_DIR / "food11_processed_mini"


# ============================================================
# Helper functions
# ============================================================

def get_category(filename: str):
    """
    Extract category number from Food-11 filename.

    Example:
        0_123.jpg -> Bread
        5_456.jpg -> Meat
        10_789.jpg -> Vegetable-Fruit
    """

    category_id = filename.split("_")[0]

    return CATEGORIES.get(category_id)


def prepare_output_directories():
    """
    Remove old processed datasets and recreate empty folders.
    """

    if PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    if MINI_DIR.exists():
        shutil.rmtree(MINI_DIR)

    for split in SPLITS:
        for category in CATEGORIES.values():

            (PROCESSED_DIR / split / category).mkdir(
                parents=True,
                exist_ok=True
            )

            (MINI_DIR / split / category).mkdir(
                parents=True,
                exist_ok=True
            )


def process_split(split: str):
    """
    Process one split: training, evaluation, or validation.
    """

    input_split = RAW_DIR / split

    if not input_split.exists():
        print(f"ERROR: Split folder does not exist: {input_split}")
        return

    # Track how many mini images we stored for each category
    mini_counts = {
        category: 0
        for category in CATEGORIES.values()
    }

    files = sorted(input_split.iterdir())

    processed_count = 0

    for file_path in files:

        # Skip folders and non-files
        if not file_path.is_file():
            continue

        category = get_category(file_path.name)

        # Skip files that do not follow Food-11 naming
        if category is None:
            print(f"Skipping unknown file: {file_path.name}")
            continue

        try:
            with Image.open(file_path) as image:

                # Convert to RGB to avoid format/mode problems
                image = image.convert("RGB")

                # Resize to 128x128
                image = image.resize(
                    IMAGE_SIZE,
                    Image.Resampling.LANCZOS
                )

                # ------------------------------------------------
                # Full processed dataset
                # ------------------------------------------------

                processed_path = (
                    PROCESSED_DIR
                    / split
                    / category
                    / file_path.name
                )

                image.save(processed_path)

                # ------------------------------------------------
                # Mini processed dataset
                # ------------------------------------------------

                if mini_counts[category] < MINI_LIMIT:

                    mini_path = (
                        MINI_DIR
                        / split
                        / category
                        / file_path.name
                    )

                    image.save(mini_path)

                    mini_counts[category] += 1

                processed_count += 1

        except Exception as error:
            print(f"Could not process {file_path.name}: {error}")

    print(f"{split}: processed {processed_count} images")


# ============================================================
# Main
# ============================================================

def main():

    print("\nFood-11 Data Preparation")
    print("-------------------------")

    print(f"Raw data: {RAW_DIR}")
    print(f"Processed data: {PROCESSED_DIR}")
    print(f"Mini data: {MINI_DIR}")

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"\nRaw dataset not found at:\n{RAW_DIR}\n"
            "\nExpected structure:\n"
            "data/food11_raw/training\n"
            "data/food11_raw/evaluation\n"
            "data/food11_raw/validation"
        )

    print("\nCreating output folders...")
    prepare_output_directories()

    print("\nProcessing images...\n")

    for split in SPLITS:
        process_split(split)

    print("\nDone!")

    print("\nCreated:")
    print("data/food11_processed")
    print("data/food11_processed_mini")


if __name__ == "__main__":
    main()