"""
[파일 역할]
- FastAPI 애플리케이션의 "진입점(entry point)"입니다.
- 환경변수 로드 → DB 테이블 생성 → FastAPI 앱 생성 → 라우터 등록 순으로 서버를 조립합니다.

[연결되는 곳]
- 실행: `uvicorn app.main:app --reload`  (app 패키지의 main 모듈 안 `app` 변수)
- import: app.database(engine, Base), app.routers.*(member, product, order, chat, document)

[핵심 개념]
- load_dotenv(): .env 파일의 KEY=VALUE 를 os.environ 에 주입
- Base.metadata.create_all(): ORM 모델 정의를 보고 없는 테이블을 생성
- APIRouter / include_router(): 기능별로 나눈 엔드포인트를 하나의 앱에 합치기

[수업 포인트]
- "import 순서가 동작에 영향을 준다"는 대표 사례 (load_dotenv 위치)
- 서버 시작 시 /docs (Swagger UI) 에서 등록된 모든 API를 바로 테스트할 수 있음
"""

# .env 파일을 읽어 os.environ 에 등록합니다. 반드시 다른 app 모듈 import "이전"에 실행해야 합니다.
# 왜? database.py, services/auth.py, ai/* 모듈들은 "import 되는 순간" 모듈 최상단에서
#     os.getenv("DATABASE_URL"), os.getenv("OPENAI_API_KEY") 등을 실행합니다.
#     load_dotenv() 보다 import 가 먼저 일어나면 값이 None 이 되어 엔진/클라이언트 생성이 실패합니다.
# 모든 모듈 임포트 전에 .env 로드

# engine: DB 연결 엔진, Base: 모든 ORM 모델의 부모 클래스(메타데이터 보관)
# 각 라우터 모듈을 import 하면 그 안에서 app.models 도 import 되므로
# Base.metadata 에 Member/Product/Order/Chat 테이블 정보가 "등록"됩니다.
# (create_all 이 테이블을 알 수 있는 이유)
# document 라우터는 import 시점에 vector_store(PGVector), semantic_cache(Redis) 가 초기화됩니다.

# 재시작시 매번 테이블 재생성을 하려면 drop_all 주석해제
# (주의: drop_all 은 모든 데이터를 삭제합니다. 개발 초기 스키마 변경 시에만 사용)
# Base.metadata.drop_all(bind=engine)

# 모델 클래스에 정의된 테이블 중 DB에 "없는" 테이블만 생성합니다.
# ⚠️ 개선 포인트: create_all 은 이미 존재하는 테이블의 컬럼 추가/변경/삭제를 반영하지 않습니다.
#               운영 환경에서는 Alembic 같은 마이그레이션 도구로 스키마 이력을 관리하는 것을 권장합니다.

# FastAPI 앱 인스턴스. title 은 Swagger(/docs) 화면 상단에 표시됩니다.

# 기능별 라우터 등록. 각 라우터는 자체 prefix(/members, /products ...)와 tags 를 가지고 있습니다.
# /members  : 회원가입, 로그인, 마이페이지
# /products : 상품 등록, 목록 검색
# /orders   : 주문 생성, 내 주문 조회
# /chats    : AI 챗봇 (의도분류 → API/RAG/sLLM 응답)
# /documents: RAG용 문장 벡터DB 저장/조회/수정
