# 025. talk별 메모 (localStorage)

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.20 반영 예정).

## 배경

북마크처럼 로그인 없이, 발표마다 개인 메모를 기기에 저장하고 싶다는 요청.

## 한 일

### 저장 (`static/app.js`)
- `strati_notes` 키에 `{ talkId: text }`로 저장. `getNote/hasNote/setNote` 추가, `window.STRATI`에 노출.
- `refresh()`가 메모 있는 `.talk[data-id]`에 `has-note` 클래스 부여.

### 입력 UI (`talk_detail.html`)
- 발표 상세에 "📝 My note" textarea + 자동 높이. 입력 400ms 후 자동 저장(저장 시 "Saved" 표시).
- 빈 값으로 저장하면 메모 삭제.

### 표시 (`style.css`, 카드들)
- 메모 있는 카드: 제목 옆 **📝**(`.talk.has-note .talk-title::after`).
- My Plan **단독(전체폭) 카드**: 메모 내용도 노란 박스로 표시(겹침 그리드 카드는 잘림 방지로 📝만).
- Program 카드: 📝 표시(상세에서 편집).

## 검증

- `app.js` / 상세 인라인 스크립트 / timetable 스크립트 `node --check` 통과.
- 상세 페이지에 `#note` textarea 렌더 확인.

## 메모

- 메모 키는 talk id. 포스터 등 talk 없는 상세(abstract-only)는 메모 미지원.
- 데이터(서버)와 무관한 순수 클라이언트 기능 — 기기별.
