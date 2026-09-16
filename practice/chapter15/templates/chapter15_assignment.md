# Chapter 15 답안 양식. 하나의 데이터 분석 프로젝트로 완성하기

> 이 내용을 `chapter15.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:
- Project Run ID:
- 최종 Submission Status: READY / READY_WITH_WARNINGS / BLOCKED

## 1. 프로젝트 질문과 범위
### 분석 질문

### 금액 범위
```text
order_status == completed
line_total = quantity × unit_price
```

### 이 금액을 회계상 순매출이라고 부르지 않는 이유

### 필수 단계

### 선택 단계와 선택/미선택 이유

### 제출 완료 기준

## 2. 데이터와 PK/FK 검증
### Primary Key
| 데이터 | PK | 중복 | 결측 | 판단 |
| --- | --- | ---: | ---: | --- |
| customers | customer_id | | | |
| products | product_id | | | |
| orders | order_id | | | |
| order_items | order_item_id | | | |

### Relationship
| 관계 | 검증 결과 | 미매칭 | 판단 |
| --- | --- | ---: | --- |
| orders.customer_id → customers.customer_id | | | |
| order_items.order_id → orders.order_id | | | |
| order_items.product_id → products.product_id | | | |

![PK FK 검증](images/step02_keys.png)

### Merge Evidence
- `validate` 관계:
- 병합 전 행 수:
- 병합 후 행 수:
- 미매칭 수:

### 나의 해석과 판단
병합이 안전하다고 판단한 근거를 작성하세요.

## 3. completed 금액 총합 불변식
| 집계 | 총합 |
| --- | ---: |
| completed source | |
| category | |
| monthly | |
| customer | |
| product | |

### 총합 일치 여부
- [ ] PASS
- [ ] FAIL

![총합 불변식](images/step03_totals.png)

### 불일치가 있다면 확인한 원인

### 나의 해석과 판단
왜 이 검증이 Core Gate인지 작성하세요.

## 4. 핵심 EDA와 시각화
### 핵심 결과 1
- 질문:
- 데이터 범위:
- 수치/그래프:
- 결과 관찰:
- 나의 해석과 판단:
- 업무·분석적 의미:
- 한계:

### 핵심 결과 2
- 질문:
- 데이터 범위:
- 수치/그래프:
- 결과 관찰:
- 나의 해석과 판단:
- 업무·분석적 의미:
- 한계:

### 핵심 결과 3
- 질문:
- 데이터 범위:
- 수치/그래프:
- 결과 관찰:
- 나의 해석과 판단:
- 업무·분석적 의미:
- 한계:

## 5. 공개 결과 개인정보 점검
- [ ] customer_id 제거/비공개
- [ ] name 제거/비공개
- [ ] email 제거/비공개
- [ ] phone 제거/비공개
- [ ] address 제거/비공개
- [ ] city 등 간접 식별 가능 정보 검토
- [ ] 기타 재식별 가능 조합 확인

### 공개 결과에 사용한 익명화 방식

### 내부 진단 자료와 공개 제출물을 분리한 방법

## 6. 선택 단계 — 분류
- 실행 상태: completed / skipped / warning
- reason_type:
- SKIP/WARN 사유(해당 시):
- 타깃 정의:
- prediction time:
- 사용 feature:
- 제외 feature/leakage:
- Dummy baseline:
- validation 선택 모델:
- validation 선택 threshold:
- final test 결과:
- 공개 prediction 식별자 제거 여부:

### 결과 관찰

### 나의 해석과 판단
이 모델이 프로젝트 질문에 실제로 추가한 가치가 있는지 작성하세요.

### 한계
시간 순서 평가, 업무 비용, calibration 등 운영 전 추가 검토가 필요한 내용을 작성하세요.

## 7. 선택 단계 — 외부 데이터
- 실행 상태: completed / skipped / warning
- reason_type:
- Provider:
- Source URL:
- Data Reference Date:
- License/Terms:
- Source SHA-256:
- 날짜 parsing 실패:
- 날짜 key 중복:
- 내부 기간 coverage:
- 미매칭 날짜:
- SKIP/WARN 사유(해당 시):

### 데이터 부재와 실제 0을 어떻게 구분했는가

### 나의 해석과 판단
외부 데이터가 실제로 추가한 맥락과 인과 해석 한계를 작성하세요.

## 8. 선택 단계 — LLM Evidence
- execution_status:
- provider/model:
- executed_at:
- prompt_version:
- step:
- input_summary:
- response_summary:
- validation_result:
- 사람이 수정한 내용:
- final_use:

### 미실행이라면
```text
execution_status = not_executed
final_use = not_used
```

### Secret/개인정보 점검
- [ ] API Key/Token/Password 없음
- [ ] 원본 개인정보 없음

### 나의 해석과 판단
LLM 사용 여부보다 사람이 무엇을 검증했는지가 중요한 이유를 작성하세요.

## 9. 자동화 계획과 실행 Evidence 구분
- 자동화 계획 문서 존재 여부:
- 실제 자동화 실행 Evidence 존재 여부:
- 실제 DAG Run ID(구현했다면):
- 로그/Validation/전달 Evidence:

### 나의 해석과 판단
`Automation Plan ≠ Automation Execution Evidence`인 이유를 작성하세요.

## 10. Project Validation
| 검증 항목 | Required | 결과 PASS/SKIP/WARN/FAIL | Evidence |
| --- | --- | --- | --- |
| Primary Key | Y | | |
| Foreign Key | Y | | |
| Safe Merge | Y | | |
| Core Validation | Y | | |
| completed 총합 불변식 | Y | | |
| 공개 고객 개인정보 | Y | | |
| 선택 분류 | N | | |
| 선택 외부 데이터 | N | | |
| 선택 LLM | N | | |
| 필수 Figure | Y | | |
| 자동화 설계 산출물 | Y | | |

![Project Validation](images/step10_validation.png)

### 상태 개수
- PASS:
- SKIP:
- WARN:
- FAIL:

### 필수 FAIL 여부

## 11. Reproducibility Manifest
- 파일: `reports/ch15_reproducibility_manifest.csv`
- Project Run ID:
- raw 입력 파일 SHA-256 기록 여부:
- Python version:
- pandas version:
- scikit-learn version:
- matplotlib version:
- random_state:

### 나의 해석과 판단
이 Manifest가 재현성에 도움이 되는 이유와, 이것만으로 결과 재현을 완전히 보장하지 못하는 이유를 작성하세요.

## 12. Deliverable Manifest
- 파일: `reports/ch15_project_deliverables.csv`
- Project Run ID:
- required artifact 수:
- required artifact 누락:
- nonempty 실패:
- SHA-256 기록 여부:
- 절대 로컬 경로 노출 여부:

![Manifest](images/step12_manifest.png)

### 나의 해석과 판단
SHA-256이 파일 변경 추적 Evidence이지만 분석 타당성을 증명하지 않는 이유를 작성하세요.

## 13. Submission Status
- [ ] READY
- [ ] READY_WITH_WARNINGS
- [ ] BLOCKED

- can_submit:
- pass_count:
- skip_count:
- warn_count:
- fail_count:
- required_missing_count:
- Manifest SHA-256:

### 선택한 상태의 근거
1.
2.
3.

### WARN이 있다면 보고서에 어떻게 설명했는가

### BLOCKED라면 해소해야 할 항목

### READY가 운영 배포 승인과 같지 않은 이유

## 14. 재현 실행
### 1차 실행
- Project Run ID:
- completed total:
- Submission Status:

### 2차 실행
- Project Run ID:
- completed total:
- Submission Status:

### 재실행 비교
- [ ] 새 Run ID가 생성됨
- [ ] 같은 입력에서 같은 의미의 핵심 총합이 유지됨
- [ ] required artifact가 다시 생성됨
- [ ] Validation이 다시 실행됨
- [ ] Manifest가 갱신됨
- [ ] 기존 사람이 작성한 LLM 로그가 의도치 않게 덮어써지지 않음

![재현 실행](images/step14_reproduce.png)

### 나의 해석과 판단
다른 사람이 이 프로젝트를 재현할 수 있다고 보는 근거를 작성하세요.

## 15. 최종 분석 결론
### 프로젝트 질문에 대한 답

### 핵심 근거 3개
1.
2.
3.

### 업무적으로 제안하는 행동/추가 검토
1.
2.
3.

### 현재 Evidence로 말할 수 없는 것

### 사용하지 않은 선택 단계와 그 이유

### 추가로 필요한 데이터/검증

### 프로젝트를 다시 한다면 바꾸고 싶은 점

## 최종 체크
- [ ] 질문과 completed 금액 범위가 명확합니다.
- [ ] Project Run ID를 기록했습니다.
- [ ] `order_item_id` 포함 PK/FK와 merge를 검증했습니다.
- [ ] 다섯 총합 불변식을 확인했습니다.
- [ ] 결과 관찰·해석·한계를 구분했습니다.
- [ ] 공개 고객 결과의 개인정보를 최소화했습니다.
- [ ] 선택 단계의 completed/SKIP/WARN 상태를 사실대로 기록했습니다.
- [ ] 외부 데이터 provenance와 coverage를 확인했습니다.
- [ ] LLM 미실행을 사용 Evidence로 표현하지 않았습니다.
- [ ] 자동화 계획과 실행 Evidence를 구분했습니다.
- [ ] Project Validation을 확인했습니다.
- [ ] Reproducibility Manifest를 확인했습니다.
- [ ] Deliverable Manifest와 분석 Validation을 구분했습니다.
- [ ] Submission Status 근거가 있습니다.
- [ ] 재현 실행을 확인했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
