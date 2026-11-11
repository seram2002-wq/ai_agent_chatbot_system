"""
[파일 역할]
  RAG 의 '지식 저장소'인 벡터 DB(PostgreSQL + pgvector)를 LangChain PGVector 객체로 초기화한다.
  서버 전체에서 공유하는 싱글턴 객체 `vector_store` 를 제공한다.

[연결 관계]
  - 사용: 환경변수 DATABASE_URL, OPENAI_API_KEY
  - 호출:
      · app/routers/document.py : add_texts(저장), delete(삭제) → 문서 관리 API
      · app/ai/rag/retriever.py : similarity_search_with_relevance_scores(검색)
  - 관련: semantic_cache.py 도 '같은 임베딩 모델'을 사용한다(벡터 공간 일치).

[핵심 개념]
  - 임베딩(Embedding): 문장을 의미를 담은 숫자 벡터로 변환한 것.
    의미가 비슷한 문장일수록 벡터 공간에서 가까이 위치한다.
    text-embedding-3-large → 3072차원 벡터 (정확도 높음, small 은 1536차원)
  - pgvector: PostgreSQL 에서 vector 타입과 유사도 연산(코사인/L2/내적)을 지원하는 확장.
    → 별도 벡터 DB(Pinecone, Chroma 등) 없이 기존 RDB 하나로 관계형 데이터 + 벡터 검색을 처리.
  - PGVector 객체 생성 시 자동으로 만들어지는 테이블 2개:
      1) langchain_pg_collection : 컬렉션(문서 묶음) 목록. 여기서는 "documents" 1개
      2) langchain_pg_embedding  : 실제 데이터
         (id[UUID], collection_id, embedding[vector], document[원문 텍스트], cmetadata[JSONB])

[수업 포인트]
  - 저장 시 임베딩 모델과 검색 시 임베딩 모델이 반드시 같아야 한다(차원/의미 공간 일치).
  - 드라이버 차이: SQLAlchemy 기본(psycopg2) vs langchain_postgres(psycopg3) → URL 스킴 변환.
"""

# langchain_postgres는 psycopg3 드라이버 사용 (postgresql+psycopg://)
# 같은 DB 를 쓰지만 app/database.py(psycopg2)와 드라이버가 달라 URL 접두어만 바꿔준다.
# 예) postgresql://user:pw@localhost:5432/db → postgresql+psycopg://user:pw@localhost:5432/db
# ⚠️ 개선 포인트: DATABASE_URL 이 없으면 빈 문자열("")이 되어 PGVector 생성 시
#    원인을 알기 어려운 연결 오류가 난다. 시작 시 값 존재 여부를 검증하는 것이 좋다.

# 임베딩 모델: 텍스트 → 3072차원 벡터. (OpenAI API 호출 = 비용 발생)

# PGVector객체가 만들어지는 시점에 아래 테이블2개가 자동으로 생성
# langchain_pg_collection(컬렉션 목록 테이블), langchain_pg_embedding(실제 데이터 테이블)
# langchain_pg_embedding : id, collection_id, embedding(vector), document(text) 컬럼으로 구성
# (pgvector 확장(CREATE EXTENSION vector)도 기본 설정으로 자동 생성 시도)

    # 저장/검색 시 사용할 임베딩 모델
    # psycopg3 형식 접속 URL
    # 컬렉션 이름(문서 그룹). 여러 지식베이스를 분리할 때 이름을 달리함
    # 메타데이터를 JSONB 로 저장(검색 필터에 유리, 권장 옵션)
