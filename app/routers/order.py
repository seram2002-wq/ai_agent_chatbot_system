"""
[파일 역할]
- 주문(order) 관련 API: 주문 생성(재고 차감), 나의 주문 내역 조회.

[엔드포인트]
    POST /orders     → 201, OrderResponse        (Bearer 토큰 필요)
    GET  /orders/me  → 200, List[OrderResponse]  (Bearer 토큰 필요)

[연결되는 곳]
- app/main.py         : app.include_router(order.router)
- app/routers/chat.py : my_orders() 를 직접 호출해 챗봇의 "내 주문" 질의(get_my_orders)에 활용
- app/ai/rag/semantic_cache.py : 주문 생성 시 해당 회원의 캐시 무효화(flush_by_member)

[핵심 개념]
- 트랜잭션: 재고 차감(UPDATE)과 주문 생성(INSERT)을 하나의 commit 으로 묶어 원자성 보장
- 캐시 무효화(Cache Invalidation): 데이터가 바뀌면 그 데이터로 만든 캐시 응답을 지워야 함

[수업 포인트]
- "캐시를 쓰면 반드시 무효화 전략도 함께 설계해야 한다"는 것을 보여주는 좋은 예시
"""


# 서버 시작 시 1회 생성된 싱글톤 캐시 객체


@router.post("", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(
    body: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    """
    주문 생성 (재고 차감 + 주문 저장 + 캐시 무효화).

    HTTP: POST /orders → 201 Created
    Args:
        body: OrderCreate (product_id, quantity)
        current_member: 주문자(로그인 회원)
    Returns:
        생성된 Order
    Raises:
        HTTPException(404): 상품이 존재하지 않음
        HTTPException(400): 재고 부족
    """
    # 1) 상품 존재 확인
    # ⚠️ 개선 포인트: 동시에 여러 주문이 들어오면 두 요청이 같은 재고를 읽고 각각 차감하는
    #               "경쟁 조건(Race Condition)"이 발생해 재고가 음수가 되거나 초과 판매될 수 있습니다.
    #               .with_for_update() 로 행 잠금(SELECT ... FOR UPDATE)을 걸거나,
    #               UPDATE products SET stock = stock - :q WHERE id=:id AND stock >= :q 같은 원자적 쿼리를 권장합니다.
    # 2) 재고 확인

    # 3) 재고 차감 — ORM 객체 속성만 바꾸면 commit 시 UPDATE 문이 자동 생성됨(dirty tracking)
    # 4) 주문 생성 — 주문자는 토큰 기반으로 서버가 지정
    # UPDATE(재고) + INSERT(주문)를 하나의 트랜잭션으로 확정

    # 주문 발생 시 해당 사용자의 캐시만 삭제
    # 왜? 이 회원이 이전에 "내 주문 내역 보여줘"라고 물어 캐시된 응답이 있다면,
    #     새 주문이 반영되지 않은 "옛날 답변"이 캐시 HIT 로 계속 나가게 됩니다(stale cache).
    #     다른 회원의 캐시는 영향이 없으므로 member_id 기준으로만 선택 삭제합니다.
    pass  # TODO: 직접 구현해 보세요


@router.get("/me", response_model=List[schemas.OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    """
    나의 주문 내역 조회.

    HTTP: GET /orders/me → 200 OK
    Returns:
        List[Order]: 로그인 회원의 전체 주문

    참고: chat.py 에서 my_orders(db=db, current_member=current_member) 로 일반 함수처럼 직접 호출됩니다.
    """
    # 본인 주문만 조회 (다른 사람의 주문을 볼 수 없도록 member_id 조건 필수)
    pass  # TODO: 직접 구현해 보세요
