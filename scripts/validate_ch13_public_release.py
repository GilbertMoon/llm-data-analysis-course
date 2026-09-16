"""Chapter 13 Public release QA without external network requests.

This validator checks the safe default, provenance/snapshot contracts, external-data
quality and merge rules using local synthetic data only. It never calls an API or
public web page.
"""

from __future__ import annotations

import json
import os
import py_compile
import shutil
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.external_data_collection import (  # noqa: E402
    build_collection_metadata,
    create_network_execution_gate,
    load_env_status,
    merge_external_data,
    redact_mapping,
    redact_url,
    run_external_data_collection_setup,
    save_json_snapshot,
    save_metadata_snapshot,
    sha256_file,
    validate_external_dataframe,
    validate_public_http_url,
    versioned_snapshot_path,
)


QA_DIR = ROOT / "tmp" / "ch13_public_qa"
SETUP_DIR = QA_DIR / "workspace"
REPORT_DIR = QA_DIR / "reports"
REPORT_PATH = QA_DIR / "qa_report.json"


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

    overall_pass = False
    env_names = [
        "PUBLIC_DATA_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ]
    old_env = {name: os.environ.get(name) for name in env_names}

    try:
        python_paths = [
            ROOT / "src" / "external_data_collection.py",
            ROOT / "scripts" / "run_external_data_collection.py",
            ROOT / "scripts" / "validate_ch13_public_release.py",
        ]
        for path in python_paths:
            py_compile.compile(str(path), doraise=True)
        record("python_syntax", True)

        setup = run_external_data_collection_setup(
            base_dir=SETUP_DIR,
            report_dir=REPORT_DIR,
        )
        outputs = setup["outputs"]
        record("network_free_setup_execution", True)

        network_gate = outputs["network_gate"]
        safe_gate = bool(
            len(network_gate) == 4
            and network_gate["default"].eq(False).all()
            and network_gate["status"].eq("SAFE_DEFAULT").all()
            and set(network_gate["flag"])
            == {
                "RUN_PUBLIC_API",
                "RUN_NAVER_API",
                "RUN_CRAWLING_EXAMPLE",
                "POLICY_CONFIRMED",
            }
        )
        record(
            "network_gate_safe_default",
            safe_gate,
            repr(network_gate.to_dict(orient="records")),
        )

        # Secret-state contract: never expose actual values, and distinguish
        # MISSING / PLACEHOLDER / CONFIGURED.
        for name in env_names:
            os.environ.pop(name, None)
        missing_status = load_env_status(None)
        missing_ok = bool(
            missing_status["state"].eq("MISSING").all()
            and missing_status["configured"].eq(False).all()
            and missing_status["value_exposed"].eq(False).all()
        )
        record("secret_state_missing", missing_ok)

        os.environ["PUBLIC_DATA_API_KEY"] = "your_public_data_api_key"
        os.environ["NAVER_CLIENT_ID"] = "replace_me"
        os.environ["NAVER_CLIENT_SECRET"] = "placeholder_secret"
        placeholder_status = load_env_status(None)
        placeholder_ok = bool(
            placeholder_status["state"].eq("PLACEHOLDER").all()
            and placeholder_status["configured"].eq(False).all()
            and placeholder_status["value_exposed"].eq(False).all()
        )
        record("secret_state_placeholder", placeholder_ok)

        os.environ["PUBLIC_DATA_API_KEY"] = "qa-public-key-value"
        os.environ["NAVER_CLIENT_ID"] = "qa-client-id-value"
        os.environ["NAVER_CLIENT_SECRET"] = "qa-client-secret-value"
        configured_status = load_env_status(None)
        configured_ok = bool(
            configured_status["state"].eq("CONFIGURED").all()
            and configured_status["configured"].eq(True).all()
            and configured_status["value_exposed"].eq(False).all()
        )
        record("secret_state_configured_without_value_exposure", configured_ok)

        # Redaction contract.
        redacted = redact_mapping(
            {
                "api_key": "should-not-survive",
                "token": "should-not-survive",
                "query": "제주 여행",
            }
        )
        redacted_url = redact_url(
            "https://example.org/api?api_key=secret&query=test"
        )
        redaction_ok = bool(
            redacted["api_key"] == "***REDACTED***"
            and redacted["token"] == "***REDACTED***"
            and redacted["query"] == "제주 여행"
            and "secret" not in redacted_url
            and "%2A%2A%2AREDACTED%2A%2A%2A" in redacted_url
        )
        record("secret_redaction", redaction_ok, redacted_url)

        # Local/private URL must be rejected before any request.
        local_rejected = False
        try:
            validate_public_http_url("http://127.0.0.1/test")
        except ValueError:
            local_rejected = True
        record("private_url_rejected", local_rejected)

        # Immutable snapshot + hash + metadata, all local synthetic data.
        raw_path = versioned_snapshot_path(
            setup["paths"]["raw"],
            "qa_snapshot",
            ".json",
        )
        save_json_snapshot(
            {"source": "synthetic qa", "items": [1, 2, 3]},
            raw_path,
        )
        hash_value = sha256_file(raw_path)
        overwrite_blocked = False
        try:
            save_json_snapshot({"source": "second"}, raw_path)
        except FileExistsError:
            overwrite_blocked = True
        record(
            "immutable_raw_snapshot",
            bool(raw_path.exists() and hash_value and overwrite_blocked),
            f"path={raw_path.name}, sha256={hash_value[:12]}..., blocked={overwrite_blocked}",
        )

        metadata = build_collection_metadata(
            provider="Synthetic QA Provider",
            source_url="https://example.org/api?api_key=do-not-log",
            collection_method="official_api",
            data_reference_date="2026-09",
            request_scope="synthetic local QA only",
            license_or_terms="QA placeholder; no external collection performed",
            raw_path=raw_path,
            policy_confirmed=False,
            extra={"token": "do-not-log", "page": 1},
        )
        metadata_path = versioned_snapshot_path(
            setup["paths"]["metadata"],
            "qa_snapshot",
            ".json",
        )
        save_metadata_snapshot(metadata, metadata_path)
        metadata_text = metadata_path.read_text(encoding="utf-8")
        metadata_ok = bool(
            metadata["sha256"] == hash_value
            and "do-not-log" not in metadata_text
            and "***REDACTED***" in metadata_text
            and metadata["data_reference_date"] == "2026-09"
            and metadata["collected_at_utc"]
        )
        record("metadata_provenance_and_redaction", metadata_ok)

        # External quality contract.
        external_good = pd.DataFrame(
            {
                "order_month": ["2026-01", "2026-02", "2026-03"],
                "external_indicator": [3, 1, 2],
            }
        )
        quality_good = validate_external_dataframe(
            external_good,
            key_columns="order_month",
        )
        quality_good_ok = bool(not quality_good["status"].eq("FAIL").any())
        record(
            "external_quality_good",
            quality_good_ok,
            repr(quality_good.to_dict(orient="records")),
        )

        external_bad = pd.concat(
            [external_good, external_good.iloc[[0]]],
            ignore_index=True,
        )
        quality_bad = validate_external_dataframe(
            external_bad,
            key_columns="order_month",
        )
        duplicate_fail = quality_bad.loc[
            quality_bad["check_item"].eq("key_duplicate:order_month"),
            "status",
        ]
        record(
            "external_duplicate_key_detected",
            bool(len(duplicate_fail) == 1 and duplicate_fail.iloc[0] == "FAIL"),
            repr(quality_bad.to_dict(orient="records")),
        )

        # Merge contract.
        internal = pd.DataFrame(
            {
                "order_month": ["2026-01", "2026-02", "2026-03"],
                "completed_amount": [1000, 1500, 1300],
            }
        )
        merged, merge_check = merge_external_data(
            internal,
            external_good,
            on="order_month",
            how="left",
            validate="one_to_one",
        )
        merge_ok = bool(
            len(merged) == len(internal)
            and merge_check["right_key_duplicate_count"].iloc[0] == 0
            and bool(merge_check["row_count_preserved"].iloc[0])
            and merge_check["left_only_count"].iloc[0] == 0
            and merge_check["status"].iloc[0] == "PASS"
        )
        record("safe_external_merge", merge_ok, repr(merge_check.to_dict(orient="records")))

        duplicate_merge_blocked = False
        try:
            merge_external_data(
                internal,
                external_bad,
                on="order_month",
                how="left",
                validate="one_to_one",
            )
        except ValueError:
            duplicate_merge_blocked = True
        record("duplicate_right_key_merge_fail_fast", duplicate_merge_blocked)

        # Required setup outputs.
        expected_names = {
            "ch13_external_data_plan.csv",
            "ch13_collection_method_summary.csv",
            "ch13_external_integration_plan.csv",
            "ch13_external_data_checklist.csv",
            "ch13_external_data_log.csv",
            "ch13_env_key_status.csv",
            "ch13_collection_metadata_template.csv",
            "ch13_api_code_review_checklist.csv",
            "ch13_network_execution_gate.csv",
            "ch13_external_data_summary.md",
        }
        missing_outputs = sorted(
            name
            for name in expected_names
            if not (REPORT_DIR / name).exists()
            or (REPORT_DIR / name).stat().st_size == 0
        )
        record("required_outputs", not missing_outputs, f"missing={missing_outputs}")

        # Initial log must not imply a collection was executed.
        external_log = outputs["external_data_log"]
        log_safe = bool(
            external_log["execution_status"].eq("NOT_EXECUTED").all()
            and external_log["quality_status"].eq("NOT_REVIEWED").all()
        )
        record("initial_log_not_executed", log_safe)

        # Notebook and documentation contracts.
        notebook = json.loads(
            (ROOT / "notebooks" / "ch13_external_data_collection.ipynb")
            .read_text(encoding="utf-8")
        )
        notebook_text = json.dumps(notebook, ensure_ascii=False)
        notebook_markers = [
            "RUN_PUBLIC_API = False",
            "RUN_NAVER_API = False",
            "RUN_CRAWLING_EXAMPLE = False",
            "POLICY_CONFIRMED = False",
            "PLACEHOLDER",
            "versioned_snapshot_path",
            "validate_external_dataframe",
            "merge_external_data",
            "SYNTHETIC",
        ]
        missing_notebook = [m for m in notebook_markers if m not in notebook_text]
        record(
            "notebook_contract",
            not missing_notebook,
            f"missing={missing_notebook}",
        )

        practice_text = (
            ROOT / "practice" / "chapter13" / "chapter13.md"
        ).read_text(encoding="utf-8")
        assignment_text = (
            ROOT / "practice" / "chapter13" / "templates" / "chapter13_assignment.md"
        ).read_text(encoding="utf-8")
        docs = practice_text + "\n" + assignment_text
        document_markers = [
            "MISSING / PLACEHOLDER / CONFIGURED",
            "RUN_PUBLIC_API",
            "POLICY_CONFIRMED",
            "Raw / Processed / Metadata",
            "SHA-256",
            "retry ≠ rate limit",
            "HTTP 200 ≠",
            "right_key_duplicate_count",
            "BLOCKED_BY_POLICY",
            "untrusted data",
        ]
        missing_docs = [m for m in document_markers if m not in docs]
        record(
            "practice_document_contract",
            not missing_docs,
            f"missing={missing_docs}",
        )

        runner_text = (
            ROOT / "scripts" / "run_external_data_collection.py"
        ).read_text(encoding="utf-8")
        runner_safe = bool(
            "performs NO network requests" in runner_text
            and "network_gate" in runner_text
            and "RUN_*" in runner_text
            and "request_json_api(" not in runner_text
            and "fetch_public_html(" not in runner_text
        )
        record("runner_network_free_contract", runner_safe)

        # Source-level safe default sanity check.
        gate_direct = create_network_execution_gate()
        record(
            "direct_network_gate_contract",
            bool(
                gate_direct["default"].eq(False).all()
                and gate_direct["status"].eq("SAFE_DEFAULT").all()
            ),
        )

    except Exception as exc:
        record("unexpected_exception", False, repr(exc))
    finally:
        for name, old_value in old_env.items():
            if old_value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = old_value

        overall_pass = bool(checks) and all(
            item["status"] == "PASS" for item in checks
        )
        report = {
            "chapter": 13,
            "network_requests_performed": False,
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
