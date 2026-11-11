"""
[파일 역할]
- SQLAlchemy ORM 모델(= DB 테이블 정의) 모음입니다.
- members(회원) / products(상품) / orders(주문) / chats(챗봇 대화 이력) 4개 테이블.

[연결되는 곳]
- app/main.py         : Base.metadata.create_all() 로 테이블 생성
- app/dependencies.py : models.Member 조회 (현재 로그인 회원)
- app/routers/*.py    : 각 모델로 CRUD 수행
- app/ai/rag/memory.py: Chat 모델로 최근 대화 이력 조회(Window Memory)

[ERD 요약]
    Member 1 ──< N Product   (Product.member_id  → members.id, 상품 등록자)
    Member 1 ──< N Order     (Order.member_id    → members.id, 주문자)
    Product 1 ──< N Order    (Order.product_id   → products.id, 주문 상품)
    Member 1 ──< N Chat      (Chat.member_id     → members.id, 대화 주체)

[핵심 개념]
- Column / ForeignKey: 실제 DB 컬럼과 외래키 제약
- relationship + back_populates: 파이썬 객체 간 양방향 탐색 (member.orders ↔ order.member)
  → DB 컬럼이 생기는 것이 아니라 ORM 레벨의 편의 기능
- default=lambda: ... : INSERT 시점마다 함수를 호출해 값 생성 (lambda 없이 쓰면 서버 시작 시각으로 고정됨!)

[수업 포인트]
- RAG 문서 테이블(langchain_pg_embedding)은 여기서 정의하지 않고 langchain_postgres 가 자동 생성합니다.
"""

# ⚠️ 개선 포인트: Enum 은 import 되었지만 사용되지 않습니다. (아래 import enum 도 마찬가지)
# ⚠️ 개선 포인트: pgvector 의 Vector 타입이 import 되었지만 어떤 모델에서도 사용하지 않습니다.
#               (벡터는 langchain_postgres 의 langchain_pg_embedding 테이블에 저장됨) 불필요한 import 는 제거 권장.


class Member(Base):
    """
    회원 테이블(members).

    컬럼:
        id         : PK, 자동 증가
        email      : 로그인 ID, 중복 불가(unique) + 검색 속도를 위한 index
        password   : bcrypt 해시 문자열 (평문 저장 금지!)
        name, age  : 선택 입력 (nullable=True)
        created_at : 가입 시각(UTC)
    관계:
        products : 내가 등록한 상품 목록
        orders   : 내 주문 목록
        chats    : 내 챗봇 대화 이력
    """
    # 실제 DB 테이블명

    # unique → 동일 이메일 중복 가입을 DB 레벨에서도 방지
    # services/auth.hash_password() 결과가 저장됨
    # lambda 로 감싸야 "행이 INSERT 될 때마다" 현재 시각을 계산합니다.
    # ⚠️ 개선 포인트: DateTime 컬럼은 기본 timezone=False(시간대 정보 없음)인데, timezone-aware(UTC) 값을 넣고 있습니다.
    #               PostgreSQL 에 저장될 때 시간대 정보가 버려집니다. DateTime(timezone=True) 로 맞추는 것을 권장.

    # back_populates 는 반대쪽 모델의 relationship 속성 이름과 짝을 이뤄야 합니다.
    pass  # TODO: 직접 구현해 보세요


class Product(Base):
    """
    상품 테이블(products).

    컬럼:
        name, category : 상품명/카테고리 (목록 검색 조건으로 사용)
        price          : 가격 (Float)
        stock          : 재고 수량 (주문 시 차감)
        member_id      : 등록자 FK → members.id
    관계:
        registrant : 상품을 등록한 Member
        orders     : 이 상품에 대한 주문 목록
    """

    # 수업 TIP: 금액은 부동소수점 오차가 있으므로 실무에서는 Numeric(Decimal) 또는 정수(원 단위)를 주로 사용합니다.
    # 존재하지 않는 회원 id 는 DB가 거부
    pass  # TODO: 직접 구현해 보세요


class Order(Base):
    """
    주문 테이블(orders). 회원과 상품의 N:M 관계를 연결하는 "연결 테이블" 역할도 합니다.

    컬럼:
        member_id  : 주문자 FK
        product_id : 주문 상품 FK
        quantity   : 주문 수량
    """
    pass  # TODO: 직접 구현해 보세요


class Chat(Base):
    """
    챗봇 대화 이력 테이블(chats).

    컬럼:
        request  : 사용자가 보낸 질문
        response : 챗봇 응답 (캐시 HIT 응답 포함)
    활용:
        - POST /chats 처리 후 매 대화를 저장
        - app/ai/rag/memory.py 에서 최근 N턴을 불러와 LLM 프롬프트에 history 로 전달(멀티턴 대화)
    """

    # memory.py 에서 최신순 정렬 기준
    pass  # TODO: 직접 구현해 보세요
