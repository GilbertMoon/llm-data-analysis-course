# Chapter 15 답안 양식. 하나의 데이터 분석 프로젝트로 완성하기

> 이 내용을 `chapter15.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:
- 최종 Submission Status: READY / READY_WITH_WARNINGS / BLOCKED

## 1. 프로젝트 질문과 범위
### 분석 질문

### 금액 범위
```text
order_status == completed
line_total = quantity × unit_price
```

### 필수 단계

### 선택 단계와 선택/미선택 이유

### 완료 기준

## 2. 데이터와 PK/FK 검증
| 관계 | 검증 결과 | 미매칭/중복 | 판단 |
| --- | --- | ---: | --- |
| orders.customer_id → customers.customer_id | | | |
| order_items.order_id → orders.order_id | | | |
| order_items.product_id → products.product_id | | | |

![PK FK 검증](images/step02_keys.png)

### 나의 해석과 판단
병합이 안전하다고 판단한 근거를 작성하세요.

## 3. completed 금액 총합 불변식
| 집계 | 총합 |
| --- | ---: |
| completed 전체 | |
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
- 수치/그래프:
- 결과 관찰:
- 나의 해석과 판단:
- 업무·분석적 의미:
- 한계:

### 핵심 결과 2
- 수치/그래프:
- 결과 관찰:
- 나의 해석과 판단:
- 업무·분석적 의미:
- 한계:

### 핵심 결과 3
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
- [ ] 기타 식별 가능 정보 확인

### 공개 결과에 사용한 익명화 방식

## 6. 선택 단계 — 분류
- 실행 상태: executed / skipped
- SKIP 사유(해당 시):
- 타깃/feature 계약:
- baseline:
- validation 선택:
- final test:
- 공개 prediction 식별자 제거 여부:

### 결과 관찰

### 나의 해석과 판단
이 모델이 프로젝트 질문에 실제로 추가한 가치가 있는지 작성하세요.

### 한계

## 7. 선택 단계 — 외부 데이터
- 실행 상태: executed / skipped
- Provider:
- Source URL:
- Data Reference Date:
- License/Terms:
- Coverage/Key 검증:
- SKIP 사유(해당 시):

### 나의 해석과 판단
외부 데이터가 실제로 추가한 맥락과 인과 해석 한계를 작성하세요.

## 8. 선택 단계 — LLM Evidence
- execution_status:
- provider/model:
- executed_at:
- prompt_version:
- validation:
- 사람이 수정한 내용:
- final_use:

### 미실행이라면
```text
execution_status = not_executed
final_use = not_used
```

### 나의 해석과 판단
LLM 사용 여부를 사실대로 기록하는 것이 왜 중요한지 작성하세요.

## 9. 자동화 계획과 실행 구분
- 자동화 계획 문서 존재 여부:
- 실제 자동화 실행 Evidence 존재 여부:
- DAG/run/log/Validation 등 실제 Evidence:

### 나의 해석과 판단
계획 문서가 실행 증거가 아닌 이유를 작성하세요.

## 10. Project Validation
| 검증 항목 | Required | 결과 PASS/WARN/FAIL | Evidence |
| --- | --- | --- | --- |
| 핵심 데이터 품질 | Y | | |
| PK/FK/merge | Y | | |
| 총합 불변식 | Y | | |
| 공개 개인정보 | Y | | |
| 선택 분류 | N | | |
| 선택 외부 데이터 | N | | |
| 선택 LLM | N | | |
| 자동화/재현 | 조건별 | | |

![Project Validation](images/step10_validation.png)

### 필수 FAIL 여부

## 11. Manifest
- Manifest 파일:
- required artifact 누락:
- nonempty 실패:
- SHA-256 기록 여부:

![Manifest](images/step11_manifest.png)

### 나의 해석과 판단
SHA-256이 분석 타당성을 증명하지 않는 이유를 작성하세요.

## 12. Submission Status
- [ ] READY
- [ ] READY_WITH_WARNINGS
- [ ] BLOCKED

### 선택한 상태의 근거
1.
2.
3.

### WARN이 있다면

### BLOCKED라면 해소해야 할 항목

## 13. 재현 실행
- 시작 조건/환경:
- 실행 순서:
- 재실행 후 completed total:
- 필수 산출물 재생성 여부:
- Validation 결과:
- Manifest 갱신 여부:

![재현 실행](images/step13_reproduce.png)

### 나의 해석과 판단
다른 사람이 이 프로젝트를 재현할 수 있다고 보는 근거를 작성하세요.

## 14. 최종 분석 결론
### 프로젝트 질문에 대한 답

### 핵심 근거 3개
1.
2.
3.

### 업무적으로 제안하는 행동/추가 검토
1.
2.
3.

### 현재 결과로 말할 수 없는 것

### 추가로 필요한 데이터/검증

### 프로젝트를 다시 한다면 바꾸고 싶은 점

## 최종 체크
- [ ] 질문과 범위가 명확합니다.
- [ ] PK/FK와 merge를 검증했습니다.
- [ ] 총합 불변식이 PASS이거나 FAIL을 BLOCKED로 처리했습니다.
- [ ] 결과 해석과 한계를 작성했습니다.
- [ ] 개인정보를 제거했습니다.
- [ ] 선택 단계의 실행/SKIP 상태를 사실대로 기록했습니다.
- [ ] LLM 미실행을 PASS로 표현하지 않았습니다.
- [ ] Manifest와 분석 Validation을 구분했습니다.
- [ ] Submission Status 근거가 있습니다.
- [ ] 재현 실행을 확인했습니다.
- [ ] 최종 Notebook URL을 제출합니다.