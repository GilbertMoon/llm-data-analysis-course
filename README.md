# LLM 기반 데이터 분석 실무 입문
## 공식 실습 자료

이 저장소는 『LLM 기반 데이터 분석 실무 입문』의 **공식 실습용 Companion Repository**입니다.

책의 본문·편집 원고·출판 제작 자료는 포함하지 않으며, 학생이 수업을 따라 실습하는 데 필요한 Python 코드, Jupyter Notebook, 샘플 데이터, 답안 템플릿, API 및 자동화 예제를 제공합니다.

---

## 제공 자료

- 장별 Jupyter Notebook
- Python 데이터 분석 실습 코드
- 개인정보가 없는 가상 쇼핑몰 샘플 데이터 생성 코드
- pandas 기반 데이터 처리·전처리·EDA 예제
- matplotlib/seaborn 기반 시각화 예제
- scikit-learn 기반 회귀·분류 실습
- LLM 기반 분석 질문·코드 검증 실습
- 외부 데이터 수집 예제
- Docker Compose / Apache Airflow 자동화 실습
- Chapter별 학생 실습 가이드
- Chapter별 답안 Markdown/Notebook 템플릿

---

## 실습 제출 방식

이 수업은 단순히 코드와 실행 화면만 제출하지 않습니다.

모든 Chapter는 가능한 한 다음 흐름으로 진행합니다.

```text
강사 Public 저장소의 템플릿 확인
→ 템플릿 다운로드 또는 복사
→ 로컬에서 STEP별 실습 진행
→ 핵심 실행 결과 화면 캡처
→ 답안에 코드/Prompt와 실행 결과 정리
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub 저장소에 업로드
→ GitHub에서 최종 파일과 이미지 확인
→ 해당 Chapter 최종 파일 URL 제출
```

공통 제출 기준:

```text
practice/SUBMISSION_GUIDE.md
```

Chapter 01 답안 템플릿:

```text
practice/chapter01/templates/chapter01_assignment.md
```

> **중요**  
> 실행 결과는 답안의 시작이지 끝이 아닙니다. 학생이 결과를 어떻게 관찰하고 해석했는지, 어떤 판단을 내렸는지, 무엇을 아직 확신할 수 없는지까지 제출 파일에서 확인할 수 있어야 합니다.

---

## 학생 개인 GitHub 저장소

학생은 자신의 GitHub 계정에 학습 결과를 누적할 별도 저장소를 하나 만드는 것을 권장합니다.

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
│  ├─ chapter02.md 또는 chapter02.ipynb
│  └─ images/
...
└─ chapter15/
```

제출 시 저장소 루트 URL이 아니라 **해당 Chapter 최종 파일 URL**을 제출합니다.

예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter01/chapter01.md
```

Chapter 01은 Git 환경설정 이전이므로 GitHub 웹의 `Add file → Upload files` 방식으로 제출해도 됩니다. Chapter 02에서 Git을 학습한 이후에는 local commit/push 방식을 권장합니다.

---

## 권장 환경

- Python 3.10 이상
- VS Code
- Jupyter Notebook
- Git
- GitHub 계정
- Docker Desktop 또는 Docker Engine (14장 Airflow 실습 시)

---

## 설치 방법

```bash
git clone https://github.com/GilbertMoon/llm-data-analysis-course.git
cd llm-data-analysis-course
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\activate
python -m pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 실습 데이터 생성

수업과 책의 실습에서는 개인정보가 없는 가상 쇼핑몰 데이터를 사용합니다.

```bash
python scripts/generate_sample_data.py
```

주요 생성 파일:

- `customers.csv`
- `products.csv`
- `orders.csv`
- `order_items.csv`

---

## Jupyter Notebook 실행

```bash
jupyter notebook
```

또는 VS Code에서 `notebooks/` 폴더의 해당 Chapter Notebook을 열어 실행합니다.

---

## 책 ↔ 주요 실습 파일 연결

| 책의 장 | 주요 실습 파일 |
| --- | --- |
| Overview | `practice/overview/overview.md` |
| 1장 AI와 함께하는 데이터 분석의 시작 | `practice/chapter01/chapter01.md` |
| 2장 개발 환경 | `notebooks/ch02_environment_setup.ipynb` |
| 3장 데이터 첫인상 | `notebooks/ch03_data_overview.ipynb` |
| 4장 pandas 기초 | `notebooks/ch04_pandas_basic.ipynb` |
| 5장 데이터 전처리 | `notebooks/ch05_data_preprocessing.ipynb` |
| 6장 EDA 질문 만들기 | `notebooks/ch06_eda_questions.ipynb` |
| 7장 데이터 시각화 | `notebooks/ch07_visualization.ipynb` |
| 8장 중간 프로젝트 | `notebooks/ch08_midterm_project.ipynb` |
| 9장 회귀 분석으로 숫자 예측하기 | `notebooks/ch09_regression_analysis.ipynb` |
| 10장 분류 분석으로 주문 취소 여부 예측하기 | `notebooks/ch10_llm_code_generation.ipynb` |
| 11장 LLM과 함께 분석 질문을 다듬기 | `notebooks/ch11_llm_prompt_analysis.ipynb` |
| 12장 LLM이 만든 분석 코드를 검증하는 방법 | `notebooks/ch12_report_generation.ipynb` |
| 13장 외부 데이터로 분석을 확장하기 | `notebooks/ch13_external_data_collection.ipynb` |
| 14장 반복되는 분석 흐름을 안전하게 자동화하기 | `notebooks/ch14_airflow_pipeline.ipynb` |
| 15장 하나의 데이터 분석 프로젝트로 완성하기 | `notebooks/ch15_final_project.ipynb` |

> 일부 Notebook 파일명은 과거 작업명과 현재 장 제목이 다를 수 있습니다. **장 제목과 실습 내용은 현재 실습 가이드와 책의 H1을 우선 기준으로 사용합니다.**

---

## 답안 작성의 기본 구조

핵심 STEP에서는 가능한 한 다음 여섯 요소를 작성합니다.

```text
① 실행 코드 / Prompt / 수행 내용
② 실행 결과 또는 화면 캡처
③ 결과 관찰
④ 나의 해석과 판단
⑤ 업무·분석적 의미
⑥ 한계와 추가 확인 사항
```

코드 셀이나 캡처만 연속해서 제출하는 방식은 권장하지 않습니다.

Notebook을 제출하는 Chapter에서는 Markdown 셀을 이용해 결과 해석과 판단을 함께 작성합니다.

---

## 화면 캡처 Evidence

모든 클릭과 명령을 캡처할 필요는 없습니다.

다음처럼 학습 목표 달성을 보여주는 핵심 화면을 우선합니다.

- Notebook 핵심 실행 결과
- DataFrame 결과
- 그래프
- LLM Prompt와 주요 응답
- 분석 검증 결과
- 오류 해결 전·후 핵심 화면
- Airflow Task 상태와 최종 Validation
- Chapter 15 Submission Status

Chapter별 별도 지시가 없다면 핵심 Evidence 약 4~8장을 권장합니다.

---

## 14장 Docker Compose 기반 Airflow 실습

Docker 설치 후 다음 명령으로 설치 여부를 확인합니다.

```bash
docker --version
docker compose version
docker run hello-world
```

Python 분석 파이프라인을 먼저 검증합니다.

```bash
python scripts/generate_sample_data.py
python scripts/run_ch14_pipeline.py
```

Airflow 실행:

```bash
cd automation/airflow
cp .env.example .env
# Windows PowerShell: copy .env.example .env
docker compose up airflow-init
docker compose up
```

자세한 내용은 `docs/ch14_docker_airflow_guide.md`를 참고하세요.

---

## API Key와 개인정보 보안

실제 API Key는 GitHub에 커밋하지 않습니다.

`.env.example`을 참고해 `.env`를 만들고 실제 값은 로컬에서만 관리합니다.

```powershell
copy .env.example .env
```

`.env`는 `.gitignore`에 포함되어야 합니다.

다음 정보는 LLM Prompt, Notebook 출력, Markdown, 화면 캡처, Public GitHub에 노출하지 않습니다.

```text
실제 API Key
Client Secret
Access Token
Password
실제 고객 개인정보
회사 내부 URL
비공개 업무자료
.env 실제 값
GitHub Personal Access Token
```

---

## 저장소 역할

이 저장소는 **학생 실습용 공개 저장소**입니다.

포함:

- 실행 코드
- Notebook
- 샘플 데이터
- 실습 환경
- 학습 보조 문서
- 학생용 실습 가이드
- 답안 템플릿
- 공개 가능한 이미지 및 예제 결과

제외:

- 책 원고
- 편집·교정 자료
- 출판용 Word/PDF/HTML 생성 과정
- 내부 검수 자료
- 실제 개인정보
- 실제 Secret

책의 본문과 출판 제작 파일은 별도의 저자 전용 저장소에서 관리합니다.
