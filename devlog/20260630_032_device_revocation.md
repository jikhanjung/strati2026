# 032. 기기 제거 = 실제 차단(revoke) + 재접속 시 분리

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.27 반영).

## 배경

031의 "기기 제거"는 목록에서만 빼서 그 기기가 다시 동기화하면 재등록되는 best-effort였음.
→ "제거된 기기가 접근하면 새 토큰을 발행해 분리하자"는 요청.

## 한 일

### 서버 (`models.py` revoked 필드 + migration 0005, `views.py`)
- `SyncDevice.revoked`(차단된 디바이스 ID 목록) 추가.
- `device/forget/`: 제거 시 해당 ID를 **revoked에 추가**.
- `api_sync`: 요청 디바이스 ID가 revoked면 데이터 제공 없이 **HTTP 409 `{revoked:true}`**.
- `pair_claim`: 청구 기기 ID(`X-Device-Id`)를 revoked에서 제거 → **재페어링 시 차단 해제**.

### 클라이언트 (`app.js`, `timetable.html`)
- `syncNow`가 409를 받으면 **싱크 토큰을 새 랜덤으로 교체(솔로 버킷)** + linked/devices 캐시 초기화,
  `sync:revoked` 이벤트 발생 → 곧 새 토큰으로 재동기화. 로컬 데이터는 유지.
- `pairClaim`이 `X-Device-Id` 헤더 전송(차단 해제용).
- My Plan: `sync:revoked` 시 "This device was unlinked from the group…" 안내.

## 검증 (curl 시나리오)

1. phone+laptop 합류 → 2. phone이 laptop 제거(devices=1) → 3. laptop 동기화 **409 revoked**
→ 4. laptop 재페어링 후 동기화 **200**(차단 해제) → 5. phone 영향 없음 **200**.

## 동작 정리

- 제거된 기기는 **다음 접속 시점에** 거부되어 공유에서 분리됨(즉시 네트워크 차단이 아닌, 다음 sync에 적용).
- 분리돼도 그 기기의 로컬 북마크/메모는 보존(서버에서 원격 삭제는 불가 — 클라 저장이라).
- 다시 합치려면 해당 기기에서 재페어링.
