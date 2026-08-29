# 13장 실습. 외부 데이터로 분석을 확장하기

> 목표는 외부 데이터를 많이 모으는 것이 아니라 **분석 질문에 필요한 공식 출처를 선택하고, 이용조건·기준일·수집 범위를 확인한 뒤 원본과 메타데이터를 보존하고 안전하게 병합·해석하는 것**입니다.

## 공통 제출 기준
- 공통 가이드: `practice/SUBMISSION_GUIDE.md`
- Chapter별 형식: `practice/CHAPTER_SUBMISSION_MATRIX.md`
- 답안 양식: `practice/chapter13/templates/chapter13_assignment.md`
- 주 제출물: `chapter13/chapter13.ipynb`

공식 Notebook:

```text
notebooks/ch13_external_data_collection.ipynb
```

보조 스크립트:

```text
scripts/run_external_data_collection.py
```

## STEP 0. 제출용 Notebook 준비
공식 Notebook을 복사해 `chapter13/chapter13.ipynb`로 사용합니다. 공식 사이트·API 응답·수집 승인 화면 등 Notebook 밖 Evidence는 `chapter13/images/`에 저장합니다.

## STEP 1. 외부 데이터가 필요한 질문 정의
먼저 내부 데이터만으로 부족한 정보를 한 문장으로 설명합니다.

```text
현재 질문:
내부 데이터로 알 수 있는 것:
부족한 정보:
외부 데이터가 추가되면 확인할 수 있는 것:
```

외부 데이터가 없어도 답할 수 있다면 불필요한 수집을 하지 않습니다.

## STEP 2. 공식 출처와 이용조건 확인
가능한 우선순위:

```text
공식 다운로드 파일
→ 공식 API
→ 필요한 경우에만 제한적인 공개 HTML 수집
```

답안에 기록할 것:
- provider/기관명
- 공식 source URL
- 데이터 기준일(`data_reference_date`)
- 내가 확인/수집한 시각(`collected_at`)
- 이용조건/라이선스/정책
- 요청 범위
- 개인정보 포함 여부

```text
수집할 수 있다 ≠ 수집해도 된다
```

## STEP 3. RUN Gate와 Secret 확인
네트워크 요청 전 다음을 확인합니다.

- [ ] 공식 출처 확인
- [ ] 이용조건 확인
- [ ] 최소 요청 범위
- [ ] timeout 설정
- [ ] 불필요한 반복 요청 없음
- [ ] API Key는 `.env`/환경변수 사용
- [ ] Notebook/로그/캡처에 Secret 없음
- [ ] 사람이 실제 요청 실행을 승인함

## STEP 4. Raw Snapshot과 Metadata 보존
수집 결과를 바로 가공본으로 덮어쓰지 않습니다.

가능한 구조:

```text
data/external/raw/        원본 snapshot
data/external/processed/  분석용 가공본
metadata                  출처·기준일·수집시각·조건·hash 등
```

시간이 지나 응답이 바뀔 수 있으므로 timestamped snapshot 또는 추적 가능한 파일명을 사용합니다.

## STEP 5. 응답과 데이터 품질 검증
API/파일 수집 시 최소 다음을 확인합니다.

```text
HTTP/다운로드 성공 여부
JSON/CSV 파싱 가능 여부
업무 상태 코드/에러 메시지
필수 컬럼
행 수
키 중복/결측
날짜 범위
페이지네이션 누락 여부
데이터 기준일
```

응답이 왔다는 사실만으로 데이터가 완전하다고 판단하지 않습니다.

## STEP 6. Processed 데이터 만들기
분석에 필요한 컬럼과 형식만 정리합니다.

Raw를 보존하고 processed만 변환합니다.

답안에는:
- 어떤 컬럼을 선택/변환했는지
- 왜 그렇게 가공했는지
- 변환 과정에서 손실 가능성이 있는지
를 작성합니다.

## STEP 7. 내부 데이터와 안전하게 병합
내부 데이터와 외부 데이터의 key와 시간 단위를 확인합니다.

예:

```text
내부 날짜 단위: 일/월
외부 날짜 단위: 일/월
timezone:
중복 key:
미매칭 내부 행:
미매칭 외부 행:
```

**미매칭 날짜를 자동으로 ‘정상일/비공휴일/0’로 간주하지 않습니다.**

## STEP 8. 외부 데이터가 준 추가 맥락 해석
병합 후 결과에 대해 다음을 구분합니다.

```text
관찰: 같이 움직이거나 차이가 보인 사실
해석: 가능한 설명
한계: 대표성·수집 시점·누락·선택 편향
인과: 현재 데이터만으로 증명할 수 있는가?
```

상관관계나 동시 변화만으로 외부 요인이 원인이라고 단정하지 않습니다.

## STEP 9. 재현 실행 확인
가능하면 실행합니다.

```powershell
python scripts/run_external_data_collection.py
```

실시간 서비스가 변할 수 있으므로 다음을 확인합니다.
- 원본 snapshot 재사용 가능 여부
- metadata가 남는지
- 실패 시 안전하게 멈추는지
- 재실행이 원본을 무조건 덮어쓰지 않는지

## STEP 10. 최종 판단
답안에 다음을 작성합니다.

1. 왜 이 외부 데이터를 선택했는가
2. 출처와 기준일을 얼마나 신뢰할 수 있는가
3. 수집·가공·병합에서 가장 큰 위험은 무엇인가
4. 외부 데이터가 내부 분석에 실제로 추가한 맥락
5. 현재 결과만으로 원인이라고 말할 수 없는 것
6. 다음에 다시 수집할 때 확인해야 할 정책/데이터 변경 가능성

## 최종 제출

```text
chapter13/
├─ chapter13.ipynb
└─ images/
```

제출 URL:

```text
https://github.com/<ID>/llm-data-analysis-study/blob/main/chapter13/chapter13.ipynb
```

## 완료 체크
- [ ] 외부 데이터 필요성 설명
- [ ] 공식 출처 우선 확인
- [ ] 이용조건/라이선스/기준일 기록
- [ ] RUN Gate와 Secret 보호
- [ ] Raw Snapshot 보존
- [ ] Metadata 기록
- [ ] 품질/페이지네이션/날짜 검증
- [ ] 안전한 merge와 미매칭 확인
- [ ] 대표성/인과 해석 한계 작성
- [ ] 최종 Notebook URL 제출