# 031. 기기 목록 + 연결 해제

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.26 반영).

## 한 일

### 서버 (`views.py`, `urls.py`)
- `GET /api/devices/` (헤더 `X-Device`): 이 버킷의 디바이스 목록 `[{id, seen}]`(최근순) + `current`(X-Device-Id).
- `POST /api/device/forget/` `{id}`: 버킷 목록에서 해당 디바이스 제거 → 남은 수 반환. (모델 변경 없음)

### 클라이언트 (`app.js`)
- `listDevices()`, `forgetDevice(id)`, `unlinkThisDevice()` 추가/노출.
- **이 기기 연결 해제**: 옛 버킷에서 자기 ID를 forget → 싱크 토큰을 새 랜덤으로 교체(솔로 버킷) →
  로컬 데이터 유지한 채 재동기화. linked/devices 캐시 초기화.

### UI (My Plan)
- 링크 상태일 때 "Manage devices" `<details>`: 각 기기(📱 This device / 🖥️ 앞 8자리) + 최근 접속(상대시간),
  타 기기는 × 로 목록에서 제거. "Unlink this device" 버튼(확인 후 이 기기 분리, 페이지 새로고침).

## 검증

- 2기기 등록 → 목록(현재기기 표시·last-seen) → forget로 1대 제거 확인.
- `node --check`, `manage.py check` 통과, UI 요소 렌더 확인.

## 메모/한계

- 타 기기 "제거"는 목록에서 빼는 best-effort — 그 기기가 다시 동기화하면 재등록됨(공유 토큰을
  진짜 무효화하려면 토큰 회전 필요, 남은 기기 재페어링 비용). 분실/미사용 기기 정리 용도로 충분.
- 확실한 분리는 각 기기에서 "Unlink this device"(토큰 회전).
