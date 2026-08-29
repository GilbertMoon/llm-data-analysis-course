# 실습 공통 제출 가이드

이 문서는 `llm-data-analysis-course`의 Chapter 01~15 실습에 공통으로 적용하는 **답안 작성·실행 Evidence·GitHub 제출 기준**입니다.

> **우선 적용 규칙**  
> 기존 Chapter 실습 문서에 과거의 `개인 메모`, `화면 제출 권장`, `별도 제출 형식 없음` 같은 표현이 남아 있더라도, **제출 방식과 답안 형식에 대해서는 이 문서와 `practice/CHAPTER_SUBMISSION_MATRIX.md`, 각 Chapter의 `templates/` 파일을 우선 적용합니다.**  
> 기존 Chapter 문서의 실행 절차·코드·성공 기준은 그대로 활용합니다.

수업에서 가장 중요한 것은 코드를 작성했다는 사실만 보여주는 것이 아닙니다.

```text
무엇을 실행했는가
→ 어떤 결과가 나왔는가
→ 그 결과를 어떻게 관찰했는가
→ 내가 어떻게 해석하고 판단했는가
→ 업무·분석적으로 어떤 의미가 있는가
→ 무엇을 아직 확신할 수 없는가
```

를 제출 파일에서 확인할 수 있어야 합니다.

---

## 1. 전체 제출 흐름

```text
강사 Public 저장소의 실습 가이드와 템플릿 확인
→ Markdown 또는 Notebook 템플릿 다운로드/복사
→ 로컬에서 STEP별 실습 진행
→ 핵심 실행 결과 화면 캡처
→ 제출 파일에 코드/Prompt/결과 정리
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub Public 저장소에 업로드
→ GitHub에서 최종 파일과 이미지 정상 표시 확인
→ 저장소 URL이 아닌 해당 Chapter 최종 파일 URL 제출
```

---

## 2. 반드시 함께 볼 문서

```text
practice/SUBMISSION_GUIDE.md
practice/CHAPTER_SUBMISSION_MATRIX.md
practice/chapterNN/chapterNN.md
practice/chapterNN/templates/chapterNN_assignment.md
```

- `SUBMISSION_GUIDE.md`: 전 Chapter 공통 제출 규칙
- `CHAPTER_SUBMISSION_MATRIX.md`: Chapter별 주 제출 파일과 핵심 Evidence
- `chapterNN.md`: 실제 실습 진행 순서
- `templates/chapterNN_assignment.md`: 학생이 작성해야 할 해석·판단 항목

---

## 3. 강사 저장소와 학생 저장소의 역할

### 강사 Public 저장소

```text
https://github.com/GilbertMoon/llm-data-analysis-course
```

강사 저장소에는 다음이 있습니다.

- 실습 가이드
- 답안 작성 템플릿
- 공식 Notebook
- 샘플 데이터
- 공개 이미지
- 실행 스크립트
- 예제 Prompt
- 자동화 예제

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
│  ├─ chapter02.md
│  └─ images/
├─ chapter03/
│  ├─ chapter03.ipynb
│  └─ images/
...
└─ chapter15/
   ├─ chapter15.ipynb
   └─ images/
```

Chapter 01~02는 Markdown 제출을 기본으로 하고, Chapter 03~15는 실행 완료 Notebook을 주 제출물로 사용합니다.

---

## 4. 제출 파일에 반드시 들어갈 6가지

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
무엇을 했는지 다른 사람이 재현할 수 있어야 합니다.

### ② 실행 결과 또는 화면 캡처
실제로 수행했다는 Evidence를 남깁니다.

### ③ 결과 관찰
데이터와 출력에서 직접 확인한 사실만 먼저 적습니다.

```text
예: 6월 completed 주문 기준 금액이 5월보다 낮았다.
```

### ④ 나의 해석과 판단
관찰된 사실을 바탕으로 학생이 내린 판단을 적습니다.

```text
예: 주문 건수 감소인지 주문당 평균 금액 감소인지 추가 확인이 필요하다고 판단했다.
```

### ⑤ 업무·분석적 의미
이 결과가 실제 의사결정이나 다음 분석에 어떤 의미가 있는지 작성합니다.

### ⑥ 한계와 추가 확인 사항
현재 데이터만으로 단정할 수 없는 것과 다음 검증 항목을 작성합니다.

```text
예: 금액 감소만으로 고객 이탈이 원인이라고 결론 내릴 수 없다.
```

---

## 5. 관찰·해석·가설을 구분합니다

좋지 않은 예:

```text
그래프가 내려갔고 마케팅이 실패한 것 같습니다.
```

더 좋은 예:

```text
관찰: 6월 completed 주문 기준 금액이 5월보다 낮았다.
해석: 주문 수 또는 주문당 평균 금액의 변화 여부를 분리해서 확인할 필요가 있다.
가설: 특정 카테고리 감소가 전체 변화에 영향을 주었을 가능성이 있다.
추가 검증: 월별·카테고리별 주문 수와 평균 금액을 함께 비교한다.
한계: 현재 데이터만으로 마케팅 효과를 원인이라고 판단할 수 없다.
```

---

## 6. 화면 캡처 규칙

모든 클릭과 명령을 캡처하지 않습니다. **학습 목표를 달성했다는 것을 보여주는 핵심 Evidence**를 남깁니다.

캡처 가치가 높은 예:

- Notebook 핵심 실행 결과
- DataFrame/집계 결과
- 그래프
- LLM Prompt와 주요 응답
- merge/총합/Validation 결과
- 오류 해결 전·후 핵심 화면
- Docker/Airflow DAG·Task 상태
- Chapter 15 Submission Status

캡처 가치가 낮은 예:

- 단순 `cd`
- 파일을 열기만 한 화면
- 코드 입력 중간 화면
- 의미 없는 긴 콘솔 로그

Chapter별 별도 지시가 없다면 **핵심 Evidence 4~8장 정도**를 권장합니다.

이미지 파일은 의미 있는 이름을 사용합니다.

```text
images/step01_environment.png
images/step03_merge_validation.png
images/graph01_monthly.png
images/step07_airflow_validation.png
```

GitHub에서 제출 파일을 열었을 때 이미지가 정상 표시되는지 확인합니다.

---

## 7. Notebook 제출 규칙 — Chapter 03~15

공식 Notebook을 복사하여 개인 저장소의 해당 Chapter 파일로 사용합니다.

예:

```text
notebooks/ch09_regression_analysis.ipynb
→ 개인 저장소 chapter09/chapter09.ipynb
```

Notebook 제출 시:

- 실행한 핵심 Code Cell의 Output을 남깁니다.
- 오류 Cell을 그대로 남겨 제출하지 않습니다.
- 핵심 분석 구간마다 Markdown Cell로 해석을 작성합니다.
- 그래프 아래에 관찰·해석·업무 의미·한계를 작성합니다.
- LLM/터미널/Airflow처럼 Notebook 밖 결과만 별도 `images/`로 첨부합니다.

권장 Markdown Cell 구조:

```markdown
### 결과 관찰
실행 결과에서 직접 확인한 사실

### 나의 해석과 판단
그 사실을 바탕으로 내린 분석적 판단

### 업무·분석적 의미
실제 업무나 다음 분석에서의 의미

### 한계와 추가 확인 사항
현재 결과만으로 단정할 수 없는 것과 추가 검증
```

---

## 8. Markdown 제출 규칙 — Chapter 01~02

Chapter 01과 02는 문서 작성·환경 Evidence의 비중이 높으므로 Markdown 제출을 기본으로 합니다.

```text
chapter01/chapter01.md
chapter02/chapter02.md
```

각 Chapter의 `templates/chapterNN_assignment.md`를 복사하여 사용합니다.

---

## 9. 개인정보·Secret 보안

제출 파일과 화면 캡처에 다음이 포함되면 안 됩니다.

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

Secret을 이미 Public GitHub에 올렸다면 문자열만 지우고 끝내지 않습니다.

```text
키 폐기 또는 재발급
→ 노출 파일 수정/삭제
→ Git 기록 노출 여부 확인
→ 새 키는 .env 또는 승인된 Secret 방식으로 관리
```

---

## 10. GitHub 업로드 방식

Chapter 01은 Git 학습 전이므로 GitHub 웹의 `Add file → Upload files`를 사용해도 됩니다.

Chapter 02에서 Git 환경을 학습한 이후에는 로컬 commit/push 방식을 권장합니다.

예:

```powershell
git add .
git commit -m "docs: complete chapter02 practice"
git push
```

학생 개인 저장소에는 **자신의 답안과 Evidence만** 올립니다. 강사 저장소 전체를 과제 저장소처럼 복제할 필요는 없습니다.

---

## 11. 제출 URL 규칙

**저장소 루트 URL을 제출하지 않습니다.**

잘못된 예:

```text
https://github.com/student-id/llm-data-analysis-study
```

올바른 Markdown 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter02/chapter02.md
```

올바른 Notebook 예:

```text
https://github.com/student-id/llm-data-analysis-study/blob/main/chapter09/chapter09.ipynb
```

교수자가 URL을 열었을 때 바로 해당 Chapter의 최종 답안을 확인할 수 있어야 합니다.

---

## 12. 최종 제출 전 공통 체크리스트

- [ ] 올바른 Chapter 실습 가이드와 템플릿을 사용했습니다.
- [ ] 필수 STEP을 모두 수행했습니다.
- [ ] 핵심 실행 Evidence가 있습니다.
- [ ] 이미지가 GitHub에서 정상 표시됩니다.
- [ ] 단순 결과 복사가 아니라 결과 관찰을 작성했습니다.
- [ ] 자신의 해석과 판단을 작성했습니다.
- [ ] 업무·분석적 의미를 작성했습니다.
- [ ] 한계와 추가 확인 사항을 작성했습니다.
- [ ] LLM 결과를 그대로 정답으로 사용하지 않았습니다.
- [ ] 개인정보가 없습니다.
- [ ] API Key·Secret·Token이 없습니다.
- [ ] 오류 Cell/미해결 필수 FAIL을 숨기지 않았습니다.
- [ ] 개인 GitHub 저장소에 최종 파일이 올라가 있습니다.
- [ ] 저장소 URL이 아니라 **최종 파일 URL**을 제출합니다.

---

## 13. 평가 관점

```text
실행 여부
+ 결과 정확성
+ Evidence
+ 결과 관찰
+ 학생의 해석과 판단
+ 업무·분석적 의미
+ 한계 인식
+ 재현 가능성
+ 보안 준수
+ GitHub 제출 완성도
```

즉, **실행 결과는 답안의 시작이지 끝이 아닙니다.**