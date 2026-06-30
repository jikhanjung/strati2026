# 038. 설정 기기 목록 정리 — 행별 Unlink + Reset를 목록 영역으로

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.36 반영).

## 배경

- 다른 기기 ×(forget)와 "Unlink this device"가 개념상 중복 → 목록의 **각 기기마다 Unlink 버튼** 하나로 통일.
- "Reset this device"를 기기 목록 영역 안으로 이동.

## 한 일 (`settings.html`, `style.css`)

- "Devices" 헤더 + 기기 목록을 **항상 펼쳐서** 표시(기존 details/summary 제거).
- 각 행에 **Unlink** 버튼:
  - 이 기기 → `unlinkThisDevice()`(새 솔로 토큰으로 분리, 데이터 유지). 솔로(이 기기뿐)면 버튼 없음.
  - 다른 기기 → `forgetDevice()`(차단 → 다음 동기화에 분리). 기존 ×·"Unlink this device" 제거.
- **Reset this device** 버튼 + 설명을 기기 섹션 안으로 이동.
- 동기화 꺼짐(서버)일 땐 페어링/목록 숨기고 "Cloud sync is turned off." 표시 + Reset은 유지.
- 목록은 로드 시 즉시 채우고 `sync:applied`/`sync:revoked`에 갱신.
- CSS `.device-unlink` 추가.

## 검증

- 설정 JS `node --check`, `manage.py check` 통과. 옛 요소(unlink-this/device-x/sync-devices) 제거 확인.
