"""
[파일 역할]
- FastAPI 의 "의존성 주입(Dependency Injection)" 함수 모음입니다.
- get_db           : 요청 1건마다 DB 세션을 열고, 응답 후 반드시 닫아 줍니다.
- get_current_member: Authorization 헤더의 JWT 를 검증해 "로그인한 회원" 객체를 돌려줍니다.

[연결되는 곳]
- app/routers/*.py 의 엔드포인트 파라미터에서 `Depends(get_db)`, `Depends(get_current_member)` 로 사용
- app/services/auth.py 의 decode_access_token 으로 토큰 해석
- app/database.py 의 SessionLocal 로 세션 생성

[핵심 개념]
- Depends(): FastAPI 가 함수 실행 전에 의존 함수를 먼저 호출하고 결과를 인자로 넣어 줌
- yield 의존성: yield 이전 = 요청 전 처리, yield 이후(finally) = 응답 후 정리(cleanup)
- HTTPBearer: "Authorization: Bearer <token>" 헤더를 파싱. 헤더가 없으면 자동으로 403 응답
- 의존성 체인: get_current_member 가 다시 get_db, bearer_scheme 에 의존

[수업 포인트]
- Swagger(/docs) 우측 상단 "Authorize" 버튼은 bearer_scheme 덕분에 생깁니다.
- 인증이 필요한 API = 파라미터에 current_member: models.Member = Depends(get_current_member) 추가
"""

# 서명 불일치, 만료(ExpiredSignatureError 의 부모) 등 JWT 관련 예외의 부모 클래스


# Bearer 토큰 추출기. 요청 헤더 "Authorization: Bearer xxx" 에서 xxx 를 꺼내 줍니다.
# 헤더가 없거나 형식이 틀리면 FastAPI 가 403 Forbidden 을 자동 반환합니다.


def get_db():
    """
    요청 단위 DB 세션을 제공하는 제너레이터 의존성.

    동작 순서:
        1) SessionLocal() 로 새 세션 생성
        2) yield db  → 라우터 함수가 이 세션을 사용
        3) 응답이 끝나면(예외가 나도) finally 에서 db.close() 로 커넥션을 풀에 반납

    Yields:
        Session: SQLAlchemy 세션 객체
    """
        # 이 시점에 라우터 함수 실행
        # 커넥션 누수 방지 — 반드시 닫아야 커넥션 풀이 고갈되지 않음
    pass  # TODO: 직접 구현해 보세요


def get_current_member(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> models.Member:
    """
    JWT 액세스 토큰을 검증하고 해당 회원(Member) ORM 객체를 반환합니다.

    Args:
        credentials: HTTPBearer 가 파싱한 인증 정보 (credentials.credentials = 토큰 문자열)
        db: get_db 로 주입된 DB 세션

    Returns:
        models.Member: 토큰의 sub(회원 id)에 해당하는 회원

    Raises:
        HTTPException(401): 토큰이 위조/만료되었거나 sub 가 없을 때, 또는 회원이 DB에 없을 때
    """
        # 서명(SECRET_KEY) 검증 + 만료시간(exp) 검증. 실패하면 JWTError 발생
        # 로그인 시 create_access_token({"sub": str(member.id)}) 로 넣은 값
        # ⚠️ 개선 포인트: 타입힌트는 int 지만 실제 값은 str 입니다(JWT 표준상 sub 는 문자열).
        #               그래서 아래 쿼리에서 int(member_id) 로 변환하고 있습니다. `member_id: str` 로 쓰는 것이 정확합니다.
        # 서명 불일치, 만료, 형식 오류 등은 모두 401 로 통일 (공격자에게 상세 원인을 알리지 않음)

    # 토큰은 유효하지만 회원이 탈퇴/삭제되었을 수 있으므로 DB 에서 재확인
    # 라우터 함수의 current_member 파라미터로 전달됨
    pass  # TODO: 직접 구현해 보세요
