# 0장 실습. 이 책의 방향과 전체 흐름

> 이 문서는 수업용 **학생 실습 진행 가이드**입니다.  
> Overview에서는 복잡한 분석 코드를 작성하기보다, 앞으로 사용할 Public 실습 저장소의 구조와 전체 학습 순서, **실습 결과 작성 방식과 GitHub 제출 방식**을 먼저 이해합니다.

---

## 실습 목표

이 실습을 마치면 다음 내용을 설명할 수 있으면 됩니다.

- 강사 Public 저장소와 학생 개인 저장소의 역할을 구분할 수 있습니다.
- Chapter 01~15가 어떤 흐름으로 연결되는지 설명할 수 있습니다.
- `notebooks`, `scripts`, `data`, `src`, `reports`, `automation`, `practice` 폴더의 역할을 구분할 수 있습니다.
- Python 기본 문법이 부족한 경우 어떤 내용을 보충해야 하는지 판단할 수 있습니다.
- 실습에서 사용하는 가상 쇼핑몰 데이터의 종류를 설명할 수 있습니다.
- LLM 결과를 그대로 정답으로 사용하지 않고 검증해야 하는 이유를 설명할 수 있습니다.
- 실습 답안에 코드와 캡처뿐 아니라 **관찰·해석·판단·업무적 의미·한계**를 작성해야 한다는 것을 이해할 수 있습니다.
- 실습 결과를 개인 GitHub 저장소에 누적하고 **최종 파일 URL**을 제출하는 방식을 설명할 수 있습니다.
- API Key, Secret, 실제 개인정보를 Public GitHub나 LLM 입력에 넣으면 안 된다는 것을 설명할 수 있습니다.

---

## 1. 공식 Public 실습 저장소

수업의 원본 실습 자료는 다음 저장소에서 제공합니다.

```text
https://github.com/GilbertMoon/llm-data-analysis-course
```

이 저장소에는 다음 자산이 있습니다.

```text
notebooks/      장별 Jupyter Notebook
scripts/        데이터 생성·분석 실행 스크립트
data/           실습 데이터
src/            재사용 Python 코드
prompts/        공개 가능한 Prompt 예제
automation/     Airflow 등 자동화 실습
reports/        공개 가능한 분석 결과
practice/       학생 실습 가이드·답안 템플릿
book/assets/    공개 이미지 자산
```

강사 저장소의 원본 파일을 직접 수정하여 제출하는 것이 아닙니다.

```text
강사 Public 저장소
= 원본 템플릿 + 실습 자료

학생 개인 저장소
= 내가 직접 수행한 결과 + Evidence + 해석
```

---

## 2. Chapter 01~15 공통 제출 방식

모든 Chapter는 가능한 한 다음 흐름으로 진행합니다.

```text
강사 Public 저장소에서 실습 가이드 확인
→ 해당 Chapter 답안 템플릿 또는 Notebook 준비
→ 로컬에서 STEP별 실습 진행
→ 핵심 실행 결과 화면 캡처
→ 결과를 답안에 정리
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub 저장소에 업로드
→ GitHub에서 최종 파일과 이미지 확인
→ 해당 Chapter의 최종 파일 URL 제출
```

공통 기준 문서:

```text
practice/SUBMISSION_GUIDE.md
```

Chapter별 실습을 시작하기 전에 이 문서의 제출 원칙을 확인합니다.

---

## 3. 답안은 코드와 캡처만으로 끝나지 않습니다

실습 답안의 핵심 구조는 다음입니다.

```text
① 실행 코드 / Prompt / 수행 내용
② 실행 결과 또는 화면 캡처
③ 결과 관찰
④ 나의 해석과 판단
⑤ 업무·분석적 의미
⑥ 한계와 추가 확인 사항
```

예를 들어 그래프가 감소하는 모습을 보여준다고 가정합니다.

### 부족한 답안

```text
그래프가 내려갔습니다.
```

### 더 좋은 답안

```text
관찰:
6월의 completed 주문 기준 금액이 5월보다 낮게 나타났다.

해석:
전체 금액 감소가 주문 수 감소 때문인지 주문당 평균 금액 감소 때문인지 추가 확인이 필요하다고 판단했다.

업무적 의미:
다음 분석에서는 주문 건수와 카테고리별 변화를 우선 확인할 필요가 있다.

한계:
현재 결과만으로 고객 이탈이나 특정 캠페인을 감소 원인이라고 결론 내릴 수 없다.
```

즉, **실행 결과는 답안의 시작이지 끝이 아닙니다.**

---

## 4. 화면 캡처는 핵심 Evidence만 남깁니다

모든 클릭과 명령을 캡처하지 않습니다.

캡처할 가치가 높은 화면:

- Notebook 핵심 실행 결과
- DataFrame 출력
- 그래프
- LLM Prompt와 주요 응답
- 검증 결과
- 오류 해결 전·후 핵심 화면
- Airflow Task와 Validation 상태
- 최종 프로젝트 제출 상태

캡처할 가치가 낮은 화면:

- 단순 폴더 이동
- 파일을 열기만 한 화면
- 의미 없는 긴 로그
- 코드 입력 중간 화면

Chapter별 별도 지시가 없다면 **핵심 Evidence 4~8장 정도**를 권장합니다.

---

## 5. 학생 개인 GitHub 저장소

학생은 자신의 GitHub 계정에 Chapter 01~15 결과를 누적할 저장소를 하나 만듭니다.

권장 이름:

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
├─ chapter03/
│  ├─ chapter03.ipynb
│  └─ images/
...
└─ chapter15/
   ├─ chapter15.md 또는 chapter15.ipynb
   └─ images/
```

이 저장소는 단순 과제 제출 공간이 아니라 **Chapter 01~15 학습 과정을 보여주는 개인 포트폴리오**가 됩니다.

---

## 6. Chapter 01에서는 GitHub 웹 업로드도 가능합니다

Chapter 01은 Git 환경설정 이전입니다.

따라서 Git을 아직 배우지 않은 학생은 브라우저에서 다음 방식으로 제출할 수 있습니다.

```text
GitHub 로그인
→ 개인 저장소 생성
→ Add file
→ Upload files
→ 결과 Markdown/Notebook과 images 업로드
→ Commit
```

Chapter 02에서 Git을 학습한 이후에는 로컬 `git add`, `commit`, `push` 방식을 사용합니다.

---

## 7. 제출 URL은 저장소 주소가 아닙니다

다음처럼 저장소 루트 URL만 제출하지 않습니다.

```text
https://github.com/student-id/llm-data-analysis-study
```

교수자가 바로 해당 Chapter 답안을 열 수 있도록 **최종 파일 URL**을 제출합니다.

예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter01/chapter01.md
```

Notebook 제출 Chapter:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter03/chapter03.ipynb
```

---

## 8. Python을 어느 정도 알아야 하나요?

Python 기본 문법은 이 과목의 절대적인 선수 조건은 아닙니다.

다만 대부분의 데이터 분석 실습을 Python 코드로 진행하기 때문에 다음 문법에 익숙하면 학습이 훨씬 편합니다.

| Python 기초 | 데이터 분석에서 사용하는 이유 |
| --- | --- |
| 변수와 자료형 | 숫자, 문자열, 날짜 등의 값을 다룹니다. |
| 리스트 | 여러 컬럼명이나 값을 묶습니다. |
| 딕셔너리 | 설정값이나 구조화된 정보를 다룹니다. |
| 조건문 | 조건에 따라 다른 처리를 합니다. |
| 반복문 | 여러 파일이나 컬럼에 작업을 반복합니다. |
| 함수 | 분석 코드를 재사용 가능한 형태로 만듭니다. |
| `import` | pandas, matplotlib 등을 불러옵니다. |
| 파일 경로 | CSV를 읽고 결과 파일을 저장합니다. |

Python 기초가 아직 익숙하지 않다면 다음 보충 자료를 병행합니다.

```text
https://blog.naver.com/dev-dog/224381453910
```

모든 문법을 외우고 시작할 필요는 없습니다.

---

## 9. 기본 환경을 가볍게 확인합니다

Overview에서는 설치를 완성하는 것이 목표가 아닙니다.

### Windows PowerShell

```powershell
python --version
git --version
```

Python 명령이 인식되지 않으면 다음도 확인할 수 있습니다.

```powershell
py --version
```

### macOS/Linux

```bash
python3 --version
git --version
```

버전이 나오지 않아도 괜찮습니다.

실제 Python·VS Code·Git·가상환경·Jupyter 설정은 Chapter 02에서 단계별로 진행합니다.

---

## 10. 가상 쇼핑몰 데이터

실습에서는 실제 개인정보가 포함된 업무 데이터를 사용하지 않습니다.

개인정보가 없는 가상 온라인 쇼핑몰 데이터를 사용합니다.

```text
customers.csv
products.csv
orders.csv
order_items.csv
```

대표 관계:

```text
customers.customer_id
        ↓
orders.customer_id

orders.order_id
        ↓
order_items.order_id

products.product_id
        ↓
order_items.product_id
```

같은 데이터를 여러 장에서 반복해서 사용하면서 분석이 확장됩니다.

---

## 11. 전체 Chapter 학습 로드맵

| Chapter | 주제 | 핵심 학습 |
| ---: | --- | --- |
| 0 | 이 책의 방향과 전체 흐름 | 저장소, 학습 지도, 제출 기준 |
| 1 | AI와 함께하는 데이터 분석의 시작 | 질문 정의, AI 초안, 사람 검증 |
| 2 | VS Code에서 시작하는 데이터 분석 환경 | Python, VS Code, Git, venv, Jupyter |
| 3 | 데이터의 첫인상 읽기 | CSV, 행·열, 컬럼, 타입, 키 |
| 4 | pandas로 데이터에 질문하기 | 선택, 필터, 정렬, 파생 컬럼, 병합, 집계 |
| 5 | 분석을 믿을 수 있게 만드는 데이터 전처리 | 결측, 중복, 타입, 이상값 |
| 6 | 데이터를 보며 질문을 만드는 EDA | 질문, 지표, 집계, 해석 |
| 7 | 그래프로 데이터의 이야기를 보여주기 | 시각화 선택과 해석 |
| 8 | 작은 데이터 분석 프로젝트 완성하기 | 전처리·EDA·시각화·보고서 통합 |
| 9 | 회귀 분석으로 숫자 예측하기 | 누수 방지, 시간 분할, 평가 |
| 10 | 분류 분석으로 주문 취소 여부 예측하기 | 분류, threshold, precision·recall·F1 |
| 11 | LLM과 함께 분석 질문을 다듬기 | Safe Context, Prompt, 답변 검증 |
| 12 | LLM이 만든 분석 코드를 검증하는 방법 | 실행 전 검토, 제한 실행, 사후 Evidence |
| 13 | 외부 데이터로 분석을 확장하기 | 공식 출처, API, provenance, 이용조건 |
| 14 | 반복되는 분석 흐름을 안전하게 자동화하기 | 로컬 검증, Airflow, Validation Gate |
| 15 | 하나의 데이터 분석 프로젝트로 완성하기 | 전체 흐름, Evidence, 제출 Gate |

---

## 12. LLM 사용의 기본 원칙

이 수업에서 반복하는 흐름은 다음입니다.

```text
사람이 질문 정의
→ LLM이 초안 지원
→ 실제 데이터와 코드로 검증
→ 사람이 수정
→ 사람이 최종 판단
```

LLM은 다음을 자동으로 보장하지 않습니다.

```text
실제 컬럼 존재
정확한 데이터 범위
올바른 계산식
데이터 누수 방지
원인과 인과관계
보안
최종 분석 타당성
```

따라서 LLM 답변을 그대로 제출하는 것은 이 수업의 목표가 아닙니다.

**LLM 답변과 학생의 검증·판단을 구분해서 기록하는 것**이 중요합니다.

---

## 13. 개인정보와 Secret 보호

다음 정보는 LLM Prompt, 코드, Notebook, 화면 캡처, GitHub 제출물에 넣지 않습니다.

```text
실제 API Key
Client Secret
Access Token
Password
DB 접속 비밀번호
실제 개인정보
회사 내부 URL
비공개 업무자료
.env 실제 값
GitHub Personal Access Token
```

특히 화면 캡처를 업로드하기 전에 Secret이 보이지 않는지 다시 확인합니다.

---

## 14. 각 Chapter에서 반복할 학습 방식

각 Chapter에서는 다음 네 가지 질문을 반복해서 확인합니다.

### 왜 하는가?

분석 목적을 이해합니다.

### 무엇을 실행하는가?

코드, Notebook, Prompt 또는 도구를 실행합니다.

### 어떤 결과가 나왔는가?

실제 출력, 파일, 그래프, 상태를 확인합니다.

### 나는 그 결과를 어떻게 해석하는가?

```text
관찰
→ 해석
→ 판단
→ 업무·분석적 의미
→ 한계
```

를 자신의 말로 정리합니다.

---

## 15. 시작 전 체크리스트

- [ ] 강사 Public 저장소와 학생 개인 저장소의 역할을 이해했습니다.
- [ ] `practice/SUBMISSION_GUIDE.md`가 공통 제출 기준이라는 것을 알고 있습니다.
- [ ] 강사 템플릿을 복사해서 내 답안을 작성한다는 것을 알고 있습니다.
- [ ] 실행 코드와 캡처만 제출하는 것이 아니라는 것을 이해했습니다.
- [ ] 결과 관찰과 나의 해석을 구분해서 작성할 수 있습니다.
- [ ] 업무·분석적 의미와 한계를 작성해야 한다는 것을 알고 있습니다.
- [ ] 개인 GitHub 저장소에 Chapter별 결과를 누적할 계획입니다.
- [ ] 최종 제출은 저장소 URL이 아니라 해당 Chapter **최종 파일 URL**입니다.
- [ ] Python이 주된 실습 언어라는 것을 알고 있습니다.
- [ ] LLM 결과는 검증해야 할 초안이라는 것을 이해했습니다.
- [ ] 실제 개인정보를 실습에 사용하지 않습니다.
- [ ] API Key와 Secret을 GitHub에 올리지 않습니다.

---

## 다음 단계

다음은 **Chapter 01. AI와 함께하는 데이터 분석의 시작**입니다.

Chapter 01에서는 실제로 다음 과정을 처음 수행합니다.

```text
답안 템플릿 준비
→ 업무 질문 구체화
→ LLM 활용
→ LLM 제안 검증
→ Prompt Log
→ 결과 해석
→ Evidence 첨부
→ 개인 GitHub 업로드
→ 최종 Markdown 파일 URL 제출
```

Chapter 01에서 만든 개인 GitHub 저장소는 Chapter 15까지 계속 사용합니다.
