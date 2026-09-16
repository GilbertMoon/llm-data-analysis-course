"""Prepare validated Chapter10 classification input from common project raw data.

Run from the project root:

    python scripts/prepare_ch10_data.py

Input:
    data/raw/customers.csv
    data/raw/products.csv
    data/raw/orders.csv
    data/raw/order_items.csv

Output:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

Chapter05의 전용 오류 탐지 데이터(`practice/chapter05/data/raw`)는 사용하지 않습니다.
Chapter10은 Chapter08·09와 같은 공통 프로젝트 데이터 흐름을 이어받습니다.
"""

from __future__ import annotations

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_loader import load_sales_data  # noqa: E402
from src.preprocessing import (  # noqa: E402
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)


RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def prepare_ch10_data(
    raw_dir: str | Path = RAW_DIR,
    processed_dir: str | Path = PROCESSED_DIR,
) -> dict[str, object]:
    """Preprocess common raw data and fail on core relationship errors."""
    raw_data = load_sales_data(raw_dir)
    processed_data = preprocess_sales_data(raw_data)
    relationship_checks = validate_relationships(processed_data)

    if (
        not relationship_checks.empty
        and not relationship_checks["invalid_count"].eq(0).all()
    ):
        failed = relationship_checks.loc[
            relationship_checks["invalid_count"].ne(0)
        ]
        raise ValueError(
            "Chapter10 입력 관계 검증에 실패했습니다:\n"
            + failed.to_string(index=False)
        )

    saved_paths = save_processed_data(processed_data, processed_dir)
    return {
        "raw_data": raw_data,
        "processed_data": processed_data,
        "relationship_checks": relationship_checks,
        "saved_paths": saved_paths,
    }


def main() -> None:
    result = prepare_ch10_data()

    print("Chapter10 모델링 입력 준비 완료")
    print(f"입력 Raw 경로: {RAW_DIR}")
    print("\n[관계 검증]")
    print(result["relationship_checks"].to_string(index=False))
    print("\n[저장된 processed 파일]")
    for path in result["saved_paths"]:
        print(f"- {path}")


if __name__ == "__main__":
    main()
