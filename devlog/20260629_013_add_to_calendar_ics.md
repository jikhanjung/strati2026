# 013. 캘린더 추가(.ics) + 5분 전 알림

- 날짜: 2026-06-29
- 상태: 완료(코드/테스트 서버). Hub 푸시 별도.

## 배경

"폰에서 스케줄 추가/알림" 요청. 로그인 없음 + localStorage 북마크 구조에선
**서버 웹푸시**는 구독·스케줄 저장 인프라가 필요해 과함. → **캘린더(.ics) 추가 + 캘린더 알림**으로 해결
(폰 캘린더에 넣으면 OS가 알림까지 처리).

## 한 일

- `GET /calendar.ics?ids=1,2,3` → `text/calendar` 첨부 다운로드.
  - VEVENT: Asia/Shanghai 시간을 UTC로 변환(`DTSTART/DTEND ...Z`), SUMMARY=제목,
    LOCATION=룸(층), DESCRIPTION=세션·제1저자.
  - **VALARM TRIGGER:-PT5M** (발표 5분 전 알림).
- 발표 상세: "📅 Add to Calendar" (단건).
- My Plan: "📅 Add all to Calendar" (JS가 북마크 id 전체로 href 구성).
- 휴식/점심은 캘린더에서 제외(발표만).

## 검증

- talk 10: `DTSTART:20260629T060000Z`(14:00 Shanghai), `DTEND ...062000Z`, `TRIGGER:-PT5M`.
- Content-Type text/calendar, attachment filename=strati2026.ics.
- 상세/ My Plan 버튼 렌더 확인.

## 메모

- iOS Safari/Android Chrome 모두 .ics 링크로 캘린더 추가 가능.
- 진짜 인앱 푸시 알림이 필요하면 Web Push(Service Worker+VAPID+구독 저장)로 별도 확장 가능(무거움).
