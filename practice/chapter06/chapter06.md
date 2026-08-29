# 6장 실습. 데이터를 보며 질문을 만드는 EDA

> 목표는 표를 많이 만드는 것이 아니라 **질문 → 지표 → 계산 → 검증 → 관찰 → 가설 → 다음 질문**을 연결하는 것입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter06/templates/chapter06_assignment.md`
- 주 제출물: 개인 저장소의 `chapter06/chapter06.ipynb`

공식 Notebook:

```text
notebooks/ch06_eda_questions.ipynb
```

보조 스크립트:

```text
scripts/preprocess_data.py
scripts/run_eda.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 개인 작업 폴더의 `chapter06/chapter06.ipynb`로 사용합니다. Notebook 밖 화면은 `chapter06/images/`에 저장합니다.

## STEP 1. 전처리 데이터 준비
`data/processed/*_clean.csv`가 있는지 확인합니다. 없다면 프로젝트 루트에서 실행합니다.

```powershell
python scripts/preprocess_data.py
```

성공 기준:
- [ ] 전처리 데이터가 존재합니다.
- [ ] Notebook이 오류 없이 데이터를 읽습니다.

## STEP 2. EDA 질문을 지표로 바꾸기
최소 3개의 EDA 질문을 작성하고 각 질문에 다음을 연결합니다.

```text
질문
→ 분석 범위
→ 필요한 데이터
→ 지표
→ 계산 방법
→ 검증 방법
```

예: `카테고리별 completed 주문 수량과 금액은 어떻게 다른가?`

답안에는 **왜 이 질문이 현재 데이터로 답할 수 있는지** 작성합니다.

## STEP 3. 핵심 분포와 집계 실행
Notebook의 고객·상품·주문·금액 관련 EDA 셀을 순서대로 실행합니다.

금액성 분석은 `order_status == "completed"` 범위를 사용하고 `line_total` 합계를 확인합니다.

Evidence 예:
- 범주형 분포
- 숫자형 분포
- 카테고리별 completed 금액
- 월별 completed 금액

## STEP 4. 집계 총합 검증
그룹별 집계가 원본 completed 주문 상세의 `line_total` 총합과 일치하는지 확인합니다.

```text
원본 completed 합계
=
카테고리 합계
=
월별 합계
(같은 분석 범위를 사용했다면)
```

불일치하면 필터 범위, merge, 중복, 결측을 먼저 확인합니다.

## STEP 5. 관찰·가설·추가 검증 분리
핵심 결과 2개 이상에 대해 다음을 Notebook Markdown 셀로 작성합니다.

```text
관찰: 데이터에서 직접 확인한 사실
가설: 그 사실을 설명할 수 있는 가능성
추가 검증: 가설을 확인하기 위해 다음에 계산할 것
```

**가설을 결론처럼 쓰지 않습니다.**

## STEP 6. LLM으로 다음 질문 확장
원본 개인정보가 아니라 구조·집계 요약만 사용해 LLM에 다음 분석 질문 후보를 요청합니다.

기록할 것:
- Prompt
- LLM 제안
- 실제 데이터로 가능한지
- 사용 / 수정 후 사용 / 보류
- 사람이 수정한 이유

## STEP 7. 재현 가능한 EDA 결과 확인
가능하면 다음도 실행합니다.

```powershell
python scripts/run_eda.py
```

`reports/`에 생성된 결과와 Notebook의 핵심 집계가 같은 범위를 사용하는지 확인합니다.

## STEP 8. 최종 해석 작성
답안 양식에 최소 다음 내용을 작성합니다.

1. 가장 의미 있다고 본 관찰 2~3개
2. 각 관찰을 설명할 수 있는 가설
3. 현재 데이터만으로 단정할 수 없는 것
4. 다음 분석 우선순위
5. 업무적으로 확인할 가치가 있는 질문

## 최종 제출
개인 GitHub 저장소에 다음 구조로 올립니다.

```text
chapter06/
├─ chapter06.ipynb
└─ images/
```

제출 URL 예:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter06/chapter06.ipynb
```

## 완료 체크
- [ ] Notebook 전체 실행
- [ ] EDA 질문 3개 이상
- [ ] completed 범위 확인
- [ ] 집계 총합 검증
- [ ] 관찰/가설/추가 검증 분리
- [ ] LLM 제안 검증
- [ ] 결과 해석과 한계 작성
- [ ] GitHub에서 Notebook 정상 표시
- [ ] 최종 Notebook URL 제출