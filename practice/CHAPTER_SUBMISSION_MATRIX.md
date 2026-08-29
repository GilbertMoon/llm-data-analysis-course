# Chapter별 제출 형식 및 Evidence 기준

이 문서는 `practice/SUBMISSION_GUIDE.md`의 공통 원칙을 각 Chapter에 어떻게 적용할지 정리한 표입니다.

기본 원칙은 동일합니다.

```text
실행
→ 결과
→ 관찰
→ 나의 해석과 판단
→ 업무·분석적 의미
→ 한계와 추가 확인 사항
→ GitHub 업로드
→ 최종 파일 URL 제출
```

## 제출 파일 형식

| Chapter | 주 제출 파일 | 핵심 Evidence | 반드시 작성할 해석 요소 |
| ---: | --- | --- | --- |
| 01 | `chapter01.md` | 질문 정의, LLM Prompt, 검증 결과 | LLM 채택/수정/보류 이유, 남은 검증 |
| 02 | `chapter02.md` | Python/Git 버전, `.venv`, 커널, `customers.head()`, Secret 보호 | 왜 해당 환경을 선택했는지, 오류 원인 판단, 재현 가능성 |
| 03 | `chapter03.ipynb` | shape, dtypes, 결측/중복, PK/FK, 날짜 변환 | 데이터의 첫인상, 이상 신호, 추가 점검 우선순위 |
| 04 | `chapter04.ipynb` | 필터, 파생 컬럼, merge 검증, groupby, 총합 일치 | 집계 결과 의미, merge 위험, 업무상 다음 질문 |
| 05 | `chapter05.ipynb` | 처리 전/후 비교, 변환 실패, 중복, clean CSV, 재실행 | 왜 그 처리 기준을 선택했는지, 정보 손실 가능성, 한계 |
| 06 | `chapter06.ipynb` | EDA 질문, 핵심 집계, 총합 검증, 다음 질문 | 관찰/가설/추가 검증을 분리하여 작성 |
| 07 | `chapter07.ipynb` | bar/line/distribution 그래프, 축·단위·범례 | 그래프가 보여 주는 사실, 오해 가능성, 업무적 의미 |
| 08 | `chapter08.ipynb` | 질문→전처리→EDA→시각화→보고서 흐름 | 핵심 인사이트, 근거, 한계, 다음 분석 제안 |
| 09 | `chapter09.ipynb` | 예측 시점, leakage 점검, 시간 분할, baseline, MAE/RMSE 등 | 모델을 신뢰할 수 있는 범위, baseline 대비 가치, 한계 |
| 10 | `chapter10.ipynb` | 클래스 비율, Dummy baseline, precision/recall/F1, threshold, FP/FN | 어떤 오류가 더 중요한지, threshold 선택 이유, 실제 사용 가능성 |
| 11 | `chapter11.ipynb` | Safe Context, Prompt, LLM 응답, 검증 기록 | 채택/수정/보류 이유, 사람이 추가한 판단, 남은 불확실성 |
| 12 | `chapter12.ipynb` | Read Before Run, 위험 스캔, 승인, 제한 실행, 사후 검증 | 왜 실행을 허용/보류했는지, 정적 점검의 한계, 변경 이유 |
| 13 | `chapter13.ipynb` | 공식 출처, 기준일, 이용조건, raw snapshot, metadata, merge | 외부 데이터가 준 추가 맥락, 대표성/시점/인과 해석 한계 |
| 14 | `chapter14.ipynb` | 로컬 파이프라인, 산출물 Validation, Docker/Airflow, DAG/Task 상태 | Task 성공과 분석 성공의 차이, 재시도/멱등성, 운영 위험 |
| 15 | `chapter15.ipynb` | 프로젝트 Validation, manifest, Submission Status, 재현 실행 | 최종 결론, 근거, 선택/생략 이유, READY/WARN/BLOCKED 판단 근거 |

## Markdown 제출 장

Chapter 01~02는 문서 작성과 환경 Evidence 비중이 높으므로 Markdown 제출을 기본으로 합니다.

```text
chapter01/chapter01.md
chapter02/chapter02.md
```

## Notebook 제출 장

Chapter 03~15는 실행 결과가 Notebook에 남기 때문에 실행 완료 Notebook을 주 제출물로 사용합니다.

학생은 공식 Notebook을 복사해 자신의 저장소에 다음처럼 저장합니다.

```text
chapter03/chapter03.ipynb
...
chapter15/chapter15.ipynb
```

Notebook에는 코드 셀만 두지 않습니다. 핵심 분석 구간마다 Markdown 셀을 추가해 다음 내용을 작성합니다.

```markdown
### 결과 관찰
데이터와 출력에서 직접 확인한 사실

### 나의 해석과 판단
그 사실을 바탕으로 내린 분석적 판단

### 업무·분석적 의미
실제 의사결정이나 다음 분석에 어떤 의미가 있는지

### 한계와 추가 확인 사항
현재 결과만으로 단정할 수 없는 것과 다음 검증
```

## Notebook 밖 Evidence

다음은 Notebook Output만으로 충분히 남기기 어려우므로 `images/` 폴더에 캡처를 저장합니다.

- VS Code 인터프리터/커널
- 터미널 환경 확인
- LLM Prompt와 응답 화면
- API/외부 서비스 응답 화면
- Docker/Airflow UI
- 오류 해결 전·후 화면
- GitHub 최종 제출 화면

## 제출 URL

저장소 URL이 아니라 해당 Chapter의 최종 파일 URL을 제출합니다.

Markdown 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter02/chapter02.md
```

Notebook 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
```

## 공통 평가 포인트

```text
실행 성공
+ 결과 정확성
+ Evidence
+ 데이터에 근거한 관찰
+ 학생의 해석과 판단
+ 업무적 의미
+ 한계 인식
+ 재현 가능성
+ GitHub 제출 완성도
```

**코드가 실행되었다는 사실만으로 완료 처리하지 않습니다.**