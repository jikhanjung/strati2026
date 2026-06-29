# 006. 상세 세션 제목 + 프로그램 배지 툴팁

- 날짜: 2026-06-29
- 상태: 완료

## 한 일

- **발표 상세 페이지**: 제목 아래 세션 코드+제목을 카드로 표시(세션 페이지로 링크).
  - 뷰(`talk_detail`/`abstract_detail`)에서 `session` 컨텍스트 전달.
  - `.detail-session` 스타일 추가.
- **프로그램/검색 목록**: 세션 코드 배지에 hover 툴팁(HTML `title`=세션 제목).
  - `_talk_item.html` 배지에 `title="{{ t.session.title }}"`.
  - `session_detail` 쿼리에 `select_related("session")` 추가(N+1 방지).

## 검증

- `/talk/10/` 상세에 "G4 · The Precambrian-Cambrian Transition…" 링크 렌더.
- 프로그램 배지 `title="The Precambrian-Cambrian Transition…"` 확인.
- 이미지 재빌드 + 테스트 컨테이너 재시작 반영.

## 메모

- 이미지 푸시는 미실행(테스트 서버 컨테이너만 갱신). 운영 반영 시 `build.sh`로 버전 bump 후 push 권장.
