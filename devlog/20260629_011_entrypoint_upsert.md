# 011. entrypoint 데이터 upsert 적재

- 날짜: 2026-06-29
- 상태: 완료(코드/테스트 서버). Hub 푸시는 별도.

## 배경

`/srv/strati2026/db.sqlite3` 는 컨테이너에 마운트되는데, 기존 entrypoint 는
`import_json --if-empty` 라 **이미 데이터가 있으면 건너뜀** → 재배포해도 데이터가 갱신되지 않음.
북마크는 localStorage 라 DB 엔 사용자 데이터가 없음 = DB 는 `output/*.json` 의 순수 파생물.

## 한 일

- `import_json --upsert` 추가: wipe 없이 **PK 기준 update + 신규 insert**
  (`bulk_create(update_conflicts=True, unique_fields, update_fields)`).
  - Session=code, Abstract/Talk=id 기준. session/abstract → talk 순서로 FK 보장.
- entrypoint 를 `import_json --if-empty` → **`--upsert`** 로 변경.
  매 기동마다 이미지의 JSON 으로 DB 동기화 → 재배포 시 데이터 자동 갱신.

## 검증

- 임시 DB: 1회/2회 upsert 모두 30/607/457 (idempotent).
- 조작한 행(talk id=10 제목)이 upsert 후 JSON 값으로 복원 → update 경로 정상.
- 컨테이너 재기동 로그 `import complete (upsert)`, 라이브 457 confirm.
- SQLite 3.45 update_conflicts 지원 확인.

## 메모

- 기본(옵션 없음)은 여전히 wipe+reload(로컬 클린 재빌드용). `--if-empty` 도 유지.
- Hub 이미지 재푸시 필요(다음 버전). 로컬 0.1.4 태그는 새 entrypoint 로 재빌드됨(Hub와 상이).
