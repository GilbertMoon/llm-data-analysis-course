# Chapter 05 실습 시작 안내

Chapter 05는 다음 세 문서를 함께 사용합니다.

1. 실행 가이드: `chapter05.md`
2. 답안 템플릿: `templates/chapter05_assignment.md`
3. 공통 제출 기준: `../SUBMISSION_GUIDE.md`

기존 `chapter05.md`의 결측·중복·타입·범주 표준화·이상값 후보·PK/FK·파생 컬럼·재실행 검증 절차는 그대로 진행합니다.

최종 제출은 실행 완료 Notebook을 사용합니다.

```text
공식 notebooks/ch05_data_preprocessing.ipynb 복사
→ 처리 전/후 Evidence 남기기
→ 각 처리 기준의 이유와 정보 손실 가능성 해석
→ scripts/preprocess_data.py 재실행 확인
→ 개인 GitHub chapter05/chapter05.ipynb 업로드
→ 최종 Notebook 파일 URL 제출
```

전처리에서 값이 사라졌다는 사실만 기록하지 않고, **왜 그 규칙을 선택했는지, 어떤 정보가 손실될 수 있는지, 다음 EDA에서 무엇을 주의할지** 자신의 말로 작성합니다.