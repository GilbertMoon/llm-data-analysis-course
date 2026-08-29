# 1장 실습. AI와 함께하는 데이터 분석의 시작

> 이 문서는 학생이 순서대로 따라갈 수 있도록 작성한 실습 진행 가이드입니다.  
> Chapter 01에서는 복잡한 분석 코드를 만드는 것보다 **질문 정의 → AI 초안 → 실제 데이터와 비교 → 사람 검증 → 결과 해석 → Evidence → GitHub 제출** 흐름을 직접 경험하는 것이 목표입니다.

---

## 실습 목표

이 실습을 마치면 다음을 할 수 있습니다.

- 막연한 업무 질문을 분석 가능한 질문으로 바꿀 수 있습니다.
- LLM에게 분석 질문 후보를 요청할 수 있습니다.
- LLM이 제안한 컬럼과 분석 방법이 실제 데이터 구조와 맞는지 확인할 수 있습니다.
- AI가 제안한 내용을 그대로 사용하지 않고 실제 반영 여부를 판단할 수 있습니다.
- 실행 결과와 LLM 응답을 단순 캡처하는 데서 끝나지 않고 자신의 해석과 판단을 작성할 수 있습니다.
- 결과의 업무·분석적 의미와 한계를 구분해 작성할 수 있습니다.
- 개인정보와 API Key를 LLM이나 Public GitHub에 올리지 않는 기본 원칙을 설명할 수 있습니다.
- 실습 결과를 개인 GitHub 저장소에 정리하고 **최종 파일 URL**을 제출할 수 있습니다.

---

## 반드시 먼저 확인할 공통 제출 기준

Chapter 01부터 Chapter 15까지 실습 제출은 다음 공통 기준을 사용합니다.

- 공통 제출 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter 01 답안 템플릿: `practice/chapter01/templates/chapter01_assignment.md`

전체 제출 흐름:

```text
강사 Public 저장소의 템플릿 확인
→ 템플릿 다운로드 또는 복사
→ STEP별 실습 진행
→ 핵심 실행 화면 캡처
→ 답안 파일에 실행 결과와 이미지 삽입
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub 저장소에 업로드
→ 최종 파일 URL 제출
```

> **중요**  
> 코드가 실행되었다는 사실이나 화면 캡처만으로 실습이 완료된 것은 아닙니다.  
> 제출 파일에서 **학생 본인의 관찰·해석·판단·한계 인식**을 확인할 수 있어야 합니다.

---

## 제출용 파일 준비

### 1. 템플릿 파일

다음 파일을 사용합니다.

```text
practice/chapter01/templates/chapter01_assignment.md
```

GitHub에서 Raw 파일을 저장하거나 저장소를 clone한 경우 파일을 복사해 사용합니다.

### 2. 내 작업 파일 이름

개인 저장소에서는 다음 이름을 권장합니다.

```text
chapter01/chapter01.md
```

### 3. 이미지 폴더

```text
chapter01/images/
```

예:

```text
chapter01/
├─ chapter01.md
└─ images/
   ├─ step01_question.png
   ├─ step02_data_structure.png
   ├─ step03_llm_response.png
   ├─ step04_validation.png
   ├─ step05_prompt_log.png
   └─ step07_notebook_result.png
```

Chapter 01에서는 **핵심 Evidence 4~6장 정도**면 충분합니다.

---

## 사용할 파일

이번 장에서 주로 확인할 파일은 다음과 같습니다.

- 실습 Notebook: `notebooks/ch01_ai_data_analysis_intro.ipynb`
- 고객 데이터: `data/raw/customers.csv`
- 상품 데이터: `data/raw/products.csv`
- 주문 데이터: `data/raw/orders.csv`
- 주문 상세 데이터: `data/raw/order_items.csv`
- 답안 템플릿: `practice/chapter01/templates/chapter01_assignment.md`
- 공통 제출 기준: `practice/SUBMISSION_GUIDE.md`
- 환경변수 예시: `.env.example`
- 저장소 안내: `README.md`

> 현재 Chapter 01 Notebook은 본격 분석용 완성 Notebook이라기보다 기본 import와 데이터 경로를 준비한 **starter scaffold**입니다.  
> Python·VS Code·가상환경·Jupyter 설정이 아직 끝나지 않았다면 Notebook 실행은 Chapter 02 이후에 진행해도 됩니다.

---

# STEP 0. 답안 템플릿 준비하기

## 0-1. 목적

실습 결과를 나중에 몰아서 작성하지 않고, 각 STEP을 수행할 때 바로 기록하기 위해 먼저 답안 파일을 준비합니다.

## 0-2. 실행

`chapter01_assignment.md`를 다운로드하거나 복사한 뒤 자신의 작업 폴더에 다음과 같이 저장합니다.

```text
chapter01/chapter01.md
```

그리고 이미지 폴더를 만듭니다.

```text
chapter01/images/
```

## 0-3. 예상 결과

```text
chapter01/
├─ chapter01.md
└─ images/
```

구조가 준비되면 됩니다.

## 성공 기준

- [ ] 답안 템플릿을 준비했습니다.
- [ ] 파일 이름을 `chapter01.md`로 정했습니다.
- [ ] `images/` 폴더를 만들었습니다.
- [ ] 각 STEP을 수행하면서 바로 답안을 작성할 준비가 되었습니다.

---

# STEP 1. 막연한 업무 질문을 분석 질문으로 바꾸기

## 1-1. 목적

데이터 분석은 코드보다 질문을 먼저 구체화해야 합니다.

다음과 같은 질문은 그대로 분석하기에는 모호합니다.

```text
요즘 매출이 줄어든 것 같은데 왜 그런가요?
```

## 1-2. 실행

아래 네 항목을 직접 적습니다.

| 항목 | 내가 정할 내용 |
| --- | --- |
| 대상 | 무엇을 분석할 것인가? |
| 기준 | 어떤 단위로 볼 것인가? |
| 비교 | 무엇과 비교할 것인가? |
| 목적 | 결과를 어디에 사용할 것인가? |

예시:

```text
대상: completed 주문 기준 금액
기준: 월별
비교: 최근 6개월 월별 변화
목적: 감소가 특정 월 또는 특정 카테고리에 집중되는지 확인
```

질문 예:

```text
최근 6개월 동안 completed 주문 기준 월별 금액은 어떻게 변했으며,
감소가 특정 상품 카테고리에서 두드러지는가?
```

## 1-3. 예상 결과

처음 질문보다 다음이 명확해져야 합니다.

```text
기간
주문 상태 범위
집계 단위
비교 기준
분석 목적
```

## 1-4. 답안에 반드시 작성할 것

템플릿의 STEP 1에 다음을 작성합니다.

```text
원래 업무 질문
→ 모호한 이유
→ 구체화한 질문
→ 결과 관찰
→ 나의 해석과 판단
→ 업무·분석적 의미
→ 한계와 추가 확인 사항
```

## 1-5. Evidence

질문을 정리한 화면 또는 작성 결과를 캡처합니다.

권장 파일명:

```text
images/step01_question.png
```

## 성공 기준

- [ ] 막연한 질문 1개를 선택했습니다.
- [ ] 대상·기준·비교·목적을 적었습니다.
- [ ] 분석 가능한 문장으로 다시 작성했습니다.
- [ ] 질문이 왜 더 좋아졌는지 자신의 말로 설명했습니다.
- [ ] 현재 질문만으로 알 수 없는 한계를 작성했습니다.
- [ ] 필요한 경우 Evidence를 첨부했습니다.

---

# STEP 2. 실제 데이터 구조와 질문 연결하기

## 2-1. 목적

좋은 질문이라도 현재 데이터에 필요한 정보가 없으면 바로 분석할 수 없습니다.

기본 데이터는 네 파일입니다.

```text
customers.csv
products.csv
orders.csv
order_items.csv
```

## 2-2. 실행

다음 관계를 확인합니다.

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

질문에 필요한 파일과 컬럼 후보를 적습니다.

예:

```text
질문: 카테고리별 completed 주문 금액을 비교하고 싶다.

필요 파일
- products.csv
- orders.csv
- order_items.csv

필요 컬럼 후보
- product_id
- category
- order_id
- order_status
- quantity
- unit_price
```

## 2-3. 답안에 반드시 작성할 것

```text
필요 파일
필요 컬럼
연결 관계
현재 데이터만으로 답할 수 있는지에 대한 판단
실제 컬럼·타입 등 아직 확인하지 못한 내용
```

## 2-4. Evidence

관계도 또는 저장소 데이터 구조를 확인한 화면을 첨부할 수 있습니다.

권장 파일명:

```text
images/step02_data_structure.png
```

## 성공 기준

- [ ] 네 파일의 역할을 설명할 수 있습니다.
- [ ] `customer_id`, `order_id`, `product_id` 관계를 이해했습니다.
- [ ] 질문에 필요한 파일을 선택했습니다.
- [ ] 필요한 컬럼 후보를 적었습니다.
- [ ] 데이터가 충분한지 자신의 판단을 작성했습니다.
- [ ] 미확인 내용을 PASS로 표시하지 않았습니다.

---

# STEP 3. LLM에게 분석 질문 후보 요청하기

## 3-1. 목적

LLM을 정답 생성기가 아니라 **아이디어와 초안을 만드는 보조 도구**로 사용합니다.

## 3-2. 실행

ChatGPT, Gemini 등 사용 가능한 LLM에 다음과 비슷한 Prompt를 입력합니다.

```text
온라인 쇼핑몰 데이터 분석을 준비하고 있습니다.

데이터는 다음 4개 파일로 구성됩니다.
- customers: 고객 정보
- products: 상품 정보
- orders: 주문 정보
- order_items: 주문 상세 정보

목적은 completed 주문 기준 금액과 구매 패턴을 이해하는 것입니다.

초보 데이터 분석자가 먼저 확인할 분석 질문 5개를 제안해 주세요.
각 질문마다 필요한 데이터 파일과 확인할 컬럼 후보도 적어 주세요.
원인을 단정하지 말고, 현재 데이터로 확인 가능한 질문만 제안해 주세요.
```

> 실제 고객 행, 실제 이메일, 전화번호, API Key, 내부 URL 같은 민감정보는 입력하지 않습니다.

## 3-3. 예상 결과

다음과 비슷한 질문 후보가 나올 수 있습니다.

```text
월별 completed 주문 금액은 어떻게 변하는가?
카테고리별 completed 주문 금액 차이는 어떤가?
고객별 구매 금액 분포는 어떤가?
주문 수와 주문당 평균 금액은 어떻게 변하는가?
취소 주문 비율은 기간별로 어떤 차이가 있는가?
```

정확히 같은 답이 나올 필요는 없습니다.

## 3-4. 답안에 반드시 작성할 것

```text
사용 목적
실제 Prompt
LLM 답변 요약 3~5개
결과 관찰
나의 해석과 판단
업무·분석적 의미
한계와 검증할 내용
```

## 3-5. Evidence

LLM Prompt와 주요 답변이 함께 보이도록 캡처합니다.

권장 파일명:

```text
images/step03_llm_response.png
```

> 개인정보나 계정 정보, API Key가 화면에 보이지 않는지 반드시 확인합니다.

## 성공 기준

- [ ] 원본 개인정보 없이 Prompt를 작성했습니다.
- [ ] 분석 질문 후보를 받았습니다.
- [ ] 전체 답을 무조건 복사하지 않고 핵심을 요약했습니다.
- [ ] 좋은 제안과 검증이 필요한 제안을 구분했습니다.
- [ ] LLM 답변을 아직 정답으로 확정하지 않았습니다.
- [ ] Evidence를 첨부했습니다.

---

# STEP 4. LLM 제안을 실제 데이터 기준으로 검증하기

## 4-1. 목적

LLM은 존재하지 않는 컬럼이나 사용할 수 없는 분석을 제안할 수 있습니다.

따라서 제안을 그대로 사용하지 않고 검증합니다.

## 4-2. 실행

LLM이 제안한 질문 중 1개 이상을 선택하고 다음 항목을 확인합니다.

| 검증 항목 | 확인 내용 |
| --- | --- |
| 질문 | 실제로 무엇을 묻는가? |
| 필요한 파일 | 저장소에 존재하는가? |
| 필요한 컬럼 | 실제 컬럼인지 확인이 필요한가? |
| 계산 범위 | completed/cancelled 등 범위가 정의되었는가? |
| 결과 해석 | 데이터에 없는 원인을 단정하고 있지 않은가? |
| 사용 여부 | 사용 / 수정 후 사용 / 보류 |

## 4-3. 판단 예

```text
LLM 제안: 연령대별 구매 금액을 비교하세요.

검증
- customers.csv에 age가 있는지 확인 필요
- 주문 금액은 orders와 order_items를 연결해야 함
- completed 주문만 포함할지 기준 필요
- 연령이 구매 원인이라고 단정하면 안 됨

판단
= 수정 후 사용
```

## 4-4. 답안에 반드시 작성할 것

```text
선택한 제안
검증 결과
수정한 내용
사용 / 수정 후 사용 / 보류
그 판단을 내린 이유
검증하지 않고 사용했을 때의 위험
남은 확인 사항
```

## 4-5. Evidence

권장 파일명:

```text
images/step04_validation.png
```

## 성공 기준

- [ ] LLM 제안 1개 이상을 검토했습니다.
- [ ] 실제 데이터가 필요한 부분을 표시했습니다.
- [ ] 계산 범위를 확인했습니다.
- [ ] 원인 단정이 있으면 제거했습니다.
- [ ] 최종 사용 여부를 사람이 결정했습니다.
- [ ] 판단 이유를 자신의 말로 작성했습니다.
- [ ] 아직 미확인인 부분을 명시했습니다.

---

# STEP 5. Prompt Log 남기기

## 5-1. 목적

AI가 분석에 어떤 영향을 주었는지 나중에 확인할 수 있도록 기록합니다.

## 5-2. 실행

다음 형식으로 정리합니다.

```text
사용 목적
입력 Prompt 요약
LLM 답변 요약
실제 반영 여부
사람이 검증한 항목
사람이 수정한 내용
남은 확인 사항
```

## 5-3. 답안에 반드시 작성할 것

단순 기록 외에 다음 질문에도 답합니다.

```text
왜 Prompt Log가 필요하다고 생각하는가?
AI의 제안과 사람의 판단이 어디에서 달라졌는가?
```

## 5-4. Evidence

권장 파일명:

```text
images/step05_prompt_log.png
```

## 성공 기준

- [ ] Prompt 사용 목적을 기록했습니다.
- [ ] LLM 답변을 핵심만 요약했습니다.
- [ ] 실제 반영 여부를 기록했습니다.
- [ ] 사람이 검증하고 수정한 내용을 기록했습니다.
- [ ] Prompt Log의 의미를 자신의 말로 설명했습니다.
- [ ] 개인정보나 Secret을 로그에 넣지 않았습니다.

---

# STEP 6. 개인정보와 Secret 보호 확인하기

## 6-1. 목적

LLM과 Public GitHub를 사용할 때 공개하면 안 되는 정보를 구분합니다.

## 6-2. 확인할 항목

다음 항목은 Prompt, 코드, 답안, 캡처 이미지에 넣지 않습니다.

```text
실제 이름
이메일
전화번호
주소
결제 정보
DB 비밀번호
API Key
Client Secret
Access Token
회사 내부 URL
비공개 업무자료
.env 실제 내용
GitHub Personal Access Token
```

## 6-3. 답안에 반드시 작성할 것

```text
이번 실습에서 Public GitHub나 LLM에 올리면 안 된다고 판단한 정보는 무엇인가?
왜 위험한가?
```

## 성공 기준

- [ ] 실제 개인정보를 Prompt에 넣지 않았습니다.
- [ ] 실제 API Key를 Notebook에 적지 않았습니다.
- [ ] Prompt Log에도 민감정보가 없습니다.
- [ ] 캡처 화면에도 Secret이 없습니다.
- [ ] `.env`와 `.env.example`의 차이를 이해했습니다.

---

# STEP 7. Chapter 01 Notebook 확인하기

## 7-1. 목적

현재 제공된 Chapter 01 Notebook의 역할을 정확히 이해합니다.

Notebook:

```text
notebooks/ch01_ai_data_analysis_intro.ipynb
```

현재 이 Notebook은 다음을 포함하는 starter scaffold입니다.

```text
pandas
numpy
matplotlib
seaborn
Path
DATA_DIR = Path('../data/raw')
```

## 7-2. 환경이 아직 준비되지 않았다면

Notebook 파일이 존재하는지만 확인하고 **Chapter 02를 먼저 진행**합니다.

답안에는 다음처럼 기록합니다.

```text
상태: 실행 전
이유: Chapter 02에서 Python/VS Code/Jupyter 환경 설정 후 실행 예정
```

실행하지 않았는데 PASS로 표시하지 않습니다.

## 7-3. 환경이 이미 준비되어 있다면

다음 import 셀을 실행합니다.

```python
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

DATA_DIR = Path('../data/raw')
sns.set_theme(style='whitegrid')
```

데이터가 준비되어 있다면 다음도 확인할 수 있습니다.

```python
customers = pd.read_csv(DATA_DIR / 'customers.csv')
customers.head()
```

## 7-4. 답안에 반드시 작성할 것

환경설정 완료 학생:

```text
실행 결과
결과 관찰
현재 Notebook의 역할에 대한 해석
Chapter 02~03에서 추가로 확인할 내용
```

환경설정 전 학생:

```text
Notebook 위치 확인
현재 미실행 상태
왜 아직 실행하지 않았는지
언제 검증할 것인지
```

## 7-5. Evidence

환경설정 완료 학생만 권장:

```text
images/step07_notebook_result.png
```

## 성공 기준

환경 미설정 학생:

- [ ] Notebook 위치를 확인했습니다.
- [ ] 실행하지 않은 상태를 정확히 기록했습니다.
- [ ] Chapter 02에서 실행할 계획을 작성했습니다.

환경 설정 완료 학생:

- [ ] Notebook이 열립니다.
- [ ] import 셀이 오류 없이 실행됩니다.
- [ ] `DATA_DIR`의 의미를 이해합니다.
- [ ] 결과를 자신의 말로 해석했습니다.
- [ ] Evidence를 첨부했습니다.

---

# STEP 8. Chapter 01 최종 해석 작성하기

## 8-1. 목적

Chapter 01에서 가장 중요한 것은 실행량이 아니라 **AI를 어떻게 검증하며 사용할 것인지 자신의 언어로 설명하는 것**입니다.

## 8-2. 답안에 작성할 질문

답안 템플릿의 최종 해석 부분에 다음을 작성합니다.

### 질문 1

```text
이번 장에서 가장 중요하다고 생각한 내용은 무엇인가?
```

3~5문장으로 작성합니다.

### 질문 2

```text
LLM을 데이터 분석에 사용할 때 가장 조심해야 할 점은 무엇인가?
```

### 질문 3

사람과 LLM의 역할을 비교합니다.

| 항목 | LLM이 도울 수 있는 부분 | 사람이 책임져야 하는 부분 |
| --- | --- | --- |
| 질문 정의 |  |  |
| 데이터 확인 |  |  |
| 코드 작성 |  |  |
| 결과 해석 |  |  |
| 최종 판단 |  |  |

### 질문 4

```text
다음 Chapter에서 실제로 확인하고 싶은 것은 무엇인가?
```

## 성공 기준

- [ ] 자신의 말로 작성했습니다.
- [ ] LLM 답변을 그대로 복사하지 않았습니다.
- [ ] 관찰과 추측을 구분했습니다.
- [ ] 사람이 책임져야 할 판단을 설명했습니다.
- [ ] 남은 확인 사항을 작성했습니다.

---

# STEP 9. 최종 제출 파일 검증하기

## 9-1. 목적

GitHub에 올리기 전에 제출 파일 자체를 검수합니다.

## 9-2. 체크리스트

- [ ] 모든 필수 STEP을 작성했습니다.
- [ ] 핵심 실행 Evidence를 첨부했습니다.
- [ ] 이미지 경로가 `images/...` 형태로 맞습니다.
- [ ] 결과 관찰을 작성했습니다.
- [ ] 나의 해석과 판단을 작성했습니다.
- [ ] 업무·분석적 의미를 작성했습니다.
- [ ] 한계와 추가 확인 사항을 작성했습니다.
- [ ] LLM 결과를 정답처럼 표현하지 않았습니다.
- [ ] 실행하지 않은 것은 PASS로 표시하지 않았습니다.
- [ ] 개인정보가 없습니다.
- [ ] API Key·Secret·Token이 없습니다.
- [ ] 캡처 화면에도 민감정보가 없습니다.

---

# STEP 10. 개인 GitHub 저장소에 업로드하기

## 10-1. 목적

실습 결과를 Chapter 15까지 누적되는 개인 학습 포트폴리오로 관리합니다.

## 10-2. 개인 저장소

처음 한 번만 다음과 같은 Public 저장소를 만듭니다.

권장 이름:

```text
llm-data-analysis-study
```

### Chapter 01 권장 구조

```text
llm-data-analysis-study/
└─ chapter01/
   ├─ chapter01.md
   └─ images/
      ├─ step01_question.png
      ├─ step02_data_structure.png
      ├─ step03_llm_response.png
      ├─ step04_validation.png
      ├─ step05_prompt_log.png
      └─ step07_notebook_result.png
```

## 10-3. Git을 아직 배우지 않은 학생

Chapter 01에서는 GitHub 웹만으로 제출해도 됩니다.

```text
개인 저장소 열기
→ Add file
→ Upload files
→ chapter01.md와 images 파일 업로드
→ Commit
```

## 10-4. Git 사용이 가능한 학생

로컬 Git을 사용할 수 있다면 다음 방식도 가능합니다.

```powershell
git add .
git commit -m "docs: complete chapter01 practice"
git push
```

> Chapter 02에서 Git과 개발 환경을 정식으로 다룹니다. Chapter 01에서 Git 명령이 익숙하지 않은 학생은 웹 업로드 방식을 사용하면 됩니다.

## 성공 기준

- [ ] 개인 저장소가 있습니다.
- [ ] `chapter01/chapter01.md`가 올라가 있습니다.
- [ ] `chapter01/images/` 이미지가 올라가 있습니다.
- [ ] GitHub에서 Markdown을 열었을 때 이미지가 정상 표시됩니다.

---

# STEP 11. 최종 파일 URL 제출하기

## 11-1. 제출할 URL

저장소 루트 URL이 아니라 **Chapter 01 최종 파일 URL**을 제출합니다.

잘못된 예:

```text
https://github.com/student-id/llm-data-analysis-study
```

올바른 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter01/chapter01.md
```

## 11-2. 제출 전 마지막 확인

제출 URL을 새 브라우저 탭에서 열어 확인합니다.

- [ ] 파일이 열립니다.
- [ ] Markdown이 정상 표시됩니다.
- [ ] 이미지가 정상 표시됩니다.
- [ ] 개인정보와 Secret이 없습니다.
- [ ] 교수자가 바로 Chapter 01 답안을 확인할 수 있습니다.

---

# 최종 산출물

학생이 제출할 최종 결과는 다음입니다.

```text
개인 GitHub Public 저장소의
Chapter 01 최종 Markdown 파일 URL
```

최종 파일에는 최소한 다음이 포함되어야 합니다.

```text
원래 업무 질문
구체화한 분석 질문
필요한 데이터
LLM Prompt
LLM 답변 요약
LLM 제안 검증
Prompt Log
핵심 실행 Evidence
결과 관찰
나의 해석과 판단
업무·분석적 의미
한계와 추가 확인 사항
Chapter 01 최종 해석
```

---

# Chapter 01 완료 기준

다음 질문에 모두 답할 수 있으면 Chapter 01의 핵심 목표를 달성한 것입니다.

```text
왜 분석은 질문에서 시작하는가?
LLM은 분석에서 무엇을 도울 수 있는가?
LLM이 만든 결과를 왜 검증해야 하는가?
실행 결과와 분석 성공은 왜 다른가?
결과를 보고 내가 어떤 판단을 내렸는가?
현재 결과만으로 말할 수 없는 것은 무엇인가?
Public GitHub에 올리면 안 되는 정보는 무엇인가?
내 최종 제출 파일을 다른 사람이 열어 재검토할 수 있는가?
```

---

# 다음 장 준비

다음은 **2장. VS Code에서 시작하는 데이터 분석 환경**입니다.

Chapter 02에서는 다음을 실제로 준비합니다.

```text
Python
→ VS Code
→ Git
→ 저장소 clone
→ .venv 생성
→ 패키지 설치
→ Jupyter Notebook
→ 커널 선택
→ 첫 실행 검증
```

Chapter 01에서 만든 개인 GitHub 저장소는 Chapter 02~15에서도 계속 사용합니다.
