# Chapter 12 답안 양식. LLM이 만든 분석 코드를 검증하는 방법

> 이 내용을 `chapter12.ipynb`의 Markdown 셀로 작성합니다.
> **생성 코드는 실행 전에 검토하며, 자동 PASS는 실행 승인이 아닙니다.**

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 사용한 LLM/생성 코드 출처:
- 검토한 코드 버전/참조:
- 최종 Notebook URL:

## 1. Generated Code가 하려는 일

### 코드 목적

### 읽는 데이터/파일

### 생성·수정·삭제 가능성이 있는 출력

### 사용하는 주요 Dataset / Column / Key

### 분석 범위와 계산 기준
- 주문 상태 범위:
- 금액 계산식:
- 예측 문제라면 Prediction Time:

---

## 2. Read Before Run — 분석 논리 점검

| 점검 항목 | 확인 결과 | Evidence | 위험/수정 필요 |
| --- | --- | --- | --- |
| 실제 컬럼 사용 |  |  |  |
| `order_items.order_item_id` 포함 PK |  |  |  |
| FK/부모 key 고유성 |  |  |  |
| merge 관계와 `validate` |  |  |  |
| merge 전후 행 수·미매칭 |  |  |  |
| completed 등 분석 범위 |  |  |  |
| `line_total = quantity × unit_price` |  |  |  |
| source total vs grouped total |  |  |  |
| Prediction-time leakage |  |  |  |

### 가장 중요한 분석 위험

### 나의 해석과 판단
이 위험이 분석 결과를 왜곡할 수 있는 이유를 작성하세요.

---

## 3. Read Before Run — 실행 안전 점검

| 위험 유형 | 존재 여부 | Static Scan / 코드 확인 | 판단 |
| --- | --- | --- | --- |
| 파일 삭제/덮어쓰기/이동 |  |  |  |
| 네트워크 전송 |  |  |  |
| OS/Shell 명령 |  |  |  |
| subprocess |  |  |  |
| 동적 코드 실행 |  |  |  |
| Package 설치 |  |  |  |
| Secret/Credential |  |  |  |
| 내부 URL/민감 경로 |  |  |  |

![실행 전 위험 점검](images/step03_risk_scan.png)

### 정적 스캔 결과
- `critical`:
- `high`:
- `review`:
- 탐지 0건 여부:

### 정적 스캔의 한계
자동 점검에서 위험이 나오지 않아도 안전을 보장할 수 없는 이유를 작성하세요.

```text
정적 스캔 0건 ≠ 코드 안전
```

---

## 4. 머신러닝 Feature Contract 검토

해당되는 경우 작성합니다.

### 문제 종류
- [ ] Chapter 09 회귀
- [ ] Chapter 10 분류
- [ ] 해당 없음

### Prediction Time

### 사용 Feature

### 금지 Feature 포함 여부

### 조건부 REVIEW Feature
분류에서 `item_count`, `total_quantity`, `order_amount`를 사용했다면 주문 생성 시 이미 확정되어 있다는 교육용 가정을 확인했는지 작성하세요.

### 평가 계약 확인

#### 회귀
- [ ] 날짜 순서 Final Split
- [ ] Train 내부 후보 선택
- [ ] 모델 고정 후 Frozen Final Test

#### 분류
- [ ] completed=0 / cancelled=1, refunded·other 제외
- [ ] Validation에서 모델 선택
- [ ] Validation에서 Threshold 선택
- [ ] Frozen Final Test

### 나의 판단
Feature Leakage가 컬럼 이름만이 아니라 Prediction Time 문제인 이유를 작성하세요.

---

## 5. Execution Gate 확인

`reports/ch12_execution_gate.csv`를 확인합니다.

| gate | status | Evidence / 의미 |
| --- | --- | --- |
| schema_and_keys |  |  |
| aggregate_validation |  |  |
| ml_leakage |  |  |
| static_scan |  |  |
| sandbox_and_package |  |  |
| human_approval |  |  |
| execution_decision |  |  |

### Gate 해석

```text
FAIL 또는 BLOCKED 존재
→ DO_NOT_EXECUTE

자동 차단 항목 없음
→ HUMAN_REVIEW_REQUIRED
```

기본 위험 예제를 검사했다면 `DO_NOT_EXECUTE`가 나오는 것이 정상일 수 있습니다. 이것은 자동화 실패가 아니라 **검사 대상 코드에 차단 사유가 있다는 뜻**입니다.

---

## 6. Sandbox와 Package 검토

### Sandbox
- [ ] 운영 원본이 아닌 복사한 소량 샘플
- [ ] read-only input 가능하면 적용
- [ ] API Key/DB password/cloud credential 없음
- [ ] disposable environment
- [ ] 쓰기 경로 allowlist
- [ ] network deny by default
- [ ] CPU / memory / timeout / process / disk limit
- [ ] 실행 전 baseline 기록
- [ ] 실행 후 변경 비교 가능

### Package 공급망 검토
- package 이름:
- 필요한 이유:
- 공식 source 확인:
- typosquatting 검토:
- exact version pin:
- Python compatibility:
- transitive dependency 검토:
- install script 검토:
- requirements / lock 기록:
- 조직 정책 확인:
- 최종 결정:

기본 상태는 다음입니다.

```text
DO_NOT_INSTALL_UNTIL_REVIEWED
```

---

## 7. 사람의 실행 승인 판단

자동 PASS와 별도로 사람이 판단합니다.

- [ ] APPROVE — 제한 실행 후보
- [ ] REVISE — 수정 후 재검토
- [ ] BLOCK — 현재 상태에서는 실행하지 않음

### 판단 근거
1.
2.
3.

### 분석 타당성 근거

### 실행 안전 근거

---

## 8. 사람이 수정한 코드/동작

| LLM 초안/원래 내용 | 발견 문제 | 사람 수정 | 수정 이유 | 재검증 Evidence |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |
|  |  |  |  |  |

### 수정 후 다시 확인한 항목

### `execution_approved`
- 수정 전:
- 수정 후:
- 승인자/검토자:
- 승인 근거:

> 실제 승인 전에는 `execution_approved = False`를 유지합니다.

---

## 9. 제한 실행 결과

> **APPROVE된 자신의 코드만 실행합니다. `DEFAULT_STATIC_SCAN_EXAMPLE` 같은 위험 예제 문자열을 실행하지 않습니다.**

### 실행 전 Evidence
- 실행 코드 버전:
- 입력 파일:
- 출력 허용 경로:
- 네트워크 정책:
- Python 버전:
- 핵심 Package 버전:
- 시작 시각:
- baseline 파일 목록/hash/크기:

![제한 실행 결과](images/step06_limited_run.png)

### 실행 후 Evidence
- 종료 시각:
- exit code:
- timeout 여부:
- 생성 파일:
- 수정 파일:
- 삭제 파일:
- allowlist 밖 변경:

### 결과 관찰

### 예상과 다른 결과/경고

---

## 10. Post-execution Validation

- 입력 행 수:
- 출력 행 수:
- merge 전후 행 수:
- 미매칭 수:
- completed 범위 확인:
- `line_total` 관계 확인:
- completed source total:
- category grouped total:
- monthly grouped total:
- 생성/수정된 파일:
- 원본 보존 여부:
- 외부 네트워크 전송 여부:
- Secret 로그 노출 여부:

![사후 검증](images/step07_post_validation.png)

### 나의 해석과 판단
실행이 성공한 것과 분석 결과가 맞는 것을 어떻게 구분했는지 작성하세요.

### 업무·분석적 의미

### 한계와 추가 확인 사항

---

## 11. 오류를 LLM에게 다시 질문했다면

- LLM 재질문 여부: 예 / 아니오
- 공유한 최소 Schema:
- 공유한 최소 재현 코드:
- 제거한 개인정보/Secret/절대 경로:
- 제공한 검증 Evidence:

### LLM에게 금지한 행동
- [ ] 파일 삭제/덮어쓰기 추가 금지
- [ ] 외부 통신 추가 금지
- [ ] OS/Shell 명령 추가 금지
- [ ] 검토 없는 Package 설치 금지
- [ ] 데이터에 없는 원인 추측 금지

### 사람이 다시 검증한 내용

---

## 12. Evidence 파일 확인

다음 파일 중 실제 생성·검토한 항목을 확인합니다.

- [ ] `ch12_dataset_inventory.csv`
- [ ] `ch12_required_column_check.csv`
- [ ] `ch12_primary_key_check.csv`
- [ ] `ch12_relationship_key_check.csv`
- [ ] `ch12_category_sales_validation.csv`
- [ ] `ch12_monthly_sales_validation.csv`
- [ ] `ch12_ml_leakage_review.csv`
- [ ] `ch12_generated_code_static_scan.csv`
- [ ] `ch12_execution_gate.csv`
- [ ] `ch12_sandbox_execution_checklist.csv`
- [ ] `ch12_package_install_review.csv`
- [ ] `ch12_human_revision_log.csv`
- [ ] `ch12_llm_code_review_checklist.csv`
- [ ] `ch12_error_fix_prompt_template.md`
- [ ] `ch12_code_validation_summary.md`

### 가장 중요한 Evidence 3개와 이유
1.
2.
3.

---

## 13. 최종 코드 신뢰 판단

- [ ] 현재 범위에서 사용 가능
- [ ] 추가 검증 후 사용 가능
- [ ] 사용 보류

### 신뢰할 수 있는 범위

### 아직 신뢰할 수 없는 부분

### 남은 위험/불확실성

### 다음에 Generated Code를 받을 때 가장 먼저 볼 항목 3개
1.
2.
3.

---

## 최종 체크
- [ ] Generated Code를 실행 전에 읽었습니다.
- [ ] processed 데이터에서 시작했습니다.
- [ ] 필수 컬럼·PK·FK를 검증했습니다.
- [ ] `order_items.order_item_id`를 PK로 확인했습니다.
- [ ] merge 관계·행 수·미매칭을 확인했습니다.
- [ ] completed 범위와 금액 계산식을 검증했습니다.
- [ ] source total과 grouped total을 대조했습니다.
- [ ] 분석 논리와 실행 안전을 별도로 검증했습니다.
- [ ] 정적 스캔을 안전 보장으로 오해하지 않았습니다.
- [ ] 회귀/분류 Feature Contract를 구분했습니다.
- [ ] Execution Gate를 확인했습니다.
- [ ] Sandbox와 Package 위험을 검토했습니다.
- [ ] 사람의 APPROVE / REVISE / BLOCK 판단을 기록했습니다.
- [ ] LLM 초안과 사람 수정 내용을 구분했습니다.
- [ ] APPROVE된 코드만 제한 실행했습니다.
- [ ] 실행 후 실제 수치·파일·총합을 다시 검증했습니다.
- [ ] 최종 코드의 신뢰 범위와 남은 한계를 작성했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
