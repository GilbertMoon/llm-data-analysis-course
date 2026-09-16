# Chapter 10 이미지 자산

현재 Chapter 10의 주제는 **분류 분석으로 주문 취소 여부 예측하기**입니다.

## 현재 강의용 SVG

다음 5개 파일을 Chapter 10 이론·실습·발표 자료의 우선 이미지로 사용합니다.

```text
ch10_classification_overview_flow.svg
ch10_target_feature_contract.svg
ch10_train_validation_test_roles.svg
ch10_threshold_confusion_matrix.svg
ch10_classification_evidence.svg
```

역할:

| 파일 | 역할 |
|---|---|
| `ch10_classification_overview_flow.svg` | Target부터 Validation Evidence까지 전체 분류 흐름 |
| `ch10_target_feature_contract.svg` | completed/cancelled Target과 예측 시점 Feature Contract |
| `ch10_train_validation_test_roles.svg` | Train·Validation·Final Test 역할과 Test 재사용 금지 |
| `ch10_threshold_confusion_matrix.svg` | Threshold 변화, Precision/Recall, FP/FN 및 혼동행렬 |
| `ch10_classification_evidence.svg` | 분류 분석 Evidence와 Internal/Public 산출물 구분 |

## 핵심 계약

```text
completed = 0
cancelled = 1
refunded / 기타 상태 = 모델링 제외

Validation
→ 모델 선택
→ Threshold 선택
→ 선택 고정

Final Test
→ 마지막 평가에만 사용
```

공개 이미지에는 실제 고객 이름, 이메일, 전화번호, 주소, 주문 ID, 고객 ID를 사용하지 않습니다.

## 레거시 자산

다음 이름을 포함한 기존 PNG/SVG는 프로젝트 초기 **LLM 코드 생성·검증** 주제에서 사용한 레거시 자산입니다.

```text
ch10_prompt_to_code_workflow.*
ch10_llm_code_generation_validation_flow.*
ch10_error_debugging_loop.*
ch10_code_review_checklist.*
ch10_code_validation_deliverables.*
```

호환성과 과거 기록을 위해 삭제하지 않지만, 현재 Chapter 10 분류 강의의 대표 이미지로 사용하지 않습니다.

## Private 이미지 기획 기준

Private 교재 저장소:

```text
book/chapters/ch10_llm_code_generation_images.md
```

파일명은 레거시 명칭이지만 내용은 현재 분류 강의 기준으로 유지합니다.
