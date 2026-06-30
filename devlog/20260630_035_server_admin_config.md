# 035. 서버 전역 설정(운영자) 페이지 + 제목 변경

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.31 반영).

## 배경

사용자별 설정(034)과 별개로, **운영자**가 서버 전체를 관리(쿼터·기능 on/off)할 수 있어야 함.
비밀번호로 보호되는 관리 페이지 요청.

## 한 일

### 모델/설정 (`models.py` ServerConfig + migration 0007, `settings.py`)
- `ServerConfig`(싱글톤): `sync_enabled`, `photo_sync_enabled`, `photo_max_mb`,
  `photo_max_per_talk`, `photo_max_per_token_mb`.
- `STRATI_ADMIN_PASSWORD`(env, 기본 `strati2026` — .env에서 변경). 업로드 한도는 ServerConfig가 결정.

### 엔드포인트 (`views.py`, `urls.py`)
- `GET/POST /api/admin/config/`: 비밀번호(헤더 `X-Admin`) 검증 후 조회/저장 + 통계(기기·사진·용량).
- `GET /api/clientconfig/`(공개): 전역 on/off 플래그 — 클라 UI 게이팅용.
- `photo_upload`/`api_sync`가 ServerConfig를 강제: 사진 off면 업로드 403, 동기화 off면 sync 503,
  쿼터(장당/talk당/토큰당)도 설정값 적용.

### 관리 페이지 (`manage.html`, `/manage/`)
- 비밀번호 입력 → 토글(Cloud sync, Photo sync) + 수치(장당 MB, talk당, 기기당 MB) 편집/저장.
- 기기·사진·사용 용량 통계 표시. 사용자 Settings 하단에 "Server admin →" 링크.

### 클라이언트 (`app.js`)
- 서버 전역 플래그 캐시(`strati_srv`) + `cfgSync()/cfgPhotos()` = 사용자설정 AND 서버플래그.
  동기화·사진 게이팅을 실효 설정으로 전환. 로드 시 `/api/clientconfig/` 갱신.

### 기타
- 헤더/제목을 "Unofficial **Planner**"로 변경(기존 Bookmarks).
- `.env.example`에 `STRATI_ADMIN_PASSWORD` 추가.

## 검증 (curl)

- 관리 GET 잘못된 비번 401 / 정상 200(설정+통계). POST로 사진 off·쿼터 변경 반영.
- clientconfig가 off 반영, 업로드 403 차단, 재활성 정상. `node --check`/`manage.py check` 통과.

## 메모

- 관리 비밀번호는 베어러 → 운영 https 필수(테스트는 Tailscale). 기본값 반드시 변경.
- 클라 UI 게이팅은 캐시라 1회 로드 지연 가능하나, 서버가 항상 강제(403/503)하므로 안전.
