# 13장. 외부 데이터로 분석을 확장하기

지금까지는 저장소 안에 준비된 온라인 쇼핑몰 데이터를 중심으로 분석했습니다. 고객, 상품, 주문, 주문 상세 데이터만으로도 많은 질문을 만들 수 있지만, 실제 분석 프로젝트에서는 내부 데이터만으로 충분하지 않은 경우가 많습니다. 지역 정보, 날씨, 관광지, 검색 트렌드, 공공 통계, 뉴스, 리뷰 데이터처럼 외부 데이터가 함께 들어오면 분석의 폭이 넓어집니다.

외부 데이터 수집은 단순히 데이터를 많이 모으는 작업이 아닙니다. 분석 질문에 필요한 데이터를 찾고, 그 데이터의 출처와 구조를 확인하고, API나 크롤링을 통해 가져온 뒤, 기존 데이터와 연결할 수 있는 형태로 정리하는 과정입니다.

이번 장에서는 공공데이터, 네이버 API, 기본 크롤링을 활용해 외부 데이터를 수집하는 흐름을 살펴봅니다. 핵심은 “어디서든 데이터를 긁어오는 기술”이 아니라, **분석 목적에 맞는 데이터를 안전하고 재현 가능한 방식으로 가져오는 습관**을 익히는 것입니다.

## 이 장에서 생각해 볼 질문

외부 데이터를 수집하기 전에 다음 질문을 먼저 생각해 봅니다.

- 현재 내부 데이터만으로 답하기 어려운 질문은 무엇인가?
- 어떤 외부 데이터가 있으면 분석이 더 좋아질까?
- 공공데이터와 민간 API는 어떤 차이가 있을까?
- API Key는 어떻게 안전하게 관리해야 할까?
- 크롤링은 언제 사용하고, 언제 피해야 할까?
- 외부 데이터의 날짜, 지역, 키워드를 기존 데이터와 어떻게 연결할 수 있을까?
- LLM에게 외부 데이터 수집 코드를 요청할 때 무엇을 주의해야 할까?

## 1. 외부 데이터가 필요한 이유

온라인 쇼핑몰 매출이 특정 월에 증가했다고 가정해 보겠습니다. 내부 주문 데이터만 보면 매출이 증가했다는 사실은 알 수 있습니다. 하지만 그 이유가 계절성 때문인지, 특정 이벤트 때문인지, 외부 환경 때문인지는 내부 데이터만으로 알기 어렵습니다.

외부 데이터는 이런 질문을 확장하는 데 도움을 줍니다.

| 내부 데이터 질문 | 함께 보면 좋은 외부 데이터 |
| --- | --- |
| 특정 월 매출이 왜 증가했을까? | 공휴일, 날씨, 이벤트, 검색 트렌드 |
| 특정 지역 고객 구매가 많은 이유는 무엇일까? | 지역 인구, 관광지, 상권 정보 |
| 여행 상품 추천 앱을 만들려면 어떤 데이터가 필요할까? | 관광지 정보, 숙박, 음식점, 위치 데이터 |
| 특정 키워드의 관심도가 높아지고 있을까? | 검색 API, 뉴스, 블로그, SNS 데이터 |
| 공공 API를 활용한 서비스 기획이 가능할까? | 공공데이터포털, 한국관광공사 OpenAPI |

외부 데이터는 분석 결과를 풍부하게 만들 수 있지만, 잘못 사용하면 오히려 혼란을 줄 수 있습니다. 출처가 불명확하거나, 업데이트 주기가 맞지 않거나, 기존 데이터와 연결 기준이 없는 데이터는 분석에 바로 사용하기 어렵습니다.

## 2. 외부 데이터 수집 방법의 종류

외부 데이터를 가져오는 대표적인 방법은 세 가지입니다.

| 방법 | 설명 | 예시 |
| --- | --- | --- |
| 파일 다운로드 | CSV, Excel, JSON 파일을 직접 내려받아 사용 | 공공데이터포털 CSV, 통계청 Excel |
| API 호출 | 정해진 주소와 파라미터로 데이터를 요청 | 공공데이터 API, 네이버 검색 API |
| 크롤링 | 웹페이지의 HTML에서 필요한 정보를 추출 | 공개 웹페이지의 표, 제목, 링크 |

가장 안정적인 방법은 공식 API나 파일 다운로드입니다. 크롤링은 API가 없고, 웹페이지에 공개된 정보를 제한적으로 확인해야 할 때만 사용합니다. 웹사이트의 이용약관, robots.txt, 저작권, 개인정보, 요청 빈도를 반드시 고려해야 합니다.

외부 데이터 수집에서는 다음 원칙을 지키는 것이 좋습니다.

- 공식 API나 다운로드 파일이 있으면 그것을 우선 사용합니다.
- API Key는 코드에 직접 쓰지 않고 `.env`에 저장합니다.
- 수집한 원본 데이터는 `data/external/` 또는 `data/raw/`에 보관합니다.
- 수집 일자와 출처를 함께 기록합니다.
- 같은 요청을 반복하지 않도록 캐시 파일을 남깁니다.
- 개인정보나 민감정보는 수집하지 않습니다.
- 크롤링 전에는 이용약관과 접근 정책을 확인합니다.

## 3. 외부 데이터 폴더 구조

외부 데이터는 내부 샘플 데이터와 구분해 관리하는 것이 좋습니다. 예를 들어 다음과 같은 구조를 사용할 수 있습니다.

```text
llm-data-analysis-course/
├─ data/
│  ├─ raw/
│  │  ├─ customers.csv
│  │  ├─ products.csv
│  │  ├─ orders.csv
│  │  └─ order_items.csv
│  ├─ processed/
│  └─ external/
│     ├─ public_data_sample.csv
│     ├─ naver_search_blog.json
│     └─ scraped_page_sample.csv
├─ notebooks/
├─ reports/
└─ .env
```

`data/raw/`는 원래 분석에 사용하는 기본 데이터, `data/processed/`는 전처리된 데이터, `data/external/`은 외부에서 가져온 데이터를 저장하는 공간으로 구분합니다.

이번 장의 코드는 `notebooks/ch13_external_data_collection.ipynb`로 구성하는 것이 좋습니다. 현재 저장소의 파일명은 기존 목차 기준으로 남아 있을 수 있으므로, 이후 새 목차에 맞춰 정리할 수 있습니다.

먼저 필요한 패키지를 불러옵니다.

```python
from pathlib import Path
import os
import time
import json

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
```

기준 폴더와 외부 데이터 저장 폴더를 설정합니다.

```python
current_dir = Path.cwd()

if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir

external_dir = base_dir / "data" / "external"
report_dir = base_dir / "reports"

external_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)

print("external_dir:", external_dir)
print("report_dir:", report_dir)
```

## 4. 공공데이터 활용 흐름

공공데이터는 국가, 공공기관, 지방자치단체 등이 공개한 데이터입니다. CSV나 Excel 파일로 내려받을 수도 있고, OpenAPI로 호출할 수도 있습니다.

공공데이터를 사용할 때는 먼저 다음을 확인합니다.

| 확인 항목 | 설명 |
| --- | --- |
| 제공 기관 | 어떤 기관이 제공하는 데이터인가? |
| 데이터 설명 | 어떤 항목을 포함하는가? |
| 파일 형식 | CSV, Excel, JSON, XML 중 무엇인가? |
| 업데이트 주기 | 매일, 매월, 매년, 비정기 중 무엇인가? |
| 사용 조건 | 출처 표시, 상업적 이용 가능 여부 등 |
| 인증 방식 | API Key가 필요한가? |
| 요청 제한 | 하루 또는 초당 호출 제한이 있는가? |

공공데이터 파일을 CSV로 내려받았다면 pandas로 바로 읽을 수 있습니다.

```python
public_data_path = external_dir / "public_data_sample.csv"

# 예시: 이미 CSV 파일을 내려받아 data/external/에 저장한 경우
if public_data_path.exists():
    public_df = pd.read_csv(public_data_path)
    display(public_df.head())
else:
    print("public_data_sample.csv 파일이 아직 없습니다.")
```

API를 사용하는 경우에는 보통 다음과 같은 흐름을 따릅니다.

```text
API 문서 확인
→ API Key 발급
→ 요청 URL과 파라미터 구성
→ requests.get() 호출
→ 응답 상태 코드 확인
→ JSON 또는 XML 파싱
→ DataFrame 변환
→ CSV 저장
```

공공 API마다 요청 주소와 파라미터가 다르므로, 실제 실습에서는 선택한 API 문서를 먼저 확인해야 합니다. 예를 들어 한국관광공사 OpenAPI를 활용한다면 관광지, 숙박, 음식점, 지역 코드, 위치 정보 등을 가져와 관광 앱 프로젝트와 연결할 수 있습니다.

## 5. API Key를 안전하게 관리하기

API Key는 비밀번호와 비슷하게 다뤄야 합니다. 코드 안에 직접 적으면 GitHub에 올라갈 위험이 있습니다. 따라서 `.env` 파일을 사용해 관리하는 것이 좋습니다.

`.env` 파일 예시는 다음과 같습니다.

```text
PUBLIC_DATA_API_KEY=여기에_공공데이터_API_KEY_입력
NAVER_CLIENT_ID=여기에_네이버_CLIENT_ID_입력
NAVER_CLIENT_SECRET=여기에_네이버_CLIENT_SECRET_입력
```

Python에서는 `python-dotenv`를 사용해 `.env` 파일을 읽을 수 있습니다.

```python
load_dotenv()

public_data_api_key = os.getenv("PUBLIC_DATA_API_KEY")
naver_client_id = os.getenv("NAVER_CLIENT_ID")
naver_client_secret = os.getenv("NAVER_CLIENT_SECRET")

print("PUBLIC_DATA_API_KEY loaded:", public_data_api_key is not None)
print("NAVER_CLIENT_ID loaded:", naver_client_id is not None)
print("NAVER_CLIENT_SECRET loaded:", naver_client_secret is not None)
```

API Key 값을 직접 출력하지 않고, 로드 여부만 확인합니다. `.env` 파일은 반드시 `.gitignore`에 포함되어야 합니다.

## 6. 네이버 검색 API 활용하기

네이버 검색 API는 키워드 기반으로 블로그, 뉴스, 쇼핑, 웹문서 등의 검색 결과를 가져오는 데 사용할 수 있습니다. 예를 들어 “제주 여행”, “부산 맛집”, “AI 데이터 분석” 같은 키워드로 검색 결과를 수집하고, 제목과 설명 텍스트를 분석할 수 있습니다.

다음 코드는 네이버 블로그 검색 API를 호출하는 기본 구조입니다. 실제 실행을 위해서는 네이버 개발자 센터에서 발급받은 `Client ID`와 `Client Secret`이 필요합니다.

```python
def search_naver_blog(query, display=10, start=1, sort="sim"):
    url = "https://openapi.naver.com/v1/search/blog.json"

    headers = {
        "X-Naver-Client-Id": naver_client_id,
        "X-Naver-Client-Secret": naver_client_secret
    }

    params = {
        "query": query,
        "display": display,
        "start": start,
        "sort": sort
    }

    response = requests.get(url, headers=headers, params=params, timeout=10)
    print("status_code:", response.status_code)
    response.raise_for_status()

    return response.json()
```

검색어를 지정해 호출합니다.

```python
if naver_client_id and naver_client_secret:
    result = search_naver_blog("제주 여행", display=10)
    print(result.keys())
else:
    print("네이버 API 인증 정보가 없습니다. .env 파일을 확인하세요.")
```

응답 결과에서 필요한 항목을 DataFrame으로 변환합니다.

```python
if naver_client_id and naver_client_secret:
    items = result.get("items", [])
    naver_blog_df = pd.DataFrame(items)
    naver_blog_df.head()
```

HTML 태그가 포함된 제목과 설명을 정리할 수 있습니다.

```python
def clean_html_text(text):
    return BeautifulSoup(text, "html.parser").get_text()

if naver_client_id and naver_client_secret:
    naver_blog_df["title_clean"] = naver_blog_df["title"].apply(clean_html_text)
    naver_blog_df["description_clean"] = naver_blog_df["description"].apply(clean_html_text)
    naver_blog_df[["title_clean", "description_clean", "link"]].head()
```

결과를 저장합니다.

```python
if naver_client_id and naver_client_secret:
    naver_blog_df.to_csv(external_dir / "naver_blog_search_jeju.csv", index=False)
```

네이버 API 결과를 분석할 때는 검색 결과가 전체 여론이나 실제 수요를 대표한다고 단정하면 안 됩니다. 검색 API 결과는 검색어, 정렬 기준, 수집 시점, API 정책의 영향을 받습니다.

## 7. 기본 크롤링 이해하기

크롤링은 웹페이지의 HTML을 가져와 필요한 정보를 추출하는 작업입니다. API가 제공되지 않는 공개 페이지에서 표나 제목, 링크 같은 정보를 가져올 때 사용할 수 있습니다.

다만 크롤링은 더 조심해야 합니다.

- 사이트의 이용약관을 확인합니다.
- robots.txt 정책을 확인합니다.
- 로그인이 필요한 페이지나 개인정보가 있는 페이지는 수집하지 않습니다.
- 짧은 시간에 너무 많은 요청을 보내지 않습니다.
- 수집한 콘텐츠의 저작권과 사용 범위를 확인합니다.
- 가능하면 공식 API나 다운로드 파일을 우선 사용합니다.

기본적인 HTML 요청은 다음과 같이 작성할 수 있습니다.

```python
def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DataAnalysisCourseBot/1.0; educational use)"
    }

    response = requests.get(url, headers=headers, timeout=10)
    print("status_code:", response.status_code)
    response.raise_for_status()

    return response.text
```

가져온 HTML에서 제목을 추출하는 예시는 다음과 같습니다.

```python
sample_url = "https://example.com"

html = fetch_page(sample_url)
soup = BeautifulSoup(html, "html.parser")

page_title = soup.title.get_text(strip=True) if soup.title else ""
page_title
```

링크 목록을 추출할 수도 있습니다.

```python
links = []

for a_tag in soup.find_all("a"):
    text = a_tag.get_text(strip=True)
    href = a_tag.get("href")

    if text or href:
        links.append({
            "text": text,
            "href": href
        })

links_df = pd.DataFrame(links)
links_df.head()
```

저장합니다.

```python
links_df.to_csv(external_dir / "scraped_example_links.csv", index=False)
```

위 예시는 크롤링의 기본 구조를 이해하기 위한 것입니다. 실제 웹사이트를 대상으로 크롤링할 때는 해당 사이트의 정책을 먼저 확인해야 합니다.

## 8. 외부 데이터를 기존 분석과 연결하기

외부 데이터를 수집한 뒤에는 기존 데이터와 어떻게 연결할지 생각해야 합니다. 연결 기준이 없으면 외부 데이터는 참고 자료에 머물 수 있습니다.

예를 들어 온라인 쇼핑몰 데이터와 외부 데이터를 연결하는 방식은 다음과 같습니다.

| 연결 기준 | 예시 |
| --- | --- |
| 날짜 | 월별 매출 + 공휴일/날씨/검색 트렌드 |
| 지역 | 고객 지역 + 지역 통계/관광지 정보 |
| 상품 카테고리 | 카테고리 매출 + 검색 키워드/뉴스 데이터 |
| 키워드 | 상품명 + 블로그/뉴스 검색 결과 |
| 위치 | 위도·경도 + 관광지/상권 데이터 |

외부 데이터는 내부 데이터와 단위가 다를 수 있습니다. 예를 들어 주문 데이터는 일자 단위인데 외부 통계는 월 단위일 수 있습니다. 이 경우 분석 단위를 맞춰야 합니다.

```python
# 예시: 월 단위 외부 데이터와 월별 매출 데이터를 연결하는 구조
# monthly_sales: order_month, total_sales, order_count
# external_monthly: order_month, external_metric

# merged_monthly = monthly_sales.merge(
#     external_monthly,
#     on="order_month",
#     how="left"
# )
```

외부 데이터를 연결할 때는 다음을 확인합니다.

- 연결 기준 컬럼이 양쪽 데이터에 모두 있는가?
- 날짜 형식이 같은가?
- 지역명 표기가 같은가?
- 연결 후 행 수가 예상과 맞는가?
- 결측치가 새로 생기지 않았는가?
- 외부 데이터의 수집 시점이 내부 데이터 기간과 맞는가?

## 9. LLM에게 외부 데이터 수집을 요청할 때

LLM은 API 문서를 이해하거나 수집 코드 초안을 작성하는 데 도움을 줄 수 있습니다. 하지만 API 주소, 파라미터, 인증 방식은 실제 공식 문서를 기준으로 확인해야 합니다. LLM이 오래된 API 주소나 존재하지 않는 파라미터를 제안할 수 있기 때문입니다.

공공데이터 API 활용 프롬프트 예시는 다음과 같습니다.

```text
공공데이터 API를 사용해 데이터를 수집하려고 합니다.

API 문서에서 확인한 정보:
- 요청 URL: 여기에 실제 요청 URL 입력
- 인증 방식: serviceKey 파라미터 사용
- 주요 파라미터: pageNo, numOfRows, type, keyword
- 응답 형식: JSON

요청:
1. Python requests를 사용한 API 호출 코드 예시를 작성해 주세요.
2. 응답 상태 코드 확인과 오류 처리를 포함해 주세요.
3. JSON 응답을 pandas DataFrame으로 변환하는 코드를 작성해 주세요.
4. 결과를 data/external 폴더에 CSV로 저장해 주세요.

주의:
- API Key를 코드에 직접 쓰지 말고 .env에서 읽어오게 해 주세요.
- 실제 문서에 없는 파라미터를 만들지 마세요.
- 요청 실패 시 확인할 항목을 함께 설명해 주세요.
```

네이버 API 활용 프롬프트 예시는 다음과 같습니다.

```text
네이버 검색 API를 사용해 특정 키워드의 블로그 검색 결과를 수집하려고 합니다.

인증 정보:
- NAVER_CLIENT_ID는 .env에서 읽음
- NAVER_CLIENT_SECRET은 .env에서 읽음

요청:
1. requests로 네이버 블로그 검색 API를 호출하는 함수를 작성해 주세요.
2. query, display, start, sort를 파라미터로 받을 수 있게 해 주세요.
3. 응답 JSON의 items를 DataFrame으로 변환해 주세요.
4. title과 description의 HTML 태그를 제거해 주세요.
5. 결과를 CSV로 저장해 주세요.

주의:
- Client ID와 Secret 값을 출력하지 마세요.
- API 호출 실패 시 status_code와 오류 메시지를 확인해 주세요.
- 검색 결과가 실제 수요를 대표한다고 단정하지 마세요.
```

크롤링 코드 요청 프롬프트 예시는 다음과 같습니다.

```text
공개 웹페이지에서 제목과 링크 목록을 수집하는 기본 크롤링 예제를 만들려고 합니다.

요청:
1. requests와 BeautifulSoup을 사용해 HTML을 가져오는 코드를 작성해 주세요.
2. User-Agent를 설정해 주세요.
3. 응답 상태 코드를 확인해 주세요.
4. a 태그의 텍스트와 href를 DataFrame으로 정리해 주세요.
5. 결과를 CSV로 저장해 주세요.

주의:
- 로그인이나 개인정보가 필요한 페이지는 대상으로 하지 마세요.
- robots.txt와 이용약관 확인이 필요하다는 설명을 포함해 주세요.
- 짧은 시간에 반복 요청하지 않도록 time.sleep 예시를 포함해 주세요.
```

LLM이 생성한 코드는 반드시 실제 문서와 비교해야 합니다. 특히 API 주소, 요청 파라미터, 인증 헤더 이름, 응답 JSON 구조는 공식 문서와 다를 수 있습니다.

## 10. 외부 데이터 수집 체크리스트

외부 데이터를 수집할 때는 다음 항목을 점검합니다.

| 점검 항목 | 확인 |
| --- | --- |
| 분석 질문에 필요한 외부 데이터인가? | □ |
| 공식 API 또는 다운로드 파일을 우선 확인했는가? | □ |
| 데이터 출처와 제공 기관을 기록했는가? | □ |
| 업데이트 주기와 수집 시점을 기록했는가? | □ |
| API Key를 `.env`에 저장했는가? | □ |
| API Key를 출력하거나 GitHub에 올리지 않았는가? | □ |
| 요청 URL과 파라미터를 공식 문서 기준으로 확인했는가? | □ |
| 응답 상태 코드와 오류 처리를 포함했는가? | □ |
| 원본 응답 또는 원본 파일을 보관했는가? | □ |
| DataFrame 변환 후 컬럼과 행 수를 확인했는가? | □ |
| 기존 데이터와 연결할 기준 컬럼이 있는가? | □ |
| 날짜, 지역, 키워드 표기를 맞췄는가? | □ |
| 크롤링 대상 사이트의 정책을 확인했는가? | □ |
| 개인정보나 민감정보를 수집하지 않았는가? | □ |
| LLM이 만든 코드와 실제 공식 문서를 비교했는가? | □ |

이 체크리스트는 외부 데이터를 “수집했다”에서 끝내지 않고, 분석에 안전하게 사용할 수 있는지 확인하기 위한 최소 기준입니다.

## 11. 수집 결과를 정리하기

외부 데이터 수집 결과는 간단한 요약표로 남겨 두는 것이 좋습니다.

```python
external_data_log = pd.DataFrame({
    "data_name": [
        "public_data_sample",
        "naver_blog_search_jeju",
        "scraped_example_links"
    ],
    "source": [
        "공공데이터 파일 또는 API",
        "네이버 블로그 검색 API",
        "공개 웹페이지 예시"
    ],
    "save_path": [
        "data/external/public_data_sample.csv",
        "data/external/naver_blog_search_jeju.csv",
        "data/external/scraped_example_links.csv"
    ],
    "usage_note": [
        "분석 목적에 따라 내부 데이터와 날짜 또는 지역 기준으로 연결 가능",
        "키워드 관심도 참고 자료로 활용 가능하나 대표성 해석 주의",
        "크롤링 구조 이해용 예시이며 실제 사이트 적용 전 정책 확인 필요"
    ]
})

external_data_log
```

저장합니다.

```python
external_data_log.to_csv(report_dir / "ch13_external_data_log.csv", index=False)
```

Markdown 요약 보고서도 만들 수 있습니다.

```python
summary_text = f"""
# Chapter 13 외부 데이터 수집 요약

## 1. 수집 목적

내부 온라인 쇼핑몰 데이터만으로 답하기 어려운 분석 질문을 확장하기 위해 공공데이터, 네이버 API, 기본 크롤링 방식의 외부 데이터 수집 흐름을 검토했습니다.

## 2. 수집 방법

{external_data_log.to_markdown(index=False)}

## 3. 활용 시 주의사항

- 외부 데이터는 출처와 수집 시점을 함께 기록해야 합니다.
- API Key는 .env 파일에 저장하고 GitHub에 올리지 않아야 합니다.
- 크롤링은 사이트 정책을 확인한 뒤 제한적으로 사용해야 합니다.
- 외부 데이터와 내부 데이터를 연결할 때 날짜, 지역, 키워드 기준을 맞춰야 합니다.
- 검색 결과나 크롤링 결과를 전체 여론이나 실제 수요로 단정하지 않아야 합니다.

## 4. 다음 단계

수집한 외부 데이터를 기존 EDA, 시각화, 머신러닝 분석에 어떻게 결합할 수 있는지 검토합니다.
"""

summary_path = report_dir / "ch13_external_data_summary.md"
summary_path.write_text(summary_text, encoding="utf-8")
```

## 12. 외부 데이터에서 다음 단계로

외부 데이터 수집은 분석 프로젝트를 한 단계 확장하는 과정입니다. 내부 데이터만 볼 때는 알 수 없던 맥락을 추가할 수 있고, 공공 API나 검색 API를 활용하면 실제 서비스 기획과도 연결할 수 있습니다.

직접 더 연습해 보고 싶다면 다음을 해볼 수 있습니다.

- 공공데이터포털에서 CSV 파일 하나를 내려받아 `data/external/`에 저장합니다.
- 해당 CSV를 pandas로 읽고 행, 열, 컬럼명을 확인합니다.
- 네이버 검색 API를 사용해 관심 키워드의 블로그 검색 결과를 수집합니다.
- 검색 결과의 제목과 설명에서 HTML 태그를 제거합니다.
- 공개 예제 페이지에서 제목과 링크를 추출하는 기본 크롤링 코드를 실행합니다.
- 수집한 외부 데이터가 기존 쇼핑몰 데이터와 날짜, 지역, 키워드 중 어떤 기준으로 연결될 수 있는지 정리합니다.
- LLM에게 API 호출 코드를 요청한 뒤 실제 공식 문서와 맞는지 검토합니다.

다음 장에서는 이렇게 수집·분석·보고한 결과를 반복 업무 흐름으로 연결하는 자동화와 파이프라인 개념을 다룹니다. Make, n8n, Airflow는 각각 다른 방식으로 반복 분석 업무를 자동화하고 운영하는 데 사용할 수 있습니다.
