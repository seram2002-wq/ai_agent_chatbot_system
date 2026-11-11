"""
[파일 역할]
- 회원(member) 관련 API: 회원가입, 로그인(JWT 발급), 마이페이지 조회.

[엔드포인트]
    POST /members/signup  → 201, MemberResponse   (인증 불필요)
    POST /members/login   → 200, TokenResponse    (인증 불필요)
    GET  /members/me      → 200, MemberResponse   (Bearer 토큰 필요)

[연결되는 곳]
- app/main.py           : app.include_router(member.router)
- app/routers/chat.py   : my_page() 를 직접 호출해 챗봇의 "내 정보" 질의(get_my_profile)에 활용
- app/services/auth.py  : 해시/검증/토큰 발급
- app/dependencies.py   : get_db, get_current_member

[핵심 개념]
- 인증 흐름: signup(해시 저장) → login(비밀번호 검증 후 토큰 발급) → 이후 요청 헤더에 토큰 첨부
- db.add → db.commit → db.refresh: INSERT 후 DB 가 생성한 id/created_at 을 객체에 다시 채움

[수업 포인트]
- 로그인 실패 메시지를 "이메일 또는 비밀번호가 틀림"으로 통일 → 어떤 이메일이 가입됐는지 노출하지 않음(계정 열거 공격 방지)
"""


# prefix: 이 파일의 모든 경로 앞에 /members 가 붙음, tags: Swagger 에서 그룹 이름


@router.post("/signup", response_model=schemas.MemberResponse, status_code=status.HTTP_201_CREATED)
def signup(body: schemas.MemberCreate, db: Session = Depends(get_db)):
    """
    회원가입.

    HTTP: POST /members/signup → 201 Created
    Args:
        body: MemberCreate (email, password, name?, age?)
        db  : DB 세션
    Returns:
        생성된 Member (response_model 에 의해 password 는 응답에서 제외)
    Raises:
        HTTPException(400): 이미 가입된 이메일
        (422): 이메일 형식 오류 등 Pydantic 검증 실패 시 FastAPI 가 자동 반환
    """
    # 1) 이메일 중복 체크 (DB unique 제약도 있지만, 친절한 에러 메시지를 위해 먼저 확인)
    # 2) ORM 객체 생성 — 비밀번호는 반드시 해시해서 저장
    # 세션에 추가(아직 DB 반영 전)
    # INSERT 실행 + 트랜잭션 확정
    # DB 가 생성한 id, created_at 등을 다시 읽어옴
    pass  # TODO: 직접 구현해 보세요


@router.post("/login", response_model=schemas.TokenResponse)
def login(body: schemas.LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 → JWT 액세스 토큰 발급.

    HTTP: POST /members/login → 200 OK
    Returns:
        {"access_token": "<JWT>"}
    Raises:
        HTTPException(401): 이메일이 없거나 비밀번호 불일치
    """
    # 이메일 없음 / 비밀번호 틀림을 구분하지 않고 같은 401 메시지 반환 (보안)
    # sub 클레임은 JWT 표준상 문자열이어야 하므로 str() 변환
    pass  # TODO: 직접 구현해 보세요


@router.get("/me", response_model=schemas.MemberResponse)
def my_page(current_member: models.Member = Depends(get_current_member)):
    """
    마이페이지: 로그인한 본인 정보 조회.

    HTTP: GET /members/me → 200 OK  (Authorization: Bearer <token> 필요)
    Returns:
        현재 로그인한 Member
    Raises:
        HTTPException(401/403): 토큰 없음/무효 (get_current_member, HTTPBearer 에서 처리)

    참고: chat.py 에서 my_page(current_member=...) 처럼 일반 함수로도 호출됩니다.
          이때는 Depends 가 동작하지 않으므로 인자를 직접 넘겨줍니다.
    """
    # 인증 로직은 전부 의존성(get_current_member)에서 끝났으므로 그대로 반환만 하면 됩니다.
    pass  # TODO: 직접 구현해 보세요
