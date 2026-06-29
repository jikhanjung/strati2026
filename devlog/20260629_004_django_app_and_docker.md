# 004. Django 앱 + Docker 배포 구성

- 날짜: 2026-06-29
- 상태: 완료(테스트 서버 구동까지)

## 한 일

`output/*.json`을 사용하는 **Django 5.2 모바일 우선 웹앱**(`congress`)과 Docker 배포 구성.

### 앱
- 화면(하단 탭바): **Program**(일자별·룸별 발표) / **Sessions**(세션→발표) /
  **Search**(제목·저자·세션) / **My Plan**(타임테이블).
- **북마크는 로그인 없이 localStorage**(`static/app.js`). My Plan은 `/api/talks/`를
  받아 북마크 ID로 클라이언트에서 일자·시간순 렌더. → 인증/유저 모델 없음.
- 모델: `Session` / `Abstract`(JSON 필드) / `Talk`(시간·룸 + `abstract` FK).
- `import_json` 커맨드로 sessions/abstracts/program JSON 적재(`--if-empty` 최초기동용).
- 정적=whitenoise, WSGI=gunicorn. DB=SQLite(`STRATI_DB_PATH`, 기본 `/srv/strati2026/db.sqlite3`).

### 배포 (`deploy/`, ../fsis2026 패턴 참고)
- `Dockerfile`(python:3.12-slim) + `entrypoint.sh`(collectstatic→migrate→import_json --if-empty→gunicorn).
- `build.sh X.Y.Z`: version bump(`config/version.py`) + `honestjung/strati2026:{X.Y.Z,latest}` build/push.
- 운영 호스트: `deploy/host/{docker-compose.yml,deploy.sh}`, `sync_to_srv.sh`로 `/srv/strati2026/`에 복사.
  `/srv/strati2026/db.sqlite3` 마운트, pre-deploy DB 스냅샷.

## 검증

- `/srv/strati2026/db.sqlite3` 적재: sessions 30 / abstracts 607 / talks 391(linked 375).
- 전체 뷰 200 (테스트 클라이언트). 초록 없는 talk에서 템플릿 None 참조 버그 수정(`obj_title`).
- `honestjung/strati2026:0.1.0` 이미지 빌드 → 컨테이너 구동: program/api/detail/static/sessions 모두 200.
- 테스트 서버(m710q) Tailscale 상시 구동: `http://100.98.176.40:8010/`,
  `http://m710q.tail339927.ts.net:8010/`.

## 다음

- 핸드북 잔여 메타(위원회·기조연사·답사), G18/S14 세션 제목, schema.sql, 운영 배포.
