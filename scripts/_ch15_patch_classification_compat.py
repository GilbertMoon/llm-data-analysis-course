from pathlib import Path

PATH = Path("src/classification.py")
text = PATH.read_text(encoding="utf-8")


def replace_function(source: str, name: str, next_name: str, replacement: str) -> str:
    start_marker = f"def {name}("
    next_marker = f"def {next_name}("
    start = source.index(start_marker)
    end = source.index(next_marker, start)
    return source[:start] + replacement.rstrip() + "\n\n\n" + source[end:]


selection_summary = '''def build_selection_summary(
    selected_model_name: str,
    selected_threshold: float,
    validation_comparison: pd.DataFrame,
    threshold_df: pd.DataFrame,
) -> pd.DataFrame:
    """Record that model and threshold selection occurred on validation data."""
    model_row = validation_comparison.loc[
        validation_comparison["model"].eq(selected_model_name)
    ]
    threshold_match = np.isclose(
        threshold_df["threshold"].astype(float).to_numpy(),
        float(selected_threshold),
    )
    if model_row.empty or not threshold_match.any():
        raise ValueError("선택 모델 또는 임계값이 validation evidence에 없습니다.")
    return pd.DataFrame(
        [
            {
                "selection_item": "model",
                "value": selected_model_name,
                "selected_on": "validation",
                "criterion": "f1 → recall → precision",
            },
            {
                "selection_item": "threshold",
                "value": selected_threshold,
                "selected_on": "validation",
                "criterion": "f1 → recall → precision → lower threshold",
            },
        ]
    )'''

if "def build_selection_summary(" not in text:
    marker = "def final_test_evaluation("
    position = text.index(marker)
    text = text[:position] + selection_summary + "\n\n\n" + text[position:]


final_test = '''def final_test_evaluation(
    model: Pipeline,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    *,
    threshold: float,
    model_name: str | None = None,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    """Evaluate one frozen model/threshold pair on final test.

    Chapter 10 legacy callers omit ``model_name`` and keep the historical
    ``evaluation_split='test'`` label. Chapter 15 supplies ``model_name`` and
    receives explicit frozen-before-test evidence.
    """
    if not 0 <= threshold <= 1:
        raise ValueError("threshold는 0과 1 사이여야 합니다.")
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_proba >= threshold).astype(int)
    row: dict[str, Any] = {
        "evaluation_split": "test_final" if model_name is not None else "test",
        "threshold": threshold,
        "selection_status": "frozen_before_test",
        **evaluate_classification_predictions(y_test, y_pred),
    }
    if model_name is not None:
        row = {"model": model_name, **row}
    return y_pred, y_proba, pd.DataFrame([row])'''
text = replace_function(
    text,
    "final_test_evaluation",
    "confusion_matrix_dataframe",
    final_test,
)


prediction_result = '''def create_prediction_result(
    y_test: pd.Series,
    y_pred: np.ndarray,
    y_proba: np.ndarray,
    *,
    model_name: str,
    threshold: float,
    source_index: pd.Index | None = None,
) -> pd.DataFrame:
    """Create prediction evidence with optional internal source traceability.

    Chapter 10 can pass ``source_index`` for an internal-only artifact. Chapter
    15 omits it, so the returned table is public-safe by construction.
    """
    if len(y_test) != len(y_pred) or len(y_pred) != len(y_proba):
        raise ValueError("테스트 실제값·예측값·확률의 길이가 일치하지 않습니다.")
    if source_index is not None and len(source_index) != len(y_test):
        raise ValueError("source_index와 테스트 결과 길이가 일치하지 않습니다.")

    result = pd.DataFrame(
        {
            "record_id": [
                f"test_{position:04d}" for position in range(1, len(y_test) + 1)
            ],
            "actual_is_cancelled": y_test.to_numpy(),
            "predicted_is_cancelled": y_pred,
            "cancel_probability": y_proba,
            "model": model_name,
            "threshold": threshold,
        }
    )
    if source_index is not None:
        result.insert(1, "source_index", source_index.to_numpy())
    return result'''
text = replace_function(
    text,
    "create_prediction_result",
    "public_prediction_result",
    prediction_result,
)


validation_function = '''def build_classification_validation(
    *,
    model_data: pd.DataFrame,
    features: list[str],
    merge_checks: pd.DataFrame,
    y_train: pd.Series,
    y_valid: pd.Series,
    y_test: pd.Series,
    validation_comparison: pd.DataFrame,
    selected_model_name: str,
    threshold_df: pd.DataFrame,
    selected_threshold: float,
    test_metrics: pd.DataFrame | None = None,
    prediction_result: pd.DataFrame | None = None,
    prediction_result_public: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Create machine-checkable evidence for Chapter 10 and Chapter 15.

    ``prediction_result_public`` is retained for the Chapter 10 pipeline.
    Chapter 15 passes ``prediction_result`` and ``test_metrics`` so the final
    test frozen-decision contract is also validated.
    """
    target_values = set(model_data[TARGET_COLUMN].dropna().unique())
    feature_forbidden = sorted(set(features) & set(FORBIDDEN_FEATURES))
    merge_pass = bool(
        not merge_checks.empty
        and merge_checks["row_count_preserved"].eq(True).all()
        and merge_checks["unmatched_count"].eq(0).all()
    )
    split_has_both = all(
        set(target.unique()) == {0, 1}
        for target in [y_train, y_valid, y_test]
    )
    selected_in_validation = bool(
        selected_model_name in set(validation_comparison["model"])
        and selected_model_name != "Dummy Most Frequent"
    )
    threshold_in_validation = bool(
        np.isclose(
            threshold_df["threshold"].astype(float).to_numpy(),
            float(selected_threshold),
        ).any()
    )

    public_frame = prediction_result if prediction_result is not None else prediction_result_public
    public_forbidden_columns = {
        "source_index",
        "order_id",
        "customer_id",
        "product_id",
        "name",
        "email",
        "phone",
        "address",
    }
    public_leak = (
        sorted(public_forbidden_columns & set(public_frame.columns))
        if public_frame is not None
        else ["prediction_result_missing"]
    )

    rows: list[dict[str, object]] = [
        {
            "check": "target_exactly_completed_cancelled",
            "value": sorted(target_values),
            "status": "PASS" if target_values == {0, 1} else "FAIL",
        },
        {
            "check": "forbidden_feature_overlap",
            "value": len(feature_forbidden),
            "status": "PASS" if not feature_forbidden else "FAIL",
        },
        {
            "check": "merge_rows_and_matches",
            "value": merge_pass,
            "status": "PASS" if merge_pass else "FAIL",
        },
        {
            "check": "all_splits_have_both_classes",
            "value": split_has_both,
            "status": "PASS" if split_has_both else "FAIL",
        },
        {
            "check": "model_selected_on_validation",
            "value": selected_in_validation,
            "status": "PASS" if selected_in_validation else "FAIL",
        },
        {
            "check": "threshold_selected_on_validation",
            "value": threshold_in_validation,
            "status": "PASS" if threshold_in_validation else "FAIL",
        },
        {
            "check": "public_prediction_identifier_columns",
            "value": ",".join(public_leak) if public_leak else "none",
            "status": "PASS" if not public_leak else "FAIL",
        },
    ]

    if test_metrics is not None:
        test_is_final = bool(
            len(test_metrics) == 1
            and "evaluation_split" in test_metrics.columns
            and test_metrics["evaluation_split"].eq("test_final").all()
            and "selection_status" in test_metrics.columns
            and test_metrics["selection_status"].eq("frozen_before_test").all()
        )
        rows.append(
            {
                "check": "test_used_as_final_evaluation",
                "value": test_is_final,
                "status": "PASS" if test_is_final else "FAIL",
            }
        )

    validation = pd.DataFrame(rows)
    failed = validation.loc[validation["status"].eq("FAIL")]
    if not failed.empty:
        raise ValueError(
            "분류 분석 핵심 검증에 실패했습니다:\\n"
            + failed.to_string(index=False)
        )
    return validation'''
text = replace_function(
    text,
    "build_classification_validation",
    "build_classification_report_text",
    validation_function,
)

PATH.write_text(text, encoding="utf-8")
print("patched", PATH)
