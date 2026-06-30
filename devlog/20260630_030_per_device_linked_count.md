# 030. 디바이스별 추적 + 연결 기기 수 표시

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.25 반영).

## 배경

029에서 `paired`는 토큰 단위(디바이스 구분 불가)라고 했는데, "디바이스별로 해도 되지 않나?"
→ **디바이스 ID와 싱크 토큰을 분리**하면 가능. 분리해서 연결 기기 수까지 표시.

## 핵심 변경: ID/토큰 분리

- **디바이스 ID**(`strati_device`): 브라우저 고유·영구. 페어링해도 안 바뀜.
- **싱크 토큰**(`strati_token`): 공유 버킷 키. 기본=디바이스 ID, **페어링 시 상대 토큰으로 교체**.
- 동기화 때 둘 다 전송(`X-Device`=토큰, `X-Device-Id`=디바이스 ID).

## 서버 (`models.py`, `views.py`, migration 0004)

- `SyncDevice.devices` JSON 추가: `[{id, seen}]` — 이 버킷을 쓴 디바이스 ID 기록(중복 방지, last-seen 갱신).
- `api_sync` 응답에 `devices`(개수) 포함, `paired = paired or count>=2`.

## 클라이언트 (`app.js`, `timetable.html`)

- `deviceId()`(영구)·`deviceToken()`(교체 가능) 분리. `pairClaim`은 **토큰만** 교체.
- 응답의 `devices` 수를 저장, `linkedCount()` 노출.
- My Plan 배지: "🔗 Linked · N devices"(N≥2) / "🔗 Linked across devices".

## 검증

- A(devA)=1·paired False → B(devB) 합류 devices=2·paired True → A 재동기화 중복 없이 2.
- `node --check`, `manage.py check` 통과.

## 메모

- 브라우저 데이터 삭제 시 새 디바이스 ID 발급 → 재페어링하면 카운트가 늘 수 있음(근사치).
  last-seen 보관하므로 추후 오래된 기기 제외/기기 목록 표시로 확장 가능.
