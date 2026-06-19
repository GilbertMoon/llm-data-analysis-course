# Chapter 13 이미지 생성 프롬프트

LLM 기반 데이터 분석 실무 입문 교재의 Chapter 13 “Make 기반 반복 분석 업무 자동화”에 사용할 교육용 인포그래픽 이미지를 생성해 주세요.

전체 이미지 스타일은 다음 기준을 따릅니다.

* 한국어 교재용 이미지
* 16:9 비율
* 흰색 배경
* 네이비/블루 계열 중심
* 깔끔한 교육용 슬라이드 스타일
* Python 분석 결과, Google Drive, Make, Gmail, Google Sheets, 자동화 로그 흐름을 직관적으로 표현
* 너무 많은 텍스트는 피하고 핵심 키워드 중심
* 아이콘, 표, 카드, 화살표, 자동화 플로우를 활용
* 실제 사람 사진은 사용하지 않음
* 전문적이지만 초보자도 이해하기 쉬운 시각 자료
* 각 이미지는 독립적인 PNG로 사용할 수 있게 구성

생성할 이미지는 총 5개입니다.

## 이미지 1

파일명:

```text id="4orkkp"
ch13_make_automation_overview.png
```

이미지 제목:

```text id="414xqc"
Make 기반 분석 업무 자동화 전체 흐름도
```

이미지 내용:

Python으로 생성한 분석 보고서가 Google Drive를 거쳐 Make 자동화로 Gmail 발송 및 Google Sheets 로그 기록까지 이어지는 전체 흐름을 표현해 주세요.

포함할 단계:

1. Python 분석 실행
2. Markdown 보고서 생성
3. 그래프 PNG 생성
4. Google Drive 저장
5. Make Scenario 실행
6. Gmail 보고서 발송
7. Google Sheets 로그 기록
8. 오류 발생 시 알림

시각 구성:

* 왼쪽에서 오른쪽으로 흐르는 프로세스
* Python, 보고서, 그래프, Drive, Make, Gmail, Sheets 아이콘 사용
* 자동화 흐름은 파란색 화살표
* 오류 알림은 주황색 분기 표시
* 하단에 핵심 문구 삽입

하단 문구:

```text id="39m8ey"
Python은 분석을 담당하고, Make는 전달·알림·기록 업무를 자동화합니다.
```

캡션:

```text id="j1ih1t"
그림 13-1. Make 기반 분석 업무 자동화 전체 흐름도
```

## 이미지 2

파일명:

```text id="g2v3og"
ch13_python_make_role_split.png
```

이미지 제목:

```text id="g14v3g"
Python과 Make의 역할 분담
```

이미지 내용:

반복 분석 자동화에서 Python과 Make가 담당하는 역할을 비교해 주세요.

왼쪽 Python 영역:

* 데이터 불러오기
* 전처리
* pandas 분석
* 시각화
* Markdown 보고서 생성

오른쪽 Make 영역:

* Google Drive 파일 감지
* Gmail 발송
* Slack 또는 이메일 알림
* Google Sheets 로그 기록
* 오류 알림

중앙 연결:

* `reports/ch12_auto_report.md`
* `reports/figures/*.png`

시각 구성:

* 2열 비교 구조
* 왼쪽은 Python 코드/분석 아이콘
* 오른쪽은 자동화/앱 연결 아이콘
* 중앙에는 파일 산출물이 두 영역을 연결하는 브릿지로 표현

하단 문구:

```text id="8ypbpt"
안정적인 자동화는 분석 로직과 업무 흐름의 역할을 나누는 것에서 시작됩니다.
```

캡션:

```text id="w6lf8o"
그림 13-2. Python과 Make의 역할 분담
```

## 이미지 3

파일명:

```text id="ddw1l4"
ch13_make_scenario_structure.png
```

이미지 제목:

```text id="9bv6ja"
Make Scenario 설계 구조
```

이미지 내용:

Make Scenario가 Trigger, Filter, Module, Log, Error Handling으로 구성되는 구조를 표현해 주세요.

포함할 요소:

1. Trigger

   * Google Drive 새 파일 감지

2. Filter

   * 파일명 확인
   * `ch12_auto_report.md`

3. Action Module

   * Gmail 발송

4. Log Module

   * Google Sheets 행 추가

5. Error Handling

   * 실패 시 관리자 알림

시각 구성:

* Make 시나리오 화면을 단순화한 흐름도
* 각 Module은 둥근 카드 또는 노드 형태
* Trigger부터 Log까지 직선 흐름
* Error Handling은 아래쪽 주황색 분기
* 필터는 다이아몬드 형태로 표현

하단 문구:

```text id="3bb1wc"
Scenario는 시작 조건, 처리 모듈, 필터, 로그, 오류 처리로 구성됩니다.
```

캡션:

```text id="qut12d"
그림 13-3. Make Scenario 설계 구조
```

## 이미지 4

파일명:

```text id="b2ob5k"
ch13_report_delivery_scenario.png
```

이미지 제목:

```text id="zqs05f"
보고서 자동 발송 시나리오
```

이미지 내용:

`ch12_auto_report.md` 보고서 파일이 자동으로 이메일 발송되는 시나리오를 구체적으로 표현해 주세요.

흐름:

1. `reports/ch12_auto_report.md`
2. Google Drive 업로드
3. Make가 새 파일 감지
4. 파일명 필터 통과
5. Gmail로 담당자에게 발송
6. Google Sheets에 성공 로그 기록

시각 구성:

* 파일 카드가 Drive로 올라가고 Make를 거쳐 Gmail로 전달되는 흐름
* 이메일 카드에는 제목 표시:

  * `[자동발송] 온라인 쇼핑몰 분석 보고서`
* Sheets 로그에는 `success` 표시
* 중복 발송 방지를 위한 작은 필터 아이콘 포함

하단 문구:

```text id="69d1fg"
파일 감지 자동화에서는 대상 파일명 필터와 실행 로그가 중요합니다.
```

캡션:

```text id="rva5m7"
그림 13-4. 보고서 자동 발송 시나리오
```

## 이미지 5

파일명:

```text id="t9r2oh"
ch13_success_error_flow.png
```

이미지 제목:

```text id="o9xgek"
Make 자동화 성공과 오류 처리 흐름
```

이미지 내용:

Make 자동화가 성공했을 때와 실패했을 때의 흐름을 함께 보여 주세요.

성공 흐름:

1. 파일 감지
2. 이메일 발송
3. 로그 기록
4. 완료

오류 흐름:

1. 파일 없음
2. 권한 오류
3. 첨부 누락
4. 수신자 오류
5. 관리자 알림
6. 오류 로그 확인

시각 구성:

* 화면을 위아래 또는 좌우로 나누어 성공 흐름과 오류 흐름 비교
* 성공은 초록색 체크 흐름
* 오류는 주황색 경고 흐름
* 오류 원인을 아이콘으로 표현
* 최종적으로 “로그 확인”으로 연결

하단 문구:

```text id="r8d7vq"
자동화는 성공 흐름뿐 아니라 실패했을 때의 확인 절차도 함께 설계해야 합니다.
```

캡션:

```text id="bmb04k"
그림 13-5. Make 자동화 성공과 오류 처리 흐름
```

## 공통 디자인 요구사항

모든 이미지는 다음 스타일을 유지해 주세요.

* 배경: 흰색
* 주요 색상: 네이비, 블루, 연한 하늘색
* 강조 색상: 자동화는 보라색, 성공은 초록색, 오류와 주의사항은 주황색
* 글꼴 느낌: 깔끔한 고딕체
* 분위기: 대학교 강의 교재, 실무형 데이터 분석 교재
* 구성: 카드, 표, 화살표, 아이콘, 자동화 플로우 중심
* 출력: PNG 이미지로 사용할 수 있는 선명한 고해상도
* 한국어 텍스트는 오탈자 없이 자연스럽게 표현

이미지 안에 너무 긴 문장은 넣지 말고, 핵심 키워드와 짧은 설명 중심으로 구성해 주세요.

## 저장 경로

생성한 이미지는 아래 폴더에 저장해 주세요.

```text id="hc0kbv"
book/assets/images/ch13/
```

권장 파일명은 다음 5개입니다.

```text id="ri39vw"
ch13_make_automation_overview.png
ch13_python_make_role_split.png
ch13_make_scenario_structure.png
ch13_report_delivery_scenario.png
ch13_success_error_flow.png
```
