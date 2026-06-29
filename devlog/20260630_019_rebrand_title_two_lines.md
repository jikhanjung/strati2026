# 019. 헤더/제목 문구 정리 + 두 줄 레이아웃

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.13 반영 예정).

## 배경

기존 헤더 "Unofficial Bookmarks for STRATI 2026 Program"이 영어로 어색
(관사 누락 "the", "Bookmarks ... Program" 구조). → 자연스러운 문구로 교체하고,
길이가 있어 두 줄로 분리.

## 한 일 (`base.html`, `style.css`)

- 문구: **"STRATI 2026 Program — Unofficial Bookmarks"**.
- 헤더 두 줄 분리(전치사/구 경계가 아닌 의미 단위로):
  - 1줄: `STRATI 2026 Program` (`.brand-main`, 굵게 16px)
  - 2줄: `Unofficial Bookmarks` (`.brand-sub`, 작게) — "Unofficial"은 기존처럼 빨강 강조(`.brand-unofficial`).
- `.brand`를 `flex-direction: column`으로.
- 브라우저 탭 기본 `<title>`도 동일 문구로 변경.

## 검증

- 렌더 확인: `.brand-main`/`.brand-sub`/`.brand-unofficial` 출력.

## 메모

- 페이지별 `{% block title %}`(예: "Program · STRATI 2026")는 그대로 유지.
