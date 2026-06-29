# 008. README + 앱바 버전 표시

- 날짜: 2026-06-29
- 상태: 완료

## 한 일

- `README.md` 작성: 프로젝트 개요, 데이터 파이프라인, 웹앱 실행, Docker/배포, 디렉토리.
- 앱바(페이지 타이틀)의 "STRATI 2026" 뒤에 **버전 표시**(`v0.1.1`).
  - `congress/context_processors.py`(`version`) 추가 → settings 등록 → 모든 템플릿에서 `{{ version }}`.
  - `config/version.py`의 단일 소스 사용.

## 검증

- 앱바에 `v0.1.1` 렌더 확인(테스트 컨테이너 재구동).

## 메모

- 코드 변경은 git 커밋. 이미지 재푸시는 미수행(현재 Hub `0.1.1`에는 버전 배지 미포함).
  운영 반영 필요 시 다음 릴리스에서 build/push.
