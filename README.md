# LLM 기반 데이터 분석 실무 입문
## 공식 실습 자료

이 저장소는 『LLM 기반 데이터 분석 실무 입문』의 **공식 학생 실습용 Companion Repository**입니다.

책 원고와 출판 제작 자료는 포함하지 않으며, 학생이 수업을 따라 실습하는 데 필요한 Python 코드, Jupyter Notebook, 샘플 데이터, Chapter별 실습 가이드, 답안 템플릿, API 및 자동화 예제를 제공합니다.

---

## 가장 먼저 확인하세요

학생 실습은 다음 문서를 기준으로 진행합니다.

```text
practice/README.md
practice/SUBMISSION_GUIDE.md
practice/CHAPTER_SUBMISSION_MATRIX.md
```

- `practice/README.md`: Overview~Chapter 15 실습 입구
- `practice/SUBMISSION_GUIDE.md`: 공통 답안 작성·Evidence·GitHub 제출 규칙
- `practice/CHAPTER_SUBMISSION_MATRIX.md`: Chapter별 주 제출 파일과 핵심 평가 포인트

> 기존 실습 문서에 과거 제출 방식 표현이 남아 있더라도 **제출 방식과 답안 형식은 위 공통 제출 문서와 각 Chapter의 `templates/`를 우선 적용합니다.**

---

## 실습 제출 방식

이 수업은 단순히 코드와 실행 화면만 제출하지 않습니다.

```text
강사 Public 저장소의 가이드/템플릿 확인
→ Markdown 또는 Notebook 다운로드/복사
→ 로컬에서 STEP별 실습
→ 핵심 실행 결과 Evidence 남기기
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub 저장소에 업로드
→ GitHub에서 최종 파일 정상 표시 확인
→ 해당 Chapter 최종 파일 URL 제출
```

핵심 STEP의 답안에는 가능한 한 다음 6개 요소가 들어갑니다.

```text
① 실행 코드 / Prompt / 수행 내용
② 실행 결과 또는 화면 캡처
③ 결과 관찰
④ 나의 해석과 판단
⑤ 업무·분석적 의미
⑥ 한계와 추가 확인 사항
```

**실행 결과는 답안의 시작이지 끝이 아닙니다.**

---

## 학생 개인 GitHub 저장소

권장 저장소 이름:

```text
llm-data-analysis-study
```

권장 구조:

```text
llm-data-analysis-study/
├─ chapter01/
│  ├─ chapter01.md
│  └─ images/
├─ chapter02/
│  ├─ chapter02.md
│  └─ images/
├─ chapter03/
│  ├─ chapter03.ipynb
│  └─ images/
...
└─ chapter15/
   ├─ chapter15.ipynb
   └─ images/
```

- Chapter 01~02: Markdown 제출 기본
- Chapter 03~15: 실행 완료 Notebook 제출 기본
- Notebook 밖의 터미널·LLM·Airflow 화면은 필요할 때 `images/`에 저장

제출 시 저장소 루트 URL이 아니라 **해당 Chapter 최종 파일 URL**을 제출합니다.

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter02/chapter02.md
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
```

Chapter 01은 Git 학습 전이므로 GitHub 웹 Upload를 사용해도 됩니다. Chapter 02 이후에는 local commit/push 방식을 권장합니다.

---

## Chapter별 실습 가이드와 답안 템플릿

| Chapter | 현재 주제 | 실습 가이드 | 답안 템플릿 | 최종 제출 파일 |
| ---: | --- | --- | --- | --- |
| 0 | 이 책의 방향과 전체 흐름 | `practice/overview/overview.md` | 안내형 | 준비 체크 |
| 1 | AI와 함께하는 데이터 분석의 시작 | `practice/chapter01/chapter01.md` | `practice/chapter01/templates/chapter01_assignment.md` | `chapter01.md` |
| 2 | VS Code에서 시작하는 데이터 분석 환경 | `practice/chapter02/chapter02.md` | `practice/chapter02/templates/chapter02_assignment.md` | `chapter02.md` |
| 3 | 데이터의 첫인상 읽기 | `practice/chapter03/chapter03.md` | `practice/chapter03/templates/chapter03_assignment.md` | `chapter03.ipynb` |
| 4 | pandas로 데이터에 질문하기 | `practice/chapter04/chapter04.md` | `practice/chapter04/templates/chapter04_assignment.md` | `chapter04.ipynb` |
| 5 | 분석을 믿을 수 있게 만드는 데이터 전처리 | `practice/chapter05/chapter05.md` | `practice/chapter05/templates/chapter05_assignment.md` | `chapter05.ipynb` |
| 6 | 데이터를 보며 질문을 만드는 EDA | `practice/chapter06/chapter06.md` | `practice/chapter06/templates/chapter06_assignment.md` | `chapter06.ipynb` |
| 7 | 그래프로 데이터의 이야기를 보여주기 | `practice/chapter07/chapter07.md` | `practice/chapter07/templates/chapter07_assignment.md` | `chapter07.ipynb` |
| 8 | 작은 데이터 분석 프로젝트 완성하기 | `practice/chapter08/chapter08.md` | `practice/chapter08/templates/chapter08_assignment.md` | `chapter08.ipynb` |
| 9 | 회귀 분석으로 숫자 예측하기 | `practice/chapter09/chapter09.md` | `practice/chapter09/templates/chapter09_assignment.md` | `chapter09.ipynb` |
| 10 | 분류 분석으로 주문 취소 여부 예측하기 | `practice/chapter10/chapter10.md` | `practice/chapter10/templates/chapter10_assignment.md` | `chapter10.ipynb` |
| 11 | LLM과 함께 분석 질문을 다듬기 | `practice/chapter11/chapter11.md` | `practice/chapter11/templates/chapter11_assignment.md` | `chapter11.ipynb` |
| 12 | LLM이 만든 분석 코드를 검증하는 방법 | `practice/chapter12/chapter12.md` | `practice/chapter12/templates/chapter12_assignment.md` | `chapter12.ipynb` |
| 13 | 외부 데이터로 분석을 확장하기 | `practice/chapter13/chapter13.md` | `practice/chapter13/templates/chapter13_assignment.md` | `chapter13.ipynb` |
| 14 | 반복되는 분석 흐름을 안전하게 자동화하기 | `practice/chapter14/chapter14.md` | `practice/chapter14/templates/chapter14_assignment.md` | `chapter14.ipynb` |
| 15 | 하나의 데이터 분석 프로젝트로 완성하기 | `practice/chapter15/chapter15.md` | `practice/chapter15/templates/chapter15_assignment.md` | `chapter15.ipynb` |

### Chapter 10·12 파일명 주의

일부 Notebook 파일명에는 과거 작업명이 남아 있습니다.

```text
Chapter 10 현재 주제: 분류 분석으로 주문 취소 여부 예측하기
공식 Notebook 파일명: notebooks/ch10_llm_code_generation.ipynb

Chapter 12 현재 주제: LLM이 만든 분석 코드를 검증하는 방법
공식 Notebook 파일명: notebooks/ch12_report_generation.ipynb
```

**파일명보다 현재 Chapter 제목, 실습 가이드와 Notebook 내부 H1을 우선합니다.**

---

## 주요 공식 Notebook

| Chapter | Notebook |
| ---: | --- |
| 1 | `notebooks/ch01_ai_data_analysis_intro.ipynb` |
| 2 | `notebooks/ch02_environment_setup.ipynb` |
| 3 | `notebooks/ch03_data_overview.ipynb` |
| 4 | `notebooks/ch04_pandas_basic.ipynb` |
| 5 | `notebooks/ch05_data_preprocessing.ipynb` |
| 6 | `notebooks/ch06_eda_questions.ipynb` |
| 7 | `notebooks/ch07_visualization.ipynb` |
| 8 | `notebooks/ch08_midterm_project.ipynb` |
| 9 | `notebooks/ch09_regression_analysis.ipynb` |
| 10 | `notebooks/ch10_llm_code_generation.ipynb` |
| 11 | `notebooks/ch11_llm_prompt_analysis.ipynb` |
| 12 | `notebooks/ch12_report_generation.ipynb` |
| 13 | `notebooks/ch13_external_data_collection.ipynb` |
| 14 | `notebooks/ch14_airflow_pipeline.ipynb` |
| 15 | `notebooks/ch15_final_project.ipynb` |

---

## Chapter별 해석 핵심

실행 방법은 달라도 학생이 자신의 말로 판단해야 한다는 원칙은 같습니다.

```text
Ch03  데이터 구조·품질에서 무엇을 먼저 의심해야 하는가?
Ch04  집계·merge 결과를 왜 믿을 수 있는가?
Ch05  전처리 규칙이 어떤 정보 손실을 만들 수 있는가?
Ch06  관찰·가설·추가 검증을 어떻게 구분했는가?
Ch07  그래프가 보여 주는 것과 보여 주지 못하는 것은 무엇인가?
Ch08  어떤 Evidence로 핵심 인사이트를 뒷받침하는가?
Ch09  leakage 없이 baseline보다 실제로 나아졌는가?
Ch10  FP/FN 중 어떤 오류를 더 중요하게 볼 것인가?
Ch11  LLM 제안을 왜 채택·수정·보류했는가?
Ch12  생성 코드를 왜 승인·수정·차단했는가?
Ch13  외부 데이터의 출처·기준일·대표성 한계는 무엇인가?
Ch14  Task 성공과 분석 Validation 성공을 어떻게 구분했는가?
Ch15  READY / READY_WITH_WARNINGS / BLOCKED 중 왜 그 상태인가?
```

---

## 권장 환경

- Python 3.10 이상
- VS Code
- Jupyter Notebook
- Git
- GitHub 계정
- Docker Desktop 또는 Docker Engine — Chapter 14 Airflow 실습

---

## 기본 설치

```bash
git clone https://github.com/GilbertMoon/llm-data-analysis-course.git
cd llm-data-analysis-course
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 실습 데이터 생성

```bash
python scripts/generate_sample_data.py
```

대표 데이터:

```text
customers.csv
products.csv
orders.csv
order_items.csv
```

수업에서는 실제 개인정보가 아닌 가상 쇼핑몰 데이터를 사용합니다.

---

## API Key와 개인정보 보안

실제 API Key는 GitHub에 커밋하지 않습니다.

`.env.example`을 참고해 `.env`를 만들고 실제 값은 로컬에서만 관리합니다.

다음 정보는 LLM Prompt, Notebook Output, Markdown, 화면 캡처와 Public GitHub에 노출하지 않습니다.

```text
실제 API Key
Client Secret
Access Token
Password
DB 접속 비밀번호
실제 고객 개인정보
회사 내부 URL
비공개 업무자료
.env 실제 값
GitHub Personal Access Token
```

---

## Chapter 14 Docker / Airflow

Airflow보다 로컬 Python 분석을 먼저 검증합니다.

```powershell
python scripts/run_ch14_pipeline.py
```

Docker 확인:

```powershell
docker --version
docker compose version
docker run hello-world
```

자세한 환경 절차는 다음 문서를 사용합니다.

```text
docs/ch14_docker_airflow_guide.md
```

핵심 원칙:

```text
Task 실행 성공 ≠ 분석 결과 Validation 성공
```

---

## 저장소 역할

이 저장소는 **학생 실습용 공개 저장소**입니다.

포함:
- 실행 코드와 Notebook
- 샘플 데이터
- Chapter별 실습 가이드
- 답안 작성 템플릿
- 공개 이미지
- 분석/자동화 스크립트
- 공개 가능한 예제 결과

제외:
- 책 원고
- 편집·교정 자료
- 출판 제작 과정
- 내부 검수 자료
- 실제 개인정보
- 실제 Secret

책 본문과 출판 제작 파일은 별도의 저자 전용 저장소에서 관리합니다.