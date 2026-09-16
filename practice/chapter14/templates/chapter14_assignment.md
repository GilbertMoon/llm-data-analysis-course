# Chapter 14 답안 양식. 반복되는 분석 흐름을 안전하게 자동화하기

> 이 내용을 `chapter14.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. Local Pipeline 검증
- 실행 명령:
- 입력 데이터:
- 생성 산출물:
- Pipeline Run ID:
- Validation 결과:

![로컬 파이프라인](images/step01_local_pipeline.png)

### 결과 관찰

### 나의 해석과 판단
Airflow 전에 Local Pipeline을 검증해야 하는 이유를 작성하세요.

### 데이터 계약 확인
- [ ] `customers.customer_id`
- [ ] `products.product_id`
- [ ] `orders.order_id`
- [ ] `order_items.order_item_id`
- [ ] FK 관계
- [ ] `line_total = quantity × unit_price`
- [ ] `order_status == "completed"` 집계 범위

## 2. 같은 입력 재실행과 멱등성
| 항목 | 1차 실행 | 2차 실행 | 차이/판단 |
| --- | --- | --- | --- |
| Pipeline Run ID | | | |
| 핵심 결과 | | | |
| 생성 파일 | | | |
| 행 수/총합 | | | |
| 중복 누적 | | | |

### 나의 해석과 판단
파일 전체 교체 방식이 왜 도움이 되는지, 그리고 파일 단위 atomicity가 전체 파이프라인 transaction과 같은 것은 아닌 이유를 작성하세요.

## 3. 같은 Run 산출물 검증
- daily CSV Run ID:
- category CSV Run ID:
- metadata Run ID:
- report Run ID:
- 서로 일치하는가: YES / NO

### 판단
최신 mtime만 확인하는 것과 Run ID를 확인하는 것은 무엇이 다른가요?

## 4. Freshness와 교차 집계
- latest raw mtime:
- 주요 output mtime:
- freshness 상태:
- daily completed amount total:
- category completed amount total:
- 차이:
- category ratio sum:

### 나의 해석과 판단
파일이 존재한다는 사실만으로 왜 PASS라고 할 수 없는지 작성하세요.

## 5. Artifact Manifest
- Manifest 경로: `reports/ch14_artifact_manifest.csv`
- 포함된 artifact 수:
- Pipeline Run ID:
- SHA-256 기록 여부:

### 판단
SHA-256이 증명하는 것과 증명하지 못하는 것을 구분해 작성하세요.

## 6. Task 계약
| Task | 입력 | 출력 | 실패 기준 | Retry 여부 | 이유 |
| --- | --- | --- | --- | --- | --- |
| check_input_files | | | | | |
| run_preprocessing | | | | | |
| run_analysis | | | | | |
| generate_visualizations | | | | | |
| generate_report | | | | | |
| validate_outputs | | | | | |

### Retry하면 안 되는 오류 사례

### 제한적으로 Retry할 수 있는 오류 사례

## 7. Docker와 Airflow 환경
- Docker version:
- Docker Compose version:
- hello-world 결과:
- Airflow version:
- `airflow-init` 결과:

![Docker 확인](images/step07_docker.png)

### Secret 확인
- [ ] `.env.example`에는 실제 Secret이 없음
- [ ] 실제 `.env`는 Git에 올리지 않음
- [ ] 캡처·Notebook·로그에 Secret이 없음

### 환경 오류가 있었다면
- 오류:
- 원인 판단:
- 해결:
- 임의로 `chmod -R 777` 같은 보안 완화부터 하지 않은 이유:

## 8. Canonical DAG와 Task 실행
Canonical DAG:

```text
automation/airflow/dags/ch14_local_analysis_pipeline.py
```

![Airflow DAG](images/step08_dag.png)
![Task 상태](images/step08_tasks.png)

- DAG Run ID:
- 실행 시각:
- `schedule=None` 확인:
- `catchup=False` 확인:
- `max_active_runs=1` 확인:
- Task별 timeout 확인:
- Task 상태:
- 실패 Task가 있다면 첫 원인:

### DAG 의존성 관찰
`run_analysis` 이후 visualization/report가 분기되고 최종 validation에서 합류했는지 작성하세요.

### 나의 해석과 판단
Task가 모두 초록색이어도 분석 성공을 확정할 수 없는 이유를 작성하세요.

## 9. 최종 산출물 Validation
- 파일 존재:
- 읽기 가능 여부:
- 이번 Run 결과 여부:
- 행/컬럼 검증:
- 총합 검증:
- category 비율 검증:
- freshness:
- mixed-run 여부:
- 보고서 Scope:
- 최종 Validation: PASS / FAIL

![최종 Validation](images/step09_validation.png)

### 나의 해석과 판단
어떤 Evidence 때문에 PASS/FAIL로 판단했는지 작성하세요.

## 10. 실패와 재시도 판단
- 선택한 오류 사례:
- transient / deterministic:
- retry 여부:
- timeout/횟수 제한:
- 다음 단계 전달 가능 여부:

### 판단 이유

## 11. 외부 전달 Gate
```text
Task 성공
AND
validate_outputs PASS
→ 외부 전달 가능
```

### 내가 설계한 전달 조건

### 중복 전달 방지 방법
Airflow Dag Run ID 또는 별도의 delivery idempotency key가 왜 필요한지 작성하세요.

## 12. 종료와 초기화
- 일반 종료 명령:
- 파괴적 초기화 명령:
- 두 명령의 차이:
- 파괴적 초기화를 실행해도 되는 상황:

## 13. Chapter 14 최종 판단
### 자동화의 가장 큰 이점

### 자동화의 가장 큰 위험

### 사람이 반드시 유지해야 할 Validation

### 로컬 학습 Compose를 운영 환경으로 그대로 사용하면 안 되는 이유

### Chapter 15 최종 프로젝트에 재사용할 자동화 원칙

## 최종 체크
- [ ] Local Pipeline PASS를 확인했습니다.
- [ ] `order_item_id` 포함 PK/FK와 금액식을 검증했습니다.
- [ ] completed 집계 Scope를 확인했습니다.
- [ ] Pipeline Run ID를 비교했습니다.
- [ ] Freshness와 집계 총합을 검증했습니다.
- [ ] Artifact Manifest를 확인했습니다.
- [ ] 같은 입력 재실행과 멱등성을 확인했습니다.
- [ ] Task 계약과 retry 근거를 작성했습니다.
- [ ] Docker/Airflow Evidence가 있습니다.
- [ ] Task Green과 Validation PASS를 구분했습니다.
- [ ] 외부 전달 Gate를 설명했습니다.
- [ ] Secret이 없습니다.
- [ ] 일반 종료와 파괴적 초기화를 구분했습니다.
- [ ] 최종 Notebook URL을 제출합니다.
