# 실습 공통 제출 가이드

이 문서는 `llm-data-analysis-course`의 Chapter 01~15 실습에 공통으로 적용하는 **답안 작성·실행 Evidence·GitHub 제출 기준**입니다.

수업에서 가장 중요한 것은 코드를 작성했다는 사실만 보여주는 것이 아닙니다.

```text
무엇을 실행했는가
→ 어떤 결과가 나왔는가
→ 그 결과를 어떻게 해석했는가
→ 내가 어떤 판단을 내렸는가
→ 무엇을 아직 확신할 수 없는가
```

를 하나의 제출 파일에서 확인할 수 있어야 합니다.

---

## 1. 전체 제출 흐름

모든 실습은 가능한 한 다음 흐름으로 진행합니다.

```text
강사 Public 저장소의 템플릿 확인
→ 템플릿 파일 다운로드 또는 복사
→ 로컬에서 STEP별 실습 진행
→ 핵심 실행 결과 화면 캡처
→ Markdown 또는 Notebook에 결과와 캡처 정리
→ 결과 관찰·해석·판단·한계 작성
→ 개인 GitHub Public 저장소에 업로드
→ GitHub에서 최종 파일 정상 표시 확인
→ 저장소 URL이 아닌 최종 파일 URL 제출
```

---

## 2. 강사 저장소와 학생 저장소의 역할

### 강사 Public 저장소

```text
https://github.com/GilbertMoon/llm-data-analysis-course
```

강사 저장소에는 다음이 있습니다.

- 실습 가이드
- 답안 템플릿
- Notebook 템플릿
- 샘플 데이터
- 공개 이미지
- 실행 스크립트
- 예제 Prompt

강사 저장소의 원본 파일을 직접 수정해서 제출하지 않습니다.

### 학생 개인 저장소

학생은 자신의 GitHub 계정에 별도의 Public 저장소를 하나 만들어 Chapter 01~15 결과를 누적합니다.

권장 저장소 이름:

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

---

## 3. 제출 파일에 반드시 들어갈 6가지

단순히 코드와 실행 화면만 제출하지 않습니다.

각 핵심 STEP에는 가능한 한 다음 여섯 항목을 포함합니다.

```text
① 실행 코드 / Prompt / 수행 내용
② 실행 결과 또는 화면 캡처
③ 결과 관찰
④ 나의 해석과 판단
⑤ 업무·분석적 의미
⑥ 한계와 추가 확인 사항
```

### ① 실행 코드 / Prompt / 수행 내용

무엇을 했는지 재현할 수 있어야 합니다.

### ② 실행 결과 또는 화면 캡처

실제로 실행했다는 Evidence를 남깁니다.

### ③ 결과 관찰

화면에 보이는 사실을 먼저 적습니다.

예:

```text
completed 주문 금액이 5월보다 6월에 감소했다.
```

### ④ 나의 해석과 판단

학생이 결과를 보고 어떤 판단을 했는지 자신의 말로 작성합니다.

예:

```text
전체 금액 감소가 주문 수 감소 때문인지 주문당 금액 감소 때문인지 추가 확인이 필요하다고 판단했다.
```

### ⑤ 업무·분석적 의미

결과가 실제 분석이나 의사결정에서 어떤 의미가 있는지 작성합니다.

예:

```text
월별 감소 원인을 파악하려면 카테고리와 주문 수를 추가로 분리해 보는 것이 다음 분석 우선순위라고 생각한다.
```

### ⑥ 한계와 추가 확인 사항

현재 데이터만으로 말할 수 없는 내용을 구분합니다.

예:

```text
금액 감소만으로 고객 이탈이 원인이라고 결론 내릴 수 없다.
```

---

## 4. 좋은 해석과 좋지 않은 해석

### 좋지 않은 예

```text
그래프가 내려갔습니다.
```

이 문장만으로는 학생의 분석 사고를 확인하기 어렵습니다.

### 더 좋은 예

```text
6월의 completed 주문 기준 금액이 5월보다 낮게 나타났다.
하지만 이 결과만으로 매출 감소 원인을 특정할 수는 없다.
주문 건수와 주문당 평균 금액을 분리해서 추가로 확인해야 한다고 판단했다.
```

핵심은 **관찰과 해석을 구분하는 것**입니다.

---

## 5. 화면 캡처 규칙

모든 클릭과 명령을 캡처할 필요는 없습니다.

**학습 목표를 달성했다는 것을 보여주는 핵심 Evidence만 캡처**합니다.

캡처 가치가 높은 예:

- Notebook 셀의 정상 실행 결과
- DataFrame 확인 결과
- 그래프
- LLM Prompt와 주요 응답
- 검증 결과
- 오류 해결 전·후 핵심 화면
- Airflow Task 상태와 최종 Validation 결과
- 최종 프로젝트 READY/WARN/BLOCKED 상태

캡처 가치가 낮은 예:

- 단순 `cd` 명령
- 파일을 열기만 한 화면
- 의미 없는 긴 콘솔 로그
- 코드 입력 중간 화면

Chapter별로 별도 지시가 없다면 **핵심 캡처 4~8장 정도**를 권장합니다.

---

## 6. 이미지 파일 이름

가능하면 의미 있는 이름을 사용합니다.

권장:

```text
images/step01_question.png
images/step03_llm_response.png
images/step04_validation.png
images/step07_notebook_result.png
```

권장하지 않음:

```text
스크린샷(1).png
image123.png
제목 없음.png
```

---

## 7. Markdown 이미지 삽입

예:

```markdown
![STEP 3 LLM 실행 결과](images/step03_llm_response.png)
```

GitHub에서 최종 Markdown 파일을 열었을 때 이미지가 정상 표시되는지 반드시 확인합니다.

---

## 8. Notebook 제출 시

Notebook을 제출하는 Chapter에서는 다음을 지킵니다.

- 실행한 핵심 셀의 Output을 남깁니다.
- Markdown 셀을 이용해 결과 해석을 작성합니다.
- 코드 셀만 연속해서 제출하지 않습니다.
- 그래프 아래에는 관찰과 해석을 작성합니다.
- 오류 셀을 그대로 남겨 제출하지 않습니다.
- 필요하면 별도 `images/` 폴더에 외부 실행 화면을 첨부합니다.

Notebook에서도 다음 구조를 권장합니다.

```text
실행
→ 결과
→ 관찰
→ 해석
→ 판단
→ 한계
```

---

## 9. 개인정보·Secret 보안

화면 캡처와 제출 파일에는 다음이 포함되면 안 됩니다.

```text
실제 API Key
Client Secret
Access Token
Password
DB 접속 비밀번호
실제 고객 개인정보
회사 내부 URL
비공개 업무자료
.env 실제 내용
GitHub Personal Access Token
```

GitHub에 올리기 전에 캡처 이미지까지 반드시 확인합니다.

Secret을 이미 Public GitHub에 올렸다면 문자열만 삭제하는 것으로 끝내지 않습니다.

```text
키 폐기 또는 재발급
→ 노출 파일 수정/삭제
→ Git 기록 노출 여부 확인
→ 새 키는 .env 또는 승인된 Secret 방식으로 관리
```

---

## 10. 개인 GitHub 저장소 만들기

Chapter 01에서는 아직 Git 환경설정을 배우기 전이므로 **GitHub 웹 브라우저만으로도 제출할 수 있습니다.**

### 처음 한 번만 수행

1. GitHub 로그인
2. `New repository` 선택
3. 저장소 이름 입력

```text
llm-data-analysis-study
```

4. 가능하면 Public 선택
5. README 생성 여부는 자유
6. 저장소 생성

> 회사/기관 데이터 또는 비공개 자료를 사용하는 경우에는 Public 저장소를 사용하면 안 됩니다. 이 수업에서는 공개 가능한 가상 데이터와 학습 결과만 제출합니다.

---

## 11. Git을 아직 배우지 않은 학생의 업로드 방법

Chapter 01에서는 GitHub 웹에서 업로드해도 됩니다.

1. 개인 저장소 열기
2. `Add file`
3. `Upload files`
4. `chapter01/` 결과 파일과 이미지 업로드
5. Commit message 작성
6. Commit

Chapter 02에서 Git 환경을 학습한 이후에는 로컬 Git을 이용해 commit/push하는 방식을 권장합니다.

---

## 12. Git 사용이 가능한 학생

예:

```powershell
git add .
git commit -m "docs: complete chapter01 practice"
git push
```

각 Chapter에서는 현재 수업 범위에 맞는 Git 절차를 사용합니다.

---

## 13. 제출 URL 규칙

**저장소 루트 URL을 제출하지 않습니다.**

잘못된 예:

```text
https://github.com/student-id/llm-data-analysis-study
```

올바른 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter01/chapter01.md
```

Notebook이라면:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter03/chapter03.ipynb
```

교수자가 URL을 열었을 때 바로 해당 Chapter의 최종 답안을 확인할 수 있어야 합니다.

---

## 14. 최종 제출 전 공통 체크리스트

- [ ] 강사 Public 저장소의 올바른 템플릿을 사용했습니다.
- [ ] 필수 STEP을 모두 수행했습니다.
- [ ] 핵심 실행 Evidence를 캡처했습니다.
- [ ] 이미지가 제출 파일에서 정상 표시됩니다.
- [ ] 단순 결과 복사가 아니라 결과 관찰을 작성했습니다.
- [ ] 자신의 해석과 판단을 작성했습니다.
- [ ] 업무·분석적 의미를 작성했습니다.
- [ ] 한계와 추가 확인 사항을 작성했습니다.
- [ ] LLM 결과를 그대로 정답으로 사용하지 않았습니다.
- [ ] 개인정보가 없습니다.
- [ ] API Key·Secret·Token이 없습니다.
- [ ] 개인 GitHub 저장소에 최종 파일이 올라가 있습니다.
- [ ] GitHub에서 최종 파일과 이미지가 정상 표시됩니다.
- [ ] 저장소 URL이 아니라 **최종 파일 URL**을 제출합니다.

---

## 15. 평가 관점

수업 운영자는 단순히 코드 실행 여부만 확인하지 않습니다.

다음 항목을 함께 봅니다.

```text
실행 여부
+ 결과 정확성
+ Evidence
+ 결과 해석
+ 사람의 판단
+ 한계 인식
+ 재현 가능성
+ 제출 완성도
```

즉, **실행 결과는 답안의 시작이지 끝이 아닙니다.**
