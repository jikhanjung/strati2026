# 014. 현재 시각 빨간 줄 + 오늘 기본 선택 + My Plan 휴식 중복 정리

- 날짜: 2026-06-29
- 상태: 완료(코드/로컬 검증). Hub 푸시 별도.

## 배경

학회 당일 사용성 개선 요청:
1. 프로그램에서 **오늘 날짜가 기본 선택**되도록.
2. **현재 시각을 빨간 줄**로, 지금 진행 중인 talk 위치에 (대략 시간 비례) 표시.
3. 스크롤로 현재 시각에서 벗어나면 **현재 시각으로 점프하는 플로팅 버튼**.
4. My Plan에서 여러 룸 talk을 북마크하면 휴식 시간이 룸마다 5분쯤 어긋나 겹쳐 보임 → **하나만** 표시.

## 한 일

### 오늘 기본 선택 (`congress/views.py`)
- `program()`에서 `?day` 미지정 시 쑤저우 시간 기준 오늘을 선택(일정에 없으면 첫째 날).

### 현재 시각 빨간 줄 (`program.html`, `_talk_item.html`, `_break_item.html`, `style.css`)
- talk/break 카드에 `data-start`/`data-end`(HH:MM) 부여.
- JS: `Intl.DateTimeFormat(timeZone:'Asia/Shanghai')`로 기기 시간대와 무관하게 현재 날짜·분 산출.
- 보고 있는 날짜 == 오늘일 때만 활성 패널에 `.nowline`(빨간 줄) 삽입.
  - 진행 중 카드 안에서는 `(now-start)/(end-start)` 비율로 카드 내부 보간,
    카드 사이 빈틈은 경계 보간, 첫 발표 전/마지막 후는 위/아래 끝.
- 룸 탭 전환·리사이즈·1분 간격으로 재배치.

### 현재 시각 점프 버튼
- `#nowbtn`(fixed, 빨강). 줄이 뷰포트 밖이면 노출, 클릭 시 줄 위치로 부드럽게 스크롤.
- `scroll`/`resize`에서 가시성 갱신.

### My Plan 휴식 중복 정리 (`timetable.html`)
- 기존: 북마크 시간범위 내 휴식을 (start,end,label) 정확일치로만 dedup → 룸별 5분 차이로 중복.
- 변경: **북마크한 talk 직전(같은 룸, `b.end==t.start`)의 휴식만** 후보로 모으고,
  시간이 겹치는 후보(`a.start<b.end && b.start<a.end`)는 하나만 표시.

## 검증

- `?day` 없이 접속 시 `daychip on` = Jun 29(오늘), JS `SEL_DAY="2026-06-29"`.
- talk 카드 `data-start/-end` 렌더 확인, `#nowbtn` 존재.
- 렌더된 program/timetable 인라인 JS `node --check` 통과.
- 스크립트 정의 순서 수정: 초기 `activate()`를 const/함수 정의 뒤로 이동(TDZ ReferenceError 방지).

## 메모

- 빨간 줄은 "대략 시간 비례"(카드 리스트 기반 보간)로, 진짜 픽셀 타임그리드는 아님.
- 점프 버튼 임계값은 상단 60px / 하단 60px 여유.
