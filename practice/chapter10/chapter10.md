# 10장 실습. 분류 분석으로 주문 취소 여부 예측하기

> 목표는 accuracy 하나만 보고 모델을 선택하는 것이 아니라 **클래스 비율, baseline, precision·recall·F1, threshold, FP/FN의 업무적 의미**를 함께 판단하는 것입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter10/templates/chapter10_assignment.md`
- 주 제출물: `chapter10/chapter10.ipynb`

현재 실습 Notebook 파일명은 과거 명칭을 유지합니다.

```text
notebooks/ch10_llm_code_generation.ipynb
```

하지만 **현재 Chapter 10의 실제 주제는 주문 취소 여부 분류 분석**입니다.

보조 스크립트:

```text
scripts/run_classification_analysis.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 개인 저장소의 `chapter10/chapter10.ipynb`로 사용합니다.

## STEP 1. 타깃과 예측 시점 정의
다음을 명확히 작성합니다.

```text
분류 타깃은 무엇인가?
어떤 값을 0/1로 두는가?
언제 예측하는가?
그 시점에 알 수 없는 정보는 무엇인가?
```

예측 이후에만 알 수 있는 정보를 feature로 사용하지 않습니다.

## STEP 2. 클래스 비율 확인
타깃 클래스의 개수와 비율을 확인합니다.

```text
클래스 0 개수/비율
클래스 1 개수/비율
```

불균형 데이터에서는 accuracy가 높아도 소수 클래스를 거의 찾지 못할 수 있음을 해석에 반영합니다.

## STEP 3. Dummy baseline 확인
복잡한 모델 전에 단순 기준 모델 성능을 확인합니다.

비교할 항목:
- accuracy
- precision
- recall
- F1
- 가능하면 confusion matrix

## STEP 4. 모델 학습과 validation 평가
모델을 학습하고 validation에서 지표를 확인합니다.

제출 답안에는 **어떤 지표를 우선할지와 그 이유**를 반드시 작성합니다.

예:

```text
취소 주문을 놓치는 FN 비용이 더 크다고 판단한다면 recall을 더 중요하게 볼 수 있다.
```

단, 실제 업무 비용은 별도 정보가 필요하므로 수업 데이터만으로 확정하지 않습니다.

## STEP 5. Threshold 비교
가능한 경우 여러 threshold에서 precision/recall/F1과 예측 결과가 어떻게 달라지는지 비교합니다.

threshold는 final test를 보며 선택하지 않습니다. validation에서 선택 기준을 정합니다.

## STEP 6. FP/FN 사례 해석
confusion matrix를 기준으로 다음을 작성합니다.

```text
FP는 어떤 오류인가?
FN은 어떤 오류인가?
현재 분석 목적에서는 어느 오류가 더 부담스러울 수 있는가?
그 판단에 추가로 필요한 업무 정보는 무엇인가?
```

## STEP 7. Final Test 1회 평가
validation에서 모델과 threshold 선택을 끝낸 후 final test를 마지막 검증으로 사용합니다.

최종 test 결과가 기대보다 낮으면 결과를 꾸미지 않고 원인 후보와 한계를 작성합니다.

## STEP 8. 스크립트 재실행

```powershell
python scripts/run_classification_analysis.py
```

Notebook과 동일한 타깃/분할/평가 원칙을 사용하는지 확인합니다.

## STEP 9. 실제 사용 가능성 판단
다음 중 하나를 선택합니다.

```text
참고용 사용 가능
추가 검증 후 사용 가능
현재 사용 보류
```

판단 근거에는 최소 다음을 포함합니다.
- 클래스 비율
- baseline 대비 개선
- precision/recall/F1
- FP/FN 비용에 대한 가정
- threshold 선택 이유
- final test 결과

## 최종 제출

```text
chapter10/
├─ chapter10.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter10/chapter10.ipynb
```

## 완료 체크
- [ ] 타깃 정의
- [ ] 예측 시점/leakage 점검
- [ ] 클래스 비율 확인
- [ ] Dummy baseline 비교
- [ ] precision/recall/F1 해석
- [ ] threshold 선택 근거
- [ ] FP/FN 업무적 의미
- [ ] validation 후 final test 1회
- [ ] 최종 사용 판단과 한계
- [ ] 최종 Notebook URL 제출