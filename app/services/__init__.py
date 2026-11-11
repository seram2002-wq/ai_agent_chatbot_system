"""
[파일 역할]
- `app.services` 패키지 표시용 파일(내용 없음).
- services 계층은 라우터(HTTP 처리)와 분리된 "비즈니스 로직/유틸리티"를 두는 곳입니다. 현재는 auth.py(인증) 1개.

[수업 포인트]
- 계층 분리: routers(요청/응답) → services(로직) → models(DB). 로직이 커지면 라우터에서 services 로 옮기는 것이 좋습니다.
"""
