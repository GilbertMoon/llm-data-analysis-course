"""Course-wide structural release QA for Chapters 01-15.

This validator is intentionally lightweight and offline. Deep functional QA for
Chapters 08-15 remains in each chapter-specific workflow; this script verifies
the shared public release contract across the whole companion repository.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "tmp" / "course_release_qa"
REPORT_PATH = REPORT_DIR / "qa_report.json"

CHAPTER_TITLES = {
    1: "AI와 함께하는 데이터 분석의 시작",
    2: "VS Code에서 시작하는 데이터 분석 환경",
    3: "데이터의 첫인상 읽기",
    4: "pandas로 데이터에 질문하기",
    5: "분석을 믿을 수 있게 만드는 데이터 전처리",
    6: "데이터를 보며 질문을 만드는 EDA",
    7: "그래프로 데이터의 이야기를 보여주기",
    8: "작은 데이터 분석 프로젝트 완성하기",
    9: "회귀 분석으로 숫자 예측하기",
    10: "분류 분석으로 주문 취소 여부 예측하기",
    11: "LLM과 함께 분석 질문을 다듬기",
    12: "LLM이 만든 분석 코드를 검증하는 방법",
    13: "외부 데이터로 분석을 확장하기",
    14: "반복되는 분석 흐름을 안전하게 자동화하기",
    15: "하나의 데이터 분석 프로젝트로 완성하기",
}

NOTEBOOKS = {
    1: "notebooks/ch01_ai_data_analysis_intro.ipynb",
    2: "notebooks/ch02_environment_setup.ipynb",
    3: "notebooks/ch03_data_overview.ipynb",
    4: "notebooks/ch04_pandas_basic.ipynb",
    5: "notebooks/ch05_data_preprocessing.ipynb",
    6: "notebooks/ch06_eda_questions.ipynb",
    7: "notebooks/ch07_visualization.ipynb",
    8: "notebooks/ch08_midterm_project.ipynb",
    9: "notebooks/ch09_regression_analysis.ipynb",
    10: "notebooks/ch10_llm_code_generation.ipynb",
    11: "notebooks/ch11_llm_prompt_analysis.ipynb",
    12: "notebooks/ch12_report_generation.ipynb",
    13: "notebooks/ch13_external_data_collection.ipynb",
    14: "notebooks/ch14_airflow_pipeline.ipynb",
    15: "notebooks/ch15_final_project.ipynb",
}

CHAPTER_QA_WORKFLOWS = {
    chapter: f".github/workflows/ch{chapter:02d}-public-qa.yml"
    for chapter in range(8, 16)
}


def add_check(checks: list[dict[str, str]], name: str, ok: bool, detail: str = "") -> None:
    checks.append({
        "check": name,
        "status": "PASS" if ok else "FAIL",
        "detail": detail,
    })


def required_file(path: Path) -> tuple[bool, str]:
    exists = path.is_file()
    size = path.stat().st_size if exists else 0
    return bool(exists and size > 0), f"path={path.relative_to(ROOT).as_posix()}; size={size}"


def validate_notebook(path: Path, chapter: int) -> tuple[bool, str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, f"{path.name}: {type(exc).__name__}"

    valid_format = data.get("nbformat") == 4 and isinstance(data.get("cells"), list)
    markdown = "\n".join(
        "".join(cell.get("source", []))
        for cell in data.get("cells", [])
        if cell.get("cell_type") == "markdown"
    )
    chapter_marker = re.search(rf"(?:Chapter\s*{chapter:02d}|Chapter\s*{chapter}|{chapter}장)", markdown, re.I)
    return bool(valid_format and chapter_marker), (
        f"nbformat={data.get('nbformat')}; cells={len(data.get('cells', []))}; "
        f"chapter_marker={bool(chapter_marker)}"
    )


def main() -> None:
    checks: list[dict[str, str]] = []
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")

    # Chapter 01-15: title, notebook, practice guide and assignment template.
    for chapter in range(1, 16):
        chapter_id = f"chapter{chapter:02d}"
        title = CHAPTER_TITLES[chapter]
        add_check(
            checks,
            f"ch{chapter:02d}_readme_title",
            title in readme,
            title,
        )

        notebook_path = ROOT / NOTEBOOKS[chapter]
        ok, detail = required_file(notebook_path)
        add_check(checks, f"ch{chapter:02d}_notebook_exists", ok, detail)
        if ok:
            notebook_ok, notebook_detail = validate_notebook(notebook_path, chapter)
            add_check(
                checks,
                f"ch{chapter:02d}_notebook_contract",
                notebook_ok,
                notebook_detail,
            )

        practice_path = ROOT / "practice" / chapter_id / f"{chapter_id}.md"
        ok, detail = required_file(practice_path)
        add_check(checks, f"ch{chapter:02d}_practice_guide", ok, detail)

        template_path = ROOT / "practice" / chapter_id / "templates" / f"{chapter_id}_assignment.md"
        ok, detail = required_file(template_path)
        add_check(checks, f"ch{chapter:02d}_assignment_template", ok, detail)

    # Deep chapter workflows are currently required from Chapter 08 onward.
    for chapter, relative_path in CHAPTER_QA_WORKFLOWS.items():
        ok, detail = required_file(ROOT / relative_path)
        add_check(checks, f"ch{chapter:02d}_qa_workflow", ok, detail)

    # Release hygiene: runtime and local-secret files must not be present.
    airflow_root_logs = sorted(
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "automation" / "airflow").glob("*.log")
        if path.is_file()
    )
    add_check(
        checks,
        "airflow_root_runtime_logs_absent",
        not airflow_root_logs,
        f"found={airflow_root_logs}",
    )

    forbidden_envs = [
        ROOT / ".env",
        ROOT / "automation" / "airflow" / ".env",
    ]
    present_envs = [
        path.relative_to(ROOT).as_posix()
        for path in forbidden_envs
        if path.exists()
    ]
    add_check(
        checks,
        "local_secret_env_files_absent",
        not present_envs,
        f"found={present_envs}",
    )

    backup_files = sorted(
        path.relative_to(ROOT).as_posix()
        for pattern in ("*.bak", "*.bak.ipynb")
        for path in ROOT.rglob(pattern)
        if ".git" not in path.parts and path.is_file()
    )
    add_check(
        checks,
        "editor_backup_files_absent",
        not backup_files,
        f"found={backup_files[:20]}",
    )

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expected_ignore_rules = [
        "automation/airflow/*.log",
        "automation/airflow/.env",
        "*.bak",
        "*.bak.ipynb",
    ]
    missing_ignore_rules = [rule for rule in expected_ignore_rules if rule not in gitignore]
    add_check(
        checks,
        "release_ignore_rules",
        not missing_ignore_rules,
        f"missing={missing_ignore_rules}",
    )

    failed = [check for check in checks if check["status"] == "FAIL"]
    report = {
        "scope": "Chapter 01-15 public structural release contract",
        "network_performed": False,
        "deep_functional_qa": "Chapter 08-15 chapter-specific workflows",
        "status": "PASS" if not failed else "FAIL",
        "summary": {
            "total": len(checks),
            "pass": len(checks) - len(failed),
            "fail": len(failed),
        },
        "checks": checks,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if failed:
        print("\nCourse release QA failed:", file=sys.stderr)
        for check in failed:
            print(f"- {check['check']}: {check['detail']}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
