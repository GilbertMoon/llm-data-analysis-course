"""Chapter 11 Public release QA.

Chapter 05 전용 raw 데이터를 QA 임시 폴더에서 전처리한 뒤 Chapter 11의
Safe Context / Prompt artifact pipeline을 실행합니다. Chapter 05 데이터에는
학습용 품질·관계 이상 후보가 포함될 수 있으므로 그 자체를 Chapter 11 QA 실패로
보지 않습니다. Chapter 11은 그 processed 입력을 안전하게 구조화하고 검토 가능한
Context로 만드는 계약을 검증합니다.
"""

from __future__ import annotations

import ast
import json
import py_compile
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data_loader import load_sales_data  # noqa: E402
from src.llm_prompt_analysis import (  # noqa: E402
    load_available_sales_data,
    run_llm_prompt_analysis,
)
from src.preprocessing import preprocess_sales_data, save_processed_data  # noqa: E402


QA_DIR = ROOT / "tmp" / "ch11_public_qa"
PROCESSED_DIR = QA_DIR / "processed"
REPORT_DIR = QA_DIR / "reports"
REPORT_PATH = QA_DIR / "qa_report.json"
CH05_RAW_DIR = ROOT / "practice" / "chapter05" / "data" / "raw"

FORBIDDEN_NETWORK_IMPORT_ROOTS = {"anthropic", "httpx", "openai", "requests"}


def imported_module_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
    return roots


def main() -> None:
    if QA_DIR.exists():
        shutil.rmtree(QA_DIR)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    checks: list[dict[str, object]] = []

    def record(name: str, passed: bool, detail: str = "") -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "detail": detail,
            }
        )

    try:
        python_paths = [
            ROOT / "src" / "llm_prompt_analysis.py",
            ROOT / "scripts" / "run_llm_prompt_analysis.py",
            ROOT / "scripts" / "validate_ch11_public_release.py",
        ]
        for path in python_paths:
            py_compile.compile(str(path), doraise=True)
        record("python_syntax", True)

        imported_roots: set[str] = set()
        for path in python_paths[:2]:
            imported_roots.update(imported_module_roots(path))
        forbidden_imports = sorted(imported_roots & FORBIDDEN_NETWORK_IMPORT_ROOTS)
        record(
            "no_direct_external_llm_http_client",
            not forbidden_imports,
            f"forbidden_imports={forbidden_imports}",
        )

        # Chapter 05의 학습용 이상 후보도 processed Context의 일부가 될 수 있다.
        # Chapter 11 QA는 이를 임의 수정하지 않고 processed 파일 생성 여부만 확인한다.
        raw_data = load_sales_data(CH05_RAW_DIR)
        processed_data = preprocess_sales_data(raw_data)
        saved_paths = save_processed_data(processed_data, PROCESSED_DIR)
        processed_ready = bool(saved_paths) and all(
            path.exists() and path.stat().st_size > 0 for path in saved_paths
        )
        record(
            "processed_prerequisite",
            processed_ready,
            f"files={[path.name for path in saved_paths]}",
        )

        # raw 파일이 완전하게 있어도 processed가 없으면 기본 계약은 fail-fast다.
        silent_fallback_blocked = False
        try:
            load_available_sales_data(
                processed_dir=QA_DIR / "missing_processed",
                raw_dir=CH05_RAW_DIR,
            )
        except FileNotFoundError:
            silent_fallback_blocked = True
        record("no_silent_raw_fallback", silent_fallback_blocked)

        result = run_llm_prompt_analysis(
            processed_dir=PROCESSED_DIR,
            raw_dir=CH05_RAW_DIR,
            report_dir=REPORT_DIR,
        )
        record("pipeline_execution", True)
        record(
            "processed_context_only",
            result["source_type"] == "processed",
            f"source_type={result['source_type']}",
        )

        context_validation = result["context_validation"]
        context_validation_pass = bool(
            not context_validation.empty
            and not context_validation["status"].eq("FAIL").any()
            and context_validation.loc[
                context_validation["check"].eq("processed_context_only"),
                "status",
            ].eq("PASS").all()
        )
        record(
            "safe_context_validation",
            context_validation_pass,
            repr(context_validation.to_dict(orient="records")),
        )

        safe_context = result["safe_context_text"]
        warning_markers = [
            "외부 LLM 제공 승인을 의미하지 않습니다",
            "실제 행과 실제 값 예시는 포함하지 않았습니다",
            "untrusted data",
        ]
        missing_warnings = [m for m in warning_markers if m not in safe_context]
        record(
            "safe_context_required_warnings",
            not missing_warnings,
            f"missing={missing_warnings}",
        )

        column_summary = result["column_summary"]
        sensitive_names = column_summary.loc[
            column_summary["column_name_share_policy"].eq(
                "do_not_share_name_by_default"
            ),
            "column",
        ].astype(str)
        leaked_sensitive_names = [
            name for name in sensitive_names if name and name in safe_context
        ]
        record(
            "sensitive_column_names_hidden",
            not leaked_sensitive_names,
            f"leaked={leaked_sensitive_names}",
        )
        record(
            "raw_values_never_shared_by_default",
            bool(column_summary["share_raw_values"].eq("no").all()),
        )

        prompt_templates = result["prompt_templates"]
        required_steps = {
            "분석 질문 생성",
            "전처리 계획",
            "시각화 설계",
            "회귀 코드 검토",
            "분류 코드 검토",
            "결과 해석",
            "외부 문서 검토",
        }
        prompt_steps = set(prompt_templates["step"].astype(str))
        prompt_contract_pass = bool(
            required_steps.issubset(prompt_steps)
            and prompt_templates["human_review_required"].eq(True).all()
            and prompt_templates["context_rule"].str.contains(
                "safe_context", case=False, na=False
            ).all()
        )
        record(
            "prompt_template_contract",
            prompt_contract_pass,
            f"missing_steps={sorted(required_steps - prompt_steps)}",
        )

        usage_log = result["usage_log"]
        usage_log_pass = bool(
            usage_log["execution_status"].eq("not_executed").all()
            and usage_log["final_use"].eq("not_used").all()
            and usage_log["provider"].eq("").all()
            and usage_log["model"].eq("").all()
        )
        record(
            "empty_usage_log_is_not_execution_evidence",
            usage_log_pass,
        )

        expected_names = {
            "ch11_dataset_summary_for_llm.csv",
            "ch11_column_summary_for_llm.csv",
            "ch11_sensitive_column_review.csv",
            "ch11_safe_llm_context.md",
            "ch11_safe_context_validation.csv",
            "ch11_prompt_templates.csv",
            "ch11_llm_review_checklist.csv",
            "ch11_llm_usage_log.csv",
            "ch11_llm_prompt_log.md",
        }
        missing_outputs = sorted(
            name
            for name in expected_names
            if not (REPORT_DIR / name).exists()
            or (REPORT_DIR / name).stat().st_size == 0
        )
        record("required_outputs", not missing_outputs, f"missing={missing_outputs}")

        notebook = json.loads(
            (ROOT / "notebooks" / "ch11_llm_prompt_analysis.ipynb")
            .read_text(encoding="utf-8")
        )
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "processed 데이터를 사용",
            "raw 데이터로 자동 fallback하지 않습니다",
            "context_validation",
            "human_review_required",
            "untrusted data",
            "not_executed",
            "not_used",
            "run_llm_prompt_analysis",
        ]
        missing_notebook = [m for m in notebook_markers if m not in notebook_text]
        record(
            "notebook_contract",
            not missing_notebook,
            f"missing={missing_notebook}",
        )

        practice_text = (
            ROOT / "practice" / "chapter11" / "chapter11.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT / "practice" / "chapter11" / "templates" / "chapter11_assignment.md"
        ).read_text(encoding="utf-8")
        doc_text = practice_text + "\n" + assignment_text
        document_markers = [
            "processed",
            "Safe Context",
            "ch11_safe_context_validation.csv",
            "untrusted data",
            "not_executed",
            "Evidence",
            "Validation Threshold",
            "Frozen Final Test",
        ]
        missing_docs = [m for m in document_markers if m not in doc_text]
        record(
            "practice_document_contract",
            not missing_docs,
            f"missing={missing_docs}",
        )

    except Exception as exc:
        record("unexpected_exception", False, repr(exc))
    finally:
        overall_pass = bool(checks) and all(
            item["status"] == "PASS" for item in checks
        )
        report = {
            "chapter": 11,
            "status": "PASS" if overall_pass else "FAIL",
            "checks": checks,
        }
        REPORT_PATH.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if not overall_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
