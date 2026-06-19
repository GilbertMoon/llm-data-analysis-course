from pathlib import Path

import pandas as pd


def load_csv(file_path: str | Path) -> pd.DataFrame:
    """CSV 파일을 읽어 pandas DataFrame으로 반환합니다."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {path}")
    return pd.read_csv(path)


def load_sales_data(data_dir: str | Path = "data/raw") -> dict[str, pd.DataFrame]:
    """실습용 쇼핑몰 CSV 파일 4개를 한 번에 불러옵니다."""
    base_dir = Path(data_dir)
    return {
        "customers": load_csv(base_dir / "customers.csv"),
        "products": load_csv(base_dir / "products.csv"),
        "orders": load_csv(base_dir / "orders.csv"),
        "order_items": load_csv(base_dir / "order_items.csv"),
    }
