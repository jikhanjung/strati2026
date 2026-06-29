# 009. 버그 수정: 브레이크 직후 talk 누락

- 날짜: 2026-06-29
- 상태: 완료
- 버전: 0.1.3

## 증상

타임테이블/프로그램에서 **Break 직후 첫 talk 하나씩이 누락**.
예: G4(p8) 15:35 브레이크 후 15:55 "Classic Cambrian Thrombolite…"가 빠짐.

## 원인

`parse_program.py`의 제목 귀속이 "가장 가까운 시간앵커(centroid)" 방식인데,
시간앵커가 없는 **"Break (20mins)" 텍스트가 직후 talk 제목에 병합** →
talk-loop의 `SKIP_TITLE`(break 포함)이 **그 talk 전체를 삭제**.

## 수정

- 제목 컬럼에서 Break/Lunch/Coffee/Tea 줄의 y를 **decoy 앵커**로 감지(`detect_break_ys`, `BREAK_RE`).
- `assign_by_anchor(..., decoy_ys)`: 브레이크 줄에 가까운 단어는 decoy로 흡수 후 폐기 →
  인접 talk 제목 오염 방지.
- decoy 감지는 break/lunch/coffee/tea로 좁혀 실제 제목 오탐 방지(SKIP_TITLE은 그대로).

## 결과

- talks **391 → 457**(+66; 세션당 오전·점심·오후 다수 브레이크).
- 초록 연결 **375 → 429** (429/448 = 95.8%).
- QA: 제목 내 break/lunch 0, 중복 0, 단문 0.

## 배포

- `program.json` 재생성 → **`/srv/strati2026/db.sqlite3` 재적재**(컨테이너의 `--if-empty`는
  기존 데이터를 건너뛰므로 명시적 `import_json` 필요) → 컨테이너 0.1.3 재구동.
- 이미지 `honestjung/strati2026:{0.1.3,latest}` build/push.
