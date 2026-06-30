# 028. 동기화 Phase 1 — 익명 토큰 + 페어링 코드 (북마크·메모)

- 날짜: 2026-06-30
- 상태: 완료(서버 end-to-end 검증). 사진은 동기화 제외(기기 로컬 유지).

## 설계

- **신원**: 로그인 없이 기기마다 랜덤 토큰(`crypto.randomUUID`)을 localStorage(`strati_device`)에 저장.
  토큰 = "서버의 어느 사물함을 열지"를 가리키는 베어러 키.
- **저장 구조(클라이언트/서버 공통)**: `{bm:{id:{v,ts}}, notes:{id:{v,ts}}}`.
  삭제는 tombstone(`v:false` / 메모 `v:""`)으로 표현 → 기기 간 삭제 전파.
- **충돌**: 항목별 **last-write-wins(ts 큰 쪽)**. 서버가 stored와 incoming을 병합해 병합본 반환(push+pull 일체).
- **사진 제외**: 용량·비용 때문에 IndexedDB 로컬 유지.

## 서버 (`congress/models.py`, `views.py`, `urls.py`, migration 0002)

- 모델 `SyncDevice(token PK, state JSON, updated)`, `PairCode(code PK, token, expires_at)`.
- `POST /api/sync/` (헤더 `X-Device`): 상태 병합 후 병합본 반환. `@csrf_exempt`(쿠키/세션 없음, 토큰은 명시 헤더).
- `POST /api/pair/new/`: 현재 토큰 → 6자리 1회용 코드(5분). 만료분 청소.
- `POST /api/pair/claim/` `{code}`: 코드로 상대 토큰 반환(1회용, 만료 410/무효 404).
- 동시쓰기: `transaction.atomic` + `select_for_update`(SQLite는 직렬화로 대체).

## 클라이언트 (`static/app.js`)

- 저장 계층을 타임스탬프 상태(`strati_state`)로 재작성. **공개 API(getBM/getNote/toggle/setNote 등) 동일**.
  구버전 키(`strati_bm`/`strati_notes`)는 최초 1회 자동 이관.
- 변경 시 디바운스(800ms) 자동 동기화, 첫 로드 시 `initSync`(최대 3초). `firstSync` promise 노출.
- `pairNew()`/`pairClaim(code)`: 페어링. claim 시 상대 토큰 채택 후 즉시 동기화(로컬 병합).

## UI

- My Plan 하단 "🔗 Link a device"(코드 표시) / "⌨️ Enter code"(입력 후 reload).
- 렌더 전에 `await STRATI.firstSync`로 동기화된 북마크 반영.

## 검증

- 엔드포인트 단위: 병합/tombstone/버킷 분리/토큰 누락 400/1회용 코드 404.
- **수렴 시나리오**: A(북마크10)→코드 발급→B(북마크20)가 claim·push→ A·B 모두 {10,20,메모} 일치.
- `app.js`·timetable 스크립트 `node --check`, `manage.py check` 통과.

## 메모/주의

- 토큰은 베어러 자격증명 → **공개 배포 시 HTTPS 필수**(현 테스트 서버는 Tailscale 사설 http라 허용).
- 분실 대비는 페어링 코드. PII 없음.
- 향후: 페어링 QR, 사진 동기화(Phase 3), 동시쓰기 정교화.
