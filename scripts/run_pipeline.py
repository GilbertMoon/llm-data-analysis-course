"""데이터 로드부터 기초 분석까지 실행하는 예제 파이프라인입니다."""

from src.analysis import category_sales_summary, customer_sales_summary, summarize_sales
from src.data_loader import load_sales_data


def main() -> None:
    data = load_sales_data()

    print("전체 매출 요약")
    print(summarize_sales(data["order_items"]))

    print("\n카테고리별 매출 상위 5개")
    print(category_sales_summary(data["products"], data["order_items"]).head())

    print("\n고객별 구매금액 상위 5명")
    print(customer_sales_summary(data["customers"], data["orders"], data["order_items"]).head())


if __name__ == "__main__":
    main()
