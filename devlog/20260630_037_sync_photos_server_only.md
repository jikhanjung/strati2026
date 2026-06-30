# 037. Cloud/Photo sync를 서버 전용으로 — 사용자 토글 제거

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.35 반영).

## 배경

사용자 설정의 Cloud sync·Photo sync 토글 삭제 요청. (시스템이 photo false인데 사용자
토글이 보이고 체크되던 문제 포함 → 토글 자체를 없애 해결.) 이 둘은 **시스템(/manage/) 설정으로만** 제어.

## 한 일

### 클라이언트 (`app.js`)
- `CFG_DEFAULT = { breaks: true }` (sync/photos 제거 — 표시 옵션만 사용자 설정).
- `cfgSync()=srvCfg().sync`, `cfgPhotos()=srvCfg().photos` (사용자 AND 제거, 서버 플래그만).
- `srvCfg()` photos 기본 false(서버 기본과 일치 → 첫 로드 깜빡임 방지).

### 설정 페이지 (`settings.html`)
- Cloud sync·Photo sync `<label>` 행 + 관련 JS(매핑/clientconfig 행 숨김) 제거.
  "Show breaks & lunch"만 남김. 동기화/기기 섹션은 유지(서버 sync 플래그로 게이팅).

### 서버 기본값 (`models.py` + migration 0008)
- `ServerConfig.photo_sync_enabled` 기본 **False**(사진 기본 off; 운영자가 /manage/에서 on).
- 테스트 서버 기존 row도 False로 맞춤.

## 검증

- 설정 페이지 토글 = breaks 1개만. clientconfig `{sync:true, photos:false}`.
- 상세/내 플랜 사진 UI는 cfgPhotos()=false라 숨김(운영자가 켜면 표시).
- 각 페이지 JS `node --check`, `manage.py check` 통과.

## 메모

- 이제 동기화/사진 on-off는 전적으로 `/manage/`(운영자)에서 관리.
- 사용자별 sync opt-out은 없어짐(요청에 따름). 기기 페어링/관리 UI는 Settings에 유지.
