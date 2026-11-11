"""
[파일 역할]
- `app.routers` 패키지 표시용 파일(내용 없음).
- 각 모듈(member, product, order, chat, document)은 `router = APIRouter(prefix=..., tags=[...])` 를 정의하고,
  app/main.py 에서 app.include_router(xxx.router) 로 등록됩니다.

[수업 포인트]
- 기능(도메인)별로 라우터 파일을 나누면 파일이 작아지고, prefix/tags 로 URL 과 Swagger 문서가 자동 정리됩니다.
"""
