# Word 강의안 생성 및 통합 가이드

이 가이드는 `book/chapters/`의 0~15장 Markdown 강의안을 공통 Word 템플릿으로 변환하고, 챕터별 수동 검수가 끝난 파일만 하나의 통합 DOCX로 합치는 절차를 설명합니다.

## 1. 파일 구성

```text
templates/
└── llm_data_analysis_reference.docx     # 공통 Word 스타일 템플릿

scripts/
├── build_chapter_docx.py                # Markdown → 챕터별 DOCX
└── merge_chapter_docx.py                # 승인된 챕터 DOCX → 통합 DOCX

requirements-docx.txt                    # Word 생성 전용 Python 패키지

book/output/docx/
├── chapters/                            # 챕터별 DOCX 생성 위치
├── chapter_review_status.csv            # 수동 검수 상태와 파일 해시
└── llm_data_analysis_course_full.docx   # 최종 통합 DOCX
```

`book/output/docx/` 아래의 생성 결과는 Git으로 관리하지 않습니다. 원본 Markdown, 템플릿, 스크립트와 가이드만 저장소에서 관리합니다.

## 2. 필요한 프로그램

- Python 3.10 이상
- Pandoc
- Microsoft Word 또는 LibreOffice

### Windows에서 Pandoc 설치

PowerShell에서 다음 명령을 실행합니다.

```powershell
winget install --id JohnMacFarlane.Pandoc --exact
```

설치 후 PowerShell 또는 VS Code 터미널을 다시 열고 확인합니다.

```powershell
pandoc --version
```

### Python 패키지 설치

프로젝트 루트에서 가상환경을 활성화한 뒤 설치합니다.

```powershell
python -m pip install -r requirements-docx.txt
```

`CairoSVG` 설치가 어려운 환경에서는 해당 줄을 제외하고 설치한 뒤 `--svg-mode keep`을 사용할 수 있습니다. 다만 Word에서 SVG가 정상 표시되는지 반드시 확인해야 합니다.

## 3. 챕터별 Word 생성

### 실행 계획만 확인

```powershell
python scripts/build_chapter_docx.py --dry-run
```

### 0~15장 전체 생성

```powershell
python scripts/build_chapter_docx.py
```

기본적으로 다음 공통 템플릿이 자동 적용됩니다.

```text
templates/llm_data_analysis_reference.docx
```

생성 위치:

```text
book/output/docx/chapters/
```

### 특정 챕터만 다시 생성

```powershell
python scripts/build_chapter_docx.py --chapters 4
python scripts/build_chapter_docx.py --chapters 4 5 6
```

챕터를 다시 생성하면 해당 챕터의 검수 상태가 `pending`으로 초기화됩니다. 이전에 승인한 파일을 다시 생성한 경우 반드시 다시 검수해야 합니다.

### SVG 처리 방식

```powershell
# 기본값: Inkscape, rsvg-convert 또는 CairoSVG를 찾으면 PNG로 변환
# 변환기가 없으면 원본 SVG를 Pandoc에 전달하고 경고 표시
python scripts/build_chapter_docx.py --svg-mode auto

# SVG를 반드시 PNG로 변환. 변환기가 없으면 오류
python scripts/build_chapter_docx.py --svg-mode png

# SVG를 그대로 Word에 전달
python scripts/build_chapter_docx.py --svg-mode keep
```

Word 버전이나 렌더러에 따라 SVG 표시 결과가 달라질 수 있으므로, 안정적인 출판 결과가 필요하면 `png` 또는 `auto`를 권장합니다. 한글이 들어간 SVG를 PNG로 변환한 뒤에는 글꼴이 깨지거나 대체되지 않았는지 Word에서 확인합니다.

## 4. 챕터별 수동 검수

생성이 끝나면 다음 파일이 함께 만들어집니다.

```text
book/output/docx/chapter_review_status.csv
```

각 챕터 DOCX를 Word에서 열고 다음 항목을 확인합니다.

- 제목과 소제목의 단계 및 글꼴
- 본문 줄 간격과 문단 간격
- 표가 페이지 밖으로 넘어가지 않는지
- 코드 블록 줄바꿈과 들여쓰기
- 이미지 누락, 잘림, 해상도 문제
- 그림 캡션 위치
- 한글과 영문 글꼴 깨짐
- 페이지 나누기와 빈 페이지
- 링크와 특수문자 표시

검수를 통과한 챕터만 CSV의 `status`를 다음과 같이 변경합니다.

```text
pending → approved
```

선택 사항으로 `reviewed_by`, `reviewed_at`, `notes`도 작성합니다.

예를 들어 Chapter 0 행에서는 기존 `source`, `output`, `source_sha256`, `docx_sha256` 값을 그대로 둔 상태에서 다음 열만 수정합니다.

| 열 | 입력 예시 |
| --- | --- |
| `status` | `approved` |
| `reviewed_by` | `문길래` |
| `reviewed_at` | `2026-07-11` |
| `notes` | `표와 이미지 확인 완료` |

`docx_sha256` 값은 수정하지 않습니다. 통합 스크립트는 승인 당시 기록된 해시와 실제 Word 파일의 해시가 같은지 검사합니다. 승인 후 Word 파일을 직접 수정했다면 해시가 달라지므로, 다시 빌드하거나 검수 상태 파일을 재생성한 뒤 재검수해야 합니다.

## 5. 검수 완료 여부 점검

통합 파일을 만들기 전에 실행 계획과 승인 상태를 확인합니다.

```powershell
python scripts/merge_chapter_docx.py --dry-run
```

다음 상황에서는 통합이 중단됩니다.

- 챕터 DOCX가 없음
- 검수 상태가 `approved`가 아님
- 검수 후 DOCX 파일이 변경됨
- DOCX 파일이 손상됨

## 6. 통합 Word 생성

모든 챕터가 승인된 후 실행합니다.

```powershell
python scripts/merge_chapter_docx.py
```

기본 출력:

```text
book/output/docx/llm_data_analysis_course_full.docx
```

통합 문서에는 다음 요소가 포함됩니다.

- 표지
- Word 목차 필드
- 챕터 0~15 순서
- 챕터 사이 페이지 나누기
- 공통 템플릿의 제목, 본문, 표, 코드 스타일
- 머리글과 페이지 번호

### 일부 챕터만 통합

```powershell
python scripts/merge_chapter_docx.py --chapters 0 1 2 3
```

### 표지 또는 목차 제외

```powershell
python scripts/merge_chapter_docx.py --no-cover
python scripts/merge_chapter_docx.py --no-toc
```

### 챕터 사이 페이지 나누기 제외

```powershell
python scripts/merge_chapter_docx.py --no-page-breaks
```

`--force`는 승인 또는 해시 검사를 무시하는 진단용 옵션입니다. 최종 출판 파일 생성에는 사용하지 않는 것을 권장합니다.

## 7. 통합 Word 최종 검수

통합 DOCX를 Microsoft Word에서 연 뒤 다음 순서로 확인합니다.

1. `Ctrl+A`로 문서 전체를 선택합니다.
2. `F9`를 눌러 목차와 필드를 업데이트합니다.
3. 목차의 페이지 번호와 제목이 올바른지 확인합니다.
4. 챕터 시작 위치와 빈 페이지를 확인합니다.
5. 표와 이미지가 통합 과정에서 이동하지 않았는지 확인합니다.
6. 머리글, 바닥글, 페이지 번호를 확인합니다.
7. PDF로 저장한 뒤 전체 페이지를 다시 확인합니다.

Word에서 필드 업데이트 확인 창이 표시되면 `전체 표 업데이트`를 선택합니다.

## 8. 공통 템플릿 수정

공통 스타일을 변경하려면 다음 파일을 Word에서 수정합니다.

```text
templates/llm_data_analysis_reference.docx
```

권장 수정 대상:

- `Normal`: 본문 글꼴, 크기, 줄 간격
- `Title`, `Subtitle`: 표지 제목
- `Heading 1`~`Heading 4`: 장과 절 제목
- `Source Code`: 코드 블록
- `Verbatim Char`: 인라인 코드
- `Caption`: 그림 및 표 캡션
- `Table`, `Table Grid`: 표 스타일
- 머리글과 바닥글
- A4 여백

템플릿을 수정한 뒤에는 챕터별 Word를 다시 생성하고 전체를 다시 검수해야 합니다.

## 9. 권장 전체 실행 순서

```powershell
# 1. 전용 패키지 설치
python -m pip install -r requirements-docx.txt

# 2. 변환 대상 확인
python scripts/build_chapter_docx.py --dry-run

# 3. 챕터별 Word 생성
python scripts/build_chapter_docx.py

# 4. Word에서 16개 파일 수동 검수
# book/output/docx/chapter_review_status.csv에서 통과한 챕터를 approved로 변경

# 5. 통합 가능 여부 확인
python scripts/merge_chapter_docx.py --dry-run

# 6. 통합 Word 생성
python scripts/merge_chapter_docx.py

# 7. 통합 Word에서 Ctrl+A → F9 후 전체 문서 최종 검수
```

## 10. 자주 발생하는 문제

### `pandoc was not found`

Pandoc을 설치한 후 터미널을 완전히 종료하고 다시 엽니다.

### 이미지가 표시되지 않음

원본 Markdown의 이미지 상대 경로와 실제 파일 위치를 확인합니다. SVG 문제라면 다음 명령으로 다시 생성합니다.

```powershell
python scripts/build_chapter_docx.py --svg-mode png
```

### `docxcompose is not installed`

```powershell
python -m pip install -r requirements-docx.txt
```

### 통합 시 `status is pending`

해당 챕터 Word를 수동 검수한 뒤 `chapter_review_status.csv`의 상태를 `approved`로 변경합니다.

### 통합 시 `DOCX changed after review`

검수 후 Word 파일이 변경된 상태입니다. 해당 챕터를 다시 생성하고 다시 검수합니다.

```powershell
python scripts/build_chapter_docx.py --chapters 8
```
