# 14장 실습. 반복되는 분석 흐름을 안전하게 자동화하기

> 목표는 Airflow 화면을 띄우는 것이 아니라 **검증된 로컬 분석을 반복 실행 가능한 Task로 나누고, 같은 실행의 산출물인지 검증하고, 실패·재시도·멱등성·Freshness를 확인한 뒤 Validation을 통과한 결과만 다음 단계로 전달하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter14/templates/chapter14_assignment.md`
- 주 제출물: `chapter14/chapter14.ipynb`

공식 Notebook:

```text
notebooks/ch14_airflow_pipeline.ipynb
```

Canonical DAG:

```text
automation/airflow/dags/ch14_local_analysis_pipeline.py
```

로컬 실행:

```text
scripts/run_ch14_pipeline.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 `chapter14/chapter14.ipynb`로 사용합니다. Docker/Airflow UI와 터미널 Evidence는 `chapter14/images/`에 저장합니다.

## STEP 1. Airflow 전에 Local Pipeline PASS
프로젝트 루트에서 먼저 실행합니다.

```powershell
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py
```

확인할 것:
- raw CSV 4개가 존재하고 0 byte가 아닌가
- `customers.customer_id`, `products.product_id`, `orders.order_id`, `order_items.order_item_id` PK가 정상인가
- FK와 `line_total = quantity × unit_price`가 정상인가
- 금액성 집계 범위가 `order_status == "completed"`인가
- daily/category 총합이 일치하는가
- Validation Log가 모두 `ok`인가

```text
Local Python PASS
→ Validation PASS
→ 그다음 Airflow
```

## STEP 2. Pipeline Run ID와 같은 실행 결과 확인
실행 후 다음 파일을 확인합니다.

```text
reports/ch14_daily_sales.csv
reports/ch14_category_sales.csv
reports/ch14_pipeline_run_metadata.csv
reports/ch14_airflow_report.md
```

관련 산출물은 같은 `pipeline_run_id`를 가져야 합니다.

```text
파일 존재 = PASS가 아님
mtime 최신 = 같은 실행 결과라는 뜻이 아님
```

답안에는 실제 Run ID와 서로 일치했는지 기록합니다.

## STEP 3. 같은 입력 재실행과 멱등성 확인
같은 입력으로 `python scripts/run_ch14_pipeline.py`를 다시 실행합니다.

확인할 것:
- CSV가 append되어 행이 두 배로 늘지 않는가
- 이전 실행과 현재 실행 산출물이 섞이지 않는가
- 결과 파일은 전체 재생성 후 교체되는가
- 새 실행에는 새로운 `pipeline_run_id`가 부여되는가

파일 하나의 원자적 교체는 여러 파일 전체의 transaction과 같지 않습니다. 그래서 Run ID 검증이 필요합니다.

## STEP 4. Task 계약 정리
각 Task의 입력·출력·실패 기준·retry 정책을 정리합니다.

| Task | 입력 | 출력 | 대표 실패 | 기본 retry |
| --- | --- | --- | --- | --- |
| `check_input_files` | raw CSV | 입력 상태 | 누락·0 byte | 0 |
| `run_preprocessing` | raw CSV | processed CSV | schema·PK·FK·금액식 오류 | 0 |
| `run_analysis` | processed CSV | 집계·Run Metadata | completed 0건·관계·총합 오류 | 0 |
| `generate_visualizations` | 검증된 집계 | PNG | 일시적 저장 실패 등 | 최대 1회 예시 |
| `generate_report` | 집계·Run Metadata | Markdown | Run ID 불일치 | 0 |
| `validate_outputs` | 전체 산출물 | Validation Log | Freshness·Run ID·총합·Scope 오류 | 0 |

결정적 데이터 오류는 blind retry하지 않습니다.

## STEP 5. Freshness와 교차 집계 검증
Validation Evidence에서 다음을 확인합니다.

```text
output mtime >= latest raw mtime
completed source total = daily total = category total
category amount ratio ≈ 100%
```

오래된 파일이 남아 있는 것과 이번 실행의 정상 결과는 구분합니다.

## STEP 6. Artifact Manifest 확인
로컬 파이프라인은 주요 산출물의 manifest를 만듭니다.

```text
reports/ch14_artifact_manifest.csv
```

확인할 항목:
- artifact 경로
- `pipeline_run_id`
- 생성 시각
- 파일 크기
- SHA-256

SHA-256은 파일 내용 변경 확인용이며 분석 타당성 보증이 아닙니다.

## STEP 7. Docker Compose 환경 확인
다음을 확인합니다.

```powershell
docker --version
docker compose version
docker run --rm hello-world
```

Docker가 정상이어도 분석 결과가 정확하다는 뜻은 아닙니다.

`.env.example`의 Secret 값은 빈 상태가 정상이며 실제 값은 untracked `.env`에만 설정합니다.

```text
AIRFLOW_DB_PASSWORD=
AIRFLOW_API_JWT_SECRET=
_AIRFLOW_WWW_USER_PASSWORD=
```

실제 Secret은 Notebook·로그·캡처·Git에 남기지 않습니다.

## STEP 8. Airflow 초기화와 Canonical DAG 확인
`docs/ch14_docker_airflow_guide.md`를 따라 실행합니다.

```powershell
cd automation/airflow
Copy-Item .env.example .env
# 실제 .env에서 서로 다른 Secret을 설정

docker compose build
docker compose up airflow-init
docker compose up -d
docker compose ps
```

Canonical DAG는 하나만 사용합니다.

```text
automation/airflow/dags/ch14_local_analysis_pipeline.py
```

루트 `dags/ch14_local_analysis_pipeline.py`는 legacy 안내 파일이며 실제 DAG를 정의하지 않습니다.

## STEP 9. DAG 수동 실행과 Task 의존성 확인
처음에는 `schedule=None` 상태에서 수동 실행합니다.

```text
check_input_files
→ run_preprocessing
→ run_analysis
   ├→ generate_visualizations ─┐
   └→ generate_report ─────────┤
                              ↓
                       validate_outputs
```

확인할 설정:
- `catchup=False`
- `max_active_runs=1`
- `max_active_tasks=2`
- 기본 `retries=0`
- Task별 `execution_timeout`
- 시각화 Task만 제한적 1회 retry 예시

Task가 모두 초록색이어도 최종 `validate_outputs`가 실패하면 배포 가능한 성공이 아닙니다.

## STEP 10. 실패와 Retry 판단
다음 중 하나의 실패 사례를 선택하거나 안전한 샘플 복사본에서 재현합니다.

```text
입력 파일 누락
PK 중복
FK 미매칭
line_total 불일치
Run ID 불일치
일시적 파일 쓰기 실패
```

답안에 다음을 기록합니다.

```text
오류 유형
→ deterministic / transient
→ retry 여부
→ retry 횟수·timeout 제한 이유
→ 다음 단계 전달 가능 여부
```

실제 업무 raw 데이터는 삭제하지 않습니다.

## STEP 11. 외부 전달 Gate 설계
Make/n8n/Gmail/Slack/Drive 같은 side effect는 분석과 분리합니다.

```text
Task 성공
AND
validate_outputs PASS
→ 외부 전달 가능
```

재실행·retry로 같은 보고서가 중복 발송되지 않도록 Airflow Dag Run ID 또는 별도의 delivery idempotency key를 둡니다.

## STEP 12. 종료와 파괴적 초기화 구분
일반 종료:

```powershell
docker compose down
```

학습 환경을 완전히 초기화할 의도가 있을 때만:

```powershell
docker compose down --volumes --remove-orphans
```

두 번째 명령은 Postgres volume, 실행 기록과 계정 metadata를 삭제할 수 있습니다.

## STEP 13. 최종 판단
답안에 다음을 작성합니다.

1. Airflow 전에 Local Pipeline을 검증해야 하는 이유
2. Pipeline Run ID가 필요한 이유
3. 파일 단위 atomicity와 전체 transaction의 차이
4. Freshness만으로 mixed-run을 막을 수 없는 이유
5. retry하면 안 되는 오류와 제한적으로 retry할 수 있는 오류
6. Task Green과 Validation PASS의 차이
7. 외부 전달을 Validation 뒤에 두어야 하는 이유
8. 로컬 Compose 환경을 운영 환경으로 그대로 사용하면 안 되는 이유

## 최종 제출

```text
chapter14/
├─ chapter14.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter14/chapter14.ipynb
```

## 완료 체크
- [ ] Local Pipeline PASS 확인
- [ ] `order_item_id` 포함 PK/FK·금액식 검증
- [ ] completed 집계 Scope 확인
- [ ] Pipeline Run ID 일치 확인
- [ ] Freshness·daily/category 총합 확인
- [ ] Artifact Manifest 확인
- [ ] 같은 입력 재실행과 멱등성 확인
- [ ] Task 계약과 retry 근거 작성
- [ ] Canonical DAG 수동 실행 Evidence
- [ ] Task Green과 Validation PASS 구분
- [ ] Secret 비노출 확인
- [ ] 외부 전달 Gate 설명
- [ ] 일반 종료와 파괴적 초기화 구분
- [ ] 최종 Notebook URL 제출
