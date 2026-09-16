"""Chapter 12 policy layer for generated-code validation.

This module keeps the existing validation primitives in ``src.llm_code_validation``
and strengthens the final decision policy without executing generated code.

Key policy changes:
- static-scan ``critical``/``high`` findings block execution;
- ``review`` findings and a clean scan both remain HUMAN REVIEW, not automatic PASS;
- ML leakage review is represented explicitly in the final execution gate;
- sandbox evidence includes disposable environment, read-only input, write allowlist,
  network denial, resource limits, and post-execution observations;
- package review includes exact-version and transitive-dependency checks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import llm_code_validation as base


BLOCKING_STATIC_SEVERITIES = {"critical", "high"}


def static_scan_gate_status(static_scan: pd.DataFrame) -> tuple[str, str]:
    """Map scanner severity to execution-gate semantics."""
    if static_scan.empty:
        return "REVIEW", "탐지 0건이어도 정적 스캔은 안전 보증이 아니므로 사람 검토 필요"

    severities = set(static_scan.get("severity", pd.Series(dtype="string")).astype(str).str.lower())
    blocking = sorted(severities & BLOCKING_STATIC_SEVERITIES)
    if blocking:
        return "BLOCKED", f"차단 심각도 탐지: {', '.join(blocking)}"
    return "REVIEW", "review 수준 탐지 항목은 목적·경로·변경 범위를 사람이 확인"


def strengthen_leakage_review(leakage_review: pd.DataFrame) -> pd.DataFrame:
    """Synchronize Chapter 12 ML review evidence with the latest Chapters 09/10."""
    review = leakage_review.copy()
    review["status"] = "REVIEW"
    review["latest_contract"] = ""

    regression_mask = review["problem"].astype(str).str.lower().eq("regression")
    classification_mask = review["problem"].astype(str).str.lower().eq("classification")

    review.loc[regression_mask, "latest_contract"] = (
        "최종 train/test는 날짜 그룹을 보존; 기본 TimeSeriesSplit은 행 단위이므로 "
        "동일 날짜가 CV 경계에서 나뉠 수 있음을 검토하고 필요 시 날짜 그룹 기반 CV 사용"
    )
    review.loc[classification_mask, "latest_contract"] = (
        "completed/cancelled 교육용 모집단; predict_proba는 보정된 실제 발생 확률로 단정 금지; "
        "작은 클래스 표본 경고; F1 임계값은 교육용이며 실제 운영은 FP/FN 업무 비용 반영; "
        "같은 validation의 model+threshold 반복 선택 한계 기록"
    )
    return review


def build_enhanced_sandbox_checklist() -> pd.DataFrame:
    items = [
        "운영 데이터가 아닌 복사한 소량 샘플을 사용하는가?",
        "입력 데이터는 가능하면 read-only로 제공되는가?",
        "API Key·클라우드 credential·DB 비밀번호가 없는 환경인가?",
        "실행 환경은 작업 후 폐기 가능한 disposable 환경인가?",
        "쓰기 허용 경로가 별도 output 폴더 등 allowlist로 제한되는가?",
        "불필요한 네트워크 접근을 기본 차단했는가?",
        "CPU·메모리·실행 시간·프로세스 수·디스크 사용량 제한이 있는가?",
        "실행 전 저장소와 대상 폴더의 baseline 상태를 기록했는가?",
        "실행 시작·종료 시각, exit code, timeout 여부를 기록할 수 있는가?",
        "실행 후 생성·수정 파일 목록과 허용 경로 밖 변경을 비교할 수 있는가?",
        "실행 환경의 Python·핵심 package 버전을 기록할 수 있는가?",
    ]
    return pd.DataFrame(
        {
            "check_item": items,
            "status": ["REVIEW"] * len(items),
            "evidence": [""] * len(items),
        }
    )


def build_enhanced_package_install_review_template() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "package": "",
                "requested_version": "",
                "purpose": "",
                "package_needed": "REVIEW",
                "official_source_verified": "REVIEW",
                "name_typo_or_typosquatting_checked": "REVIEW",
                "exact_version_pinned": "REVIEW",
                "python_compatibility_checked": "REVIEW",
                "transitive_dependencies_reviewed": "REVIEW",
                "install_script_reviewed": "REVIEW",
                "isolated_environment_planned": "REVIEW",
                "requirements_or_lock_recorded": "REVIEW",
                "organization_policy_checked": "REVIEW",
                "decision": "DO_NOT_INSTALL_UNTIL_REVIEWED",
            }
        ]
    )


def strengthen_code_review_checklist(checklist: pd.DataFrame) -> pd.DataFrame:
    extra = pd.DataFrame(
        [
            {
                "category": "보안",
                "check_item": "오류 메시지뿐 아니라 공유 코드의 문자열 literal·설정 예시·URL·환경변수 참조에도 Secret 또는 내부 정보가 없는가?",
                "status": "REVIEW",
                "evidence": "",
                "reviewer": "",
            },
            {
                "category": "샌드박스",
                "check_item": "read-only input, write allowlist, network deny, resource limit, disposable 환경이 실제로 적용되는가?",
                "status": "REVIEW",
                "evidence": "",
                "reviewer": "",
            },
            {
                "category": "사후 검증",
                "check_item": "exit code·timeout·생성/수정 파일·허용 경로 밖 변경·환경 버전을 실행 Evidence로 남겼는가?",
                "status": "REVIEW",
                "evidence": "",
                "reviewer": "",
            },
        ]
    )
    return pd.concat([checklist.copy(), extra], ignore_index=True)


def build_execution_gate(
    required_column_check: pd.DataFrame,
    primary_key_check: pd.DataFrame,
    relationship_check: pd.DataFrame,
    category_validation: pd.DataFrame,
    monthly_validation: pd.DataFrame,
    leakage_review: pd.DataFrame,
    static_scan: pd.DataFrame,
) -> pd.DataFrame:
    static_status, static_meaning = static_scan_gate_status(static_scan)

    schema_status = (
        "PASS"
        if required_column_check["status"].eq("PASS").all()
        and primary_key_check["status"].eq("PASS").all()
        and relationship_check["status"].eq("PASS").all()
        else "FAIL"
    )
    aggregate_status = (
        "PASS"
        if not category_validation["status"].eq("FAIL").any()
        and not monthly_validation["status"].eq("FAIL").any()
        else "FAIL"
    )

    leakage_status = "REVIEW"
    if "status" in leakage_review.columns and leakage_review["status"].eq("FAIL").any():
        leakage_status = "FAIL"

    rows = [
        {"gate": "schema_and_keys", "status": schema_status, "meaning": "필수 구조·PK·관계"},
        {"gate": "aggregate_validation", "status": aggregate_status, "meaning": "completed 범위·병합·총합"},
        {
            "gate": "ml_leakage",
            "status": leakage_status,
            "meaning": "문제별 prediction time·forbidden feature·split/selection 계약을 실제 생성 코드에 대조",
        },
        {"gate": "static_scan", "status": static_status, "meaning": static_meaning},
        {
            "gate": "sandbox_and_package",
            "status": "REVIEW",
            "meaning": "격리 환경·쓰기 범위·네트워크·리소스 제한·공급망을 사람이 확인",
        },
        {
            "gate": "human_approval",
            "status": "REVIEW",
            "meaning": "자동 Evidence와 별도로 명시적 실행 승인 필요",
        },
    ]
    gate = pd.DataFrame(rows)
    decision = (
        "DO_NOT_EXECUTE"
        if gate["status"].isin(["FAIL", "BLOCKED"]).any()
        else "HUMAN_REVIEW_REQUIRED"
    )
    gate.loc[len(gate)] = {
        "gate": "execution_decision",
        "status": decision,
        "meaning": "자동 승인하지 않음",
    }
    return gate


def run_llm_code_validation(
    processed_dir: str | Path = "data/processed",
    report_dir: str | Path = "reports",
    code_for_static_scan: str = base.DEFAULT_STATIC_SCAN_EXAMPLE,
) -> dict[str, object]:
    """Run the existing evidence pipeline, then apply the strengthened policy layer.

    The supplied generated code is still parsed only. This wrapper does not execute it.
    """
    result = base.run_llm_code_validation(
        processed_dir=processed_dir,
        report_dir=report_dir,
        code_for_static_scan=code_for_static_scan,
    )
    outputs = result["outputs"]

    leakage_review = strengthen_leakage_review(outputs["leakage_review"])
    sandbox_checklist = build_enhanced_sandbox_checklist()
    package_review = build_enhanced_package_install_review_template()
    code_review_checklist = strengthen_code_review_checklist(outputs["code_review_checklist"])
    execution_gate = build_execution_gate(
        outputs["required_column_check"],
        outputs["primary_key_check"],
        outputs["relationship_check"],
        outputs["category_validation"],
        outputs["monthly_validation"],
        leakage_review,
        outputs["static_scan"],
    )

    outputs["leakage_review"] = leakage_review
    outputs["sandbox_checklist"] = sandbox_checklist
    outputs["package_review"] = package_review
    outputs["code_review_checklist"] = code_review_checklist
    outputs["execution_gate"] = execution_gate
    outputs["validation_summary"] = base.build_validation_summary(
        inventory=outputs["inventory"],
        required_column_check=outputs["required_column_check"],
        primary_key_check=outputs["primary_key_check"],
        relationship_check=outputs["relationship_check"],
        category_validation=outputs["category_validation"],
        monthly_validation=outputs["monthly_validation"],
        leakage_review=leakage_review,
        static_scan=outputs["static_scan"],
        execution_gate=execution_gate,
    )
    result["output_paths"] = base.save_validation_outputs(outputs, report_dir=report_dir)
    return result
