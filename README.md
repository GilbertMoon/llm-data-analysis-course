# LLM 기반 데이터 분석 실무 입문

이 저장소는 **LLM 기반 데이터 분석 실무 입문** 과정을 위한 실습 및 ebook형 강의안 저장소입니다. Python 데이터 분석의 기본 흐름을 익힌 뒤, 간단한 머신러닝, LLM 활용, 외부 데이터 수집, 보고서 작성, 자동화 개념까지 하나의 분석 프로젝트 흐름으로 연결합니다.

전체 방향은 전통적인 수업 교재보다는 **일반 ebook처럼 읽히는 강의안**에 가깝게 구성합니다. 각 장은 개념 설명, 짧은 예시, 실습 아이디어, 프로젝트 확장 흐름을 함께 담아 수업 자료와 자기주도 학습 자료로 모두 활용할 수 있도록 합니다.

## 저장소 목적

- 데이터 분석 입문자가 따라갈 수 있는 Python 기반 분석 흐름 제공
- pandas, matplotlib, seaborn 기반의 기초 분석 코드 예제 제공
- scikit-learn을 활용한 간단한 회귀/분류 머신러닝 실습 제공
- ChatGPT/Gemini 같은 LLM을 분석 질문, 코드 생성, 결과 해석, 보고서 작성에 활용하는 방법 정리
- 공공데이터, 네이버 API, 크롤링을 통한 외부 데이터 수집 흐름 소개
- Make, n8n, Airflow를 활용한 분석 자동화와 파이프라인 개념 실습 제공
- 중간 프로젝트와 기말 프로젝트 제출을 위한 공통 기준 제공

## 15주 강의 구성 요약

| 주차 | 주제 | 주요 내용 |
| --- | --- | --- |
| 1주차 | AI 기반 데이터 분석 개요 및 개발 환경 설정 | 데이터 분석 흐름, LLM 활용 방향, Python, VS Code, Jupyter Notebook 개념, GitHub, 가상환경, 패키지 설치 |
| 2주차 | 데이터 구조 이해 | CSV 데이터 읽기, 컬럼/행 구조, 데이터 타입, 기본 탐색 |
| 3주차 | pandas 기초 | DataFrame, 선택, 필터링, 정렬, 집계 기초 |
| 4주차 | 데이터 전처리 | 결측치, 중복, 이상치, 날짜 처리, 데이터 정리 |
| 5주차 | EDA 질문 만들기 | 분석 질문, 가설 설정, 그룹별 비교, 탐색적 분석 흐름 |
| 6주차 | 데이터 시각화 | matplotlib/seaborn, 막대그래프, 선그래프, 분포 시각화 |
| 7주차 | 머신러닝 기초 | 지도학습 개념, 분류/회귀 개념, feature/target, train/test split, 평가 지표 |
| 8주차 | 중간 프로젝트 | 샘플 데이터 기반 EDA, 전처리, 시각화, 기초 인사이트 제출 |
| 9주차 | 회귀 분석 실습 | 매출/가격 예측, Linear Regression, RandomForestRegressor, MAE/RMSE/R² |
| 10주차 | 분류 분석 실습 | 주문 취소/구매 여부 예측, Logistic Regression, RandomForestClassifier, accuracy/precision/recall |
| 11주차 | LLM을 활용한 분석 프롬프트 | 데이터 설명, 분석 질문 생성, 전처리/시각화/ML 코드 생성 프롬프트 |
| 12주차 | LLM 코드 생성과 검증 | LLM이 생성한 pandas/ML 코드 검토, 오류 수정, 결과 검증, 보고서 초안 작성 |
| 13주차 | 외부 데이터 수집 | 공공데이터, 네이버 API, 기본 크롤링 개념 및 활용 |
| 14주차 | 분석 자동화와 파이프라인 | Make, n8n, Airflow 개념, Airflow DAG 기초 실습 |
| 15주차 | 기말 프로젝트 | EDA + 시각화 + ML + LLM 활용 + 자동화 아이디어 발표 |

## 사용 기술 스택

- Python 3.10 이상
- VS Code
- Jupyter Notebook
- pandas, numpy
- matplotlib, seaborn
- scikit-learn
- Faker
- python-docx
- python-dotenv
- Google Gemini API
- 공공데이터 API, 네이버 API, 기본 크롤링 도구
- Make, n8n
- Apache Airflow, Docker 기반 개념 실습
- GitHub

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

브라우저가 열리면 `notebooks/` 폴더의 주차별 노트북을 순서대로 실행합니다. 실제 수업 진행은 VS Code를 중심으로 하되, Jupyter Notebook은 코드 실행 결과와 해석을 함께 정리하는 분석 노트 형식으로 활용합니다.

## 중간/기말 프로젝트 안내

중간 프로젝트는 8주차에 진행합니다. 제공된 샘플 데이터를 바탕으로 분석 질문을 만들고, 전처리, 집계, 시각화, 기초 인사이트 작성을 수행합니다. 머신러닝은 필수보다는 선택 확장 요소로 둡니다.

기말 프로젝트는 15주차에 진행합니다. EDA, 시각화, 간단한 머신러닝 모델, LLM 프롬프트 활용, 분석 보고서, 자동화 아이디어를 함께 정리합니다.

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
