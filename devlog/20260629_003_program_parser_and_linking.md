# 003. 학술 프로그램 파서 + 초록 연결

- 날짜: 2026-06-29
- 상태: 완료
- 산출: `scripts/parse_program.py` → `output/program.json` (391 talks)

## 한 일

핸드북 p7–25(학술 프로그램)에서 **발표별 시간·장소·세션·제목·제1저자**를 좌표 기반 추출하고,
각 talk을 `output/abstracts.json`의 초록과 연결(`abstract_id`).

talk 레코드: `{id, date, room, session, time_start, time_end, title,
first_author, kind, page, abstract_id}`. (kind: talk | plenary)

## 레이아웃 처리

- 페이지당 **좌/우 2단**, 각 단은 독립 헤더 `DATE SESSION(s) Session (ROOM)`. → x<635 / ≥635 분리.
- 컬럼(Time/Session/Title/First Author) 경계는 헤더 단어 좌표로 동적 산출.
- 제목은 시간 앵커 **위아래로 걸쳐** 있음 → 각 단어를 **가장 가까운 시간앵커(centroid)**에 귀속.
  (초기 "위쪽 앵커 귀속"은 제목 첫 줄을 이전 발표에 붙여 행이 섞였음 → 수정)
- 좁은 컬럼의 **줄바꿈 하이픈 분절**("Implica- tions") 복원.
- Break/Lunch/Coffee/개회·폐회 행 제외. p7 개회/기조는 Session 컬럼 없음(kind=plenary).

## 초록 연결 (375/382 = 98.2%)

1. 정규화 정확매칭(공백·하이픈·문장부호 제거) 352
2. 동일세션 내 difflib 퍼지(≥0.90) — 핸드북 오타/대소문자/인코딩 차이 흡수 18
3. 접두사 양방향(저자명이 제목칸 번짐 / talk 제목 잘림) 5

미연결 7건: Ordovician subcommission 미팅 1, 초록집 미수록(구두전용) ~4,
핸드북-초록집 제목 자체가 다른 편집본 ~2. (파서 문제 아님)

## 검증

- p8(G4) 레코드가 원본 레이아웃과 정확히 일치(시간·세션·저자).
- 시간 필드 유효성 100%, 날짜 분포(June29/30·July2/3)·룸 6개 합리적.
- 퍼지/접두사 연결 전수 육안 확인 — 오매칭 없음.

## 다음

- (선택) 핸드북 잔여 메타: 위원회·기조연사 약력·답사 → `output/handbook.json`.
- G18/S14 세션 제목 보강.
- 데이터 준비 완료 → Django 앱(타임테이블) 착수 가능.
