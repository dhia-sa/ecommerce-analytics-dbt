"""
Download the Olist Brazilian E-commerce dataset from Kaggle into data/raw/.

Requires a Kaggle API token:
  - locally: put kaggle.json in ~/.kaggle/ (Windows: C:\\Users\\<you>\\.kaggle\\)
  - in CI:   set KAGGLE_USERNAME and KAGGLE_KEY environment variables

Usage:
    python scripts/download_data.py
"""
from pathlib import Path

DATASET = "olistbr/brazilian-ecommerce"
RAW_DIR = Path(__file__).resolve().parents[1] / "data" / "raw"

EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    missing = [f for f in EXPECTED_FILES if not (RAW_DIR / f).exists()]
    if not missing:
        print(f"All files already present in {RAW_DIR}")
        return

    from kaggle.api.kaggle_api_extended import KaggleApi  # imported late: authenticates on import

    api = KaggleApi()
    api.authenticate()
    print(f"Downloading {DATASET} to {RAW_DIR} ...")
    api.dataset_download_files(DATASET, path=str(RAW_DIR), unzip=True, quiet=False)

    still_missing = [f for f in EXPECTED_FILES if not (RAW_DIR / f).exists()]
    if still_missing:
        raise SystemExit(f"Download finished but files are missing: {still_missing}")
    print("Done.")


if __name__ == "__main__":
    main()
