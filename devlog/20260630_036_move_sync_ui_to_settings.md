# 036. 동기화 UI를 My Plan → 설정 페이지로 이동

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.33 반영).

## 배경

기기 동기화 관련 항목(Link/Enter code/Linked 배지/Manage devices/Unlink)을 사용자 설정 쪽으로
모으자는 요청.

## 한 일 (`timetable.html`, `settings.html`)

- My Plan(`timetable.html`)에서 `.sync` 섹션 마크업 + 페어링 IIFE 스크립트 제거.
  상단 안내문도 동기화 문구 → "Bookmarked talks, with your notes & photos."로.
- Settings(`settings.html`)에 동일 섹션 + 페어링/기기관리 스크립트 추가.
  - 코드 안내 문구를 "open Settings → Enter code"로 갱신.
  - settings-info의 중복 "Sync status" 줄 제거(섹션의 Linked 배지로 대체), Device id만 표시.
- 동작/게이팅 동일: `cfgSync()` 꺼지면 섹션 숨김, `sync:applied`/`sync:revoked`로 갱신.

## 검증

- `/settings/`에 sync-link·sync-devices·unlink-this 존재, `/timetable/`엔 동기화 UI 없음.
- settings/My Plan JS `node --check`, `manage.py check` 통과.
