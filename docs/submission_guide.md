# 제출 가이드

> 이 문서는 과거 제출 안내 경로와의 호환을 위해 유지합니다.  
> **현재 수업의 공식 제출 기준은 `practice/SUBMISSION_GUIDE.md`와 `practice/CHAPTER_SUBMISSION_MATRIX.md`입니다.**

## 현재 공식 제출 기준

반드시 다음 문서를 우선 사용하세요.

```text
practice/README.md
practice/SUBMISSION_GUIDE.md
practice/CHAPTER_SUBMISSION_MATRIX.md
practice/chapterNN/chapterNN.md
practice/chapterNN/templates/chapterNN_assignment.md
```

## 핵심 제출 흐름

```text
강사 Public 저장소의 가이드/템플릿 확인
→ 로컬에서 STEP별 실습
→ 핵심 실행 Evidence 남기기
→ 결과 관찰 작성
→ 나의 해석과 판단 작성
→ 업무·분석적 의미 작성
→ 한계와 추가 확인 사항 작성
→ 개인 GitHub Public 저장소에 업로드
→ GitHub에서 최종 파일 정상 표시 확인
→ 저장소 URL이 아닌 해당 Chapter 최종 파일 URL 제출
```

## 제출 파일 형식

```text
Chapter 01~02 → Markdown
Chapter 03~15 → 실행 완료 Jupyter Notebook
```

Chapter별 정확한 제출 파일은 `practice/CHAPTER_SUBMISSION_MATRIX.md`를 확인합니다.

## 개인 GitHub 저장소

권장 저장소 이름:

```text
llm-data-analysis-study
```

예:

```text
llm-data-analysis-study/
├─ chapter01/chapter01.md
├─ chapter02/chapter02.md
├─ chapter03/chapter03.ipynb
...
└─ chapter15/chapter15.ipynb
```

## 제출 URL

저장소 루트 URL이나 Pull Request URL이 아니라 **최종 답안 파일 URL**을 제출합니다.

Markdown 예:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter02/chapter02.md
```

Notebook 예:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter10/chapter10.ipynb
```

## 답안에 필요한 핵심 내용

단순 코드와 실행 화면만으로 제출을 완료하지 않습니다.

핵심 STEP에는 가능한 한 다음을 포함합니다.

```text
① 실행 코드 / Prompt / 수행 내용
② 실행 결과 또는 화면 캡처
③ 결과 관찰
④ 나의 해석과 판단
⑤ 업무·분석적 의미
⑥ 한계와 추가 확인 사항
```

## 보안

다음 정보는 LLM Prompt, Notebook Output, Markdown, 화면 캡처, Public GitHub에 올리지 않습니다.

```text
실제 API Key
Client Secret
Access Token
Password
실제 개인정보
회사 내부 URL
비공개 업무자료
.env 실제 값
GitHub Personal Access Token
```

---

이 문서의 과거 제출 안내보다 **`practice/SUBMISSION_GUIDE.md`의 최신 기준을 우선합니다.**