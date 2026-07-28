# LLM 기반 데이터 분석 실무 입문
## 공식 실습 자료

이 저장소는 『LLM 기반 데이터 분석 실무 입문』의 **공식 실습용 Companion Repository**입니다.

책의 본문·편집 원고·출판 제작 자료는 포함하지 않으며, 독자가 책을 따라 실습하는 데 필요한 Python 코드, Jupyter Notebook, 샘플 데이터 생성 코드, API 및 자동화 예제를 제공합니다.

## 제공 자료

- 장별 Jupyter Notebook
- Python 데이터 분석 실습 코드
- 개인정보가 없는 가상 쇼핑몰 샘플 데이터 생성 코드
- pandas 기반 데이터 처리·전처리·EDA 예제
- matplotlib/seaborn 기반 시각화 예제
- scikit-learn 기반 회귀·분류 실습
- Gemini API를 활용한 LLM 데이터 분석 실습
- 외부 데이터 수집 예제
- Docker Compose / Apache Airflow 자동화 실습

## 권장 환경

- Python 3.10 이상
- VS Code
- Jupyter Notebook
- Git
- Docker Desktop (14장 Airflow 실습 시)

## 설치 방법

```bash
git clone https://github.com/GilbertMoon/llm-data-analysis-course.git
cd llm-data-analysis-course
python -m venv .venv
```

Windows PowerShell 또는 명령 프롬프트:

```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

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

## Jupyter Notebook 실행

```bash
jupyter notebook
```

브라우저가 열리면 `notebooks/` 폴더에서 책의 장에 해당하는 Notebook을 실행합니다.

## 책 ↔ 실습 파일 연결

| 책의 장 | 주요 실습 Notebook |
| --- | --- |
| 2장 개발 환경 | `notebooks/ch02_environment_setup.ipynb` |
| 3장 데이터 첫인상 | `notebooks/ch03_data_overview.ipynb` |
| 5장 데이터 전처리 | `notebooks/ch05_data_preprocessing.ipynb` |
| 6장 EDA 질문 만들기 | `notebooks/ch06_eda_questions.ipynb` |
| 7장 데이터 시각화 | `notebooks/ch07_visualization.ipynb` |
| 9장 회귀 분석 | `notebooks/ch09_regression_analysis.ipynb` |
| 10장 LLM 코드 생성·검증 | `notebooks/ch10_llm_code_generation.ipynb` |
| 11장 LLM 프롬프트 분석 | `notebooks/ch09_llm_prompt_analysis.ipynb` |
| 12장 보고서 생성 | `notebooks/ch12_report_generation.ipynb` |
| 14장 Airflow 파이프라인 | `notebooks/ch14_airflow_pipeline.ipynb` |

> 저장소의 파일명은 책의 최종 편집 과정에서 일부 변경될 수 있습니다. 해당 장의 최신 파일을 우선 사용하세요.

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

## API Key 보안

실제 API Key는 GitHub에 커밋하지 않습니다. `.env.example`을 복사하여 `.env`를 만들고 개인 키는 `.env`에만 저장하세요.

```powershell
copy .env.example .env
```

`.env`는 `.gitignore`에 포함되어야 합니다.

## 저장소 역할

이 저장소는 **독자 실습용 공개 저장소**입니다.

- 포함: 실행 코드, Notebook, 샘플 데이터, 실습 환경, 학습 보조 문서
- 제외: 책 원고, 편집·교정 자료, 출판용 Word/PDF/HTML 생성 과정, 내부 검수 자료

책의 본문과 출판 제작 파일은 별도의 저자 전용 저장소에서 관리합니다.
