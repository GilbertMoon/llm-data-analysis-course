# ch13 강의안 검토 리포트

> **대상 독자**: 파이썬 기초 경험이 있는 비전공자, 데이터 분석 기본 개념 보유 학생  
> **검토 기준**: 한 학기 강의 교재로서 독립적 학습 가능 여부  
> **작성일**: 2026-06-19  
> **검토 파일**: `book/chapters/ch13_make_automation.md`

---

## 검토 지침 (Codex Prompt Format)

아래 각 항목은 `[섹션명]` 위치를 기준으로 문제를 설명하고, 구체적인 수정/보완 방향을 제시합니다.  
**[필수 수정]** = 학습에 직접적 혼란을 야기하는 항목  
**[보완 권장]** = 추가 시 학습 효과가 크게 향상되는 항목

---

## 1. 필수 수정 항목

---

### [1-1] 수업 시간 합계와 본문 불일치 — [수업 시간 구성 표]

**문제**  
수업 시간 구성 표 합계 (연습 문제 60~90분 제외):  
30+35+35+40+45+45+40+40 = **310분 = 5시간 10분**  
본문: "기본 수업은 약 3시간을 기준으로 구성되어 있습니다"  
2시간 10분 격차. ch01~ch13 전 장 반복 문제.

**수정 지시**  
방법 A: 각 항목 시간을 줄여 합계 180분 이내로 재편성한다.  
방법 B: 본문을 "기본 수업은 약 5시간을 기준으로 구성되어 있습니다"로 수정한다.

---

### [1-2] `to_csv()` 저장에 인코딩 없음 — [섹션 7.2, 7.3, 7.4, 7.5, 7.8]

**문제**  
아래 5회 `to_csv()` 호출 모두 `encoding` 옵션이 없다:
- 섹션 7.2: `ch13_automation_file_check.csv`
- 섹션 7.3: `ch13_make_scenario_plan.csv`
- 섹션 7.4: `ch13_make_execution_log_template.csv`
- 섹션 7.5: `ch13_make_validation_checklist.csv`
- 섹션 7.8: `ch13_make_test_log_example.csv`

한글 컬럼(`check_item`, `action`, `memo` 등)이 포함된 CSV를 Windows에서 Excel로 열면 깨진다. ch04~ch13 전 장 반복 문제.

**수정 지시**  
모든 `to_csv()` 호출에 `encoding="utf-8-sig"` 추가:

```python
automation_file_check.to_csv(
    report_dir / "ch13_automation_file_check.csv",
    index=False, encoding="utf-8-sig"
)
make_scenario_plan.to_csv(
    report_dir / "ch13_make_scenario_plan.csv",
    index=False, encoding="utf-8-sig"
)
execution_log_template.to_csv(
    report_dir / "ch13_make_execution_log_template.csv",
    index=False, encoding="utf-8-sig"
)
make_validation_checklist.to_csv(
    report_dir / "ch13_make_validation_checklist.csv",
    index=False, encoding="utf-8-sig"
)
test_log.to_csv(
    report_dir / "ch13_make_test_log_example.csv",
    index=False, encoding="utf-8-sig"
)
```

---

### [1-3] `base_dir` 자동 감지 패턴이 두 번 중복 정의 — [섹션 5.3, 7.1]

**문제**  
섹션 5.3과 섹션 7.1에서 동일한 `base_dir` 설정 코드 블록이 두 번 나온다:
```python
current_dir = Path.cwd()
if current_dir.name == "notebooks":
    base_dir = current_dir.parent
else:
    base_dir = current_dir
```
하나의 Notebook에서 동일한 초기화 코드가 반복 등장하면 학생이 "어느 셀을 실행해야 하는가?"라고 혼란스럽다.

**수정 지시**  
5.3절의 코드 블록을 7.1절 기본 설정 코드와 통합하거나, 5.3절에서 7.1절을 먼저 실행하도록 안내한다:

```python
# 7.1에서 설정한 base_dir, report_dir, figure_dir 변수를 사용합니다.
# 이 셀을 먼저 실행하지 않았다면 7.1 기본 설정 셀을 먼저 실행하세요.
```

또한 ch06~ch13 모두 `Path.cwd().name == "notebooks"` 패턴 반복 문제로, 파일 존재 기반 감지로 전환한다. (ch06 리뷰 [1-8] 참조)

---

### [1-4] 텍스트 파일 저장 시 `encoding="utf-8"` — BOM 없음 — [섹션 7.6, 7.7]

**문제**  
섹션 7.6과 7.7에서 텍스트/Markdown 파일을 저장할 때:
```python
email_template_path.write_text(email_template, encoding="utf-8")
automation_plan_path.write_text(automation_plan_text, encoding="utf-8")
```
ch12 리뷰 [1-7]과 동일하게 BOM 없는 UTF-8로 저장한다. Windows 메모장이나 일부 도구에서 한글이 깨질 수 있다.

**수정 지시**  
```python
# 수정 전
email_template_path.write_text(email_template, encoding="utf-8")
automation_plan_path.write_text(automation_plan_text, encoding="utf-8")

# 수정 후
email_template_path.write_text(email_template, encoding="utf-8-sig")
automation_plan_path.write_text(automation_plan_text, encoding="utf-8-sig")
```

---

### [1-5] 자동화 설계서 `~~~` 코드 펜스 — [섹션 7.7]

**문제**  
섹션 7.7의 `automation_plan_text` f-string 내부에서 `` ~~~ `` 코드 펜스를 사용한다:
```python
## 4. 이메일 본문 템플릿

~~~text
{email_template}
~~~
```
ch09, ch10에서 반복적으로 지적된 비표준 Markdown 문제다. 일부 Markdown 렌더러에서 코드 블록이 표시되지 않는다.

**수정 지시**  
```python
TRIPLE_TICK = "```"

automation_plan_text = f"""
...
## 4. 이메일 본문 템플릿

{TRIPLE_TICK}text
{email_template}
{TRIPLE_TICK}
...
"""
```

---

### [1-6] ch12 보고서 파일 의존성 — 없을 때 대응 없음 — [섹션 5.3, 7.2]

**문제**  
섹션 5.3과 7.2에서 ch12 산출물 파일들(`ch12_auto_report.md`, 그래프 PNG 3개)의 존재 여부를 `print(file_path.exists())`로 확인하지만, 파일이 없을 때 학생이 어떻게 대응해야 하는지 안내가 없다. `False` 출력이 나와도 계속 진행하면 나중에 Make 설정 시 파일을 찾지 못한다.

**수정 지시**  
```python
missing_files = [f for f in files_to_check if not f.exists()]
if missing_files:
    print("⚠️ 다음 파일이 없습니다:")
    for f in missing_files:
        print(f"   - {f}")
    print()
    print("notebooks/ch12_report_generation.ipynb 을 먼저 실행하세요.")
    print("파일이 모두 준비된 후에 이 장의 Make 설정을 진행하세요.")
else:
    print("✅ 모든 파일이 존재합니다. Make 자동화 설정을 진행할 수 있습니다.")
```

---

## 2. 보완 권장 항목

---

### [2-1] Google Drive 데스크톱 앱 설치 전제 미안내 — [섹션 3.5, 5.1]

**문제**  
섹션 3.5에서 "Python 보고서 저장 경로를 Google Drive 동기화 폴더에 저장"한다고 설명하는데, 이는 Google Drive 데스크톱 앱(구 Backup and Sync / Drive for Desktop)이 설치되어 있어야 가능하다. 설치하지 않고 브라우저로만 사용하는 학생은 이 실습이 불가능하다. 또한 macOS는 `~/Library/CloudStorage/GoogleDrive-*/` 경로, Windows는 `G:/My Drive/` 등 OS마다 다르다.

**보완 지시**  
섹션 5.1 또는 섹션 3.5에 다음 안내를 추가한다:

```markdown
## 사전 준비

이번 장의 Make 실습을 위해서는 다음이 필요합니다:

1. **Google Drive 데스크톱 앱 설치**: [https://drive.google.com/drive/download](https://drive.google.com/drive/download)
   - Windows: 보통 `G:\My Drive\` 또는 `C:\Users\계정명\Google Drive\`
   - macOS: `~/Library/CloudStorage/GoogleDrive-이메일/My Drive/`
   - 로컬 경로는 설치 후 탐색기/Finder에서 확인하세요.

2. **Make 계정 생성**: [https://www.make.com](https://www.make.com)
   - 무료 계정: 월 1,000 operations (실습 충분)
   - 회원가입 후 "Free" 플랜으로 진행 가능

3. Google Drive, Gmail, Google Sheets **연결 권한 허가** 필요
```

---

### [2-2] Make 무료 계정 제한사항 미안내 — [섹션 5.1]

**문제**  
Make 무료 계정은 월 1,000 operations까지만 사용할 수 있다. 학생이 반복 테스트를 여러 번 하다 제한에 걸릴 수 있다. 또한 무료 계정에서는 일부 기능(예: 반복 실행 최소 15분 간격)이 제한된다.

**보완 지시**  
섹션 5.1 도구 표에 다음 메모를 추가한다:

```markdown
⚠️ Make 무료 계정 주의사항:
- 월 1,000 operations 한도 (초과 시 해당 월 자동화 중단)
- 반복 실행 최소 간격: 15분 (유료는 1분까지 가능)
- 실습 테스트는 수동 실행(Run once)으로 진행하면 operations 소비를 줄일 수 있음
```

---

### [2-3] Make 실제 설정 화면 안내 없음 — [섹션 6]

**문제**  
섹션 6에서 Make Scenario 설정을 텍스트와 표로만 설명한다. 비전공자에게 Make UI는 처음 보는 도구이며, "Watch files in a folder", "Add a row" 같은 Make 전용 용어를 표로만 보면 화면에서 어디를 클릭해야 하는지 알 수 없다.

**보완 지시**  
다음 중 하나를 추가한다:
- 섹션 6 앞에 Make 화면 구성 요소 설명 그림(그림 번호)을 추가한다.
- 또는 각 섹션 앞에 "Make에서 이 단계를 설정하는 방법은 [Make 공식 문서](https://www.make.com/en/help)를 참고하세요"를 안내한다.
- automation/ 폴더에 이미 있는 `make_scenario_guide.md`(`automation/make/make_scenario_guide.md`)를 교재에서 링크한다.

---

### [2-4] 실습용 계정 권장 이유 미설명 — [섹션 5.1]

**문제**  
"실제 수업에서는 개인 계정을 사용하기보다 실습용 계정을 사용하는 것이 좋습니다"라고만 안내하고, 왜 그런지 이유를 설명하지 않는다.

**보완 지시**  
다음 설명을 추가한다:

```markdown
**실습용 계정 권장 이유**:
- 개인 Gmail 계정에 자동화 권한을 부여하면 실수로 이메일이 대량 발송될 수 있습니다.
- Google Drive 연결 오류 시 개인 파일에 영향을 줄 수 있습니다.
- 실습용 Google 계정을 별도 생성하면 실수의 영향 범위를 줄일 수 있습니다.
```

---

### [2-5] 연습 문제에 힌트/채점 기준 없음 — [섹션 11]

**문제**  
ch01~ch12와 동일.

**보완 지시**  
심화 과제 평가 기준 예시:

```
평가 기준 (Make 자동화 설계):
- Python과 Make의 역할을 구분해 설명했는가? (20%)
- 자동화 흐름이 단계별로 명확한가? (20%)
- 파일명 필터와 중복 발송 방지 조건이 포함되었는가? (20%)
- 검증 체크리스트를 작성했는가? (20%)
- 오류 처리 방안을 설명했는가? (20%)
```

---

### [2-6] 핵심 용어 정리 섹션 부재 — [전체 구조]

**문제**  
ch01~ch12와 동일. ch13 신규 용어: Scenario, Trigger, Module, Connection, Filter, Router, Error Handler, Webhook, Operations, Google Drive Watch files, 중복 발송 방지.

**보완 지시**  
섹션 12(정리) 이후에 "이 장에서 사용한 주요 용어" 표를 추가한다:

| 용어 | 설명 |
|------|------|
| Scenario | Make에서 자동화 전체 흐름을 부르는 단위 |
| Trigger | 자동화 시작 조건 (파일 생성, 시간, Webhook 등) |
| Module | Scenario 안에서 실행하는 작업 단위 |
| Connection | Make가 외부 서비스에 연결하는 인증 정보 |
| Filter | Module 사이에 조건을 추가해 분기하는 기능 |
| Router | 여러 흐름으로 나누는 분기 모듈 |
| Operations | Make에서 Module 실행 1회를 1 operation으로 계산 |
| Error Handler | 오류 발생 시 처리 흐름을 정의하는 모듈 |
| Webhook | 외부 앱이 URL을 호출해 Scenario를 시작하는 방식 |

---

## 3. 우선순위 요약

| 우선순위 | 항목 | 분류 |
|---------|------|------|
| 🔴 높음 | [1-6] ch12 파일 의존성 — 없을 때 명확한 안내 없음 | 필수 수정 |
| 🟠 중간 | [1-1] 수업 시간 합계 격차 (310분 vs "약 3시간") | 필수 수정 |
| 🟠 중간 | [1-2] `to_csv()` 인코딩 5회 누락 (ch04~ch13 반복) | 필수 수정 |
| 🟠 중간 | [1-3] `base_dir` 코드 두 번 중복 정의 (섹션 5.3, 7.1) | 필수 수정 |
| 🟠 중간 | [1-4] `write_text(encoding="utf-8")` — BOM 없음 (ch12 반복) | 필수 수정 |
| 🟡 낮음 | [1-5] `~~~` 코드 펜스 비표준 사용 (ch09, ch10 반복) | 필수 수정 |
| 🔴 높음 | [2-1] Google Drive 데스크톱 앱 설치 전제 미안내 | 보완 권장 |
| 🟢 권장 | [2-2] Make 무료 계정 제한사항 미안내 | 보완 권장 |
| 🟢 권장 | [2-3] Make 실제 설정 화면 안내 없음 | 보완 권장 |
| 🟢 참고 | [2-4] 실습용 계정 권장 이유 미설명 | 보완 권장 |
| 🟢 참고 | [2-5] 연습 문제 채점 기준 없음 | 보완 권장 |
| 🟢 참고 | [2-6] 핵심 용어 정리 섹션 부재 | 보완 권장 |

---

## 4. 전반적 평가

**잘 된 점**
- 섹션 3.3의 Python vs Make 역할 분담 표가 매우 명확하다. "Python은 분석, Make는 전달·알림·기록"이라는 핵심 개념을 표 한 개로 정리한 것이 탁월하다.
- Notebook 파일명이 실제 파일(`ch13_make_automation.ipynb`)과 일치하는 유일한 후반 장이다. (ch04, ch06~ch12 불일치와 달리)
- 섹션 3.6의 자동화 검증 필요 이유 표(문제 유형 7가지)가 학생이 자동화를 과신하지 않도록 잘 안내한다.
- 섹션 7.5의 자동화 검증 체크리스트 14개 항목이 실무적으로 구체적이다.
- 섹션 7.8에서 테스트 로그 샘플 데이터를 제공하는 구조가 좋다 — 학생이 Google Sheets 시트 구조를 즉시 이해할 수 있다.
- 섹션 6에서 4개 Scenario를 별도 섹션으로 구분한 것이 흐름 이해에 도움이 된다.

**전체적 방향 제안**  
ch13은 외부 서비스(Make, Google Drive, Gmail, Google Sheets)를 처음 연결하는 장으로, 비전공자에게 진입 장벽이 가장 높은 장 중 하나다. **[2-1] Google Drive 데스크톱 앱 설치 전제 미안내**와 **[2-2] Make 무료 계정 제한 미안내**는 학생이 실습 시작 전부터 막히게 만들 수 있으므로 보완 권장 항목임에도 실질적으로는 높은 우선순위다. 또한 `automation/make/make_scenario_guide.md` 파일이 이미 workspace에 존재하므로, 교재 본문에서 이 파일을 명시적으로 참조하면 좋다. Python 코드 측면에서는 `to_csv()` 인코딩 누락이 가장 즉각적인 수정 사항이다.
