# 039. Unlink vs Reset 라벨·설명 명확화

- 날짜: 2026-06-30
- 상태: 완료(테스트 서버 0.1.37 반영).

## 배경

"This device의 Unlink와 Reset this device 기능이 같냐"는 질문 → 둘은 정반대(데이터 유지 vs 삭제).
혼동 방지를 위해 라벨·설명·확인 문구를 다듬어 달라는 요청.

## 차이 (정리)

- **Unlink (이 기기)** = `unlinkThisDevice()`: 그룹에서 빠지되(새 솔로 토큰) **북마크·메모는 이 기기에 유지**.
- **Reset** = `resetLocal()`: 이 기기의 **북마크·메모·동기화 신원을 모두 삭제**(빈 상태). 다른 기기·서버 버킷은 영향 없음.

## 한 일 (`settings.html`)

- 이 기기 줄 버튼: "Unlink" → **"Unlink (keep data)"** (다른 기기는 "Unlink" 유지).
- Reset 버튼: "Reset this device" → **"Reset (erase this device)"**.
- 기기 섹션 하단 설명: Unlink=데이터 유지 / Reset=삭제 / 다른 기기 무영향 을 명시.
- 확인 대화상자 3종(이 기기 Unlink·다른 기기 Unlink·Reset) 문구를 동작에 맞게 보강.

## 검증

- 설정 JS `node --check`, `manage.py check` 통과. 라벨 렌더 확인.
