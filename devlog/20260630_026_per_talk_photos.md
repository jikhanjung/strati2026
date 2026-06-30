# 026. talk별 사진 첨부 (IndexedDB)

- 날짜: 2026-06-30
- 상태: 완료(코드/문법 검증). 런타임은 폰/브라우저에서 확인 필요(헤드리스 브라우저 미설치).

## 배경

메모(025)에 이어 발표별 사진(슬라이드/포스터 촬영)을 기기에 저장하고 싶다는 요청.
localStorage는 용량(~5–10MB)이 작아 부적합 → **IndexedDB**(Blob 저장, 대용량).

## 한 일

### 저장 (`static/app.js`)
- IndexedDB `strati` DB, `photos` 스토어(`keyPath:id autoIncrement`, `talkId` 인덱스).
- 빠른 "사진 보유" 조회용 localStorage 인덱스 `strati_photo_ids`(talkId 목록).
- API: `addPhotoFile(talkId,file)`(저장 전 최대변 1280px·JPEG 0.8로 축소), `getPhotos(talkId)`,
  `deletePhoto(photoId,talkId)`, `hasPhoto(id)`. `window.STRATI`에 노출.
- `refresh()`가 `has-photo` 클래스도 토글.

### 입력/조회 UI (`talk_detail.html`)
- "📷 Photos" 섹션 + "＋ Add photo"(`<input type=file accept=image/*>` — 모바일에서 카메라/앨범 선택).
- 추가 시 축소→IndexedDB 저장→썸네일 갱신. 썸네일 탭=라이트박스 확대, ×=삭제(확인).

### 표시 (`style.css`, 카드)
- 메모/사진 보유 표시를 제목 옆 이모지로(📝 / 📷 / 📝📷, `::after` 한 곳에서 조합).
- My Plan **단독(전체폭) 카드**: 사진 썸네일(최대 4장) 비동기 로드(겹침 그리드 카드는 잘림 방지로 제외).

## 검증

- `app.js` / 상세·timetable 인라인 스크립트 `node --check` 통과.
- 상세에 `#photo-input`·`#photo-strip` 렌더 확인.
- IndexedDB 동작은 브라우저 필요 → 테스트 서버에서 실기 확인 예정.

## 메모

- 기기 로컬·비동기. 동기화/백업 없음(브라우저 데이터 삭제 시 사라짐).
- HEIC 등 브라우저가 못 읽는 포맷은 "unsupported image" 알림.
- 정적파일은 manifest 해시 URL이라 배포 시 캐시 자동 무효화(entrypoint collectstatic).
