"""Chapter 15 최종 데이터 분석 프로젝트 파이프라인.

앞 장에서 검증한 전처리, 완료 주문 기준 EDA, 분류 모델링,
외부 데이터 연결, LLM 사용 기록, 자동화 설계를 하나의 재현 가능한
프로젝트로 묶습니다.

기본 실행은 네트워크를 호출하지 않습니다. 외부 데이터 통합은
data/external/processed/holidays.csv가 있을 때만 수행합니다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

from src.classification import (
    build_classification_checklist,
    build_classification_dataset,
    build_split_summary,
    choose_threshold,
    classification_report_dataframe,
    confusion_matrix_dataframe,
    create_prediction_result,
    final_test_evaluation,
    split_train_validation_test,
    target_distribution,
    threshold_metrics,
    train_and_compare_on_validation,
)
from src.data_loader import load_sales_data
from src.external_data_collection import merge_external_data, sha256_file
from src.midterm_project import (
    build_analysis_tables,
    build_key_duplicate_checks,
    summarize_datasets,
)
from src.preprocessing import (
    compare_shapes,
    preprocess_sales_data,
    save_processed_data,
    validate_relationships,
)
from src.visualization import setup_korean_font


def get_project_paths(base_dir: str | Path = ".") -> dict[str, Path]:
    """최종 프로젝트 폴더 경로를 생성하고 반환합니다."""
    base_path = Path(base_dir).resolve()
    external_root = base_path / "data" / "external"
    paths = {
        "base_dir": base_path,
        "raw_dir": base_path / "data" / "raw",
        "processed_dir": base_path / "data" / "processed",
        "external_root": external_root,
        "external_raw_dir": external_root / "raw",
        "external_processed_dir": external_root / "processed",
        "external_metadata_dir": external_root / "metadata",
        "report_dir": base_path / "reports",
        "figure_dir": base_path / "reports" / "figures",
    }
    for key, path in paths.items():
        if key != "raw_dir":
            path.mkdir(parents=True, exist_ok=True)
    return paths


def prepare_core_analysis(
    base_dir: str | Path = ".",
) -> dict[str, Any]:
    """원본 로드, 전처리, 관계 검증, 완료 주문 기준 EDA를 수행합니다."""
    paths = get_project_paths(base_dir)
    raw_data = load_sales_data(paths["raw_dir"])
    dataset_summary = summarize_datasets(raw_data)
    processed = preprocess_sales_data(raw_data)
    preprocessing_comparison = compare_shapes(raw_data, processed)
    key_duplicate_checks = build_key_duplicate_checks(processed)
    relationship_checks = validate_relationships(processed)

    save_processed_data(
        processed,
        output_dir=paths["processed_dir"],
        encoding="utf-8-sig",
    )

    tables = build_analysis_tables(processed)

    # 외부 배포용 고객 결과에는 원본 식별자를 포함하지 않습니다.
    customer_sales_public = tables["customer_sales"].drop(
        columns=["customer_id"],
        errors="ignore",
    )

    completed_sales_items = tables["completed_sales_items"]
    product_group_columns = [
        column
        for column in [
            "product_id",
            "product_name",
            "category",
            "price",
        ]
        if column in completed_sales_items.columns
    ]
    product_sales = (
        completed_sales_items.groupby(
            product_group_columns,
            as_index=False,
        )
        .agg(
            total_quantity=("quantity", "sum"),
            total_sales=("line_total", "sum"),
        )
        .sort_values("total_sales", ascending=False)
        .reset_index(drop=True)
    )
    product_sales["avg_unit_revenue"] = (
        product_sales["total_sales"]
        / product_sales["total_quantity"].replace(0, pd.NA)
    ).round(0)

    public_tables = {
        "category_sales": tables["category_sales"],
        "monthly_sales": tables["monthly_sales"],
        "customer_sales": customer_sales_public,
        "product_sales": product_sales,
        "order_status_summary": tables["order_status_summary"],
        "amount_scope_summary": tables["amount_scope_summary"],
        "merge_checks": tables["merge_checks"],
    }

    return {
        "paths": paths,
        "raw_data": raw_data,
        "processed": processed,
        "dataset_summary": dataset_summary,
        "preprocessing_comparison": preprocessing_comparison,
        "key_duplicate_checks": key_duplicate_checks,
        "relationship_checks": relationship_checks,
        "analysis_tables": tables,
        "public_tables": public_tables,
    }


def save_core_outputs(core: dict[str, Any]) -> dict[str, Path]:
    """핵심 데이터 품질 및 EDA 결과를 저장합니다."""
    report_dir = core["paths"]["report_dir"]
    outputs = {
        "dataset_summary": report_dir / "ch15_dataset_summary.csv",
        "preprocessing_comparison": report_dir / "ch15_preprocessing_comparison.csv",
        "key_duplicate_checks": report_dir / "ch15_key_duplicate_checks.csv",
        "relationship_checks": report_dir / "ch15_relationship_checks.csv",
        "merge_checks": report_dir / "ch15_merge_checks.csv",
        "amount_scope_summary": report_dir / "ch15_amount_scope_summary.csv",
        "category_sales": report_dir / "ch15_category_sales.csv",
        "monthly_sales": report_dir / "ch15_monthly_sales.csv",
        "customer_sales": report_dir / "ch15_customer_sales.csv",
        "product_sales": report_dir / "ch15_product_sales.csv",
        "order_status_summary": report_dir / "ch15_order_status_summary.csv",
    }

    frames = {
        "dataset_summary": core["dataset_summary"],
        "preprocessing_comparison": core["preprocessing_comparison"],
        "key_duplicate_checks": core["key_duplicate_checks"],
        "relationship_checks": core["relationship_checks"],
        **core["public_tables"],
    }
    for name, path in outputs.items():
        frames[name].to_csv(path, index=False, encoding="utf-8-sig")
    return outputs


def generate_project_figures(
    public_tables: dict[str, pd.DataFrame],
    figure_dir: str | Path,
) -> dict[str, Path]:
    """완료 주문 기준 핵심 시각화를 저장합니다."""
    output_dir = Path(figure_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    setup_korean_font()

    category_sales = public_tables["category_sales"]
    monthly_sales = public_tables["monthly_sales"]
    customer_sales = public_tables["customer_sales"]
    order_status = public_tables["order_status_summary"]

    outputs: dict[str, Path] = {}

    plt.figure(figsize=(10, 5))
    plt.bar(category_sales["category"], category_sales["total_sales"])
    plt.title("카테고리별 완료 주문 매출")
    plt.xlabel("카테고리")
    plt.ylabel("완료 주문 매출")
    plt.xticks(rotation=45)
    plt.tight_layout()
    outputs["category_sales"] = output_dir / "ch15_category_sales.png"
    plt.savefig(outputs["category_sales"], dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(10, 5))
    plt.plot(
        monthly_sales["order_month"],
        monthly_sales["total_sales"],
        marker="o",
    )
    plt.title("월별 완료 주문 매출")
    plt.xlabel("주문 월")
    plt.ylabel("완료 주문 매출")
    plt.xticks(rotation=45)
    plt.tight_layout()
    outputs["monthly_sales"] = output_dir / "ch15_monthly_sales.png"
    plt.savefig(outputs["monthly_sales"], dpi=150, bbox_inches="tight")
    plt.close()

    top_customers = (
        customer_sales.head(10)
        .copy()
        .sort_values("total_sales")
    )
    plt.figure(figsize=(10, 6))
    plt.barh(
        top_customers["customer_label"],
        top_customers["total_sales"],
    )
    plt.title("완료 주문 구매 금액 상위 고객군")
    plt.xlabel("완료 주문 구매 금액")
    plt.ylabel("익명 고객 라벨")
    plt.tight_layout()
    outputs["top_customers"] = output_dir / "ch15_top_customers.png"
    plt.savefig(outputs["top_customers"], dpi=150, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(8, 5))
    plt.bar(
        order_status["order_status"].astype(str),
        order_status["order_count"],
    )
    plt.title("주문 상태별 주문 수")
    plt.xlabel("주문 상태")
    plt.ylabel("주문 수")
    plt.tight_layout()
    outputs["order_status"] = output_dir / "ch15_order_status.png"
    plt.savefig(outputs["order_status"], dpi=150, bbox_inches="tight")
    plt.close()

    return outputs


def run_classification_stage(
    processed: dict[str, pd.DataFrame],
    report_dir: str | Path,
    *,
    random_state: int = 42,
) -> dict[str, Any]:
    """10장과 같은 기준으로 주문 취소 분류 모델을 실행합니다."""
    output_dir = Path(report_dir)

    try:
        (
            model_data,
            numeric_features,
            categorical_features,
            merge_checks,
            data_quality_checks,
        ) = build_classification_dataset(
            customers=processed["customers"],
            orders=processed["orders"],
            order_items=processed["order_items"],
        )

        target_dist = target_distribution(model_data)
        (
            X_train,
            X_valid,
            X_test,
            y_train,
            y_valid,
            y_test,
            features,
        ) = split_train_validation_test(
            model_data,
            numeric_features,
            categorical_features,
            random_state=random_state,
        )
        split_summary = build_split_summary(
            y_train,
            y_valid,
            y_test,
        )
        (
            models,
            validation_comparison,
            _validation_predictions,
            validation_probabilities,
        ) = train_and_compare_on_validation(
            X_train,
            X_valid,
            y_train,
            y_valid,
            numeric_features,
            categorical_features,
            random_state=random_state,
        )

        candidate_models = validation_comparison.query(
            "model != 'Dummy Most Frequent'"
        )
        if candidate_models.empty:
            raise ValueError("학습 모델 비교 결과가 없습니다.")

        selected_model_name = str(
            candidate_models.iloc[0]["model"]
        )
        selected_model = models[selected_model_name]
        validation_proba = validation_probabilities[
            selected_model_name
        ]
        threshold_df = threshold_metrics(
            y_valid,
            validation_proba,
        )
        selected_threshold = choose_threshold(threshold_df)

        (
            y_pred_test,
            y_proba_test,
            test_metrics,
        ) = final_test_evaluation(
            selected_model,
            X_test,
            y_test,
            threshold=selected_threshold,
        )
        test_metrics.insert(0, "model", selected_model_name)
        confusion_df = confusion_matrix_dataframe(
            y_test,
            y_pred_test,
        )
        report_df = classification_report_dataframe(
            y_test,
            y_pred_test,
        )
        predictions = create_prediction_result(
            source_index=X_test.index,
            y_test=y_test,
            y_pred=y_pred_test,
            y_proba=y_proba_test,
            model_name=selected_model_name,
            threshold=selected_threshold,
        )
        checklist = build_classification_checklist()

        frames = {
            "classification_target_distribution": target_dist,
            "classification_merge_checks": merge_checks,
            "classification_data_quality_checks": data_quality_checks,
            "classification_split_summary": split_summary,
            "classification_validation_comparison": validation_comparison,
            "classification_threshold_metrics": threshold_df,
            "classification_test_metrics": test_metrics,
            "classification_predictions": predictions,
            "classification_confusion_matrix": confusion_df.reset_index(
                names="actual_class"
            ),
            "classification_report": report_df,
            "classification_checklist": checklist,
        }
        output_paths: dict[str, Path] = {}
        for name, frame in frames.items():
            path = output_dir / f"ch15_{name}.csv"
            frame.to_csv(path, index=False, encoding="utf-8-sig")
            output_paths[name] = path

        status = pd.DataFrame(
            [
                {
                    "stage": "classification",
                    "status": "completed",
                    "selected_model": selected_model_name,
                    "selected_threshold": selected_threshold,
                    "feature_count": len(features),
                    "note": (
                        "모델과 임계값은 validation에서 선택하고 "
                        "test는 최종 평가에만 사용"
                    ),
                }
            ]
        )
        status_path = output_dir / "ch15_classification_status.csv"
        status.to_csv(status_path, index=False, encoding="utf-8-sig")
        output_paths["classification_status"] = status_path

        return {
            "status": status,
            "model_data": model_data,
            "validation_comparison": validation_comparison,
            "test_metrics": test_metrics,
            "confusion_matrix": confusion_df,
            "selected_model_name": selected_model_name,
            "selected_threshold": selected_threshold,
            "output_paths": output_paths,
        }

    except ValueError as exc:
        status = pd.DataFrame(
            [
                {
                    "stage": "classification",
                    "status": "skipped",
                    "selected_model": "",
                    "selected_threshold": "",
                    "feature_count": "",
                    "note": str(exc),
                }
            ]
        )
        status_path = output_dir / "ch15_classification_status.csv"
        status.to_csv(status_path, index=False, encoding="utf-8-sig")
        return {
            "status": status,
            "model_data": pd.DataFrame(),
            "validation_comparison": pd.DataFrame(),
            "test_metrics": pd.DataFrame(),
            "confusion_matrix": pd.DataFrame(),
            "selected_model_name": "",
            "selected_threshold": None,
            "output_paths": {
                "classification_status": status_path,
            },
        }


def create_holiday_template(report_dir: str | Path) -> Path:
    """실제 출처 데이터로 교체할 공휴일 파일 템플릿을 생성합니다."""
    path = Path(report_dir) / "ch15_holidays_template.csv"
    template = pd.DataFrame(
        columns=[
            "date",
            "holiday_name",
            "is_holiday",
            "provider",
            "source_url",
            "data_reference_date",
            "license_or_terms",
        ]
    )
    template.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def run_external_integration_stage(
    analysis_tables: dict[str, pd.DataFrame],
    paths: dict[str, Path],
) -> dict[str, Any]:
    """공휴일 파일이 있을 때만 완료 주문 일매출과 연결합니다."""
    holiday_path = (
        paths["external_processed_dir"] / "holidays.csv"
    )
    template_path = create_holiday_template(paths["report_dir"])
    status_rows: list[dict[str, Any]] = []

    if not holiday_path.exists():
        status_rows.append(
            {
                "stage": "external_integration",
                "status": "skipped",
                "source_file": str(holiday_path),
                "note": (
                    "실제 출처의 holidays.csv가 없습니다. "
                    "템플릿을 채우고 다시 실행하세요."
                ),
            }
        )
        status = pd.DataFrame(status_rows)
        status_path = (
            paths["report_dir"]
            / "ch15_external_integration_status.csv"
        )
        status.to_csv(
            status_path,
            index=False,
            encoding="utf-8-sig",
        )
        return {
            "status": status,
            "comparison": pd.DataFrame(),
            "merge_check": pd.DataFrame(),
            "output_paths": {
                "external_status": status_path,
                "holiday_template": template_path,
            },
        }

    holidays = pd.read_csv(holiday_path)
    required = {"date", "holiday_name", "is_holiday"}
    missing = sorted(required - set(holidays.columns))
    if missing:
        raise KeyError(
            f"holidays.csv에 필요한 컬럼이 없습니다: {missing}"
        )

    holidays["date"] = pd.to_datetime(
        holidays["date"],
        errors="coerce",
    )
    holidays = holidays.dropna(subset=["date"]).copy()
    holidays["order_day"] = holidays["date"].dt.date

    duplicate_dates = int(
        holidays["order_day"].duplicated().sum()
    )
    if duplicate_dates:
        raise ValueError(
            "holidays.csv의 날짜가 중복되어 있습니다: "
            f"{duplicate_dates}건"
        )

    completed_order_sales = analysis_tables[
        "completed_order_sales"
    ].copy()
    completed_order_sales["order_day"] = (
        pd.to_datetime(
            completed_order_sales["order_date"],
            errors="coerce",
        ).dt.date
    )
    daily_sales = (
        completed_order_sales.dropna(subset=["order_day"])
        .groupby("order_day", as_index=False)
        .agg(
            total_sales=("line_total", "sum"),
            order_count=("order_id", "nunique"),
        )
    )

    holiday_lookup = holidays[
        ["order_day", "holiday_name", "is_holiday"]
    ].copy()
    merged, merge_check = merge_external_data(
        daily_sales,
        holiday_lookup,
        on="order_day",
        how="left",
        validate="many_to_one",
    )
    merged["is_holiday"] = (
        merged["is_holiday"].fillna(0).astype(int)
    )
    merged["holiday_name"] = merged[
        "holiday_name"
    ].fillna("일반일")

    comparison = (
        merged.groupby("is_holiday", as_index=False)
        .agg(
            day_count=("order_day", "count"),
            avg_daily_sales=("total_sales", "mean"),
            avg_order_count=("order_count", "mean"),
            total_sales=("total_sales", "sum"),
        )
    )
    comparison["day_type"] = comparison[
        "is_holiday"
    ].map({0: "일반일", 1: "공휴일"})
    comparison = comparison[
        [
            "day_type",
            "day_count",
            "avg_daily_sales",
            "avg_order_count",
            "total_sales",
        ]
    ]

    source_hash = sha256_file(holiday_path)
    status = pd.DataFrame(
        [
            {
                "stage": "external_integration",
                "status": (
                    "completed"
                    if set(comparison["day_type"])
                    == {"일반일", "공휴일"}
                    else "warning"
                ),
                "source_file": str(holiday_path),
                "note": (
                    "공휴일과 일반일 표본을 모두 확인"
                    if set(comparison["day_type"])
                    == {"일반일", "공휴일"}
                    else "공휴일 또는 일반일 표본이 없어 해석 제한"
                ),
                "source_sha256": source_hash,
            }
        ]
    )

    output_paths = {
        "external_status": (
            paths["report_dir"]
            / "ch15_external_integration_status.csv"
        ),
        "external_daily_sales": (
            paths["report_dir"]
            / "ch15_holiday_daily_sales.csv"
        ),
        "external_comparison": (
            paths["report_dir"]
            / "ch15_holiday_sales_comparison.csv"
        ),
        "external_merge_check": (
            paths["report_dir"]
            / "ch15_external_merge_check.csv"
        ),
        "holiday_template": template_path,
    }
    status.to_csv(
        output_paths["external_status"],
        index=False,
        encoding="utf-8-sig",
    )
    merged.to_csv(
        output_paths["external_daily_sales"],
        index=False,
        encoding="utf-8-sig",
    )
    comparison.to_csv(
        output_paths["external_comparison"],
        index=False,
        encoding="utf-8-sig",
    )
    merge_check.to_csv(
        output_paths["external_merge_check"],
        index=False,
        encoding="utf-8-sig",
    )

    return {
        "status": status,
        "comparison": comparison,
        "merge_check": merge_check,
        "output_paths": output_paths,
    }


def build_llm_usage_log_template() -> pd.DataFrame:
    """실제 사용 내역을 기록하기 위한 빈 LLM 로그 템플릿을 만듭니다."""
    steps = [
        "분석 질문 검토",
        "코드 초안 검토",
        "머신러닝 코드 검토",
        "외부 데이터 연결 검토",
        "오류 해결",
        "결과 해석",
        "보고서 문장 보완",
        "자동화 설계",
    ]
    return pd.DataFrame(
        {
            "executed_at": [""] * len(steps),
            "provider": [""] * len(steps),
            "model": [""] * len(steps),
            "prompt_version": ["v1"] * len(steps),
            "step": steps,
            "input_summary": [""] * len(steps),
            "response_summary": [""] * len(steps),
            "validation_result": [""] * len(steps),
            "revision_note": [""] * len(steps),
            "final_use": ["미사용"] * len(steps),
        }
    )


def build_automation_plan() -> str:
    """반복 실행을 위한 자동화 설계 초안을 반환합니다."""
    return """# Chapter 15 자동화 설계서

## 실행 순서

1. 원본 파일 존재·스키마 확인
2. 전처리 및 키 관계 검증
3. 완료 주문 기준 EDA와 시각화
4. 분류 모델 validation 선택 및 test 최종 평가
5. 허용된 외부 데이터 파일 존재 여부 확인
6. 외부 데이터 병합 검증
7. 프로젝트 검증표와 산출물 manifest 생성
8. 최종 보고서 저장
9. 실패·경고 상태 알림

## 운영 원칙

- 단계별 입력과 출력을 고정합니다.
- 실패한 검증을 무시하고 다음 단계로 진행하지 않습니다.
- 네트워크 수집과 분석 실행을 분리합니다.
- API Key와 개인정보는 로그에 남기지 않습니다.
- 실행 성공과 분석 타당성을 별도로 검토합니다.
"""


def build_project_validation(
    core: dict[str, Any],
    classification_result: dict[str, Any],
    external_result: dict[str, Any],
    figure_paths: dict[str, Path],
) -> pd.DataFrame:
    """최종 프로젝트의 핵심 일관성 검증표를 생성합니다."""
    amount_scope = core["public_tables"][
        "amount_scope_summary"
    ].set_index("scope")
    completed_amount = float(
        amount_scope.loc["completed_order_items", "amount"]
    )

    category_total = float(
        core["public_tables"]["category_sales"][
            "total_sales"
        ].sum()
    )
    monthly_total = float(
        core["public_tables"]["monthly_sales"][
            "total_sales"
        ].sum()
    )
    customer_total = float(
        core["public_tables"]["customer_sales"][
            "total_sales"
        ].sum()
    )
    product_total = float(
        core["public_tables"]["product_sales"][
            "total_sales"
        ].sum()
    )

    merge_checks = core["public_tables"]["merge_checks"]
    relationship_checks = core["relationship_checks"]
    customer_columns = set(
        core["public_tables"]["customer_sales"].columns
    )

    rows = [
        {
            "check": "완료 주문 매출 합계 일치",
            "status": (
                "PASS"
                if all(
                    abs(value - completed_amount) < 1e-6
                    for value in [
                        category_total,
                        monthly_total,
                        customer_total,
                        product_total,
                    ]
                )
                else "FAIL"
            ),
            "detail": (
                f"completed={completed_amount}, "
                f"category={category_total}, monthly={monthly_total}, "
                f"customer={customer_total}, product={product_total}"
            ),
        },
        {
            "check": "병합 후 행 수 보존",
            "status": (
                "PASS"
                if merge_checks["row_count_preserved"].fillna(False).all()
                else "FAIL"
            ),
            "detail": (
                f"검증 병합 {len(merge_checks)}건"
            ),
        },
        {
            "check": "외래키 관계",
            "status": (
                "PASS"
                if relationship_checks["invalid_count"].fillna(0).eq(0).all()
                else "FAIL"
            ),
            "detail": (
                f"무효 관계 합계 "
                f"{int(relationship_checks['invalid_count'].fillna(0).sum())}"
            ),
        },
        {
            "check": "고객 결과 익명화",
            "status": (
                "PASS"
                if not {
                    "customer_id",
                    "name",
                    "email",
                    "phone",
                    "address",
                }.intersection(customer_columns)
                else "FAIL"
            ),
            "detail": ", ".join(sorted(customer_columns)),
        },
        {
            "check": "분류 평가 단계",
            "status": (
                "PASS"
                if classification_result["status"].iloc[0]["status"]
                == "completed"
                else "WARN"
            ),
            "detail": str(
                classification_result["status"].iloc[0]["note"]
            ),
        },
        {
            "check": "외부 데이터 통합",
            "status": (
                "PASS"
                if external_result["status"].iloc[0]["status"]
                == "completed"
                else "WARN"
            ),
            "detail": str(
                external_result["status"].iloc[0]["note"]
            ),
        },
        {
            "check": "시각화 파일 생성",
            "status": (
                "PASS"
                if all(path.exists() for path in figure_paths.values())
                else "FAIL"
            ),
            "detail": f"{len(figure_paths)}개 파일",
        },
    ]
    return pd.DataFrame(rows)


def build_final_report(
    core: dict[str, Any],
    classification_result: dict[str, Any],
    external_result: dict[str, Any],
    validation: pd.DataFrame,
) -> str:
    """검증 결과를 포함한 최종 보고서를 생성합니다."""
    public_tables = core["public_tables"]
    classification_text = (
        classification_result["test_metrics"].to_string(index=False)
        if not classification_result["test_metrics"].empty
        else classification_result["status"].to_string(index=False)
    )
    external_text = (
        external_result["comparison"].to_string(index=False)
        if not external_result["comparison"].empty
        else external_result["status"].to_string(index=False)
    )

    return f"""# 온라인 쇼핑몰 데이터 분석 최종 보고서

## 1. 프로젝트 목적

완료 주문 기준 매출 현황과 고객·상품·월별 패턴을 분석하고,
주문 취소 분류 모델과 선택형 외부 데이터 통합 가능성을 검토했습니다.

## 2. 데이터 개요

```text
{core['dataset_summary'].to_string(index=False)}
```

## 3. 데이터 품질과 분석 범위

```text
{public_tables['amount_scope_summary'].to_string(index=False)}
```

매출 지표는 `order_status == "completed"`인 주문만 사용했습니다.
취소·환불 주문 금액은 매출에서 제외하고 별도 범위표에 기록했습니다.

## 4. 핵심 EDA

### 카테고리별 완료 주문 매출

```text
{public_tables['category_sales'].head(10).to_string(index=False)}
```

### 월별 완료 주문 매출

```text
{public_tables['monthly_sales'].head(12).to_string(index=False)}
```

### 익명화된 고객별 완료 주문 구매 금액

```text
{public_tables['customer_sales'].head(10).to_string(index=False)}
```

## 5. 주문 취소 분류 모델

```text
{classification_text}
```

모델과 임계값은 validation 데이터에서 선택하고,
test 데이터는 최종 평가에만 사용했습니다. 모델 결과는 취소 원인을
증명하지 않습니다.

## 6. 외부 데이터 통합

```text
{external_text}
```

외부 파일이 없으면 통합 단계는 실패가 아니라 선택 단계의
`skipped` 상태로 기록됩니다. 실제 외부 데이터에는 출처, 기준일,
라이선스와 파일 해시가 필요합니다.

## 7. 프로젝트 검증

```text
{validation.to_string(index=False)}
```

## 8. 한계

- 샘플 데이터의 기간과 크기에 결과가 제한됩니다.
- 완료 주문 매출은 현재 주문 상태 정의에 의존합니다.
- 고객 결과는 익명화했지만 소규모 집단은 추가 검토가 필요합니다.
- 분류 모델은 운영 적용 전 시간 순서 분할, 비용 기준, 공정성 검토가 필요합니다.
- 외부 데이터와 매출의 동시 변화는 인과관계를 의미하지 않습니다.
- LLM을 사용했다면 제공자, 모델, 실행일, 프롬프트와 수정 내용을 별도 로그에 기록해야 합니다.

## 9. 다음 단계

1. 더 긴 기간의 데이터를 확보합니다.
2. 프로모션, 재고, 광고, 반품 데이터를 추가합니다.
3. 외부 데이터 기준일과 업데이트 주기를 관리합니다.
4. 검증 실패 시 자동화를 중단하도록 운영 규칙을 설정합니다.
"""


def build_deliverable_manifest(
    files: dict[str, Path],
    *,
    required_names: set[str],
) -> pd.DataFrame:
    """산출물 존재 여부, 크기, SHA-256을 기록합니다."""
    rows = []
    for name, path in sorted(files.items()):
        exists = path.exists()
        rows.append(
            {
                "deliverable": name,
                "required": name in required_names,
                "path": str(path),
                "exists": exists,
                "size_bytes": path.stat().st_size if exists else 0,
                "sha256": sha256_file(path) if exists else "",
            }
        )
    return pd.DataFrame(rows)


def run_final_project(
    base_dir: str | Path = ".",
    *,
    random_state: int = 42,
) -> dict[str, Any]:
    """15장 최종 프로젝트 전체 파이프라인을 실행합니다."""
    core = prepare_core_analysis(base_dir)
    paths = core["paths"]

    core_output_paths = save_core_outputs(core)
    figure_paths = generate_project_figures(
        core["public_tables"],
        paths["figure_dir"],
    )
    classification_result = run_classification_stage(
        core["processed"],
        paths["report_dir"],
        random_state=random_state,
    )
    external_result = run_external_integration_stage(
        core["analysis_tables"],
        paths,
    )

    llm_usage_log = build_llm_usage_log_template()
    llm_usage_path = (
        paths["report_dir"] / "ch15_llm_usage_log.csv"
    )
    llm_usage_log.to_csv(
        llm_usage_path,
        index=False,
        encoding="utf-8-sig",
    )

    automation_path = (
        paths["report_dir"] / "ch15_automation_plan.md"
    )
    automation_path.write_text(
        build_automation_plan(),
        encoding="utf-8",
    )

    validation = build_project_validation(
        core,
        classification_result,
        external_result,
        figure_paths,
    )
    validation_path = (
        paths["report_dir"] / "ch15_project_validation.csv"
    )
    validation.to_csv(
        validation_path,
        index=False,
        encoding="utf-8-sig",
    )

    final_report_path = (
        paths["report_dir"] / "ch15_final_report.md"
    )
    final_report_path.write_text(
        build_final_report(
            core,
            classification_result,
            external_result,
            validation,
        ),
        encoding="utf-8",
    )

    all_files: dict[str, Path] = {
        **core_output_paths,
        **{
            f"figure_{name}": path
            for name, path in figure_paths.items()
        },
        **classification_result["output_paths"],
        **external_result["output_paths"],
        "llm_usage_log": llm_usage_path,
        "automation_plan": automation_path,
        "project_validation": validation_path,
        "final_report": final_report_path,
    }
    required_names = {
        "dataset_summary",
        "preprocessing_comparison",
        "key_duplicate_checks",
        "relationship_checks",
        "merge_checks",
        "amount_scope_summary",
        "category_sales",
        "monthly_sales",
        "customer_sales",
        "product_sales",
        "order_status_summary",
        "classification_status",
        "llm_usage_log",
        "automation_plan",
        "project_validation",
        "final_report",
    }
    manifest = build_deliverable_manifest(
        all_files,
        required_names=required_names,
    )
    manifest_path = (
        paths["report_dir"]
        / "ch15_project_deliverables.csv"
    )
    manifest.to_csv(
        manifest_path,
        index=False,
        encoding="utf-8-sig",
    )
    all_files["deliverable_manifest"] = manifest_path

    return {
        "paths": paths,
        "core": core,
        "classification": classification_result,
        "external": external_result,
        "llm_usage_log": llm_usage_log,
        "validation": validation,
        "manifest": manifest,
        "output_paths": all_files,
        "final_report_path": final_report_path,
        "deliverables_path": manifest_path,
    }
