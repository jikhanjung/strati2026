# 005. My Plan 저자·층 표시 + 이미지 푸시

- 날짜: 2026-06-29
- 상태: 완료

## 한 일

### My Plan(타임테이블) 개선
- 북마크한 발표에 **제1저자**와 **층** 표시.
- 룸 → 층 매핑(`ROOM_FLOOR`, `congress/models.py`): 핸드북 p28 Floor Plan 기준.
  - International Room I/II/III, Room 773/775/776 → **7F**
  - Kunshan Hall(개회/기조) → 3F
- `Talk.floor` 속성 추가, `/api/talks/` 페이로드에 `floor` 포함.
- My Plan 카드: 세션 배지 + 제1저자, 그 아래 `📍 room · floor`.
- 발표 상세: 룸 옆 `(7F)` 표시.

### Docker 이미지 푸시
- `honestjung/strati2026:0.1.0` + `latest` 빌드·푸시 완료.
- digest `sha256:7639bcf1…dcc77a39` (두 태그 동일, 위 변경 포함).

## 검증

- `/api/talks/` 샘플에 `author`, `floor:"7F"` 확인. 상세 "International Room I (7F)".
- 테스트 서버(m710q) 컨테이너 재빌드·재시작 후 live 반영.

## 메모

- 운영 배포는 호스트에서 `deploy.sh 0.1.0`로 수행(미실행).
- 남은 항목: 핸드북 잔여 메타(위원회·기조연사·답사), G18/S14 세션 제목, schema.sql, 운영 실제 배포.
