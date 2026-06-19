# Chapter 14 이미지 생성 프롬프트

LLM 기반 데이터 분석 실무 입문 교재의 Chapter 14 “Airflow 기반 데이터 분석 파이프라인”에 사용할 교육용 인포그래픽 이미지를 생성해 주세요.

전체 이미지 스타일은 다음 기준을 따릅니다.

* 한국어 교재용 이미지
* 16:9 비율
* 흰색 배경
* 네이비/블루 계열 중심
* 깔끔한 교육용 슬라이드 스타일
* Airflow, DAG, Task, Python 분석 스크립트, 데이터 파이프라인, 실패 재시도, 결과 검증 흐름을 직관적으로 표현
* 너무 많은 텍스트는 피하고 핵심 키워드 중심
* 아이콘, 카드, 화살표, DAG 노드, 체크리스트를 활용
* 실제 사람 사진은 사용하지 않음
* 전문적이지만 초보자도 이해하기 쉬운 시각 자료
* 각 이미지는 독립적인 PNG로 사용할 수 있게 구성

생성할 이미지는 총 5개입니다.

## 이미지 1

파일명:

```text id="cbmo41"
ch14_airflow_pipeline_overview.png
```

이미지 제목:

```text id="j4yc2s"
Airflow 기반 데이터 분석 파이프라인 전체 흐름도
```

이미지 내용:

온라인 쇼핑몰 데이터 분석 과정이 Airflow DAG로 자동 실행되는 전체 흐름을 표현해 주세요.

포함할 단계:

1. 원본 CSV 확인
2. 데이터 전처리
3. pandas 분석
4. 시각화 생성
5. Markdown 보고서 생성
6. 결과 파일 검증
7. 실행 로그 확인
8. 필요 시 Make로 보고서 발송

시각 구성:

* 왼쪽에서 오른쪽으로 흐르는 파이프라인
* 각 단계는 Airflow Task 카드 형태
* CSV 아이콘, Python 아이콘, pandas 표 아이콘, 그래프 아이콘, 보고서 아이콘, 체크 아이콘 사용
* Airflow가 전체 흐름을 관리하는 느낌
* 하단에 핵심 문구 삽입

하단 문구:

```text id="4szmw5"
Airflow는 분석 작업의 순서, 실행 상태, 실패 여부를 관리하는 파이프라인 도구입니다.
```

캡션:

```text id="i4ul1h"
그림 14-1. Airflow 기반 데이터 분석 파이프라인 전체 흐름도
```

## 이미지 2

파일명:

```text id="qthcjj"
ch14_airflow_dag_structure.png
```

이미지 제목:

```text id="0et20q"
Airflow DAG와 Task 구조
```

이미지 내용:

Airflow의 핵심 개념인 DAG, Task, Operator, Dependency를 시각화해 주세요.

포함할 요소:

1. DAG

   * 전체 작업 흐름

2. Task

   * 개별 작업 노드

3. Operator

   * BashOperator
   * PythonOperator

4. Dependency

   * 작업 순서 화살표

5. Schedule

   * 수동 실행 또는 정기 실행

시각 구성:

* 중앙에 DAG 그래프 형태
* 여러 Task 노드를 화살표로 연결
* 각 Task 아래에 Operator 라벨 표시
* 오른쪽에 개념 설명 카드 배치
* 초보자가 DAG와 Task 관계를 직관적으로 이해할 수 있게 구성

하단 문구:

```text id="0s51ql"
DAG는 전체 흐름이고, Task는 DAG 안에서 실행되는 개별 작업입니다.
```

캡션:

```text id="7h1b3a"
그림 14-2. Airflow DAG와 Task 구조
```

## 이미지 3

파일명:

```text id="m62fyx"
ch14_python_airflow_role_split.png
```

이미지 제목:

```text id="d6c2nq"
Python 분석 스크립트와 Airflow DAG의 역할 분담
```

이미지 내용:

Python 스크립트와 Airflow DAG가 각각 어떤 역할을 담당하는지 비교해 주세요.

왼쪽 Python 스크립트 영역:

* 입력 파일 확인
* 전처리
* 분석
* 시각화
* 보고서 생성
* 결과 검증

오른쪽 Airflow DAG 영역:

* Task 순서 관리
* 스케줄 실행
* 실패 감지
* 재시도
* 로그 확인
* 상태 모니터링

중앙 연결:

* `scripts/*.py`
* `dags/ch14_analysis_pipeline_dag.py`

시각 구성:

* 2열 비교 구조
* 왼쪽은 코드 파일 아이콘 중심
* 오른쪽은 DAG 노드와 모니터링 아이콘 중심
* 중앙에는 “분석 로직은 scripts, 실행 관리는 Airflow” 메시지 표시

하단 문구:

```text id="s4ktuy"
분석 로직은 Python 스크립트에 두고, Airflow는 실행 흐름을 관리하도록 구성합니다.
```

캡션:

```text id="bhpah8"
그림 14-3. Python 분석 스크립트와 Airflow DAG의 역할 분담
```

## 이미지 4

파일명:

```text id="535x7k"
ch14_airflow_task_dependency.png
```

이미지 제목:

```text id="rj5l2e"
Airflow Task 의존성과 재시도 흐름
```

이미지 내용:

Airflow Task들이 순서대로 실행되고, 실패 시 재시도되는 흐름을 표현해 주세요.

Task 순서:

1. `check_input_files`
2. `run_preprocessing`
3. `run_analysis`
4. `generate_visualizations`
5. `generate_report`
6. `validate_outputs`

추가 요소:

* 성공 시 다음 Task 실행
* 실패 시 retry
* retry 실패 시 pipeline stop
* Airflow log 확인

시각 구성:

* Task 노드를 순서대로 연결
* 각 Task에 성공 체크 아이콘
* 실패 지점에서 주황색 retry 루프 표시
* 마지막에 검증 완료 카드 표시
* Airflow UI의 실행 상태 느낌을 단순화해서 표현

하단 문구:

```text id="1n7zw0"
Task 의존성을 명확히 설정하면 실패한 단계 이후의 작업이 잘못 실행되는 것을 막을 수 있습니다.
```

캡션:

```text id="jupq4x"
그림 14-4. Airflow Task 의존성과 재시도 흐름
```

## 이미지 5

파일명:

```text id="2lr2o0"
ch14_pipeline_monitoring_retry_flow.png
```

이미지 제목:

```text id="c33pgy"
Airflow 파이프라인 모니터링과 재시도 흐름
```

이미지 내용:

Airflow에서 파이프라인 실행 상태를 모니터링하고 실패 Task를 확인·재실행하는 과정을 표현해 주세요.

포함할 단계:

1. DAG 실행 시작
2. Task별 상태 확인
3. 성공 Task 확인
4. 실패 Task 로그 확인
5. 원인 수정
6. 실패 Task 재실행
7. 결과 파일 검증
8. 최종 완료

시각 구성:

* Airflow UI를 추상화한 대시보드 형태
* Task 상태를 색상으로 표시

  * 성공: 초록색
  * 실패: 주황색 또는 빨간색
  * 대기: 회색
* 오른쪽에는 로그 확인 카드
* 아래쪽에는 “수정 후 재실행” 루프 표현

하단 문구:

```text id="gxq3jj"
Airflow의 장점은 실패 지점을 확인하고 필요한 Task만 다시 실행할 수 있다는 점입니다.
```

캡션:

```text id="afwunu"
그림 14-5. Airflow 파이프라인 모니터링과 재시도 흐름
```

## 공통 디자인 요구사항

모든 이미지는 다음 스타일을 유지해 주세요.

* 배경: 흰색
* 주요 색상: 네이비, 블루, 연한 하늘색
* 강조 색상: Airflow/DAG는 보라색, 성공은 초록색, 오류와 재시도는 주황색
* 글꼴 느낌: 깔끔한 고딕체
* 분위기: 대학교 강의 교재, 실무형 데이터 분석 교재
* 구성: 카드, DAG 노드, 화살표, 아이콘, 체크리스트 중심
* 출력: PNG 이미지로 사용할 수 있는 선명한 고해상도
* 한국어 텍스트는 오탈자 없이 자연스럽게 표현

이미지 안에 너무 긴 문장은 넣지 말고, 핵심 키워드와 짧은 설명 중심으로 구성해 주세요.

## 저장 경로

생성한 이미지는 아래 폴더에 저장해 주세요.

```text id="9ji9kt"
book/assets/images/ch14/
```

권장 파일명은 다음 5개입니다.

```text id="4h6wta"
ch14_airflow_pipeline_overview.png
ch14_airflow_dag_structure.png
ch14_python_airflow_role_split.png
ch14_airflow_task_dependency.png
ch14_pipeline_monitoring_retry_flow.png
```
