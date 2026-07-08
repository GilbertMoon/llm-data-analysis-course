"""Chapter 7 데이터 시각화 실행 스크립트.

실행 방법:
    python scripts/run_visualization.py

전제 조건:
    python scripts/preprocess_data.py

입력:
    data/processed/customers_clean.csv
    data/processed/products_clean.csv
    data/processed/orders_clean.csv
    data/processed/order_items_clean.csv

출력:
    reports/figures/ch07_category_sales_bar.png
    reports/figures/ch07_monthly_sales_line.png
    reports/figures/ch07_product_price_hist.png
    reports/figures/ch07_price_quantity_scatter.png
    reports/figures/ch07_top_customers_barh.png
    reports/figures/ch07_order_status_bar.png
    reports/ch07_visualization_summary.md
"""

from pathlib import Path

from src.visualization import (
    build_visualization_report,
    create_all_figures,
    create_visualization_summary,
    prepare_visualization_data,
    setup_korean_font,
)


PROCESSED_DIR = Path("data/processed")
REPORT_DIR = Path("reports")
FIGURE_DIR = REPORT_DIR / "figures"
SUMMARY_PATH = REPORT_DIR / "ch07_visualization_summary.md"


def main() -> None:
    """전처리 데이터를 불러와 7장 주요 그래프와 요약 보고서를 저장합니다."""
    REPORT_DIR.mkdir(exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    setup_korean_font()
    data = prepare_visualization_data(PROCESSED_DIR)
    saved_figures = create_all_figures(data, FIGURE_DIR, show=False)

    visualization_summary = create_visualization_summary()
    SUMMARY_PATH.write_text(
        build_visualization_report(visualization_summary),
        encoding="utf-8",
    )

    print("7장 시각화 완료")
    print("\n[생성한 그래프 파일]")
    for path in saved_figures:
        print(f"- {path}")

    print(f"\n[요약 보고서] {SUMMARY_PATH}")
    print("\n[시각화 요약]")
    print(visualization_summary.to_string(index=False))


if __name__ == "__main__":
    main()
