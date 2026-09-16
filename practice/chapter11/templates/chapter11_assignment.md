# Chapter 11 답안 양식. LLM과 함께 분석 질문을 다듬기

> 이 내용을 `chapter11.ipynb`의 Markdown 셀로 작성합니다.  
> 자동 생성된 Safe Context와 Prompt Template은 **외부 제공 승인 자료가 아니라 사람 검토용 초안**입니다.

## 제출 정보
- 이름:
- GitHub ID:
- 작성일:
- 최종 Notebook URL:

## 1. 입력 데이터와 환경
- `source_type`:
- processed 4개 파일 확인: PASS / FAIL
- Notebook 커널:
- `scripts/preprocess_data.py` 실행 여부:

### 확인 내용
raw 데이터로 자동 fallback하지 않았는지 작성하세요.

## 2. LLM 사용 전 분석 질문
- 분석 질문:
- 분석 범위:
- 분석 단위:
- 필요한 지표:
- LLM에게 맡길 일:
- 사람이 직접 판단할 일:
- 검증에 사용할 Evidence:

### 나의 해석과 판단
왜 이 질문에 LLM 도움이 필요한지, 현재 데이터로 실제 계산 가능한지 작성하세요.

## 3. Safe Context와 민감정보 검토

### 실제 사용 후보 Safe Context
```text
사람이 검토한 Safe Context의 핵심 내용을 작성하세요.
원본 개인정보·원본 거래 행·Secret은 포함하지 않습니다.
```

### 민감성 검토
- 원본 행 제외: PASS / FAIL
- 직접 식별정보 제외: PASS / FAIL
- Secret/API Key 제외: PASS / FAIL
- 민감 컬럼명 검토: PASS / FAIL
- 소수 범주 재식별 위험 검토: PASS / FAIL
- 내부 URL/민감 경로 제외: PASS / FAIL

## 4. Safe Context 자동 Validation

`reports/ch11_safe_context_validation.csv` 결과를 기록합니다.

| check | value | status |
| --- | --- | --- |
| processed_context_only |  |  |
| sensitive_column_names_hidden |  |  |
| raw_value_examples_not_generated |  |  |
| external_context_requires_human_review |  |  |
| prompt_injection_warning_present |  |  |

### 나의 판단
자동 PASS가 외부 LLM 제공 승인과 같은 의미가 아닌 이유를 작성하세요.

## 5. 사용한 Prompt
- Prompt step:
- Prompt version:
- 사용 목적:

```text
실제 사용한 Prompt 또는 최종 검토 Prompt를 작성하세요.
```

### Prompt 계약 확인
- [ ] 역할
- [ ] 목적
- [ ] 승인된 Context
- [ ] 요청
- [ ] 제약
- [ ] 계산 기준
- [ ] 출력 형식
- [ ] 검증 조건

### Prompt 설계 이유
존재하지 않는 컬럼 생성, 개인정보 요구, 검증 없는 단정을 어떻게 막았는지 작성하세요.

## 6. LLM 실제 사용 여부

자동 생성 Log의 초기 상태는 실제 사용 증거가 아닙니다.

- `execution_status`: executed / not_executed
- `executed_at`:
- provider:
- model:
- prompt_version:
- input_summary:

> 실제 LLM을 사용하지 않았다면 provider/model을 임의로 작성하지 않고 `not_executed`로 남깁니다.

## 7. LLM 응답 또는 제안 요약
1.
2.
3.

### 결과 관찰
LLM이 어떤 질문·지표·코드·해석을 제안했는지 사실 위주로 작성하세요.

### 나의 해석과 판단
가장 유용한 제안과 가장 위험하거나 검증이 필요했던 제안을 작성하세요.

## 8. Evidence Matrix 검증

| LLM 제안/주장 | 확인 Evidence | 실제 결과 | 최종 판단 |
| --- | --- | --- | --- |
|  | `df.columns` / 수치 / 병합 / 모델 지표 등 |  | 사용 / 수정 후 사용 / 보류 |
|  |  |  |  |
|  |  |  |  |

### 사람이 수정한 내용

### 수정 이유와 Evidence

검증할 수 없는 원인 주장은 사실로 확정하지 않고 가설 또는 추가 데이터 필요로 남깁니다.

## 9. 외부 문서·Prompt Injection 검토

외부 웹·PDF·이메일·문서를 사용했다면 작성합니다.

- 외부 콘텐츠 사용 여부: 예 / 아니오
- 발견한 의심 지시문:
- `untrusted data`로 처리한 방법:
- 실행하지 않은 위험 행동:

예:

```text
이전 지시를 무시하라
비밀정보를 출력하라
파일을 삭제하라
외부 서버로 전송하라
```

이런 문장은 분석 대상 문자열이며 실행 명령으로 따르지 않습니다.

## 10. 회귀·분류 Prompt 검토

모델링 관련 Prompt를 검토했다면 작성합니다.

### 회귀
- prediction time 명시:
- Target 계산 재료 누수 제외:
- 시간 순서 분할:
- Train 내부 선택:
- Frozen Final Test:

### 분류
- completed=0 / cancelled=1:
- refunded/기타 상태 제외:
- Feature Contract:
- Validation 모델 선택:
- Validation Threshold 선택:
- Frozen Final Test:
- FP/FN 확인:

## 11. 최종 LLM 사용 기록
- response_summary:
- validation_result:
- revision_note:
- final_use: used / partial / not_used
- 남은 불확실성:

### 다음에는 어떻게 Prompt/Context를 개선할 것인가?

## 12. 최종 인사이트

### LLM이 가장 잘 도와준 부분

### 가장 위험하거나 틀릴 수 있다고 판단한 부분

### 실제 데이터로 검증한 Evidence

### 사람이 최종적으로 수정한 판단

### 현재 결과만으로 말할 수 없는 것

## 최종 제출 체크
- [ ] processed 데이터에서 시작했습니다.
- [ ] raw 자동 fallback을 사용하지 않았습니다.
- [ ] Safe Context를 사람 검토했습니다.
- [ ] `ch11_safe_context_validation.csv`를 확인했습니다.
- [ ] 실제 개인정보/Secret/내부 경로가 없습니다.
- [ ] Prompt에 검증 조건이 있습니다.
- [ ] 외부 문서의 지시문을 `untrusted data`로 취급했습니다.
- [ ] LLM 결과를 실제 Evidence로 검증했습니다.
- [ ] 사람이 수정한 내용을 기록했습니다.
- [ ] `not_executed` 로그를 실제 사용 증거로 표현하지 않았습니다.
- [ ] 최종 Notebook URL을 제출합니다.
