# LLM 기반 데이터 분석 실무 입문

이 저장소는 15주 강의에서 사용할 실습용 저장소입니다. Python 데이터 분석의 기본 흐름을 익히고, ChatGPT/Gemini 같은 LLM을 데이터 이해, 코드 생성, 인사이트 도출, 보고서 작성, 자동화 실습에 활용하는 방법을 단계적으로 연습합니다.

## 저장소 목적

- 데이터 분석 입문자가 수업 중 바로 실행할 수 있는 실습 환경 제공
- pandas, matplotlib, seaborn 기반의 기초 분석 코드 예제 제공
- LLM 프롬프트를 분석 과정에 안전하게 활용하는 연습 제공
- Word/PDF 보고서 자동화, Make, Airflow 개념 실습을 위한 기본 구조 제공
- 중간 프로젝트와 기말 프로젝트 제출을 위한 공통 기준 제공

## 15주 강의 구성 요약

| 주차 | 주제 |
| --- | --- |
| 1주차 | AI 기반 데이터 분석 개요 |
| 2주차 | Python, Jupyter, GitHub 환경 설정 |
| 3주차 | 데이터 구조 이해와 분석 흐름 |
| 4주차 | pandas 기초 |
| 5주차 | 데이터 전처리 |
| 6주차 | EDA 질문 만들기 |
| 7주차 | 데이터 시각화 |
| 8주차 | 중간 프로젝트 |
| 9주차 | LLM을 활용한 분석 프롬프트 |
| 10주차 | LLM 코드 생성과 검증 |
| 11주차 | 인사이트 생성과 해석 |
| 12주차 | 보고서 자동 생성 |
| 13주차 | Make 자동화 개념 실습 |
| 14주차 | Airflow 파이프라인 개념 실습 |
| 15주차 | 기말 프로젝트 발표 및 제출 |

## 사용 기술 스택

- Python 3.10 이상
- Jupyter Notebook
- pandas, numpy
- matplotlib, seaborn
- Faker
- python-docx
- python-dotenv
- Google Gemini API
- Make
- Apache Airflow, Docker 기반 개념 실습

## 설치 방법

```bash
git clone https://github.com/GilbertMoon/llm-data-analysis-course.git
cd llm-data-analysis-course
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS 또는 Linux에서는 가상환경 활성화 명령만 다릅니다.

```bash
source .venv/bin/activate
```

## 실습 데이터 다운로드 또는 생성 방법

수업에서는 개인정보가 없는 가상 쇼핑몰 데이터를 사용합니다. 아래 명령으로 `data/raw/` 폴더에 CSV 파일을 생성할 수 있습니다.

```bash
python scripts/generate_sample_data.py
```

생성되는 파일은 다음과 같습니다.

- `customers.csv`
- `products.csv`
- `orders.csv`
- `order_items.csv`

## Jupyter Notebook 실행 방법

```bash
jupyter notebook
```

브라우저가 열리면 `notebooks/` 폴더의 주차별 노트북을 순서대로 실행합니다.

## 중간/기말 프로젝트 안내

중간 프로젝트는 8주차에 진행합니다. 제공된 샘플 데이터를 바탕으로 분석 질문을 만들고, 전처리, 집계, 시각화, 인사이트 작성을 수행합니다.

기말 프로젝트는 15주차에 진행합니다. 분석 과정에 LLM 프롬프트를 활용하고, 분석 결과를 보고서 형식으로 정리하며, 자동화 아이디어를 함께 제시합니다.

## GitHub 제출 방법

1. 본인 계정으로 저장소를 fork합니다.
2. 실습 노트북과 보고서 파일을 작성합니다.
3. 변경사항을 commit합니다.
4. GitHub 저장소 URL 또는 Pull Request URL을 LMS에 제출합니다.

```bash
git add .
git commit -m "Add week 1 practice"
git push origin main
```

## API Key 보안 주의사항

실제 API Key는 절대 GitHub에 커밋하지 않습니다. `.env.example` 파일을 복사해 `.env` 파일을 만들고, 개인 키는 `.env`에만 저장합니다.

```bash
copy .env.example .env
```

`.env` 파일은 `.gitignore`에 포함되어 있어 GitHub에 업로드되지 않습니다.
