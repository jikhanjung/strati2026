# STRATI 2026 학회 정보 데이터베이스화 프로젝트

## 프로젝트 목표

STRATI 2026 (5th International Congress on Stratigraphy, 2026-06-28~07-03, 중국 쑤저우)
학회의 **핸드북**과 **초록집** PDF를 파싱하여 데이터화하고, 이를 기반으로
**참가자가 발표(talk)를 둘러보고 원하는 것을 북마크하면 그 발표들의 시간·장소를
타임테이블로 보여주는 웹 앱**을 만든다.

- 1단계(현재): PDF → 구조화 **JSON 산출물**(`output/`). DB 적재는 production에서 별도 수행.
- 2단계: Django 웹 앱(아래 "애플리케이션" 참조).

> **핵심**: 타임테이블 기능을 위해 각 초록(발표)을 핸드북 일정표의 **시간·장소(room)** 와
> 연결해야 한다. → 핸드북 프로그램 파싱이 초록↔일정 매핑 키를 만들어야 함.

## 애플리케이션 (`congress` 앱)

- 프레임워크: **Django 5.2** (프로젝트 `config`, 앱 `congress`).
- UI: **모바일(스마트폰) 우선** — 하단 탭바(Program/Sessions/Search/My Plan).
  발표 탐색 → ☆ 북마크 → 내 타임테이블(시간/장소).
- **북마크는 로그인 없이 localStorage**(기기별). 타임테이블은 `/api/talks/`를 받아 JS로 렌더.
  → 인증/유저 모델 없음.
- DB: **SQLite**. 경로는 `STRATI_DB_PATH`(기본 `/srv/strati2026/db.sqlite3`).
  이 개발/테스트 서버도 동일하게 `/srv/strati2026/db.sqlite3` 사용.
- 정적파일: **whitenoise**, WSGI: **gunicorn**.
- 데이터 적재: `python manage.py import_json` (output/*.json → DB. `--if-empty`는 최초기동용).

### 모델 (`congress/models.py`)
- `Session(code, category, title, poster_count)`
- `Abstract(session, page, title, abstract_text, keywords[], authors[], affiliations[])` (JSON 필드)
- `Talk(date, day_label, room, session, time_start, time_end, title, first_author, kind, abstract FK, page)`

### 실행
- 로컬 개발: `STRATI_DB_PATH=/srv/strati2026/db.sqlite3 python manage.py runserver`
- 테스트 서버(Tailscale): Docker 컨테이너 `strati2026`가 `0.0.0.0:8010`에 상시 구동.
  접근: `http://m710q.tail339927.ts.net:8010/` 또는 `http://100.98.176.40:8010/`.
- 데이터 갱신 시: `output/*.json` 재생성 → `import_json` 재실행(컨테이너면 재적재).

### 배포 (`deploy/`, fsis2026 패턴 참고)
- `deploy/Dockerfile` + `deploy/entrypoint.sh`(collectstatic→migrate→import_json --if-empty→gunicorn).
- `deploy/build.sh X.Y.Z`: version bump + `honestjung/strati2026:{X.Y.Z,latest}` build/push.
- 운영 호스트: `deploy/host/{docker-compose.yml,deploy.sh}` → `sync_to_srv.sh`로 `/srv/strati2026/`에 복사,
  `/srv/strati2026/deploy.sh X.Y.Z`로 버전 스왑(+pre-deploy DB 스냅샷). DB는 `/srv/strati2026/db.sqlite3` 마운트.
- 버전: `config/version.py` (현재 `0.1.0`). `.env`는 `.env.example` 참고.

## 데이터 소스 (`data/`)

| 파일 | 페이지 | 내용 |
|------|--------|------|
| `strati2026_handbook.pdf` | 34 | 위원회/주최, 기조연사, 학술 일정표, 답사, 일반정보, 행사장/지도, 교통, 사회 프로그램 |
| `strati2026_abstract_volume.pdf` | 923 | 약 600+ 초록, 세션 G1–G18(G14 결번), S1–S14(S8 결번) |

> `data/`는 `.gitignore` 대상 (대용량 PDF + 생성된 DB). 원본은 외부 백업 권장.

## PDF 추출 특성 (중요 — 시행착오로 확인됨)

- **추출 도구: PyMuPDF(`pymupdf`) 우선, 보조로 `pdfplumber`.** OCR(tesseract)은 불필요.
- **초록집 본문 형식** (세션 헤더가 매 페이지 러닝헤더로 반복됨):
  ```
  Session G1                         ← 러닝헤더 (반복, 파싱 시 제거)
  5th International Congress ...      ← 러닝헤더 (반복)
  <제목>                              ← 여러 줄 가능
  <저자들> 상첨자 숫자=소속번호, * = 교신저자
  <소속 목록> (번호순, 본문에선 번호가 줄바꿈으로 분리됨)
  Abstract
  <초록 본문>
  Key words <키워드 콤마구분>
  <페이지번호>                        ← 푸터
  ```
  - 앞부분 약 37페이지는 **목차(Sessions Overview + Contents)** — 본문 파싱에서 제외.
  - `Key words` 표기 흔들림 주의(`Key words`/`Keywords`/대소문자). 일부 초록엔 키워드가 없을 수 있음.
  - 저자명의 상첨자 소속번호/`*`는 텍스트 추출 시 일반 숫자로 평문화됨 → span의 `font`/`size`/`flags`(superscript)로 구분 필요.
- **핸드북 일정표(Daily Program) 폰트 인코딩 깨짐 → 복호화 가능**:
  - 일부 표 셀 텍스트가 ASCII **-29 시프트**로 인코딩됨 (예: `5HJLVWUDWLRQ` → `Registration`, `\x14\x17\x1d...` → `14:00-`). 숫자·시간 포함 전부 복원됨.
  - 해당 span만 골라 `chr(ord(c)+29)` 적용. (정상 폰트 span에 적용하면 깨지므로 **폰트별 분기** 필요. 정상 본문 폰트: ArialMT/Arial-BoldMT/TimesNewRomanPS-BoldMT/SourceHanSansCN-Medium.)

## 세션 제목 출처 (PDF에 없음)

초록집/핸드북 PDF에는 세션 제목 전문이 없어 학회 웹사이트에서 확보 → `output/sessions.json`.
- 출처: `strati2026.org` 포스터 세션 페이지 콤보박스. 데이터 API:
  `GET https://api.yw.strati2026.org/strati2026/api/submission/getTopics/{conferenceId}`
  (`conferenceId = 1899130655669882882`, **인증 토큰 필요** — 비로그인 호출은 401).
  현재 `output/sessions.json`은 렌더링된 콤보박스 HTML에서 추출한 값.
- **미확보**: `G18`, `S14` 제목 (포스터 콤보박스엔 없으나 초록집엔 존재). 추후 보강 필요.
- 결번: `G14`, `S8` (실제로 존재하지 않는 세션).

## DB 설계 (production 참고용, `schema.sql`)

### 초록집
- `session(id, code, category[G|S], title, page_start)`
- `abstract(id, session_id, title, page, abstract_text, keywords_raw)`
- `author(id, full_name, normalized_name)` — 동명이인/표기변형 정규화 대상
- `affiliation(id, raw, name, country)`
- `abstract_author(abstract_id, author_id, author_order, is_corresponding)`
- `abstract_author_affiliation(abstract_id, author_id, affiliation_id)` — 소속은 초록별로 매핑
- `keyword(id, term)`, `abstract_keyword(abstract_id, keyword_id)`

### 핸드북
- `committee_member(id, name, role, committee, organization)`
- `plenary_speaker(id, name, affiliation, talk_title)`
- `program_event(id, date, time_start, time_end, content, session_code, room, floor)`
- `field_excursion(id, code, title, date, description)`

> 행사장/교통/일반정보 등 서술형 콘텐츠는 DB 대신 마크다운 문서로 보관 검토.

## 작업 파이프라인

1. **추출**: PDF → 페이지별 구조화 텍스트 (중간산출물, `build/`)
2. **파싱**: 초록 단위로 분리 → {세션, 제목, 저자, 소속, 본문, 키워드} 레코드화
3. **정규화**: 저자·소속 중복 제거 및 표준화, 세션코드 ↔ `sessions.json` 매핑
4. **JSON 출력**: `output/`에 스키마에 대응하는 JSON 산출 (production insert용)
5. **검증(QA)**: 초록 수 카운트, 세션별 집계, 무작위 샘플 대조

### 산출 JSON (production insert 대상)

- `output/sessions.json` — 세션 코드/제목 (✅ 완료, G18·S14 제목 보강 필요)
- `output/sessions.json` — 세션 코드/제목
- `output/abstracts.json` — 초록 + 저자/소속/키워드 (607건)
- `output/program.json` — 발표 일정(시간·룸·세션·제목·제1저자) + `abstract_id` 연결 (391건)
- `output/handbook.json` — 위원회/기조연사/답사 등 (예정)

## 디렉토리 구조

```
strati2026/
├── data/        # 원본 PDF (gitignore)
├── scripts/     # 추출·파싱 스크립트
├── build/       # 중간 산출물 (gitignore)
├── output/      # 최종 JSON 산출물 (git 추적 — 이것이 결과물)
├── devlog/      # 작업 기록 (YYYYMMDD_NNN_title.md)
├── schema.sql   # production DB 스키마 (참고용)
└── CLAUDE.md
```

## devlog 규칙

작업이 논리적 단위로 끝날 때마다 `devlog/`에 `YYYYMMDD_NNN_title.md`로 기록.
일련번호 `NNN`은 **날짜와 무관하게 단조 증가**(전체에서 유일).

## 환경

- Python venv: `/home/jikhanjung/venv/strati2026` (작업 전 activate 필요)
- 설치됨: `pymupdf` 1.27, `pdfplumber` 0.11
- 시스템: `sqlite3`, `pdftoppm` 사용 가능 / `tesseract` 미설치(불필요)

## 진행 현황

- [x] 데이터 소스 구조 파악, 추출 특성 분석
- [x] CLAUDE.md 및 계획 수립
- [x] 세션 제목 확보 → `output/sessions.json` (G18·S14 제목 제외)
- [x] 초록집 파싱 → `output/abstracts.json` (607건, TOC 대조 검증) — `scripts/parse_abstracts.py`
- [x] 학술 프로그램 파싱 + 초록 연결 → `output/program.json` (391 talks, 375 연결) — `scripts/parse_program.py`
- [x] Django 5.2 앱(`congress`) — Program/Sessions/Search/My Plan, localStorage 북마크, 모바일 UI
- [x] Docker 이미지(`honestjung/strati2026:0.1.0`) 빌드·구동 검증 + `deploy/` 스크립트(fsis2026 패턴)
- [x] 테스트 서버 Tailscale 구동 (`:8010`)
- [ ] 핸드북 잔여 메타(위원회·기조연사·답사) → `output/handbook.json`
- [ ] G18·S14 세션 제목 보강
- [ ] `schema.sql` 작성 (production 참고용)
- [ ] 운영 서버 실제 배포(이미지 push + `/srv/strati2026/deploy.sh`)
