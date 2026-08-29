# Chapter 10 답안 양식. 분류 분석으로 주문 취소 여부 예측하기

> 이 내용을 `chapter10.ipynb`의 Markdown 셀로 작성합니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. 분류 문제 정의
- 타깃:
- 0의 의미:
- 1의 의미:
- 예측 시점:
- 예측 시점에 사용할 수 있는 정보:
- 예측 이후에만 알 수 있어 제외한 정보:

### 나의 해석과 판단
왜 이 타깃과 예측 시점을 선택했는지 작성하세요.

## 2. 클래스 비율
| 클래스 | 개수 | 비율 |
| --- | ---: | ---: |
| 0 | | |
| 1 | | |

![클래스 비율](images/step02_class_ratio.png)

### 결과 관찰

### 나의 해석과 판단
클래스 불균형이 accuracy 해석에 어떤 영향을 주는지 작성하세요.

## 3. Dummy Baseline
| 모델 | Accuracy | Precision | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Dummy | | | | |
| 실제 모델 | | | | |

![Baseline 비교](images/step03_baseline.png)

### 결과 관찰

### 나의 해석과 판단
실제 모델이 Dummy baseline보다 의미 있게 나아졌는지 작성하세요.

### 업무·분석적 의미

### 한계와 추가 확인 사항

## 4. Validation 성능과 우선 지표
- Accuracy:
- Precision:
- Recall:
- F1:

### 내가 가장 중요하게 본 지표

### 그 이유

> 실제 FP/FN 비용 정보가 없다면 가정임을 명시하세요.

## 5. Threshold 비교
| Threshold | Precision | Recall | F1 | 예상 특징 |
| ---: | ---: | ---: | ---: | --- |
| | | | | |
| | | | | |
| | | | | |

![Threshold 비교](images/step05_threshold.png)

### 내가 선택한 Threshold

### 선택 이유

### 나의 해석과 판단
Threshold를 final test가 아니라 validation에서 정해야 하는 이유를 작성하세요.

## 6. FP/FN 해석
- FP 의미:
- FN 의미:
- 현재 목적에서 더 부담스러울 수 있는 오류:
- 그 판단에 추가로 필요한 업무 정보:

![Confusion Matrix](images/step06_confusion_matrix.png)

### 업무·분석적 의미

### 한계와 추가 확인 사항

## 7. Final Test
- Accuracy:
- Precision:
- Recall:
- F1:
- Validation 대비 변화:

### 결과 관찰

### 나의 해석과 판단
Final test 결과를 보고 모델 일반화에 대해 어떻게 판단했는지 작성하세요.

## 8. 최종 사용 판단
- [ ] 참고용 사용 가능
- [ ] 추가 검증 후 사용 가능
- [ ] 현재 사용 보류

### 판단 근거
1.
2.
3.

### 현재 모델의 가장 큰 위험

### 다음 개선 우선순위
1.
2.
3.

## 최종 체크
- [ ] 타깃과 예측 시점을 정의했습니다.
- [ ] 클래스 비율을 확인했습니다.
- [ ] Dummy baseline과 비교했습니다.
- [ ] precision/recall/F1을 해석했습니다.
- [ ] Threshold 선택 이유를 작성했습니다.
- [ ] FP/FN의 의미를 설명했습니다.
- [ ] Validation과 Final Test를 구분했습니다.
- [ ] 최종 Notebook URL을 제출합니다.