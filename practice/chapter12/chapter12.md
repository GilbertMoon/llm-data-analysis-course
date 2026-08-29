# 12장 실습. LLM이 만든 분석 코드를 검증하는 방법

> 목표는 생성 코드를 바로 실행하는 것이 아니라 **분석 타당성 검증과 실행 안전 검증을 분리하고, 사람이 승인한 코드만 제한된 환경에서 실행한 뒤 사후 결과까지 검증하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter12/templates/chapter12_assignment.md`
- 주 제출물: `chapter12/chapter12.ipynb`

현재 Notebook 파일명은 과거 명칭을 유지합니다.

```text
notebooks/ch12_report_generation.ipynb
```

하지만 **현재 Chapter 12의 실제 주제는 LLM 생성 분석 코드 검증**입니다.

보조 스크립트:

```text
scripts/run_llm_code_validation.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 개인 저장소의 `chapter12/chapter12.ipynb`로 사용합니다. 실행 승인/검증 화면이 Notebook 밖에 있으면 `chapter12/images/`에 저장합니다.

## STEP 1. Generated Code를 실행하지 않고 먼저 읽기
LLM이 만든 코드 또는 제공된 검증 대상 코드를 먼저 읽습니다.

확인할 것:

```text
어떤 파일을 읽는가?
어떤 파일을 쓰거나 삭제하는가?
어떤 컬럼과 key를 사용하는가?
어떤 주문 상태/분석 범위를 사용하는가?
외부 네트워크 요청이 있는가?
OS 명령이나 패키지 설치가 있는가?
환경변수/Secret을 읽는가?
```

**아직 실행하지 않습니다.**

## STEP 2. 분석 논리 검증
다음 항목을 실제 데이터·이전 Chapter 규칙과 비교합니다.

- 실제 존재하는 컬럼인가
- PK/FK 관계가 맞는가
- merge로 행이 증식할 위험이 없는가
- completed 주문 범위가 필요한 분석에서 정확히 적용되는가
- 금액 계산식이 맞는가
- 회귀/분류에서 prediction-time leakage가 없는가
- 그룹별 총합과 원본 총합을 비교할 수 있는가

분석적으로 틀리면 문법이 맞아도 실행 승인하지 않습니다.

## STEP 3. 실행 안전 위험 스캔
다음 위험을 별도로 확인합니다.

```text
파일 삭제/덮어쓰기
네트워크 전송
shell/OS 명령
패키지 설치
민감 경로 접근
Secret 출력
임의 subprocess 실행
```

자동/정적 점검 결과가 0건이어도 안전하다고 단정하지 않습니다.

```text
정적 스캔 0건 ≠ 안전 보장
자동 검증 PASS ≠ 실행 승인
```

## STEP 4. 사람의 승인/보류 판단
실행 전 다음 중 하나를 선택하고 근거를 작성합니다.

```text
APPROVE — 제한 실행 가능
REVISE — 수정 후 재검토
BLOCK — 실행 보류
```

판단 근거에는 분석 논리와 실행 안전 두 축을 모두 포함합니다.

## STEP 5. 코드 수정 기록
수정했다면 다음을 기록합니다.

```text
원래 코드/동작
→ 발견한 문제
→ 수정 내용
→ 수정 이유
→ 수정 후 다시 확인한 항목
```

LLM이 만든 원본과 사람 수정본을 구분합니다.

## STEP 6. 제한된 환경에서 실행
승인된 경우에만 Notebook의 실행 단계 또는 검증 스크립트를 수행합니다.

```powershell
python scripts/run_llm_code_validation.py
```

가능하면 원본 파일을 보존하고, 결과가 별도 경로에 생성되는지 확인합니다.

## STEP 7. 실행 후 분석 결과 검증
실행 성공 메시지만 보지 않습니다.

확인할 것:
- 입력/출력 행 수
- merge 결과
- completed 범위
- 금액 총합
- 파일 변경 범위
- 예상한 결과 파일만 생성되었는가
- 원본 데이터가 보존되었는가
- 오류/경고가 숨겨지지 않았는가

```text
코드 실행 성공 ≠ 분석 타당성
```

## STEP 8. Evidence와 최종 판단
답안에는 최소 다음을 포함합니다.

1. 생성 코드가 하려던 일
2. 실행 전 발견한 분석 위험
3. 실행 전 발견한 안전 위험
4. 승인/수정/차단 판단
5. 사람이 수정한 내용
6. 제한 실행 결과
7. 실행 후 검증 결과
8. 최종적으로 이 코드를 신뢰할 수 있는 범위
9. 아직 남은 위험/한계

## 최종 제출

```text
chapter12/
├─ chapter12.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter12/chapter12.ipynb
```

## 완료 체크
- [ ] Read Before Run 수행
- [ ] 분석 논리 검증
- [ ] 실행 안전 위험 검토
- [ ] 정적 스캔을 안전 보장으로 오해하지 않음
- [ ] 사람의 APPROVE/REVISE/BLOCK 판단
- [ ] 수정 기록
- [ ] 승인 후에만 제한 실행
- [ ] 실행 후 결과/파일/총합 검증
- [ ] 신뢰 범위와 한계 작성
- [ ] 최종 Notebook URL 제출