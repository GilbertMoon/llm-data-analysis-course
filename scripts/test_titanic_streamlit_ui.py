from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
APP_DIR = PROJECT_ROOT / "src" / "titanic_app"
APP_PATH = APP_DIR / "app.py"


def assert_no_exceptions(at: AppTest, stage: str) -> None:
    if len(at.exception) > 0:
        messages = [str(item.value) for item in at.exception]
        raise RuntimeError(f"Streamlit AppTest exception during {stage}: {messages}")


def main() -> None:
    if not APP_PATH.is_file():
        raise FileNotFoundError(APP_PATH)

    if str(APP_DIR) not in sys.path:
        sys.path.insert(0, str(APP_DIR))

    at = AppTest.from_file(str(APP_PATH), default_timeout=15).run()
    assert_no_exceptions(at, "initial render")

    if len(at.title) != 1:
        raise RuntimeError(f"Expected one title, found {len(at.title)}")
    if len(at.button) != 1:
        raise RuntimeError(f"Expected one form submit button, found {len(at.button)}")
    if len(at.selectbox) != 3:
        raise RuntimeError(f"Expected three selectboxes, found {len(at.selectbox)}")
    if len(at.number_input) != 4:
        raise RuntimeError(f"Expected four number inputs, found {len(at.number_input)}")

    # 기본 입력값으로 실제 form submit을 실행해 prediction branch까지 검증합니다.
    at.button[0].click().run()
    assert_no_exceptions(at, "prediction submit")

    prediction_messages = len(at.success) + len(at.warning)
    if prediction_messages < 1:
        raise RuntimeError("Prediction result message was not rendered.")
    if len(at.metric) != 1:
        raise RuntimeError(f"Expected one probability metric, found {len(at.metric)}")
    if len(at.info) < 1:
        raise RuntimeError("Model limitation/info text was not rendered.")

    print("Streamlit AppTest initial render PASS")
    print("Streamlit AppTest form submit PASS")
    print("prediction result elements:", prediction_messages)
    print("metric:", at.metric[0].value)
    print("Streamlit UI logic QA: PASS")


if __name__ == "__main__":
    main()
