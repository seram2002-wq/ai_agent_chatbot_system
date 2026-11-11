"""
[파일 역할]
- 상품(product) 관련 API: 상품 등록, 상품 목록 검색(이름/카테고리 부분일치).

[엔드포인트]
    POST /products  → 201, ProductResponse       (Bearer 토큰 필요, 등록자 = 로그인 회원)
    GET  /products  → 200, List[ProductResponse] (인증 불필요, ?name=&category= 쿼리 파라미터)

[연결되는 곳]
- app/main.py : app.include_router(product.router)
- app/routers/order.py : 주문 시 Product 재고(stock) 확인/차감

[핵심 개념]
- body.model_dump(): Pydantic 모델 → dict 변환 (Pydantic v2 메서드, v1 의 .dict())
- **dict 언패킹: dict 의 key=value 를 키워드 인자로 펼쳐서 전달
- Optional 쿼리 파라미터: 함수 인자에 기본값 None → URL 쿼리스트링으로 자동 매핑
- ilike: 대소문자 무시 LIKE 검색 (PostgreSQL ILIKE). f"%{name}%" → 부분 일치

[수업 포인트]
- ⚠️ 개선 포인트: README 에 있는 "상품 상세 조회" API(GET /products/{product_id})가 구현되어 있지 않습니다.
                → 실습 과제로 추가해 보기 좋습니다. (없으면 404 HTTPException)
- 동적 쿼리 작성 패턴: query 객체에 조건을 하나씩 filter 로 이어 붙인 뒤 마지막에 .all()
"""


@router.post("", response_model=schemas.ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    body: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),  # 로그인 필수
):
    """
    상품 등록.

    HTTP: POST /products → 201 Created
    Args:
        body: ProductCreate (name, category, price, stock)
        current_member: 토큰으로 식별된 로그인 회원 → 상품 등록자(member_id)로 저장
    Returns:
        생성된 Product
    """
    # model_dump() 로 {"name":..., "category":..., "price":..., "stock":...} 를 만든 뒤
    # ** 언패킹으로 Product(name=..., category=..., ...) 처럼 전달. 등록자는 토큰 기반으로 서버가 지정(위조 방지)
    pass  # TODO: 직접 구현해 보세요


@router.get("", response_model=List[schemas.ProductResponse])
def list_products(
    name: Optional[str] = None,       # ?name=노트북
    category: Optional[str] = None,   # ?category=전자
    db: Session = Depends(get_db),
):
    """
    상품 목록 검색. 조건이 없으면 전체 목록을 반환합니다.

    HTTP: GET /products?name=...&category=... → 200 OK
    Args:
        name    : 상품명 부분 일치(대소문자 무시)
        category: 카테고리 부분 일치(대소문자 무시)
    Returns:
        List[Product]
    """
    # 아직 SQL 이 실행되지 않은 "쿼리 객체"
        # SQLAlchemy 가 파라미터 바인딩을 하므로 f-string 이어도 SQL Injection 에 안전합니다.
    # 수업 TIP: 데이터가 많아지면 offset/limit 페이지네이션을 추가해야 합니다.
    # 이 시점에 SELECT 실행
    pass  # TODO: 직접 구현해 보세요
