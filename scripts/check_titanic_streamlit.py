from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_ROOT / "src" / "titanic_app" / "app.py"
QA_DIR = PROJECT_ROOT / "tmp" / "titanic_public_qa"
LOG_PATH = QA_DIR / "streamlit.log"
HEALTH_URL = "http://127.0.0.1:8501/_stcore/health"
PAGE_URL = "http://127.0.0.1:8501/"


def wait_for_streamlit(timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            response = requests.get(HEALTH_URL, timeout=2)
            if response.status_code == 200 and response.text.strip().lower() == "ok":
                page = requests.get(PAGE_URL, timeout=5)
                page.raise_for_status()
                print("Streamlit health PASS")
                print("Streamlit page status:", page.status_code)
                return
        except Exception as exc:  # noqa: BLE001 - QA helper keeps last connection error
            last_error = exc

        time.sleep(1)

    raise RuntimeError(f"Streamlit health check failed: {last_error}")


def main() -> None:
    if not APP_PATH.is_file():
        raise FileNotFoundError(APP_PATH)

    QA_DIR.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_PATH),
        "--server.headless",
        "true",
        "--server.port",
        "8501",
    ]

    env = os.environ.copy()
    env.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")

    print("$", " ".join(command))

    with LOG_PATH.open("w", encoding="utf-8") as log_file:
        process = subprocess.Popen(
            command,
            cwd=PROJECT_ROOT,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            env=env,
        )

        try:
            wait_for_streamlit()
        except Exception:
            log_file.flush()
            print("\n--- Streamlit log ---")
            if LOG_PATH.is_file():
                print(LOG_PATH.read_text(encoding="utf-8", errors="replace"))
            raise
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)

    print("Streamlit process cleanup PASS")
    print("log:", LOG_PATH)


if __name__ == "__main__":
    main()
