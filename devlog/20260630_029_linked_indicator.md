# 029. "Linked" 상태 표시

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.24 반영).

## 배경

페어링된 기기에 "연결됨"을 표시해달라는 요청.

## 설계 포인트

- 페어링하면 두 기기가 **같은 토큰**을 쓰므로 서버는 기기를 구분 못 함 →
  `paired`는 **디바이스별이 아니라 토큰(공유 버킷) 단위** 속성.
- 버킷에 한 번이라도 페어링이 일어나면 `paired=True`, 그 토큰을 쓰는 모든 기기가 동일하게 표시.

## 한 일

- `SyncDevice.paired` 필드 + migration 0003.
- `pair_claim` 성공 시 대상 토큰 버킷 `paired=True`.
- `api_sync` 응답에 `paired` 포함(클라 `mergeInto`는 bm/notes만 보므로 무해).
- 클라(`app.js`): 동기화 응답 `paired` 또는 claim 성공 시 `localStorage.strati_linked` 설정,
  `isLinked()` 노출.
- My Plan: "🔗 Linked across devices" 배지(초록). `sync:applied` 이벤트로 갱신.

## 검증

- 새 기기 paired=False → 페어링 후 청구 기기 즉시 / 생성 기기는 다음 동기화에 True.
- `node --check`, `manage.py check` 통과, `#sync-status` 렌더 확인.

## 메모

- "몇 대가 연결됐는지"는 표시 불가(같은 토큰이라 카운트 불가) — 불리언 "Linked"만.
