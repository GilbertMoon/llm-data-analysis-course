# 8장 실습. 작은 데이터 분석 프로젝트 완성하기

> 목표는 예쁜 보고서를 만드는 것이 아니라 **질문 → 데이터 점검 → 전처리 → EDA → 시각화 → 해석 → 한계**가 다시 실행 가능한 하나의 흐름으로 연결되게 만드는 것입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter08/templates/chapter08_assignment.md`
- 주 제출물: `chapter08/chapter08.ipynb`

공식 Notebook:

```text
notebooks/ch08_midterm_project.ipynb
```

보조 스크립트:

```text
scripts/run_midterm_project.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 개인 저장소용 `chapter08/chapter08.ipynb`로 사용합니다. 외부 Evidence는 `chapter08/images/`에 저장합니다.

## STEP 1. 프로젝트 질문과 완료 기준 정하기
분석 질문 1~3개를 정하고 다음을 명시합니다.

```text
분석 대상
분석 범위
사용 데이터
사용 지표
성공적으로 답했다고 판단할 기준
```

질문이 너무 크면 여러 하위 질문으로 나눕니다.

## STEP 2. 입력 데이터와 전처리 상태 검증
Chapter 05의 processed 데이터를 사용하고 다음을 확인합니다.

- 파일 존재
- shape
- 결측/중복 핵심 항목
- PK/FK 관계
- completed 금액 범위

전처리가 맞다고 가정하지 말고 최소 검증을 다시 수행합니다.

## STEP 3. 핵심 EDA 실행
질문에 직접 필요한 집계만 수행합니다.

각 집계에 대해:

```text
질문
→ 지표
→ 계산
→ 총합/범위 검증
→ 관찰
```

을 기록합니다.

## STEP 4. 대표 시각화 작성
프로젝트 질문에 가장 도움이 되는 그래프 2~4개를 선택합니다.

각 그래프 아래에 다음을 작성합니다.

- 그래프가 보여 주는 사실
- 왜 이 그래프를 선택했는가
- 업무적으로 어떤 의미가 있는가
- 그래프만으로 단정할 수 없는 것

## STEP 5. 핵심 인사이트 작성
최소 3개의 핵심 인사이트를 작성합니다.

좋은 형식:

```text
관찰된 수치/패턴
→ 내 해석
→ 근거
→ 업무적으로 확인할 가치
→ 한계
```

원인을 확인하지 못했다면 원인처럼 표현하지 않습니다.

## STEP 6. LLM 보조 사용 기록
LLM을 사용했다면 다음을 남깁니다.

- 사용 목적
- Safe Context
- Prompt
- LLM 제안
- 실제 반영 여부
- 사람이 수정한 내용
- 검증 근거

LLM을 사용하지 않았다면 `미사용`과 이유를 기록합니다.

## STEP 7. 프로젝트 재실행
가능하면 실행합니다.

```powershell
python scripts/run_midterm_project.py
```

Notebook 결과와 스크립트 결과의 분석 범위와 핵심 수치가 일치하는지 확인합니다.

## STEP 8. 최종 보고서 관점 정리
답안에 다음을 포함합니다.

1. 분석 질문
2. 데이터 범위
3. 전처리 검증
4. EDA 핵심 결과
5. 대표 시각화
6. 핵심 인사이트
7. 업무·분석적 의미
8. 한계
9. 다음 분석 제안
10. 재현 방법

## 최종 제출 구조

```text
chapter08/
├─ chapter08.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter08/chapter08.ipynb
```

## 완료 체크
- [ ] 질문과 지표가 연결됨
- [ ] 입력 데이터 최소 재검증
- [ ] 핵심 EDA 총합/범위 검증
- [ ] 대표 그래프와 해석
- [ ] 인사이트에 근거 포함
- [ ] 원인 과대 해석 없음
- [ ] 재실행 가능성 확인
- [ ] 한계와 다음 분석 작성
- [ ] 최종 Notebook URL 제출