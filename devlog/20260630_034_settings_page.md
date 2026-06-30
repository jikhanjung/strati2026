# 034. 설정 페이지 (동기화·사진·표시 토글 + 기기 초기화)

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.30 반영).

## 배경

"이런저런 설정(사진 동기화 on/off 등)을 할 수 있는 페이지" 요청. 로그인 없는 앱이라
**기기별 사용자 설정** 페이지로 구현(값은 localStorage).

## 한 일

### 설정 저장 (`static/app.js`)
- `strati_cfg` = `{sync, photos, breaks}`(기본 모두 true). `getCfg/setCfg/resetLocal` 노출.
- 게이팅:
  - `sync` off → `syncNow/scheduleSync/initSync`가 서버 호출 안 함(순수 로컬). My Plan 페어링 UI 숨김.
  - `photos` off → `syncPhotoTalks/migratePhotos` 중단, 상세 사진 섹션·My Plan 썸네일 숨김.
  - `breaks` off → `<body class="hide-breaks">` → `.brk`/`.gap` 숨김.

### 페이지 (`views.py`, `urls.py`, `settings.html`, base 헤더)
- `/settings/`(`settings_page`) + 앱바 ⚙️ 링크.
- 토글 3개(Cloud sync / Photo sync / Show breaks), 변경 시 setCfg + 새로고침으로 반영.
- 상태 정보(디바이스 ID 앞 8자리, 동기화/링크 상태), "Reset this device"(로컬 초기화 후 홈).

## 검증

- `/settings/` 200, 헤더 ⚙️, 토글 3개 렌더. `app.js`/settings/상세/My Plan JS `node --check` 통과.

## 메모

- 토글은 기기별. 동기화 off는 서버 통신만 중단하고 로컬 데이터는 보존(다시 켜면 재개).
- Reset은 이 기기의 북마크·메모·동기화 신원만 삭제. 서버에 올라간 사진은 다른 기기 토큰 아래 보존.
