# 학생 실습 진행 안내

이 폴더는 Overview부터 Chapter 15까지의 **실습 진행 가이드·답안 템플릿·제출 기준**을 모아 둔 곳입니다.

## 먼저 읽을 문서

1. `SUBMISSION_GUIDE.md` — 공통 제출·Evidence·GitHub URL 규칙
2. `CHAPTER_SUBMISSION_MATRIX.md` — 장별 제출 파일 형식과 핵심 해석 기준
3. 해당 Chapter의 `chapterNN.md` — 실제 실행 순서
4. 해당 Chapter의 `templates/chapterNN_assignment.md` — 답안 작성 양식

> 제출 방식과 답안 형식에 대해서는 공통 제출 가이드와 템플릿을 우선합니다. Chapter 02~05의 기존 실습 가이드에 과거 산출물 표현이 남아 있어도 실행 절차는 그대로 따르고, 최종 제출은 새 기준을 적용합니다.

## 전체 제출 흐름

```text
공식 가이드/템플릿 확인
→ 로컬 실습
→ 핵심 실행 Evidence
→ 결과 관찰
→ 나의 해석과 판단
→ 업무·분석적 의미
→ 한계와 추가 확인
→ 개인 GitHub 업로드
→ 최종 파일 URL 제출
```

## Chapter별 바로가기 구조

| Chapter | 실습 가이드 | 답안 템플릿 | 주 제출물 |
| ---: | --- | --- | --- |
| 01 | `chapter01/chapter01.md` | `chapter01/templates/chapter01_assignment.md` | `chapter01.md` |
| 02 | `chapter02/chapter02.md` | `chapter02/templates/chapter02_assignment.md` | `chapter02.md` |
| 03 | `chapter03/chapter03.md` | `chapter03/templates/chapter03_assignment.md` | `chapter03.ipynb` |
| 04 | `chapter04/chapter04.md` | `chapter04/templates/chapter04_assignment.md` | `chapter04.ipynb` |
| 05 | `chapter05/chapter05.md` | `chapter05/templates/chapter05_assignment.md` | `chapter05.ipynb` |
| 06 | `chapter06/chapter06.md` | `chapter06/templates/chapter06_assignment.md` | `chapter06.ipynb` |
| 07 | `chapter07/chapter07.md` | `chapter07/templates/chapter07_assignment.md` | `chapter07.ipynb` |
| 08 | `chapter08/chapter08.md` | `chapter08/templates/chapter08_assignment.md` | `chapter08.ipynb` |
| 09 | `chapter09/chapter09.md` | `chapter09/templates/chapter09_assignment.md` | `chapter09.ipynb` |
| 10 | `chapter10/chapter10.md` | `chapter10/templates/chapter10_assignment.md` | `chapter10.ipynb` |
| 11 | `chapter11/chapter11.md` | `chapter11/templates/chapter11_assignment.md` | `chapter11.ipynb` |
| 12 | `chapter12/chapter12.md` | `chapter12/templates/chapter12_assignment.md` | `chapter12.ipynb` |
| 13 | `chapter13/chapter13.md` | `chapter13/templates/chapter13_assignment.md` | `chapter13.ipynb` |
| 14 | `chapter14/chapter14.md` | `chapter14/templates/chapter14_assignment.md` | `chapter14.ipynb` |
| 15 | `chapter15/chapter15.md` | `chapter15/templates/chapter15_assignment.md` | `chapter15.ipynb` |

## 개인 저장소 구조

```text
llm-data-analysis-study/
├─ chapter01/chapter01.md
├─ chapter02/chapter02.md
├─ chapter03/chapter03.ipynb
...
└─ chapter15/chapter15.ipynb
```

필요한 Chapter에는 `images/` 폴더를 두어 Notebook 밖의 터미널·LLM·Airflow Evidence를 저장합니다.

## 제출 URL

저장소 루트가 아니라 **최종 파일 URL**을 제출합니다.

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter02/chapter02.md
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter15/chapter15.ipynb
```

## 최종 원칙

```text
실행 성공 ≠ 분석 성공
LLM 답변 ≠ 검증된 정답
Task 성공 ≠ 결과 Validation 성공
파일 존재 ≠ 최신·정상 결과
```

학생의 제출물에는 항상 **근거에 기반한 관찰·해석·판단·한계**가 함께 있어야 합니다.