"""Chapter 13 외부 데이터 수집 공통 함수 모음.

공식 파일/API를 우선 사용하고, 네트워크 요청·인증 정보·robots.txt·출처 기록을
안전하고 재현 가능한 방식으로 다루기 위한 교육용 함수들을 제공합니다.

네트워크 수집은 기본 실행 과정에 포함하지 않습니다. 실제 API 또는 웹페이지를
호출하기 전에는 공식 문서, 이용약관, 라이선스, 개인정보 처리 기준을 직접 확인해야 합니다.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib.robotparser import RobotFileParser

import pandas as pd

try:
    import requests
    from requests import Response, Session
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:  # pragma: no cover
    requests = None
    Response = Any
    Session = Any
    HTTPAdapter = None
    Retry = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover
    BeautifulSoup = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None


DEFAULT_USER_AGENT = (
    "DataAnalysisCourseBot/1.0 "
    "(+https://github.com/GilbertMoon/llm-data-analysis-course)"
)
DEFAULT_TIMEOUT = (3.05, 20)
MAX_HTML_BYTES = 2_000_000
ROBOTS_MAX_BYTES = 512_000

SECRET_NAME_PARTS = {
    "authorization",
    "api_key",
    "apikey",
    "client_secret",
    "servicekey",
    "service_key",
    "secret",
    "token",
}

EXTERNAL_DATA_CHECK_ITEMS = [
    "분석 질문에 필요한 외부 데이터인가?",
    "공식 API 또는 공식 다운로드 파일을 우선 확인했는가?",
    "제공 기관, 원본 URL, 라이선스·이용조건을 기록했는가?",
    "데이터 기준일과 실제 수집 시각을 구분해 기록했는가?",
    "API Key를 .env 또는 안전한 비밀 저장소에 보관했는가?",
    "API Key와 인증 헤더를 출력·로그·GitHub에 남기지 않았는가?",
    "요청 URL, 파라미터, 인증 방식, 응답 구조를 공식 문서에서 확인했는가?",
    "연결·읽기 timeout과 HTTP 오류 처리를 포함했는가?",
    "429·5xx 응답에 대한 재시도와 Retry-After 처리를 고려했는가?",
    "원본 응답과 정제 결과를 분리해 보관했는가?",
    "응답의 행 수, 컬럼, 결측치, 중복, 기준일을 확인했는가?",
    "기존 데이터와 연결할 키와 분석 단위가 명확한가?",
    "날짜, 지역, 키워드, 좌표계 표기를 맞췄는가?",
    "크롤링 전 robots.txt와 이용약관을 각각 확인했는가?",
    "robots.txt 허용을 법적·계약상 허가로 오해하지 않았는가?",
    "로그인·우회·접근 제한 회피를 시도하지 않았는가?",
    "개인정보·민감정보·저작물 원문을 불필요하게 수집하지 않았는가?",
    "LLM이 만든 코드를 실제 공식 문서와 비교했는가?",
]


def utc_now_iso() -> str:
    """현재 UTC 시각을 ISO 8601 형식으로 반환합니다."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ensure_external_dirs(base_dir: str | Path = ".") -> dict[str, Path]:
    """외부 데이터 원본·정제·메타데이터·보고서 폴더를 생성합니다."""
    base_path = Path(base_dir).resolve()
    external_root = base_path / "data" / "external"
    paths = {
        "external_root": external_root,
        "raw": external_root / "raw",
        "processed": external_root / "processed",
        "metadata": external_root / "metadata",
        "reports": base_path / "reports",
    }
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
    return paths


def load_env_status(env_path: str | Path | None = None) -> pd.DataFrame:
    """환경변수의 로드 여부만 반환하며 실제 비밀값은 반환하지 않습니다."""
    if load_dotenv is not None:
        load_dotenv(dotenv_path=env_path, override=False)

    key_names = [
        "PUBLIC_DATA_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ]
    return pd.DataFrame(
        [
            {
                "env_key": key,
                "loaded": bool(os.getenv(key)),
                "value_exposed": False,
            }
            for key in key_names
        ]
    )


def _require_requests() -> None:
    if requests is None or HTTPAdapter is None or Retry is None:
        raise ImportError(
            "requests 패키지가 필요합니다. "
            "python -m pip install -r requirements.txt 를 실행하세요."
        )


def build_http_session(
    *,
    total_retries: int = 3,
    backoff_factor: float = 0.5,
) -> Session:
    """GET 요청에 제한적인 재시도 정책을 적용한 Session을 생성합니다."""
    _require_requests()
    retry = Retry(
        total=total_retries,
        connect=total_retries,
        read=total_retries,
        status=total_retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def validate_public_http_url(url: str) -> str:
    """HTTP(S) 공개 주소인지 확인하고 로컬·사설 네트워크 주소를 거부합니다.

    이 검사는 교육용 방어선이며 DNS rebinding 같은 모든 네트워크 공격을
    완전히 차단하는 보안 경계로 간주해서는 안 됩니다.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("http 또는 https URL만 사용할 수 있습니다.")
    if parsed.username or parsed.password:
        raise ValueError("사용자명이나 비밀번호가 포함된 URL은 허용하지 않습니다.")
    if not parsed.hostname:
        raise ValueError("호스트 이름이 없는 URL입니다.")

    hostname = parsed.hostname.rstrip(".").lower()
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("localhost 주소는 허용하지 않습니다.")

    addresses: set[str] = set()
    try:
        addresses.add(str(ipaddress.ip_address(hostname)))
    except ValueError:
        try:
            for info in socket.getaddrinfo(
                hostname,
                parsed.port or (443 if parsed.scheme == "https" else 80),
            ):
                addresses.add(info[4][0])
        except socket.gaierror as exc:
            raise ValueError(f"호스트 이름을 확인할 수 없습니다: {hostname}") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address)
        if not ip.is_global:
            raise ValueError(
                "공개 인터넷 주소가 아닌 호스트는 요청할 수 없습니다: "
                f"{hostname} ({address})"
            )
    return url


def _is_secret_name(name: str) -> bool:
    normalized = name.lower().replace("-", "_")
    return any(part in normalized for part in SECRET_NAME_PARTS)


def redact_mapping(values: Mapping[str, Any] | None) -> dict[str, Any]:
    """요청 파라미터나 메타데이터에서 비밀값으로 보이는 항목을 마스킹합니다."""
    if not values:
        return {}
    return {
        str(key): "***REDACTED***" if _is_secret_name(str(key)) else value
        for key, value in values.items()
    }


def redact_url(url: str) -> str:
    """URL 쿼리 문자열에서 인증 정보로 보이는 값을 마스킹합니다."""
    parsed = urlparse(url)
    redacted_query = urlencode(
        [
            (
                key,
                "***REDACTED***" if _is_secret_name(key) else value,
            )
            for key, value in parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        ],
        doseq=True,
    )
    return urlunparse(parsed._replace(query=redacted_query))


def _response_metadata(
    response: Response,
    *,
    requested_url: str,
    params: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "requested_url": redact_url(requested_url),
        "final_url": redact_url(response.url),
        "status_code": int(response.status_code),
        "content_type": response.headers.get("Content-Type", ""),
        "collected_at_utc": utc_now_iso(),
        "request_params": json.dumps(
            redact_mapping(params),
            ensure_ascii=False,
            default=str,
        ),
    }


def request_json_api(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    session: Session | None = None,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
) -> tuple[Any, dict[str, Any]]:
    """공개 JSON API를 호출하고 응답 데이터와 비밀값이 제거된 메타데이터를 반환합니다."""
    _require_requests()
    validate_public_http_url(url)
    client = session or build_http_session()

    response = client.get(
        url,
        params=dict(params or {}),
        headers=dict(headers or {}),
        timeout=timeout,
        allow_redirects=False,
    )
    if 300 <= response.status_code < 400:
        location = response.headers.get("Location", "")
        raise RuntimeError(
            "API가 다른 주소로 리다이렉트했습니다. "
            f"공식 문서에서 새 주소를 확인하세요: {redact_url(location)}"
        )

    response.raise_for_status()
    validate_public_http_url(response.url)

    try:
        payload = response.json()
    except ValueError as exc:
        content_type = response.headers.get("Content-Type", "")
        preview = response.text[:200].replace("\n", " ")
        raise ValueError(
            "JSON 응답을 해석할 수 없습니다. "
            f"Content-Type={content_type!r}, preview={preview!r}"
        ) from exc

    return payload, _response_metadata(
        response,
        requested_url=url,
        params=params,
    )


def _validate_naver_search_params(
    query: str,
    display: int,
    start: int,
    sort: str,
) -> None:
    if not query or not query.strip():
        raise ValueError("검색어 query는 비어 있을 수 없습니다.")
    if not 1 <= display <= 100:
        raise ValueError("display는 1~100 범위여야 합니다.")
    if not 1 <= start <= 1000:
        raise ValueError("start는 1~1000 범위여야 합니다.")
    if sort not in {"sim", "date"}:
        raise ValueError("sort는 'sim' 또는 'date'여야 합니다.")


def search_naver_blog(
    query: str,
    *,
    display: int = 10,
    start: int = 1,
    sort: str = "sim",
    client_id: str | None = None,
    client_secret: str | None = None,
    session: Session | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """네이버 블로그 검색 API를 호출하고 응답과 수집 메타데이터를 반환합니다."""
    _validate_naver_search_params(query, display, start, sort)

    client_id = client_id or os.getenv("NAVER_CLIENT_ID")
    client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError(
            "NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다."
        )

    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "User-Agent": DEFAULT_USER_AGENT,
    }
    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort,
    }
    payload, metadata = request_json_api(
        url,
        params=params,
        headers=headers,
        session=session,
    )
    if not isinstance(payload, dict):
        raise TypeError("네이버 검색 API 응답이 JSON 객체가 아닙니다.")
    metadata["provider"] = "Naver Search API"
    metadata["query"] = query
    return payload, metadata


def clean_html_text(text: Any) -> str:
    """검색 API 텍스트에 포함된 HTML 태그를 제거합니다."""
    if pd.isna(text):
        return ""
    value = str(text)
    if BeautifulSoup is None:
        return value.replace("<b>", "").replace("</b>", "")
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def naver_blog_items_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    """네이버 블로그 검색 API의 items를 분석 가능한 표로 변환합니다."""
    items = result.get("items", [])
    if not isinstance(items, list):
        raise TypeError("네이버 API 응답의 items가 배열이 아닙니다.")

    df = pd.DataFrame(items)
    if df.empty:
        return df

    for column in ["title", "description"]:
        if column in df.columns:
            df[f"{column}_clean"] = df[column].apply(clean_html_text)

    if "postdate" in df.columns:
        df["postdate"] = pd.to_datetime(
            df["postdate"],
            format="%Y%m%d",
            errors="coerce",
        )
    return df


def _robots_url_for(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse(
        (parsed.scheme, parsed.netloc, "/robots.txt", "", "", "")
    )


def check_robots_permission(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    session: Session | None = None,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """robots.txt 접근 규칙을 확인합니다.

    4xx는 robots.txt가 없는 상태로 보고 접근 가능으로 처리하며, 5xx 또는
    네트워크 오류는 보수적으로 접근 불가로 처리합니다. robots.txt는 접근
    권한이나 이용허락을 의미하지 않으므로 이용약관·저작권 검토는 별도입니다.
    """
    _require_requests()
    validate_public_http_url(url)
    robots_url = _robots_url_for(url)
    client = session or build_http_session()

    try:
        response = client.get(
            robots_url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            allow_redirects=True,
        )
        validate_public_http_url(response.url)
    except requests.RequestException as exc:
        return {
            "allowed": False,
            "robots_url": robots_url,
            "status": "unreachable",
            "status_code": None,
            "reason": type(exc).__name__,
        }

    if 400 <= response.status_code < 500:
        return {
            "allowed": True,
            "robots_url": robots_url,
            "status": "unavailable",
            "status_code": int(response.status_code),
            "reason": "robots.txt가 제공되지 않음",
        }

    if response.status_code >= 500:
        return {
            "allowed": False,
            "robots_url": robots_url,
            "status": "unreachable",
            "status_code": int(response.status_code),
            "reason": "서버 오류로 robots.txt 규칙을 확인할 수 없음",
        }

    response.raise_for_status()
    robots_bytes = response.content[:ROBOTS_MAX_BYTES]
    robots_text = robots_bytes.decode(
        response.encoding or "utf-8",
        errors="replace",
    )
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(robots_text.splitlines())
    allowed = parser.can_fetch(user_agent, url)

    return {
        "allowed": bool(allowed),
        "robots_url": robots_url,
        "status": "parsed",
        "status_code": int(response.status_code),
        "reason": "robots.txt 규칙 확인",
    }


def fetch_public_html(
    url: str,
    *,
    policy_confirmed: bool,
    respect_robots: bool = True,
    user_agent: str = DEFAULT_USER_AGENT,
    session: Session | None = None,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_HTML_BYTES,
) -> tuple[str, dict[str, Any]]:
    """정책 확인 후 공개 HTML 한 페이지를 제한적으로 가져옵니다."""
    _require_requests()
    if not policy_confirmed:
        raise ValueError(
            "이용약관·라이선스·수집 목적을 확인한 뒤 "
            "policy_confirmed=True로 명시하세요."
        )
    validate_public_http_url(url)
    client = session or build_http_session()

    robots_result = {
        "allowed": True,
        "status": "not_checked",
        "robots_url": _robots_url_for(url),
    }
    if respect_robots:
        robots_result = check_robots_permission(
            url,
            user_agent=user_agent,
            session=client,
            timeout=timeout,
        )
        if not robots_result["allowed"]:
            raise PermissionError(
                "robots.txt 규칙을 확인할 수 없거나 접근이 허용되지 않습니다: "
                f"{robots_result}"
            )

    response = client.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout,
        allow_redirects=False,
    )
    if 300 <= response.status_code < 400:
        location = response.headers.get("Location", "")
        raise RuntimeError(
            "페이지가 다른 주소로 리다이렉트했습니다. "
            f"대상과 정책을 다시 확인하세요: {redact_url(location)}"
        )

    response.raise_for_status()
    validate_public_http_url(response.url)

    content_type = response.headers.get("Content-Type", "").lower()
    if not (
        "text/html" in content_type
        or "application/xhtml+xml" in content_type
    ):
        raise ValueError(
            "HTML 문서가 아닌 응답입니다. "
            f"Content-Type={content_type!r}"
        )

    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > max_bytes:
        raise ValueError(
            f"응답 크기가 제한({max_bytes} bytes)을 초과합니다."
        )
    if len(response.content) > max_bytes:
        raise ValueError(
            f"응답 크기가 제한({max_bytes} bytes)을 초과합니다."
        )

    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    metadata = _response_metadata(
        response,
        requested_url=url,
    )
    metadata.update(
        {
            "robots_checked": bool(respect_robots),
            "robots_status": robots_result.get("status", ""),
            "policy_confirmed": True,
            "content_bytes": len(response.content),
        }
    )
    return response.text, metadata


def extract_title_and_links(
    html: str,
    *,
    base_url: str = "",
) -> tuple[str, pd.DataFrame]:
    """HTML에서 페이지 제목과 링크 텍스트·주소를 추출합니다."""
    if BeautifulSoup is None:
        raise ImportError("beautifulsoup4 패키지가 필요합니다.")

    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    rows = []
    for tag in soup.find_all("a"):
        text = tag.get_text(" ", strip=True)
        href = tag.get("href")
        if text or href:
            rows.append(
                {
                    "page_title": page_title,
                    "link_text": text,
                    "href": href or "",
                    "source_url": base_url,
                }
            )
    return page_title, pd.DataFrame(rows)


def save_json_snapshot(data: Any, path: str | Path) -> Path:
    """API 원본 JSON을 UTF-8 파일로 저장합니다."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return output_path


def save_text_snapshot(text: str, path: str | Path) -> Path:
    """원본 텍스트 또는 HTML을 UTF-8 파일로 저장합니다."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def sha256_file(path: str | Path) -> str:
    """저장된 파일의 SHA-256 해시를 계산합니다."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def summarize_external_dataframe(
    df: pd.DataFrame,
    *,
    data_name: str,
    provider: str,
    source_url: str,
    collection_method: str,
    data_reference_date: str = "",
) -> pd.DataFrame:
    """외부 DataFrame의 구조와 출처 메타데이터를 한 행으로 요약합니다."""
    return pd.DataFrame(
        [
            {
                "data_name": data_name,
                "provider": provider,
                "source_url": source_url,
                "collection_method": collection_method,
                "data_reference_date": data_reference_date,
                "collected_at_utc": utc_now_iso(),
                "rows": int(df.shape[0]),
                "columns": int(df.shape[1]),
                "column_list": ", ".join(map(str, df.columns)),
                "missing_values": int(df.isna().sum().sum()),
                "duplicated_rows": int(df.duplicated().sum()),
            }
        ]
    )


def merge_external_data(
    internal_df: pd.DataFrame,
    external_df: pd.DataFrame,
    *,
    on: str | list[str],
    how: str = "left",
    validate: str = "many_to_one",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """외부 데이터를 병합하고 행 수·미매칭을 검증합니다."""
    before_rows = len(internal_df)
    merged = internal_df.merge(
        external_df,
        on=on,
        how=how,
        validate=validate,
        indicator=True,
    )
    check = pd.DataFrame(
        [
            {
                "join_key": ", ".join(on) if isinstance(on, list) else on,
                "how": how,
                "validate": validate,
                "before_rows": before_rows,
                "after_rows": len(merged),
                "row_count_preserved": before_rows == len(merged),
                "left_only_count": int(
                    (merged["_merge"] == "left_only").sum()
                ),
                "both_count": int((merged["_merge"] == "both").sum()),
            }
        ]
    )
    return merged.drop(columns="_merge"), check


def create_external_data_plan() -> pd.DataFrame:
    """내부 질문과 연결 가능한 외부 데이터 후보를 정리합니다."""
    return pd.DataFrame(
        {
            "internal_question": [
                "특정 월 매출 변동과 함께 확인할 외부 요인은 무엇인가?",
                "특정 지역 매출 차이와 함께 볼 지역 지표는 무엇인가?",
                "관광 앱에 필요한 공식 데이터는 무엇인가?",
                "특정 키워드 검색 결과가 시간에 따라 어떻게 달라지는가?",
            ],
            "external_data_candidate": [
                "공휴일, 날씨, 행사, 검색 결과",
                "지역 인구, 관광지, 상권 정보",
                "관광지, 숙박, 음식점, 위치 데이터",
                "공식 검색 API 결과",
            ],
            "connection_key": [
                "날짜 또는 월",
                "행정구역 코드",
                "지역 코드, 콘텐츠 유형, 좌표",
                "키워드, 수집 시각",
            ],
            "interpretation_caution": [
                "함께 움직여도 원인으로 단정하지 않기",
                "지역 단위와 표본 차이 확인",
                "이용조건과 기준일 확인",
                "검색 결과를 전체 수요나 여론으로 일반화하지 않기",
            ],
        }
    )


def create_collection_method_summary() -> pd.DataFrame:
    """수집 방법별 우선순위와 검증 항목을 요약합니다."""
    return pd.DataFrame(
        {
            "method": ["공식 파일", "공식 API", "제한적 크롤링"],
            "priority": [1, 2, 3],
            "strength": [
                "원본 보존과 재현이 쉬움",
                "최신 데이터와 자동 수집에 유리",
                "API가 없는 공개 HTML 일부를 확인 가능",
            ],
            "required_checks": [
                "기준일, 인코딩, 라이선스",
                "공식 문서, 인증, 제한, 오류 처리",
                "이용약관, robots.txt, 저작권, 개인정보, 요청 빈도",
            ],
        }
    )


def create_external_integration_plan() -> pd.DataFrame:
    """외부 데이터와 내부 데이터의 연결 기준을 정리합니다."""
    return pd.DataFrame(
        {
            "connection_key": [
                "날짜",
                "지역",
                "상품 카테고리",
                "키워드",
                "위치",
            ],
            "normalization": [
                "날짜형·시간대·일/월 단위 통일",
                "행정구역 코드와 명칭 매핑",
                "내부·외부 분류 체계 매핑표 작성",
                "검색어 정의와 수집 시각 기록",
                "좌표계와 거리 단위 확인",
            ],
            "validation": [
                "기간 겹침과 중복 확인",
                "미매칭 지역과 경계 변경 확인",
                "일대다 관계와 행 증가 확인",
                "대표성·정렬 방식·페이지 범위 확인",
                "좌표 오류와 누락 확인",
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
    """출처·수집 조건·파일 무결성을 기록할 로그 템플릿을 생성합니다."""
    columns = [
        "data_name",
        "provider",
        "source_url",
        "collection_method",
        "data_reference_date",
        "collected_at_utc",
        "license_or_terms",
        "robots_checked",
        "request_scope",
        "raw_path",
        "processed_path",
        "sha256",
        "row_count",
        "notes",
    ]
    return pd.DataFrame(
        [
            {
                "data_name": "",
                "provider": "",
                "source_url": "",
                "collection_method": "",
                "data_reference_date": "",
                "collected_at_utc": "",
                "license_or_terms": "",
                "robots_checked": "",
                "request_scope": "",
                "raw_path": "",
                "processed_path": "",
                "sha256": "",
                "row_count": "",
                "notes": "",
            }
        ],
        columns=columns,
    )


def build_external_data_summary(
    data_plan: pd.DataFrame,
    method_summary: pd.DataFrame,
    integration_plan: pd.DataFrame,
    checklist: pd.DataFrame,
) -> str:
    """외부 데이터 수집 준비 결과를 Markdown으로 정리합니다."""
    return f"""# Chapter 13 외부 데이터 수집 준비 요약

## 1. 분석 질문과 외부 데이터 후보

```text
{data_plan.to_string(index=False)}
```

## 2. 수집 방법 우선순위

```text
{method_summary.to_string(index=False)}
```

## 3. 내부 데이터 연결 기준

```text
{integration_plan.to_string(index=False)}
```

## 4. 수집 전 체크리스트

```text
{checklist.to_string(index=False)}
```

## 5. 핵심 원칙

- 공식 파일과 공식 API를 먼저 확인합니다.
- API Key와 인증 헤더는 출력하거나 저장소에 커밋하지 않습니다.
- timeout, 오류 처리, 제한적 재시도, 원본 응답 보관을 포함합니다.
- robots.txt와 이용약관은 별도로 확인합니다.
- robots.txt는 접근 권한이나 이용허락을 의미하지 않습니다.
- 외부 데이터의 출처, 기준일, UTC 수집 시각, 요청 범위, 파일 해시를 기록합니다.
- 검색 결과나 동시 변화를 전체 수요 또는 인과관계로 단정하지 않습니다.
"""


def save_external_data_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    """13장 외부 데이터 수집 준비 결과물을 저장합니다."""
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
        value = outputs[key]
        if not isinstance(value, pd.DataFrame):
            raise TypeError(f"{key} 결과는 DataFrame이어야 합니다.")
        path = output_dir / filename
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
    """네트워크 호출 없이 13장 실습 폴더·계획·체크리스트를 생성합니다."""
    paths = ensure_external_dirs(base_dir)
    output_report_dir = (
        Path(report_dir)
        if report_dir is not None
        else paths["reports"]
    )
    output_report_dir.mkdir(parents=True, exist_ok=True)

    base_path = Path(base_dir).resolve()
    env_status = load_env_status(base_path / ".env")
    data_plan = create_external_data_plan()
    method_summary = create_collection_method_summary()
    integration_plan = create_external_integration_plan()
    checklist = create_external_data_checklist()
    external_data_log = create_external_data_log()
    summary_text = build_external_data_summary(
        data_plan,
        method_summary,
        integration_plan,
        checklist,
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
    output_paths = save_external_data_outputs(
        outputs,
        output_report_dir,
    )

    return {
        "paths": paths,
        "report_dir": output_report_dir,
        "outputs": outputs,
        "output_paths": output_paths,
    }
