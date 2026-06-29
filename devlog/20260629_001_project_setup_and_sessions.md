# 001. 프로젝트 셋업 및 세션 목록 확보

- 날짜: 2026-06-29
- 상태: 완료

## 한 일

- `data/`의 두 PDF(handbook 34p, abstract_volume 923p) 구조 분석.
- `CLAUDE.md` 작성: 프로젝트 목표/데이터 특성/파이프라인/디렉토리 구조 정의.
- 산출 전략 확정: 로컬 DB 빌드 대신 **`output/`에 JSON 산출** → production 서버에서 insert.
- `.gitignore` 구성 (`data/`, `build/` 무시, `output/` 추적).
- 세션 제목 확보 → `output/sessions.json`.

## 핵심 발견

- 초록집 본문은 폰트/크기로 구조가 명확:
  - 제목 = 14pt Bold, 저자 = 11pt + 7pt 상첨자(소속번호/`*`=교신), 소속 = 10pt Italic, 본문 = 11pt.
  - 앞 ~37p는 목차.
- 핸드북 일정표는 폰트 인코딩이 ASCII **-29 시프트** → OCR 없이 복호화 가능.
- 세션 제목은 PDF에 없음 → 학회 사이트 콤보박스/API(`getTopics/{conferenceId}`)에서 확보.
  - `G18`, `S14` 제목 미확보(포스터 콤보박스에 없음). `G14`, `S8`은 결번.

## 다음

- 초록집 파싱 → `output/abstracts.json`.
