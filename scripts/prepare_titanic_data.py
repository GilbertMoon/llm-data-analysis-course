from __future__ import annotations

import argparse
import hashlib
import io
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE_URL = (
    "https://raw.githubusercontent.com/mlcommons/croissant/"
    "main/datasets/1.0/titanic/data/titanic.csv"
)
SOURCE_SHA256 = "c617db2c7470716250f6f001be51304c76bcc8815527ab8bae734bdca0735737"

RAW_COLUMNS = [
    "pclass",
    "survived",
    "name",
    "sex",
    "age",
    "sibsp",
    "parch",
    "ticket",
    "fare",
    "cabin",
    "embarked",
    "boat",
    "body",
    "home.dest",
]

KEEP_COLUMNS = [
    "pclass",
    "survived",
    "name",
    "sex",
    "age",
    "sibsp",
    "parch",
    "ticket",
    "fare",
    "cabin",
    "embarked",
]

RENAME_COLUMNS = {
    "pclass": "Pclass",
    "survived": "Survived",
    "name": "Name",
    "sex": "Sex",
    "age": "Age",
    "sibsp": "SibSp",
    "parch": "Parch",
    "ticket": "Ticket",
    "fare": "Fare",
    "cabin": "Cabin",
    "embarked": "Embarked",
}

OUTPUT_COLUMNS = [
    "Pclass",
    "Survived",
    "Name",
    "Sex",
    "Age",
    "SibSp",
    "Parch",
    "Ticket",
    "Fare",
    "Cabin",
    "Embarked",
]

EXPECTED_RAW_SHAPE = (1309, 14)
EXPECTED_OUTPUT_SHAPE = (1309, 11)
EXPECTED_MISSING = {
    "Age": 263,
    "Fare": 1,
    "Cabin": 1014,
    "Embarked": 2,
}

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "titanic" / "train.csv"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_prepared(df: pd.DataFrame) -> None:
    if tuple(df.shape) != EXPECTED_OUTPUT_SHAPE:
        raise ValueError(
            f"Unexpected prepared shape: {df.shape}; expected {EXPECTED_OUTPUT_SHAPE}"
        )

    if list(df.columns) != OUTPUT_COLUMNS:
        raise ValueError(
            "Unexpected prepared columns:\n"
            f"actual={list(df.columns)}\nexpected={OUTPUT_COLUMNS}"
        )

    if df["Survived"].isna().any():
        raise ValueError("Target Survived contains missing values.")

    target_values = set(df["Survived"].astype(int).unique().tolist())
    if not target_values.issubset({0, 1}):
        raise ValueError(f"Unexpected Survived values: {sorted(target_values)}")

    actual_missing = {
        column: int(df[column].isna().sum()) for column in EXPECTED_MISSING
    }
    if actual_missing != EXPECTED_MISSING:
        raise ValueError(
            "Unexpected missing-value counts:\n"
            f"actual={actual_missing}\nexpected={EXPECTED_MISSING}"
        )


def download_verified_source() -> bytes:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "llm-data-analysis-course/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw_bytes = response.read()
    except Exception as exc:
        raise RuntimeError(
            "Titanic source download failed. Check the network and try again."
        ) from exc

    actual_sha256 = sha256_bytes(raw_bytes)
    if actual_sha256 != SOURCE_SHA256:
        raise RuntimeError(
            "Source integrity check failed. Do not continue with an unverified file.\n"
            f"actual={actual_sha256}\nexpected={SOURCE_SHA256}"
        )

    return raw_bytes


def prepare_from_raw(raw_bytes: bytes) -> pd.DataFrame:
    raw_df = pd.read_csv(io.BytesIO(raw_bytes), na_values=["?"])

    if tuple(raw_df.shape) != EXPECTED_RAW_SHAPE:
        raise ValueError(
            f"Unexpected raw shape: {raw_df.shape}; expected {EXPECTED_RAW_SHAPE}"
        )

    if list(raw_df.columns) != RAW_COLUMNS:
        raise ValueError(
            "Unexpected raw columns:\n"
            f"actual={list(raw_df.columns)}\nexpected={RAW_COLUMNS}"
        )

    prepared = raw_df[KEEP_COLUMNS].rename(columns=RENAME_COLUMNS).copy()
    prepared["Age"] = pd.to_numeric(prepared["Age"], errors="coerce")
    prepared["Fare"] = pd.to_numeric(prepared["Fare"], errors="coerce")

    validate_prepared(prepared)
    return prepared


def validate_existing(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        existing = pd.read_csv(path)
        validate_prepared(existing)
    except Exception as exc:
        print(f"Existing file is not valid: {path}")
        print(exc)
        return False

    print("Titanic course dataset already exists and passed validation.")
    print(f"path: {path}")
    print(f"shape: {existing.shape}")
    print(f"sha256: {sha256_file(path)}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download, verify, and prepare the Titanic course dataset."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and rebuild train.csv even when a valid file already exists.",
    )
    args = parser.parse_args()

    if not args.force and validate_existing(OUTPUT_PATH):
        return

    raw_bytes = download_verified_source()
    prepared = prepare_from_raw(raw_bytes)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(OUTPUT_PATH, index=False)

    written = pd.read_csv(OUTPUT_PATH)
    validate_prepared(written)

    print("Titanic course dataset prepared successfully.")
    print(f"source: {SOURCE_URL}")
    print(f"source sha256: {SOURCE_SHA256}")
    print(f"path: {OUTPUT_PATH}")
    print(f"shape: {written.shape}")
    print(f"columns: {list(written.columns)}")
    print(
        "missing: "
        + str({column: int(written[column].isna().sum()) for column in EXPECTED_MISSING})
    )
    print(f"output sha256: {sha256_file(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
