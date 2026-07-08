"""Chapter 13 외부 데이터 수집 공통 함수 모음.

공공데이터 파일/API, 네이버 검색 API, 기본 크롤링, 내부 데이터와 외부 데이터 연결 검토를
안전하고 재현 가능한 방식으로 연습하기 위한 함수들을 제공합니다.
API Key는 코드에 직접 쓰지 않고 환경변수 또는 .env 파일을 통해 읽는 것을 전제로 합니다.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


EXTERNAL_DATA_CHECK_ITEMS = [
    "분석 질문에 필요한 외부 데이터인가?",
    "공식 API 또는 다운로드 파일을 우선 확인했는가?",
    "데이터 출처와 제공 기관을 기록했는가?",
    "업데이트 주기와 수집 시점을 기록했는가?",
    "API Key를 .env에 저장했는가?",
    "API Key를 출력하거나 GitHub에 올리지 않았는가?",
    "요청 URL과 파라미터를 공식 문서 기준으로 확인했는가?",
    "응답 상태 코드와 오류 처리를 포함했는가?",
    "원본 응답 또는 원본 파일을 보관했는가?",
    "DataFrame 변환 후 컬럼과 행 수를 확인했는가?",
    "기존 데이터와 연결할 기준 컬럼이 있는가?",
    "날짜, 지역, 키워드 표기를 맞췄는가?",
    "크롤링 대상 사이트의 정책을 확인했는가?",
    "개인정보나 민감정보를 수집하지 않았는가?",
    "LLM이 만든 코드와 실제 공식 문서를 비교했는가?",
]


def ensure_external_dirs(
    base_dir: str | Path = ".",
) -> tuple[Path, Path]:
    """외부 데이터 폴더와 보고서 폴더를 생성합니다."""
    base_path = Path(base_dir)
    external_dir = base_path / "data" / "external"
    report_dir = base_path / "reports"
    external_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    return external_dir, report_dir


def load_env_keys(env_path: str | Path | None = None) -> dict[str, bool]:
    """환경변수 로드 여부만 반환합니다. 실제 API Key 값은 반환하지 않습니다."""
    if load_dotenv is not None:
        if env_path:
            load_dotenv(env_path)
        else:
            load_dotenv()

    key_names = [
        "PUBLIC_DATA_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ]
    return {key: os.getenv(key) is not None for key in key_names}


def create_external_data_plan() -> pd.DataFrame:
    """내부 분석 질문과 연결 가능한 외부 데이터 후보를 정리합니다."""
    return pd.DataFrame(
        {
            "internal_question": [
                "특정 월 매출이 왜 증가했을까?",
                "특정 지역 고객 구매가 많은 이유는 무엇일까?",
                "여행 상품 추천 앱을 만들려면 어떤 데이터가 필요할까?",
                "특정 키워드 관심도가 높아지고 있을까?",
                "공공 API를 활용한 서비스 기획이 가능할까?",
            ],
            "external_data_candidate": [
                "공휴일, 날씨, 이벤트, 검색 트렌드",
                "지역 인구, 관광지, 상권 정보",
                "관광지, 숙박, 음식점, 위치 데이터",
                "검색 API, 뉴스, 블로그, SNS 데이터",
                "공공데이터포털, 한국관광공사 OpenAPI",
            ],
            "connection_key": [
                "날짜 또는 월",
                "지역명 또는 행정구역 코드",
                "위치, 지역 코드, 카테고리",
                "키워드, 날짜",
                "API 제공 키, 지역, 카테고리",
            ],
            "caution": [
                "매출 증가 원인을 단정하지 말 것",
                "지역명 표기 차이 확인",
                "상업적 이용 조건과 출처 확인",
                "검색 결과가 실제 수요를 대표한다고 단정하지 말 것",
                "API 문서와 요청 제한 확인",
            ],
        }
    )


def create_collection_method_summary() -> pd.DataFrame:
    """외부 데이터 수집 방법별 특징을 요약합니다."""
    return pd.DataFrame(
        {
            "method": ["파일 다운로드", "API 호출", "크롤링"],
            "description": [
                "CSV, Excel, JSON 파일을 직접 내려받아 사용",
                "정해진 주소와 파라미터로 데이터를 요청",
                "웹페이지 HTML에서 필요한 정보를 추출",
            ],
            "example": [
                "공공데이터포털 CSV, 통계청 Excel",
                "공공데이터 API, 네이버 검색 API",
                "공개 웹페이지의 표, 제목, 링크",
            ],
            "priority": [
                "안정적이며 우선 검토",
                "공식 문서와 인증 필요",
                "정책 확인 후 제한적으로 사용",
            ],
        }
    )


def read_external_csv(file_path: str | Path) -> pd.DataFrame:
    """외부 CSV 파일을 읽고 기본 구조를 반환합니다."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"외부 CSV 파일을 찾을 수 없습니다: {path}")
    return pd.read_csv(path)


def summarize_external_dataframe(
    df: pd.DataFrame,
    data_name: str,
    source: str,
    collection_method: str,
) -> pd.DataFrame:
    """수집한 외부 DataFrame의 기본 구조를 요약합니다."""
    return pd.DataFrame(
        [
            {
                "data_name": data_name,
                "source": source,
                "collection_method": collection_method,
                "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rows": df.shape[0],
                "columns": df.shape[1],
                "column_list": ", ".join(df.columns),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        ]
    )


def clean_html_text(text: Any) -> str:
    """HTML 태그가 포함된 텍스트에서 태그를 제거합니다."""
    if pd.isna(text):
        return ""
    text = str(text)
    if BeautifulSoup is None:
        return text.replace("<b>", "").replace("</b>", "")
    return BeautifulSoup(text, "html.parser").get_text()


def search_naver_blog(
    query: str,
    display: int = 10,
    start: int = 1,
    sort: str = "sim",
    client_id: str | None = None,
    client_secret: str | None = None,
) -> dict[str, Any]:
    """네이버 블로그 검색 API를 호출합니다. 인증 정보는 출력하지 않습니다."""
    if requests is None:
        raise ImportError("requests 패키지가 필요합니다.")

    client_id = client_id or os.getenv("NAVER_CLIENT_ID")
    client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")

    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def naver_blog_items_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    """네이버 블로그 검색 API 응답의 items를 DataFrame으로 변환합니다."""
    items = result.get("items", [])
    df = pd.DataFrame(items)
    if df.empty:
        return df

    for col in ["title", "description"]:
        if col in df.columns:
            df[f"{col}_clean"] = df[col].apply(clean_html_text)

    return df


def fetch_page(url: str) -> str:
    """공개 웹페이지 HTML을 가져옵니다. 실제 사용 전 사이트 정책을 확인해야 합니다."""
    if requests is None:
        raise ImportError("requests 패키지가 필요합니다.")

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("http 또는 https URL만 요청할 수 있습니다.")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DataAnalysisCourseBot/1.0; educational use)",
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text


def extract_title_and_links(html: str, base_url: str | None = None) -> tuple[str, pd.DataFrame]:
    """HTML에서 페이지 제목과 링크 목록을 추출합니다."""
    if BeautifulSoup is None:
        raise ImportError("beautifulsoup4 패키지가 필요합니다.")

    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(strip=True) if soup.title else ""
    links = []

    for a_tag in soup.find_all("a"):
        text = a_tag.get_text(strip=True)
        href = a_tag.get("href")
        if text or href:
            links.append(
                {
                    "page_title": page_title,
                    "text": text,
                    "href": href,
                    "base_url": base_url or "",
                }
            )

    return page_title, pd.DataFrame(links)


def create_external_integration_plan() -> pd.DataFrame:
    """외부 데이터와 내부 데이터의 연결 기준을 정리합니다."""
    return pd.DataFrame(
        {
            "connection_key": ["날짜", "지역", "상품 카테고리", "키워드", "위치"],
            "internal_data_example": [
                "월별 매출, 주문 일자",
                "고객 city",
                "상품 category",
                "상품명, 카테고리명",
                "고객 지역, 관광지 위치",
            ],
            "external_data_example": [
                "공휴일, 날씨, 검색 트렌드",
                "지역 인구, 관광지, 상권 정보",
                "검색 키워드, 뉴스 데이터",
                "블로그/뉴스 검색 결과",
                "위도·경도 기반 관광지/상권 데이터",
            ],
            "validation_check": [
                "날짜 형식과 분석 단위 일치 확인",
                "지역명 표기와 행정구역 단위 확인",
                "카테고리 매핑 기준 확인",
                "검색어 대표성 및 수집 시점 확인",
                "좌표계와 거리 기준 확인",
            ],
        }
    )


def create_external_data_checklist() -> pd.DataFrame:
    """외부 데이터 수집 체크리스트를 생성합니다."""
    return pd.DataFrame(
        {
            "check_item": EXTERNAL_DATA_CHECK_ITEMS,
            "status": ["□"] * len(EXTERNAL_DATA_CHECK_ITEMS),
            "memo": [""] * len(EXTERNAL_DATA_CHECK_ITEMS),
        }
    )


def create_external_data_log() -> pd.DataFrame:
    """외부 데이터 수집 결과 로그 템플릿을 생성합니다."""
    return pd.DataFrame(
        {
            "data_name": [
                "public_data_sample",
                "naver_blog_search_jeju",
                "scraped_example_links",
            ],
            "source": [
                "공공데이터 파일 또는 API",
                "네이버 블로그 검색 API",
                "공개 웹페이지 예시",
            ],
            "save_path": [
                "data/external/public_data_sample.csv",
                "data/external/naver_blog_search_jeju.csv",
                "data/external/scraped_example_links.csv",
            ],
            "collection_method": ["파일 다운로드 또는 공공 API", "API 호출", "크롤링"],
            "usage_note": [
                "분석 목적에 따라 내부 데이터와 날짜 또는 지역 기준으로 연결 가능",
                "키워드 관심도 참고 자료로 활용 가능하나 대표성 해석 주의",
                "크롤링 구조 이해용 예시이며 실제 사이트 적용 전 정책 확인 필요",
            ],
            "collected_at": [""] * 3,
        }
    )


def build_external_data_summary(
    data_plan: pd.DataFrame,
    method_summary: pd.DataFrame,
    integration_plan: pd.DataFrame,
    checklist: pd.DataFrame,
    external_data_log: pd.DataFrame,
) -> str:
    """외부 데이터 수집 요약 Markdown 문자열을 생성합니다."""
    return f"""# Chapter 13 외부 데이터 수집 요약

## 1. 수집 목적

내부 온라인 쇼핑몰 데이터만으로 답하기 어려운 분석 질문을 확장하기 위해 공공데이터, 검색 API, 기본 크롤링 방식의 외부 데이터 수집 흐름을 검토했습니다.

## 2. 외부 데이터 후보

```text
{data_plan.to_string(index=False)}
```

## 3. 수집 방법 비교

```text
{method_summary.to_string(index=False)}
```

## 4. 내부 데이터와 연결 기준

```text
{integration_plan.to_string(index=False)}
```

## 5. 수집 결과 로그 템플릿

```text
{external_data_log.to_string(index=False)}
```

## 6. 외부 데이터 수집 체크리스트

```text
{checklist.to_string(index=False)}
```

## 7. 활용 시 주의사항

- 외부 데이터는 출처와 수집 시점을 함께 기록해야 합니다.
- API Key는 .env 파일에 저장하고 GitHub에 올리지 않아야 합니다.
- API 주소, 파라미터, 응답 구조는 공식 문서 기준으로 확인해야 합니다.
- 크롤링은 사이트 정책을 확인한 뒤 제한적으로 사용해야 합니다.
- 외부 데이터와 내부 데이터를 연결할 때 날짜, 지역, 키워드 기준을 맞춰야 합니다.
- 검색 결과나 크롤링 결과를 전체 여론이나 실제 수요로 단정하지 않아야 합니다.

## 8. 다음 단계

수집한 외부 데이터를 기존 EDA, 시각화, 머신러닝 분석에 어떻게 결합할 수 있는지 검토합니다.
"""


def save_external_data_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """13장 외부 데이터 수집 결과물을 저장합니다."""
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_map = {
        "data_plan": "ch13_external_data_plan.csv",
        "method_summary": "ch13_collection_method_summary.csv",
        "integration_plan": "ch13_external_integration_plan.csv",
        "checklist": "ch13_external_data_checklist.csv",
        "external_data_log": "ch13_external_data_log.csv",
        "env_status": "ch13_env_key_status.csv",
    }

    paths: dict[str, Path] = {}
    for key, filename in file_map.items():
        path = output_dir / filename
        value = outputs[key]
        if isinstance(value, pd.DataFrame):
            value.to_csv(path, index=False, encoding="utf-8-sig")
        paths[key] = path

    summary_path = output_dir / "ch13_external_data_summary.md"
    summary_path.write_text(str(outputs["summary_text"]), encoding="utf-8")
    paths["summary_text"] = summary_path
    return paths


def run_external_data_collection_setup(
    base_dir: str | Path = ".",
    report_dir: str | Path | None = None,
) -> dict[str, object]:
    """13장 외부 데이터 수집 실습용 기본 산출물을 생성합니다."""
    base_path = Path(base_dir)
    external_dir, default_report_dir = ensure_external_dirs(base_path)
    output_report_dir = Path(report_dir) if report_dir else default_report_dir
    output_report_dir.mkdir(parents=True, exist_ok=True)

    env_status = pd.DataFrame(
        [
            {"env_key": key, "loaded": loaded}
            for key, loaded in load_env_keys().items()
        ]
    )
    data_plan = create_external_data_plan()
    method_summary = create_collection_method_summary()
    integration_plan = create_external_integration_plan()
    checklist = create_external_data_checklist()
    external_data_log = create_external_data_log()
    summary_text = build_external_data_summary(
        data_plan=data_plan,
        method_summary=method_summary,
        integration_plan=integration_plan,
        checklist=checklist,
        external_data_log=external_data_log,
    )

    outputs: dict[str, pd.DataFrame | str] = {
        "data_plan": data_plan,
        "method_summary": method_summary,
        "integration_plan": integration_plan,
        "checklist": checklist,
        "external_data_log": external_data_log,
        "env_status": env_status,
        "summary_text": summary_text,
    }
    output_paths = save_external_data_outputs(outputs, output_report_dir)

    return {
        "external_dir": external_dir,
        "report_dir": output_report_dir,
        "outputs": outputs,
        "output_paths": output_paths,
    }
