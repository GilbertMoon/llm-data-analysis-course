# Chapter 04 실습 시작 안내

Chapter 04는 다음 세 문서를 함께 사용합니다.

1. 실행 가이드: `chapter04.md`
2. 답안 템플릿: `templates/chapter04_assignment.md`
3. 공통 제출 기준: `../SUBMISSION_GUIDE.md`

기존 `chapter04.md`의 선택·필터·정렬·파생 컬럼·merge·groupby·총합 검증 절차는 그대로 진행합니다.

최종 제출은 실행 완료 Notebook을 사용합니다.

```text
공식 notebooks/ch04_pandas_basic.ipynb 복사
→ 핵심 셀 실행
→ merge/집계/총합 Evidence 확인
→ Markdown 셀에 관찰·해석·판단·업무 의미·한계 작성
→ 개인 GitHub chapter04/chapter04.ipynb 업로드
→ 최종 Notebook 파일 URL 제출
```

특히 `merge()`가 실행되었다는 사실만으로 안전하다고 판단하지 않고, 행 수·`validate`·`indicator`·총합을 함께 검증한 근거를 답안에 남깁니다.