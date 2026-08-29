# Chapter 14 답안 양식. 반복되는 분석 흐름을 안전하게 자동화하기

> 이 내용을 `chapter14.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. 로컬 파이프라인 검증
- 실행 명령:
- 입력 데이터:
- 생성 산출물:
- Validation 결과:

![로컬 파이프라인](images/step01_local_pipeline.png)

### 결과 관찰

### 나의 해석과 판단
Airflow 전에 로컬 분석을 검증해야 하는 이유를 작성하세요.

### 한계와 추가 확인 사항

## 2. 같은 입력 재실행과 멱등성
| 항목 | 1차 실행 | 2차 실행 | 차이/판단 |
| --- | --- | --- | --- |
| 핵심 결과 | | | |
| 생성 파일 | | | |
| 행 수/총합 | | | |
| 중복 누적 | | | |

### 나의 해석과 판단
이 파이프라인이 충분히 멱등적이라고 보는지와 근거를 작성하세요.

## 3. Task 계약
| Task | 입력 | 출력 | 실패 기준 | Retry 여부 | 이유 |
| --- | --- | --- | --- | --- | --- |
| preprocessing | | | | | |
| analysis | | | | | |
| visualization/report | | | | | |
| validation | | | | | |

### Retry하면 안 되는 오류 사례

### Retry할 수 있는 오류 사례

## 4. Docker와 Airflow 환경
- Docker version:
- Docker Compose version:
- hello-world 결과:
- Airflow 초기화 결과:

![Docker 확인](images/step04_docker.png)

### 환경 오류가 있었다면
- 오류:
- 원인 판단:
- 해결:
- 임의로 보안 설정을 변경하지 않은 이유:

## 5. DAG와 Task 실행
![Airflow DAG](images/step05_dag.png)
![Task 상태](images/step05_tasks.png)

- DAG 실행 시각/run:
- Task 상태:
- 실패 Task가 있다면 원인:

### 결과 관찰

### 나의 해석과 판단
Task가 모두 초록색이어도 분석 성공을 확정할 수 없는 이유를 작성하세요.

## 6. 최종 산출물 Validation
- 파일 존재:
- 이번 run 결과 여부:
- 행/컬럼 검증:
- 총합/핵심 수치 검증:
- freshness:
- mixed-run 여부:
- 최종 Validation: PASS / FAIL

![최종 Validation](images/step06_validation.png)

### 나의 해석과 판단
어떤 Evidence 때문에 PASS/FAIL로 판단했는지 작성하세요.

### 업무·분석적 의미

### 한계와 추가 확인 사항

## 7. 실패와 재시도 판단
- 선택한 오류 사례:
- transient / deterministic:
- retry 여부:
- timeout/횟수 제한:
- 다음 단계 전달 가능 여부:

### 판단 이유

## 8. 외부 전달 Gate
```text
내가 설계한 전달 조건을 작성하세요.
```

### 중복 전달 방지 방법
run id / idempotency key 등이 왜 필요한지 작성하세요.

## 9. Chapter 14 최종 판단
### 자동화의 가장 큰 이점

### 자동화의 가장 큰 위험

### 사람이 반드시 유지해야 할 검증 단계

### 운영 환경으로 옮기기 전에 추가로 필요한 것

## 최종 체크
- [ ] 로컬 검증 후 자동화했습니다.
- [ ] 멱등성을 확인했습니다.
- [ ] Task 계약을 작성했습니다.
- [ ] Docker/Airflow Evidence가 있습니다.
- [ ] Task 성공과 결과 Validation을 구분했습니다.
- [ ] Retry 판단 근거가 있습니다.
- [ ] 외부 전달 Gate를 설명했습니다.
- [ ] Secret이 없습니다.
- [ ] 최종 Notebook URL을 제출합니다.