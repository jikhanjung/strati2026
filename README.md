# STRATI 2026 Companion

STRATI 2026 (5th International Congress on Stratigraphy, 2026-06-28~07-03, Suzhou, China)
핸드북·초록집 PDF를 데이터화하고, 참가자가 발표를 둘러보며 **북마크 → 내 타임테이블(시간·장소)**
을 볼 수 있는 모바일 우선 웹 앱.

- **데이터 파이프라인**: PDF → 구조화 JSON (`scripts/` → `output/`)
- **웹 앱**: Django 5.2 + SQLite, 북마크는 로그인 없이 브라우저 localStorage
- **배포**: Docker 이미지 `honestjung/strati2026`, 운영 서버 `/srv/strati2026`

> 개발 가이드/설계 상세는 [`CLAUDE.md`](CLAUDE.md), 작업 기록은 [`devlog/`](devlog/) 참고.

## 데이터

원본 PDF(`data/`, git 미추적)에서 파싱한 산출물이 `output/`에 있고, 이것이 DB 적재 대상이다.

| 파일 | 내용 | 생성 스크립트 |
|------|------|---------------|
| `output/sessions.json` | 세션 코드/제목 (28개; G18·S14 제목 미확보) | 학회 사이트에서 수집 |
| `output/abstracts.json` | 초록 607건 (제목·저자·본문·키워드) | `scripts/parse_abstracts.py` |
| `output/program.json` | 발표 391건 (시간·룸·세션·제1저자) + 초록 연결(375) | `scripts/parse_program.py` |

```bash
# 산출물 재생성 (원본 PDF 필요)
pip install -r requirements-dev.txt
python scripts/parse_abstracts.py
python scripts/parse_program.py   # abstracts.json 을 읽어 초록 연결
```

## 웹 앱 (`congress`)

- 화면(하단 탭): **Program**(일자→룸 탭별 발표) / **Sessions** / **Search** / **My Plan**(타임테이블)
- 발표 ☆ 북마크는 **localStorage**(기기별, 로그인 없음). My Plan 은 `/api/talks/` 로 렌더.
- 모델: `Session` / `Abstract` / `Talk`(시간·룸 + 초록 FK).

### 로컬 실행

```bash
pip install -r requirements.txt
export STRATI_DB_PATH=/srv/strati2026/db.sqlite3   # 기본값과 동일
python manage.py migrate
python manage.py import_json        # output/*.json → DB
python manage.py runserver
```

주요 환경변수 (`.env.example` 참고): `STRATI_DB_PATH`, `STRATI_DEBUG`,
`STRATI_SECRET_KEY`, `STRATI_ALLOWED_HOSTS`, `STRATI_CSRF_TRUSTED_ORIGINS`.

## Docker / 배포

DB 는 SQLite 단일 파일(`/srv/strati2026/db.sqlite3`)을 컨테이너에 마운트한다.
배포 스크립트는 `deploy/` 참고 (책임 분리: 빌드 머신 = `build.sh`, 운영 호스트 = `host/deploy.sh`).

```bash
# 빌드 머신: 버전 bump + 이미지 build/push (honestjung/strati2026:X.Y.Z + latest)
./deploy/build.sh 0.1.1

# 운영 호스트(/srv/strati2026): git pull 후
./deploy/sync_to_srv.sh             # deploy/host/* → /srv/strati2026/
/srv/strati2026/deploy.sh 0.1.1     # pull + compose 스왑 (+ pre-deploy DB 스냅샷)
```

최초 기동 시 컨테이너가 `migrate` + `import_json --if-empty` 로 빈 DB 를 자동 적재한다
(이미지에 `output/*.json` 포함). 로컬 빌드/구동은 `deploy/docker-compose.dev.yml` 사용.

## 디렉토리

```
config/      Django 프로젝트(settings/urls/wsgi) + version.py
congress/    앱(models/views/templates) + management/commands/import_json
scripts/     PDF 파싱 스크립트
output/      파싱 산출 JSON (DB 적재 대상)
deploy/      Dockerfile, entrypoint, build/sync 스크립트, host/ (compose·deploy.sh)
data/        원본 PDF (git 미추적)
devlog/      작업 기록 (YYYYMMDD_NNN_title.md)
```
