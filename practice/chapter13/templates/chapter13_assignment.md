# Chapter 13 답안 양식. 외부 데이터로 분석을 확장하기

> 이 내용을 `chapter13.ipynb`의 Markdown 셀로 작성합니다.  
> **실제 수집을 하지 않았다면 가짜 결과를 만들지 말고 `SKIPPED`, `NO_DATA`, `BLOCKED_BY_POLICY` 등 실제 상태를 기록합니다.**

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

---

## 1. 외부 데이터가 필요한 분석 질문
- 현재 분석 질문:
- 내부 데이터로 이미 알 수 있는 것:
- 내부 데이터에 없는 정보:
- 필요한 최소 외부 데이터:
- 내부·외부 연결 단위:
- 외부 데이터 없이도 답할 수 있는가:

### 나의 판단
불필요한 수집을 하지 않고 이 외부 데이터가 필요한 이유를 작성하세요.

---

## 2. 공식 출처와 현재 이용조건
- Provider/기관:
- 공식 Source URL:
- 수집 방법: official file / official API / limited public HTML
- Data Reference Date / Reference Period:
- Collected At UTC:
- 이용조건/라이선스/출처 표시 조건:
- 요청 범위:
- Pagination 종료 조건:
- 내부 데이터와 연결할 Key:
- 개인정보·민감정보 포함 여부:

![공식 출처와 이용조건](images/step02_source_terms.png)

### 왜 이 Source를 선택했는가?

### 실행 시점에 다시 확인한 공식 문서 항목
- API URL / 다운로드 URL:
- HTTP Method:
- 인증 방식/위치:
- Parameter:
- Response 구조:
- Rate Limit:
- 오류 구조:
- 이용조건 변경 여부:

### 한계와 추가 확인 사항
정책 변경, 최신성, 대표성 등 다음 수집 시 다시 확인할 점을 작성하세요.

---

## 3. Network Gate와 Secret 보호

준비 단계 Network Gate를 기록합니다.

| flag | 기본값 | 현재값 | 사람 승인 근거 |
| --- | --- | --- | --- |
| RUN_PUBLIC_API | False |  |  |
| RUN_NAVER_API | False |  |  |
| RUN_CRAWLING_EXAMPLE | False |  |  |
| POLICY_CONFIRMED | False |  |  |

### Secret 상태
실제 값은 적지 않습니다.

| env_key | state | configured | value_exposed |
| --- | --- | --- | --- |
| PUBLIC_DATA_API_KEY | MISSING / PLACEHOLDER / CONFIGURED |  | False |
| NAVER_CLIENT_ID | MISSING / PLACEHOLDER / CONFIGURED |  | False |
| NAVER_CLIENT_SECRET | MISSING / PLACEHOLDER / CONFIGURED |  | False |

### 네트워크 실행 전 확인
- [ ] 공식 출처 확인
- [ ] 현재 이용조건/라이선스 확인
- [ ] 최소 요청 범위
- [ ] 인증 위치 확인
- [ ] Secret 안전 저장
- [ ] connect/read timeout 확인
- [ ] 제한적 retry 확인
- [ ] rate limit / Retry-After 확인
- [ ] pagination 종료 조건 확인
- [ ] Raw / Metadata 저장 경로 확인
- [ ] 사람이 실제 요청 실행 승인

### 최종 실행 상태
- [ ] RUN 승인
- [ ] SKIPPED
- [ ] BLOCKED_BY_POLICY
- [ ] NO_DATA

### 판단 이유

---

## 4. HTTP / API 요청 계약
실제 API를 사용한 경우 작성합니다.

- Connect Timeout:
- Read Timeout:
- Retry 대상 상태:
- Retry 최대 횟수:
- Rate Limit:
- Retry-After 확인:
- Pagination 시작/종료 조건:
- 최대 요청/Page 범위:
- Redirect 정책:
- JSON Response Size Gate:
- HTTP Status:
- Content-Type:
- JSON Parse 결과:
- API 업무 성공 여부:

### 나의 판단
왜 `retry ≠ rate limit`, `HTTP 200 ≠ 업무 성공`인지 작성하세요.

---

## 5. Raw Snapshot과 Metadata
- Raw 파일 경로:
- Processed 파일 경로:
- Metadata 파일 경로:
- Snapshot timestamp:
- Source URL:
- Data Reference Date:
- Collected At UTC:
- Request Scope:
- License / Terms:
- SHA-256:
- 보유기간:
- 접근범위:
- 재배포 가능 여부:
- 삭제/만료 정책:
- 민감 콘텐츠 검토 여부:

![Raw와 Metadata](images/step04_snapshot_metadata.png)

### Raw 비덮어쓰기 확인
- [ ] timestamped path를 사용했습니다.
- [ ] 기존 Raw 파일을 조용히 덮어쓰지 않았습니다.

### 나의 해석과 판단
Raw / Processed / Metadata를 분리하는 이유를 작성하세요.

### Hash 해석
SHA-256이 보장하는 것과 보장하지 않는 것을 각각 작성하세요.

---

## 6. 외부 데이터 품질 검증

![외부 데이터 품질 검증](images/step05_quality.png)

- 수집/다운로드 상태:
- 행 수:
- 열 수:
- 필수 컬럼:
- Key 결측:
- Key 중복:
- 전체 중복:
- dtype:
- 날짜 Parsing Failure:
- 숫자 Parsing Failure:
- 기준 기간:
- 예상 범위 밖 값:
- 품질 최종 상태: PASS / REVIEW / FAIL / NO_DATA

### 결과 관찰

### 나의 해석과 판단
수집 성공과 분석 사용 가능성이 왜 같은 의미가 아닌지 작성하세요.

---

## 7. Processed 데이터 가공

| 처리 항목 | 적용 내용 | 적용 이유 | 정보 손실 가능성 |
| --- | --- | --- | --- |
|  |  |  |  |
|  |  |  |  |

### Raw는 보존되었는가?

### 가공 결과를 다시 재현할 수 있는가?

---

## 8. 내부·외부 분석 단위 확인
- 내부 데이터 한 행의 의미:
- 외부 데이터 한 행의 의미:
- 내부 시간 단위:
- 외부 시간 단위:
- Timezone:
- 내부 지역 단위:
- 외부 지역 단위:
- 연결 Key:
- 기대 병합 관계: one_to_one / many_to_one / 기타

### 단위를 맞추기 위해 수행한 집계/정규화

---

## 9. 내부 데이터와 병합 검증

![외부 데이터 병합](images/step07_merge.png)

- Join Key:
- `validate`:
- 외부 오른쪽 Key 중복 수:
- 병합 전 내부 행 수:
- 병합 후 행 수:
- Row Count Preserved:
- `left_only_count`:
- `both_count`:

### 미매칭 해석
미매칭을 자동으로 `0`, 정상일, 비공휴일 등으로 처리하지 않은 이유를 작성하세요.

```text
실제 값 0
≠
외부 데이터 부재
```

---

## 10. 검색 API / 웹 결과의 대표성
해당되는 경우 작성합니다.

- Query:
- Sort:
- Page / Start:
- Page Size:
- Request Count:
- Collected At UTC:
- 검색 서비스/플랫폼:
- 반환 범위 한계:
- 중복 처리:

### 잘못된 과대 해석 문장

### 범위를 명확히 한 수정 문장

### 대표성 한계

---

## 11. 공개 HTML 수집 검토
해당되는 경우 작성합니다.

- 공식 파일/API 존재 여부 확인:
- robots.txt 상태:
- 이용약관 검토:
- 라이선스/저작권 검토:
- 개인정보 검토:
- 요청량 검토:
- 로그인/CAPTCHA/paywall/접근제한 우회 여부: 없음 / 있음

### 나의 판단
왜 `robots.txt 허용 ≠ 이용허락 완료`인지 작성하세요.

---

## 12. 외부 문서와 LLM 사용 검토
- 외부 HTML/PDF/검색 결과를 LLM Context로 사용했는가: 예 / 아니오
- 발견한 의심 지시문:
- 필요한 텍스트만 최소화했는가:
- Secret/PII 제거 여부:
- 문서 안의 지시문을 실행하지 않았는가:

### 나의 판단
외부 문서를 `untrusted data`로 다룬 방법을 작성하세요.

---

## 13. 실제 수집 상태

다음 중 실제 상태를 선택합니다.

- [ ] EXECUTED
- [ ] NO_DATA
- [ ] SKIPPED
- [ ] BLOCKED_BY_POLICY
- [ ] REQUEST_FAILED
- [ ] VALIDATION_FAILED
- [ ] SYNTHETIC_DEMO_ONLY

### 실제 상태 설명

### 실패/보류라면 원인

### Demo/Synthetic 데이터를 사용했다면
실제 수집 결과가 아니라는 점을 명확히 작성하세요.

---

## 14. 외부 데이터가 준 추가 맥락

### 결과 관찰

### 나의 해석과 판단

### 업무·분석적 의미

### 인과 해석 한계
외부 변수와 내부 지표가 같이 움직였다는 사실만으로 원인이라고 말할 수 없는 이유를 작성하세요.

### 대표성 / 수집 시점 / 정책 한계

---

## 15. 준비 Evidence 파일 확인

- [ ] `ch13_external_data_plan.csv`
- [ ] `ch13_collection_method_summary.csv`
- [ ] `ch13_external_integration_plan.csv`
- [ ] `ch13_external_data_checklist.csv`
- [ ] `ch13_external_data_log.csv`
- [ ] `ch13_env_key_status.csv`
- [ ] `ch13_collection_metadata_template.csv`
- [ ] `ch13_api_code_review_checklist.csv`
- [ ] `ch13_network_execution_gate.csv`
- [ ] `ch13_external_data_summary.md`

### 가장 중요한 Evidence 3개와 이유
1.
2.
3.

---

## 16. 최종 사용 판단
- [ ] 현재 분석에 사용 가능
- [ ] 추가 검증 후 사용 가능
- [ ] 현재 사용 보류

### 판단 근거
1.
2.
3.

### 신뢰할 수 있는 범위

### 현재 결과만으로 말할 수 없는 것

### 다음 수집 시 다시 확인할 것
1.
2.
3.

---

## 최종 체크
- [ ] 외부 데이터 필요성을 질문에서 정의했습니다.
- [ ] 공식 파일/API를 우선 확인했습니다.
- [ ] 실행 시점의 공식 문서와 이용조건을 확인했습니다.
- [ ] Data Reference Date와 Collected At을 구분했습니다.
- [ ] Network Gate 기본 OFF를 확인했습니다.
- [ ] Secret 실제 값을 코드·로그·캡처에 남기지 않았습니다.
- [ ] MISSING / PLACEHOLDER / CONFIGURED를 구분했습니다.
- [ ] timeout / retry / rate limit / pagination을 구분했습니다.
- [ ] HTTP 성공과 업무 성공을 구분했습니다.
- [ ] Raw / Processed / Metadata를 분리했습니다.
- [ ] Raw Snapshot을 조용히 덮어쓰지 않았습니다.
- [ ] SHA-256을 데이터 품질 보증으로 오해하지 않았습니다.
- [ ] 외부 데이터 품질을 검증했습니다.
- [ ] 내부·외부 분석 단위를 맞췄습니다.
- [ ] 외부 오른쪽 Key와 병합 미매칭을 검증했습니다.
- [ ] 검색/웹 결과를 모집단으로 과장하지 않았습니다.
- [ ] 외부 문서를 untrusted data로 취급했습니다.
- [ ] 실제 수집 실패를 가짜 결과로 대체하지 않았습니다.
- [ ] 인과관계를 과대 해석하지 않았습니다.
- [ ] 최종 Notebook URL을 제출합니다.
