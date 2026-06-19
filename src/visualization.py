from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def plot_monthly_sales(
    monthly_sales: pd.DataFrame,
    output_path: str | Path | None = None,
) -> None:
    """월별 매출 그래프를 그립니다."""
    plt.figure(figsize=(10, 5))
    sns.lineplot(data=monthly_sales, x="month", y="total_sales", marker="o")
    plt.title("월별 매출 추이")
    plt.xlabel("월")
    plt.ylabel("매출")
    plt.xticks(rotation=45)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()


def plot_category_sales(
    category_sales: pd.DataFrame,
    output_path: str | Path | None = None,
) -> None:
    """카테고리별 매출 막대 그래프를 그립니다."""
    plt.figure(figsize=(10, 5))
    sns.barplot(data=category_sales, x="category", y="total_sales")
    plt.title("카테고리별 매출")
    plt.xlabel("카테고리")
    plt.ylabel("매출")
    plt.xticks(rotation=30)
    plt.tight_layout()
    if output_path:
        plt.savefig(output_path, dpi=150)
    plt.show()
