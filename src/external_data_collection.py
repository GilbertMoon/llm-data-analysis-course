"""Chapter 13 utilities for safe, reproducible external-data collection.

The default workflow performs no network requests. Network helpers are provided for
approved exercises only and are designed around these rules:

1. prefer official files, then official APIs, then limited public-HTML collection,
2. verify current documentation, terms, licence and request limits before execution,
3. never expose credentials in logs or saved metadata,
4. preserve raw snapshots and metadata separately from processed outputs,
5. validate data quality and merge cardinality before interpretation,
6. treat search/crawling results as samples, not population or causal evidence.
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
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse
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
    "LLMDataAnalysisCourseBot/1.0 "
    "(+https://github.com/GilbertMoon/llm-data-analysis-course)"
)
DEFAULT_TIMEOUT = (3.05, 20)
MAX_HTML_BYTES = 2_000_000
MAX_JSON_BYTES = 3_000_000
ROBOTS_MAX_BYTES = 500 * 1024
MAX_ROBOTS_REDIRECTS = 5

NAVER_BLOG_SEARCH_URL = "https://openapi.naver.com/v1/search/blog.json"
NAVER_BLOG_DOCS_URL = "https://developers.naver.com/docs/serviceapi/search/blog/blog.md"

PLACEHOLDER_VALUE_PARTS = {
    "your_",
    "replace_me",
    "change_me",
    "example",
    "placeholder",
}

SECRET_NAME_PARTS = {
    "authorization",
    "api_key",
    "apikey",
    "client_secret",
    "servicekey",
    "service_key",
    "secret",
    "token",
    "credential",
    "password",
}

EXTERNAL_DATA_CHECK_ITEMS = [
    "분석 질문에 필요한 최소 외부 데이터인가?",
    "공식 다운로드 파일을 먼저 확인했는가?",
    "공식 API를 크롤링보다 우선 확인했는가?",
    "제공기관·공식 URL·데이터 기준일을 기록했는가?",
    "라이선스·이용약관·출처표시 조건을 현재 문서에서 확인했는가?",
    "데이터 기준일과 실제 UTC 수집 시각을 구분했는가?",
    "API Key를 .env 또는 승인된 Secret 저장소에 보관했는가?",
    "Key·Secret·인증 헤더가 화면·로그·Git에 남지 않는가?",
    "요청 URL·HTTP method·parameter·인증 위치를 공식 문서에서 확인했는가?",
    "연결·읽기 timeout과 HTTP 오류 처리를 포함했는가?",
    "재시도 대상이 429·일시적 5xx 등으로 제한되어 있는가?",
    "retry 설정과 rate limit 관리를 같은 것으로 혼동하지 않는가?",
    "Retry-After와 서비스별 rate limit을 확인했는가?",
    "pagination 범위와 종료 조건을 공식 문서에서 확인했는가?",
    "페이지를 읽는 동안 원본이 바뀌어도 같은 snapshot으로 보이지 않는가?",
    "JSON 응답 크기를 Content-Length와 실제 수신 바이트 모두로 제한했는가?",
    "HTTP 200과 JSON 파싱 성공, API 업무 성공을 각각 구분했는가?",
    "URL validator가 완전한 SSRF 차단이 아니라 defence-in-depth임을 이해하는가?",
    "raw·processed·metadata를 서로 다른 경로에 저장하는가?",
    "raw snapshot을 조용히 덮어쓰지 않는가?",
    "raw snapshot의 보유기간·접근범위·재배포 가능 여부를 검토했는가?",
    "SHA-256은 무결성 확인이며 데이터 타당성 보증이 아님을 이해하는가?",
    "행·열·dtype·결측·중복·파싱 실패를 확인했는가?",
    "내부 데이터와 연결할 키·시간대·분석 단위가 명확한가?",
    "외부 오른쪽 키 중복과 병합 전후 행 수를 확인했는가?",
    "크롤링 전 robots.txt와 이용약관을 각각 확인했는가?",
    "robots.txt 허용을 접근 권한·저작권 허가로 오해하지 않는가?",
    "로그인·CAPTCHA·paywall·접근 제한을 우회하지 않는가?",
    "개인정보·민감정보·저작물 원문을 불필요하게 저장하지 않는가?",
    "검색 결과를 전체 시장·여론으로 일반화하지 않는가?",
    "외부 변수의 동시 변화를 인과관계로 단정하지 않는가?",
    "수집한 외부 HTML·검색 텍스트를 LLM context에 그대로 신뢰하지 않는가?",
    "외부 문서 안의 문장이 지시문처럼 실행되지 않도록 최소 권한·사람 승인을 거치는가?",
    "LLM이 만든 API 코드를 현재 공식 문서와 사람이 다시 비교했는가?",
]


def utc_now_iso() -> str:
    """Return current UTC time in ISO-8601 format without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_timestamp_slug() -> str:
    """Return a filesystem-friendly UTC timestamp for immutable snapshots."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_external_dirs(base_dir: str | Path = ".") -> dict[str, Path]:
    """Create raw/processed/metadata/report directories for Chapter 13."""
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


def _looks_like_placeholder(value: str | None) -> bool:
    if value is None:
        return False
    normalized = value.strip().lower()
    if not normalized:
        return False
    return any(part in normalized for part in PLACEHOLDER_VALUE_PARTS)


def load_env_status(env_path: str | Path | None = None) -> pd.DataFrame:
    """Return only secret configuration state; never return secret values."""
    if load_dotenv is not None:
        load_dotenv(dotenv_path=env_path, override=False)

    key_names = [
        "PUBLIC_DATA_API_KEY",
        "NAVER_CLIENT_ID",
        "NAVER_CLIENT_SECRET",
    ]
    rows = []
    for key in key_names:
        value = os.getenv(key)
        if not value:
            state = "MISSING"
            configured = False
        elif _looks_like_placeholder(value):
            state = "PLACEHOLDER"
            configured = False
        else:
            state = "CONFIGURED"
            configured = True
        rows.append(
            {
                "env_key": key,
                "state": state,
                "configured": configured,
                "value_exposed": False,
            }
        )
    return pd.DataFrame(rows)


def _require_requests() -> None:
    if requests is None or HTTPAdapter is None or Retry is None:
        raise ImportError(
            "requests 패키지가 필요합니다. "
            "프로젝트 requirements.txt를 확인한 뒤 승인된 환경에 설치하세요."
        )


def build_http_session(
    *,
    total_retries: int = 3,
    backoff_factor: float = 0.5,
) -> Session:
    """Create a GET-only session with limited transient-error retries."""
    _require_requests()
    if total_retries < 0 or total_retries > 5:
        raise ValueError("교육용 예제의 total_retries는 0~5 범위로 제한합니다.")
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
    """Reject non-HTTP(S), credential-bearing, local and non-global addresses.

    This is an educational defence-in-depth check, not a complete SSRF security
    boundary. DNS can change between validation and connection.
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
    """Mask values whose key names look credential-like."""
    if not values:
        return {}
    return {
        str(key): "***REDACTED***" if _is_secret_name(str(key)) else value
        for key, value in values.items()
    }


def redact_url(url: str) -> str:
    """Mask secret-like query parameters in a URL before logging."""
    parsed = urlparse(url)
    redacted_query = urlencode(
        [
            (key, "***REDACTED***" if _is_secret_name(key) else value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
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
            redact_mapping(params), ensure_ascii=False, default=str
        ),
    }


def request_json_api(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    session: Session | None = None,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
    max_bytes: int = MAX_JSON_BYTES,
) -> tuple[Any, dict[str, Any]]:
    """Call an approved public JSON API and return payload + redacted metadata."""
    _require_requests()
    validate_public_http_url(url)
    client = session or build_http_session()
    response = client.get(
        url,
        params=dict(params or {}),
        headers=dict(headers or {}),
        timeout=timeout,
        allow_redirects=False,
        stream=True,
    )
    if 300 <= response.status_code < 400:
        location = response.headers.get("Location", "")
        raise RuntimeError(
            "API가 리다이렉트했습니다. 자동 추적하지 말고 공식 문서를 다시 확인하세요: "
            f"{redact_url(location)}"
        )
    response.raise_for_status()
    validate_public_http_url(response.url)

    content_type = response.headers.get("Content-Type", "")
    content_type_json_like = "json" in content_type.lower()
    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            declared_bytes = int(content_length)
        except ValueError:
            declared_bytes = None
        if declared_bytes is not None and declared_bytes > max_bytes:
            raise ValueError(
                f"JSON 응답 크기(Content-Length={declared_bytes} bytes)가 "
                f"제한({max_bytes} bytes)을 초과합니다."
            )

    body = bytearray()
    try:
        for chunk in response.iter_content(chunk_size=64 * 1024):
            if not chunk:
                continue
            body.extend(chunk)
            if len(body) > max_bytes:
                raise ValueError(
                    f"JSON 응답 실제 수신 크기가 제한({max_bytes} bytes)을 초과합니다."
                )
    finally:
        response.close()
    received_bytes = len(body)

    try:
        payload = json.loads(bytes(body))
    except ValueError as exc:
        raise ValueError(
            "JSON 응답을 해석할 수 없습니다. "
            f"status={response.status_code}, Content-Type={content_type!r}. "
            "민감정보를 제거한 뒤 공식 오류 구조를 확인하세요."
        ) from exc

    metadata = _response_metadata(response, requested_url=url, params=params)
    metadata["response_top_level_type"] = type(payload).__name__
    metadata["content_type_json_like"] = content_type_json_like
    metadata["response_bytes"] = received_bytes
    return payload, metadata


def _validate_naver_search_params(query: str, display: int, start: int, sort: str) -> None:
    if not query or not query.strip():
        raise ValueError("검색어 query는 비어 있을 수 없습니다.")
    if not 1 <= display <= 100:
        raise ValueError("display는 현재 공식 문서 기준 1~100 범위여야 합니다.")
    if not 1 <= start <= 1000:
        raise ValueError("start는 현재 공식 문서 기준 1~1000 범위여야 합니다.")
    if sort not in {"sim", "date"}:
        raise ValueError("sort는 현재 공식 문서 기준 'sim' 또는 'date'여야 합니다.")


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
    """Call Naver Blog Search after the caller has reviewed current official docs."""
    _validate_naver_search_params(query, display, start, sort)
    client_id = client_id or os.getenv("NAVER_CLIENT_ID")
    client_secret = client_secret or os.getenv("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")
    if _looks_like_placeholder(client_id) or _looks_like_placeholder(client_secret):
        raise ValueError("네이버 인증정보가 placeholder 상태입니다. 실제 발급값을 안전하게 설정하세요.")

    headers = {
        "X-Naver-Client-Id": client_id,
        "X-Naver-Client-Secret": client_secret,
        "User-Agent": DEFAULT_USER_AGENT,
    }
    params = {"query": query, "display": display, "start": start, "sort": sort}
    payload, metadata = request_json_api(
        NAVER_BLOG_SEARCH_URL,
        params=params,
        headers=headers,
        session=session,
    )
    if not isinstance(payload, dict):
        raise TypeError("네이버 검색 API 응답이 JSON 객체가 아닙니다.")
    if "items" not in payload:
        raise ValueError("네이버 검색 응답에 items가 없습니다. 현재 공식 응답 구조를 확인하세요.")
    metadata.update(
        {
            "provider": "Naver Search API",
            "official_docs_url": NAVER_BLOG_DOCS_URL,
            "query": query,
            "policy_recheck_required": True,
        }
    )
    return payload, metadata


def clean_html_text(text: Any) -> str:
    """Remove search-result emphasis tags without keeping raw HTML markup."""
    if pd.isna(text):
        return ""
    value = str(text)
    if BeautifulSoup is None:
        return value.replace("<b>", "").replace("</b>", "")
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def naver_blog_items_to_dataframe(result: dict[str, Any]) -> pd.DataFrame:
    """Convert Naver `items` to a minimal analysis table."""
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
        original_missing = int(df["postdate"].isna().sum())
        df["postdate"] = pd.to_datetime(
            df["postdate"], format="%Y%m%d", errors="coerce"
        )
        new_missing = int(df["postdate"].isna().sum())
        if new_missing > original_missing:
            raise ValueError(
                "postdate 날짜 변환에 새 실패가 발생했습니다: "
                f"{new_missing - original_missing}행"
            )
    return df


def _robots_url_for(url: str) -> str:
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))


def _fetch_robots_with_safe_redirects(
    robots_url: str,
    *,
    user_agent: str,
    session: Session,
    timeout: tuple[float, float],
) -> Response:
    current_url = robots_url
    for redirect_count in range(MAX_ROBOTS_REDIRECTS + 1):
        validate_public_http_url(current_url)
        response = session.get(
            current_url,
            headers={"User-Agent": user_agent},
            timeout=timeout,
            allow_redirects=False,
        )
        if not (300 <= response.status_code < 400):
            return response
        if redirect_count >= MAX_ROBOTS_REDIRECTS:
            raise RuntimeError("robots.txt redirect가 교육용 제한 5회를 초과했습니다.")
        location = response.headers.get("Location", "")
        if not location:
            raise RuntimeError("robots.txt redirect 응답에 Location이 없습니다.")
        current_url = urljoin(current_url, location)
    raise RuntimeError("robots.txt redirect 처리에 실패했습니다.")


def check_robots_permission(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    session: Session | None = None,
    timeout: tuple[float, float] = DEFAULT_TIMEOUT,
) -> dict[str, Any]:
    """Check robots.txt separately from legal/contractual permission."""
    _require_requests()
    validate_public_http_url(url)
    robots_url = _robots_url_for(url)
    client = session or build_http_session()
    try:
        response = _fetch_robots_with_safe_redirects(
            robots_url,
            user_agent=user_agent,
            session=client,
            timeout=timeout,
        )
    except (requests.RequestException, ValueError, RuntimeError) as exc:
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
            "reason": "robots.txt unavailable; terms/licence review still required",
        }
    if response.status_code >= 500:
        return {
            "allowed": False,
            "robots_url": robots_url,
            "status": "unreachable",
            "status_code": int(response.status_code),
            "reason": "server error; conservative disallow",
        }

    response.raise_for_status()
    robots_bytes = response.content[:ROBOTS_MAX_BYTES]
    robots_text = robots_bytes.decode(response.encoding or "utf-8", errors="replace")
    parser = RobotFileParser()
    parser.set_url(robots_url)
    parser.parse(robots_text.splitlines())
    allowed = parser.can_fetch(user_agent, url)
    return {
        "allowed": bool(allowed),
        "robots_url": robots_url,
        "status": "parsed",
        "status_code": int(response.status_code),
        "reason": "robots.txt parsed; this is not legal/contract permission",
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
    """Fetch one approved public HTML page without redirect following."""
    _require_requests()
    if not policy_confirmed:
        raise ValueError(
            "이용약관·라이선스·저작권·개인정보·수집 목적을 확인한 뒤 "
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
            url, user_agent=user_agent, session=client, timeout=timeout
        )
        if not robots_result["allowed"]:
            raise PermissionError(
                "robots.txt를 확인할 수 없거나 접근이 허용되지 않습니다. "
                "접근 제한을 우회하지 마세요."
            )

    response = client.get(
        url,
        headers={"User-Agent": user_agent},
        timeout=timeout,
        allow_redirects=False,
    )
    if 300 <= response.status_code < 400:
        raise RuntimeError(
            "HTML 페이지가 리다이렉트했습니다. 자동 추적하지 말고 대상·정책을 다시 확인하세요."
        )
    response.raise_for_status()
    validate_public_http_url(response.url)

    content_type = response.headers.get("Content-Type", "").lower()
    if "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        raise ValueError(f"HTML 문서가 아닌 응답입니다. Content-Type={content_type!r}")

    content_length = response.headers.get("Content-Length")
    if content_length:
        try:
            if int(content_length) > max_bytes:
                raise ValueError(f"응답 크기가 제한({max_bytes} bytes)을 초과합니다.")
        except ValueError as exc:
            if "초과" in str(exc):
                raise
    if len(response.content) > max_bytes:
        raise ValueError(f"응답 크기가 제한({max_bytes} bytes)을 초과합니다.")

    response.encoding = response.encoding or response.apparent_encoding or "utf-8"
    metadata = _response_metadata(response, requested_url=url)
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
    """Extract only page title, link text and HTTP(S) link targets."""
    if BeautifulSoup is None:
        raise ImportError("beautifulsoup4 패키지가 필요합니다.")
    soup = BeautifulSoup(html, "html.parser")
    page_title = soup.title.get_text(" ", strip=True) if soup.title else ""
    rows: list[dict[str, str]] = []
    for tag in soup.find_all("a"):
        text = tag.get_text(" ", strip=True)
        raw_href = (tag.get("href") or "").strip()
        if not raw_href:
            continue
        resolved = urljoin(base_url, raw_href) if base_url else raw_href
        scheme = urlparse(resolved).scheme.lower()
        if scheme not in {"http", "https"}:
            continue
        rows.append(
            {
                "page_title": page_title,
                "link_text": text,
                "href": resolved,
                "source_url": base_url,
            }
        )
    return page_title, pd.DataFrame(rows)


def versioned_snapshot_path(directory: str | Path, stem: str, suffix: str) -> Path:
    """Create a timestamped path so raw collection snapshots are not overwritten."""
    output_dir = Path(directory)
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return output_dir / f"{stem}_{utc_timestamp_slug()}{clean_suffix}"


def _assert_snapshot_write_allowed(path: Path, *, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"기존 snapshot을 덮어쓰지 않습니다: {path}. "
            "새 timestamp 경로를 사용하세요."
        )


def save_json_snapshot(data: Any, path: str | Path, *, overwrite: bool = False) -> Path:
    """Save raw JSON without silently overwriting an existing snapshot."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _assert_snapshot_write_allowed(output_path, overwrite=overwrite)
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    return output_path


def save_text_snapshot(text: str, path: str | Path, *, overwrite: bool = False) -> Path:
    """Save raw text/HTML without silently overwriting an existing snapshot."""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _assert_snapshot_write_allowed(output_path, overwrite=overwrite)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def sha256_file(path: str | Path) -> str:
    """Return SHA-256 for integrity/change detection, not semantic validity."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_collection_metadata(
    *,
    provider: str,
    source_url: str,
    collection_method: str,
    data_reference_date: str,
    request_scope: str,
    license_or_terms: str,
    raw_path: str | Path,
    processed_path: str | Path | None = None,
    policy_confirmed: bool | str = False,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build redacted provenance metadata for a collected snapshot."""
    raw_file = Path(raw_path)
    if not raw_file.exists():
        raise FileNotFoundError(f"raw snapshot이 없습니다: {raw_file}")
    metadata: dict[str, Any] = {
        "provider": provider,
        "source_url": redact_url(source_url),
        "collection_method": collection_method,
        "data_reference_date": data_reference_date,
        "collected_at_utc": utc_now_iso(),
        "request_scope": request_scope,
        "license_or_terms": license_or_terms,
        "policy_confirmed": policy_confirmed,
        "raw_path": str(raw_file),
        "processed_path": str(processed_path or ""),
        "sha256": sha256_file(raw_file),
    }
    if extra:
        for key, value in redact_mapping(extra).items():
            metadata[key] = value
    return metadata


def save_metadata_snapshot(
    metadata: Mapping[str, Any],
    path: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Save provenance metadata separately from raw and processed data."""
    return save_json_snapshot(dict(metadata), path, overwrite=overwrite)


def summarize_external_dataframe(
    df: pd.DataFrame,
    *,
    data_name: str,
    provider: str,
    source_url: str,
    collection_method: str,
    data_reference_date: str = "",
) -> pd.DataFrame:
    """Summarize structure/provenance without copying raw record values."""
    return pd.DataFrame(
        [
            {
                "data_name": data_name,
                "provider": provider,
                "source_url": redact_url(source_url),
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


def validate_external_dataframe(
    df: pd.DataFrame,
    *,
    key_columns: str | list[str] | None = None,
    date_columns: str | list[str] | None = None,
) -> pd.DataFrame:
    """Create basic quality evidence before an external-data merge."""
    keys = [key_columns] if isinstance(key_columns, str) else list(key_columns or [])
    dates = [date_columns] if isinstance(date_columns, str) else list(date_columns or [])
    rows: list[dict[str, Any]] = [
        {
            "check_item": "rows_positive",
            "value": len(df),
            "status": "PASS" if len(df) > 0 else "WARN",
        },
        {
            "check_item": "duplicated_rows",
            "value": int(df.duplicated().sum()),
            "status": "PASS",
        },
        {
            "check_item": "missing_values",
            "value": int(df.isna().sum().sum()),
            "status": "REVIEW",
        },
    ]
    for key in keys:
        if key not in df.columns:
            rows.append(
                {"check_item": f"key_exists:{key}", "value": False, "status": "FAIL"}
            )
            continue
        duplicate_count = int(df.loc[df[key].notna(), key].duplicated().sum())
        missing_count = int(df[key].isna().sum())
        rows.extend(
            [
                {
                    "check_item": f"key_missing:{key}",
                    "value": missing_count,
                    "status": "PASS" if missing_count == 0 else "FAIL",
                },
                {
                    "check_item": f"key_duplicate:{key}",
                    "value": duplicate_count,
                    "status": "PASS" if duplicate_count == 0 else "FAIL",
                },
            ]
        )
    for column in dates:
        if column not in df.columns:
            rows.append(
                {
                    "check_item": f"date_exists:{column}",
                    "value": False,
                    "status": "FAIL",
                }
            )
            continue
        original_missing = int(df[column].isna().sum())
        parsed = pd.to_datetime(df[column], errors="coerce")
        new_missing = int(parsed.isna().sum())
        failure_count = max(0, new_missing - original_missing)
        rows.append(
            {
                "check_item": f"date_parse_failure:{column}",
                "value": failure_count,
                "status": "PASS" if failure_count == 0 else "FAIL",
            }
        )
    return pd.DataFrame(rows)


def merge_external_data(
    internal_df: pd.DataFrame,
    external_df: pd.DataFrame,
    *,
    on: str | list[str],
    how: str = "left",
    validate: str = "many_to_one",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Merge external data with explicit key/cardinality/row-count evidence."""
    keys = [on] if isinstance(on, str) else list(on)
    missing_internal = [key for key in keys if key not in internal_df.columns]
    missing_external = [key for key in keys if key not in external_df.columns]
    if missing_internal or missing_external:
        raise KeyError(
            f"병합 키 누락: internal={missing_internal}, external={missing_external}"
        )

    right_duplicate_count = int(
        external_df.loc[external_df[keys].notna().all(axis=1), keys]
        .duplicated()
        .sum()
    )
    if validate in {"many_to_one", "one_to_one"} and right_duplicate_count:
        raise ValueError(
            "외부 데이터 오른쪽 키가 고유하지 않습니다: "
            f"keys={keys}, duplicates={right_duplicate_count}"
        )

    before_rows = len(internal_df)
    merged = internal_df.merge(
        external_df,
        on=keys,
        how=how,
        validate=validate,
        indicator=True,
    )
    after_rows = len(merged)
    left_only_count = int((merged["_merge"] == "left_only").sum())
    both_count = int((merged["_merge"] == "both").sum())
    row_count_preserved = before_rows == after_rows
    if how == "left" and not row_count_preserved:
        raise ValueError(
            f"left merge 행 수가 변했습니다: before={before_rows}, after={after_rows}"
        )

    check = pd.DataFrame(
        [
            {
                "join_key": ", ".join(keys),
                "how": how,
                "validate": validate,
                "right_key_duplicate_count": right_duplicate_count,
                "before_rows": before_rows,
                "after_rows": after_rows,
                "row_count_preserved": row_count_preserved,
                "left_only_count": left_only_count,
                "both_count": both_count,
                "status": "WARN" if left_only_count else "PASS",
            }
        ]
    )
    return merged.drop(columns="_merge"), check


def create_external_data_plan() -> pd.DataFrame:
    """Create a plan that must be completed before any network execution."""
    return pd.DataFrame(
        [
            {
                "analysis_question": "특정 월 완료 주문 금액 변동과 함께 볼 외부 요인은?",
                "external_data_needed": "공휴일·날씨·행사 중 질문에 필요한 최소 데이터",
                "provider": "",
                "source_type": "official_file / official_api / limited_html",
                "official_url": "",
                "reference_date": "",
                "collection_range": "",
                "join_key": "날짜 또는 월",
                "license_or_terms": "",
                "collection_enabled": False,
                "interpretation_caution": "동시 변화는 원인 증명이 아님",
            },
            {
                "analysis_question": "특정 지역 완료 주문 금액 차이와 함께 볼 지역 지표는?",
                "external_data_needed": "인구·관광·지역 통계 중 필요한 지표",
                "provider": "",
                "source_type": "official_file / official_api",
                "official_url": "",
                "reference_date": "",
                "collection_range": "",
                "join_key": "행정구역 코드",
                "license_or_terms": "",
                "collection_enabled": False,
                "interpretation_caution": "지역 단위·기준일·표본 차이 확인",
            },
            {
                "analysis_question": "특정 검색어 결과가 시간에 따라 어떻게 달라지는가?",
                "external_data_needed": "공식 검색 API의 제한된 결과",
                "provider": "Naver Search API 등",
                "source_type": "official_api",
                "official_url": NAVER_BLOG_DOCS_URL,
                "reference_date": "",
                "collection_range": "query / page / collection time",
                "join_key": "검색어·수집 시각",
                "license_or_terms": "현재 공식 정책 재확인",
                "collection_enabled": False,
                "interpretation_caution": "검색 결과는 전체 시장·여론이 아님",
            },
        ]
    )


def create_collection_method_summary() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "method": ["공식 파일", "공식 API", "제한적 공개 HTML"],
            "priority": [1, 2, 3],
            "strength": [
                "원본 보존·재현이 쉬움",
                "최신성·자동화에 유리",
                "API가 없는 공개 페이지의 최소 정보 확인",
            ],
            "required_checks": [
                "제공기관·기준일·인코딩·라이선스·hash",
                "공식 문서·method·인증·rate limit·pagination·오류 구조",
                "이용약관·robots.txt·저작권·개인정보·요청량",
            ],
        }
    )


def create_external_integration_plan() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "connection_key": ["날짜/월", "지역", "상품 카테고리", "키워드", "위치"],
            "normalization": [
                "날짜형·시간대·일/월 단위 통일",
                "공식 행정구역 코드와 명칭 매핑",
                "내부·외부 분류 체계 매핑표",
                "검색어 정의·정렬·page·수집 UTC 기록",
                "좌표계·위도/경도·거리 단위 확인",
            ],
            "validation": [
                "기간 겹침·키 중복·월 누락 확인",
                "미매칭 지역·경계 변경 확인",
                "오른쪽 키 고유성·many_to_one 확인",
                "대표성·페이지 범위·검색 정책 확인",
                "좌표 오류·누락·범위 확인",
            ],
        }
    )


def create_external_data_checklist() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "check_item": EXTERNAL_DATA_CHECK_ITEMS,
            "status": ["REVIEW"] * len(EXTERNAL_DATA_CHECK_ITEMS),
            "memo": [""] * len(EXTERNAL_DATA_CHECK_ITEMS),
        }
    )


def create_external_data_log() -> pd.DataFrame:
    columns = [
        "execution_status",
        "data_name",
        "provider",
        "source_url",
        "collection_method",
        "data_reference_date",
        "collected_at_utc",
        "license_or_terms",
        "robots_status",
        "request_scope",
        "query",
        "page",
        "page_size",
        "sort",
        "request_count",
        "page_count",
        "first_request_at",
        "last_request_at",
        "retry_after_seen",
        "retry_count",
        "stop_reason",
        "raw_path",
        "processed_path",
        "metadata_path",
        "sha256",
        "row_count",
        "column_count",
        "quality_status",
        "notes",
    ]
    row = {column: "" for column in columns}
    row["execution_status"] = "NOT_EXECUTED"
    row["quality_status"] = "NOT_REVIEWED"
    return pd.DataFrame([row], columns=columns)


def create_metadata_template() -> pd.DataFrame:
    """Return a provenance/retention metadata template."""
    return pd.DataFrame(
        [
            {
                "provider": "",
                "source_url": "",
                "data_reference_date": "",
                "collected_at_utc": "",
                "request_scope": "",
                "license_or_terms": "",
                "raw_path": "",
                "processed_path": "",
                "sha256": "",
                "row_count": "",
                "column_count": "",
                "retention_period": "",
                "access_scope": "",
                "redistribution_allowed": "",
                "deletion_or_expiry": "",
                "sensitive_content_reviewed": False,
            }
        ]
    )


def create_api_code_review_checklist() -> pd.DataFrame:
    items = [
        "현재 공식 URL과 HTTP method인가?",
        "인증 위치가 header/query 중 공식 문서와 일치하는가?",
        "parameter 이름·필수 여부·범위가 현재 문서와 일치하는가?",
        "응답 JSON/XML path와 오류 구조를 확인했는가?",
        "connect/read timeout이 있는가?",
        "retry가 429·일시적 5xx 등에 제한되는가?",
        "retry 설정만 있고 rate limit 관리는 빠져 있지 않은가?",
        "Retry-After와 rate limit을 존중하는가?",
        "pagination 종료 조건과 최대 범위를 검토했는가?",
        "pagination 도중 원본이 바뀌어도 하나의 snapshot처럼 다루지 않는가?",
        "JSON 응답 크기를 Content-Length와 실제 수신 바이트 모두로 제한하는가?",
        "raw/processed/metadata를 분리하는가?",
        "Key·Secret·내부 URL·PII를 출력하지 않는가?",
        "로그인·접근 제한·CAPTCHA 우회 코드를 만들지 않는가?",
        "LLM이 제안한 값이 아니라 공식 문서를 사람이 최종 확인했는가?",
    ]
    return pd.DataFrame(
        {
            "check_item": items,
            "status": ["REVIEW"] * len(items),
            "evidence": [""] * len(items),
        }
    )


def create_network_execution_gate() -> pd.DataFrame:
    """Document the safe default: no network collection is enabled."""
    return pd.DataFrame(
        [
            {"flag": "RUN_PUBLIC_API", "default": False, "status": "SAFE_DEFAULT"},
            {"flag": "RUN_NAVER_API", "default": False, "status": "SAFE_DEFAULT"},
            {
                "flag": "RUN_CRAWLING_EXAMPLE",
                "default": False,
                "status": "SAFE_DEFAULT",
            },
            {"flag": "POLICY_CONFIRMED", "default": False, "status": "SAFE_DEFAULT"},
        ]
    )


def build_external_data_summary(
    data_plan: pd.DataFrame,
    method_summary: pd.DataFrame,
    integration_plan: pd.DataFrame,
    checklist: pd.DataFrame,
    network_gate: pd.DataFrame,
) -> str:
    return f"""# Chapter 13 외부 데이터 수집 준비 요약

## 1. 분석 질문과 외부 데이터 계획
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

## 4. 네트워크 실행 기본 상태
```text
{network_gate.to_string(index=False)}
```

## 5. 수집 전 체크리스트
```text
{checklist.to_string(index=False)}
```

## 핵심 원칙
- 공식 파일 → 공식 API → 제한적 공개 HTML 순으로 검토합니다.
- 네트워크 실행은 기본 비활성화이며 현재 공식 문서·정책 확인 후에만 명시적으로 활성화합니다.
- API Key·Secret은 화면·로그·Git에 남기지 않습니다.
- raw snapshot은 덮어쓰지 않고 processed와 metadata를 분리합니다.
- 데이터 기준일과 UTC 수집 시각을 구분하고 SHA-256을 기록합니다.
- 외부 오른쪽 키 고유성, 병합 전후 행 수, left_only를 확인합니다.
- 검색 결과·상관관계를 전체 시장·여론·인과관계로 과장하지 않습니다.
"""


def save_external_data_outputs(
    outputs: dict[str, pd.DataFrame | str],
    report_dir: str | Path = "reports",
) -> dict[str, Path]:
    output_dir = Path(report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    file_map = {
        "data_plan": "ch13_external_data_plan.csv",
        "method_summary": "ch13_collection_method_summary.csv",
        "integration_plan": "ch13_external_integration_plan.csv",
        "checklist": "ch13_external_data_checklist.csv",
        "external_data_log": "ch13_external_data_log.csv",
        "env_status": "ch13_env_key_status.csv",
        "metadata_template": "ch13_collection_metadata_template.csv",
        "api_code_review": "ch13_api_code_review_checklist.csv",
        "network_gate": "ch13_network_execution_gate.csv",
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
    """Create Chapter 13 planning/evidence files without any network request."""
    paths = ensure_external_dirs(base_dir)
    output_report_dir = Path(report_dir) if report_dir is not None else paths["reports"]
    output_report_dir.mkdir(parents=True, exist_ok=True)

    base_path = Path(base_dir).resolve()
    env_status = load_env_status(base_path / ".env")
    data_plan = create_external_data_plan()
    method_summary = create_collection_method_summary()
    integration_plan = create_external_integration_plan()
    checklist = create_external_data_checklist()
    external_data_log = create_external_data_log()
    metadata_template = create_metadata_template()
    api_code_review = create_api_code_review_checklist()
    network_gate = create_network_execution_gate()
    summary_text = build_external_data_summary(
        data_plan,
        method_summary,
        integration_plan,
        checklist,
        network_gate,
    )

    outputs: dict[str, pd.DataFrame | str] = {
        "data_plan": data_plan,
        "method_summary": method_summary,
        "integration_plan": integration_plan,
        "checklist": checklist,
        "external_data_log": external_data_log,
        "env_status": env_status,
        "metadata_template": metadata_template,
        "api_code_review": api_code_review,
        "network_gate": network_gate,
        "summary_text": summary_text,
    }
    output_paths = save_external_data_outputs(outputs, output_report_dir)
    return {
        "paths": paths,
        "report_dir": output_report_dir,
        "outputs": outputs,
        "output_paths": output_paths,
    }
