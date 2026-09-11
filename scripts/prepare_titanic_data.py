from __future__ import annotations

import argparse
import hashlib
import io
import urllib.request
from pathlib import Path

import pandas as pd

SOURCE_COMMIT = "54cf59b4fabae5db3b8c7b6b6003f9275596d5f2"
SOURCE_URL = (
    "https://raw.githubusercontent.com/pandas-dev/pandas/"
    f"{SOURCE_COMMIT}/doc/data/titanic.csv"
)

EXPECTED_COLUMNS = [
    "PassengerId",
    "Survived",
    "Pclass",
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
EXPECTED_SHAPE = (891, 12)
EXPECTED_MISSING = {
    "Age": 177,
    "Cabin": 687,
    "Embarked": 2,
}
EXPECTED_TARGET_COUNTS = {0: 549, 1: 342}

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


def validate_dataset(df: pd.DataFrame) -> None:
    if tuple(df.shape) != EXPECTED_SHAPE:
        raise ValueError(
            f"Unexpected shape: {df.shape}; expected {EXPECTED_SHAPE}"
        )

    if list(df.columns) != EXPECTED_COLUMNS:
        raise ValueError(
            "Unexpected columns:\n"
            f"actual={list(df.columns)}\nexpected={EXPECTED_COLUMNS}"
        )

    if df["PassengerId"].isna().any():
        raise ValueError("PassengerId contains missing values.")

    if not df["PassengerId"].is_unique:
        raise ValueError("PassengerId must be unique.")

    passenger_ids = df["PassengerId"].astype(int).tolist()
    if passenger_ids != list(range(1, 892)):
        raise ValueError("PassengerId must be exactly 1..891 in order.")

    if df["Survived"].isna().any():
        raise ValueError("Target Survived contains missing values.")

    target_values = set(df["Survived"].astype(int).unique().tolist())
    if target_values != {0, 1}:
        raise ValueError(f"Unexpected Survived values: {sorted(target_values)}")

    target_counts = {
        int(key): int(value)
        for key, value in df["Survived"].astype(int).value_counts().sort_index().items()
    }
    if target_counts != EXPECTED_TARGET_COUNTS:
        raise ValueError(
            "Unexpected target counts:\n"
            f"actual={target_counts}\nexpected={EXPECTED_TARGET_COUNTS}"
        )

    actual_missing = {
        column: int(df[column].isna().sum()) for column in EXPECTED_MISSING
    }
    if actual_missing != EXPECTED_MISSING:
        raise ValueError(
            "Unexpected missing-value counts:\n"
            f"actual={actual_missing}\nexpected={EXPECTED_MISSING}"
        )


def download_source() -> bytes:
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "llm-data-analysis-course/1.0"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except Exception as exc:
        raise RuntimeError(
            "Titanic source download failed. Check the network and try again."
        ) from exc


def prepare_from_raw(raw_bytes: bytes) -> pd.DataFrame:
    df = pd.read_csv(io.BytesIO(raw_bytes))
    validate_dataset(df)
    return df


def validate_existing(path: Path) -> bool:
    if not path.exists():
        return False

    try:
        existing = pd.read_csv(path)
        validate_dataset(existing)
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
        description="Download and validate the 891-row Titanic training dataset."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download and rebuild train.csv even when a valid file already exists.",
    )
    args = parser.parse_args()

    if not args.force and validate_existing(OUTPUT_PATH):
        return

    raw_bytes = download_source()
    prepared = prepare_from_raw(raw_bytes)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prepared.to_csv(OUTPUT_PATH, index=False)

    written = pd.read_csv(OUTPUT_PATH)
    validate_dataset(written)

    print("Titanic course dataset prepared successfully.")
    print(f"source commit: {SOURCE_COMMIT}")
    print(f"source: {SOURCE_URL}")
    print(f"download sha256: {sha256_bytes(raw_bytes)}")
    print(f"path: {OUTPUT_PATH}")
    print(f"shape: {written.shape}")
    print(f"columns: {list(written.columns)}")
    print(
        "missing: "
        + str({column: int(written[column].isna().sum()) for column in EXPECTED_MISSING})
    )
    print(
        "target counts: "
        + str(
            {
                int(key): int(value)
                for key, value in written["Survived"]
                .astype(int)
                .value_counts()
                .sort_index()
                .items()
            }
        )
    )
    print(f"output sha256: {sha256_file(OUTPUT_PATH)}")


if __name__ == "__main__":
    main()
