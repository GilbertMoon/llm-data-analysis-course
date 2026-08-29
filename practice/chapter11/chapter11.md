# 11장 실습. LLM과 함께 분석 질문을 다듬기

> 목표는 LLM에게 많은 데이터를 전달하는 것이 아니라 **허용된 최소 정보로 질문을 설계하고, LLM 제안을 실제 데이터·코드·수치로 검증한 뒤 사람이 수정·승인하는 과정**을 경험하는 것입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter11/templates/chapter11_assignment.md`
- 주 제출물: `chapter11/chapter11.ipynb`

공식 Notebook:

```text
notebooks/ch11_llm_prompt_analysis.ipynb
```

보조 스크립트:

```text
scripts/run_llm_prompt_analysis.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 개인 저장소의 `chapter11/chapter11.ipynb`로 사용합니다. LLM 화면 캡처는 `chapter11/images/`에 저장합니다.

## STEP 1. 분석 질문을 먼저 정의하기
LLM을 열기 전에 분석 질문과 검증 기준을 작성합니다.

```text
무엇이 궁금한가?
현재 데이터로 계산 가능한가?
어떤 지표가 필요한가?
LLM에게 무엇을 맡기고 무엇은 사람이 판단할 것인가?
```

LLM 사용 목적이 불명확하면 Prompt도 평가하기 어렵습니다.

## STEP 2. Safe Context 만들기
원본 개인정보나 전체 거래 행을 그대로 넣지 않습니다.

가능하면 다음 정도만 제공합니다.

```text
데이터셋 이름
행/열 규모
필요한 컬럼명과 의미
dtype
집계된 값
분석 범위
개인정보를 제거한 오류 메시지
```

컬럼명이나 집계값도 민감할 수 있는 실제 업무에서는 조직 정책을 먼저 확인합니다.

## STEP 3. Prompt 작성하기
좋은 분석 Prompt에는 가능한 한 다음이 포함됩니다.

```text
목적
데이터 Context
분석 범위
제약 조건
원하는 출력 형식
검증할 항목
모르는 것은 단정하지 말라는 조건
```

사용한 Prompt를 답안에 기록합니다. 실제 Secret, 고객 개인정보, 내부 URL은 포함하지 않습니다.

## STEP 4. LLM 응답을 초안으로 받기
LLM이 제안한 질문·지표·코드·해석 후보를 요약합니다.

전체 답변을 무조건 복사하기보다 핵심 제안을 구분합니다.

```text
제안 A
제안 B
제안 C
```

## STEP 5. 실제 데이터 기준으로 검증하기
각 제안을 다음 기준으로 확인합니다.

| 검증 항목 | 확인 내용 |
| --- | --- |
| 실제 컬럼인가? | 실제 schema와 비교 |
| 계산 가능한 지표인가? | 데이터 범위/키 확인 |
| 기존 completed 범위와 일치하는가? | 필터 기준 확인 |
| 원인을 단정하는가? | 데이터가 실제 원인을 포함하는지 확인 |
| 추가 데이터가 필요한가? | 현재 데이터 한계 확인 |

제안마다 다음 중 하나를 선택합니다.

```text
사용
수정 후 사용
보류
```

## STEP 6. 사람이 수정한 내용 기록하기
LLM 결과를 수정했다면 다음을 기록합니다.

```text
원래 LLM 제안
→ 문제가 된 부분
→ 내가 수정한 내용
→ 수정한 이유
→ 실제 검증 근거
```

이 기록이 AI 결과와 사람 판단을 구분하는 Evidence가 됩니다.

## STEP 7. Prompt 버전과 사용 기록 남기기
최소 다음을 기록합니다.

- 사용 목적
- 사용한 Safe Context
- Prompt 버전 또는 최종 Prompt
- LLM 답변 요약
- 채택/수정/보류
- 사람이 검증한 항목
- 사람이 수정한 내용
- 남은 불확실성

## STEP 8. 보조 스크립트 확인
가능하면 실행합니다.

```powershell
python scripts/run_llm_prompt_analysis.py
```

스크립트가 사용하는 Context와 Prompt가 실제 보안·분석 범위를 지키는지 확인합니다.

API를 사용하는 환경이라면 실제 키는 `.env` 또는 승인된 Secret 방식으로 관리하고 캡처에 노출하지 않습니다.

## STEP 9. 최종 해석 작성
답안에 다음을 작성합니다.

1. LLM이 가장 잘 도와준 부분
2. 가장 위험하거나 틀릴 수 있다고 판단한 부분
3. 실제 데이터로 검증한 Evidence
4. 사람이 최종적으로 수정한 판단
5. 현재 LLM 답변만으로 말할 수 없는 것
6. 다음 분석에서 LLM을 사용할지와 이유

## 최종 제출

```text
chapter11/
├─ chapter11.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter11/chapter11.ipynb
```

## 완료 체크
- [ ] 분석 질문을 LLM보다 먼저 정의함
- [ ] Safe Context 사용
- [ ] 실제 개인정보/Secret 없음
- [ ] Prompt 기록
- [ ] LLM 제안을 실제 데이터로 검증
- [ ] 사용/수정 후 사용/보류 판단
- [ ] 사람 수정 내용과 근거 기록
- [ ] 결과의 업무적 의미와 한계 작성
- [ ] 최종 Notebook URL 제출