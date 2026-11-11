"""
[파일 역할]
- SQLAlchemy 를 이용한 PostgreSQL 연결 설정 모듈입니다.
- engine(연결 풀), SessionLocal(세션 팩토리), Base(ORM 모델 부모 클래스) 3가지를 제공합니다.

[연결되는 곳]
- app/main.py          : engine, Base 로 테이블 생성(create_all)
- app/models/__init__.py: Base 를 상속해 테이블 클래스 정의
- app/dependencies.py   : SessionLocal 로 요청마다 DB 세션 생성(get_db)
- app/ai/rag/retriever.py: engine 으로 직접 SQL 실행(BM25용 전체 문장 조회)

[핵심 개념]
- Engine  : DB 연결 정보 + 커넥션 풀. 애플리케이션 전체에서 1개만 생성해 공유
- Session : "작업 단위(Unit of Work)". add/commit/rollback/query 를 수행하는 객체
- declarative_base: 파이썬 클래스 ↔ DB 테이블 매핑(ORM)을 위한 기반 클래스

[수업 포인트]
- DATABASE_URL 형식: postgresql://user:password@host:5432/dbname
- autocommit=False → 명시적으로 db.commit() 해야 반영 (트랜잭션 제어)
- autoflush=False  → 쿼리 전에 자동 flush 하지 않음 (의도치 않은 INSERT/UPDATE 방지)
"""

# ⚠️ 개선 포인트: SQLAlchemy 2.0 부터 sqlalchemy.ext.declarative.declarative_base 는 deprecated 입니다.
#               `from sqlalchemy.orm import declarative_base` (또는 DeclarativeBase 클래스 상속) 사용을 권장합니다.

# .env 의 DATABASE_URL 값을 읽습니다. (main.py 에서 load_dotenv() 가 먼저 실행되어 있어야 함)
# 값이 없으면 None → create_engine(None) 에서 에러가 발생합니다.

# DB 엔진 생성: 실제 연결은 처음 쿼리할 때 맺어지며(lazy), 내부적으로 커넥션 풀을 관리합니다.
# psycopg2(동기 드라이버)를 사용합니다. (requirements.txt 의 psycopg2-binary)

# 세션 "팩토리": SessionLocal() 을 호출할 때마다 새 Session 객체를 만들어 줍니다.
# - autocommit=False: 변경사항은 commit() 호출 시에만 DB 에 반영
# - autoflush=False : query 실행 전 자동 flush 비활성화
# - bind=engine     : 이 세션이 사용할 DB 엔진 지정

# 모든 ORM 모델(Member, Product, Order, Chat)이 상속할 부모 클래스.
# Base.metadata 에 테이블 정의가 모이고, create_all/drop_all 이 이를 사용합니다.
