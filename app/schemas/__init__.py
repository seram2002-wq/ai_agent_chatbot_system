"""
[파일 역할]
- Pydantic 스키마(DTO) 모음입니다. API 의 "요청 바디 검증"과 "응답 형태 정의"를 담당합니다.
- 명명 규칙: XxxCreate / XxxRequest = 요청(입력), XxxResponse = 응답(출력)

[연결되는 곳]
- app/routers/*.py : 엔드포인트 파라미터 타입(body: schemas.MemberCreate) 및 response_model 로 사용

[핵심 개념]
- ORM 모델(models) vs 스키마(schemas) 분리 이유
  · models  = DB 구조 (password 해시 등 내부 정보 포함)
  · schemas = 외부에 노출할 API 계약. 예) MemberResponse 에 password 가 없으므로 응답에서 자동 제외
- response_model: 라우터가 ORM 객체를 반환해도 스키마에 정의된 필드만 골라 JSON 으로 직렬화
- from_attributes=True: dict 가 아닌 "객체 속성(member.id)"에서 값을 읽을 수 있게 허용 (ORM 객체 → 스키마 변환)
- EmailStr: 이메일 형식 자동 검증 (pydantic[email] 필요). 형식이 틀리면 422 Unprocessable Entity

[수업 포인트]
- ⚠️ 개선 포인트: 아래의 `class Config: from_attributes = True` 는 Pydantic v1 스타일 문법입니다.
  Pydantic v2 에서는 `model_config = ConfigDict(from_attributes=True)` 로 작성하는 것이 권장 방식입니다.
  (현재도 v2 에서 호환 동작하지만 deprecation 경고가 발생할 수 있음)
"""


# ──────────────────────────── Member ────────────────────────────
class MemberCreate(BaseModel):
    """회원가입 요청 바디 (POST /members/signup)."""
    # 이메일 형식 검증
    # 평문 비밀번호 → 라우터에서 bcrypt 해시 후 저장
    # 선택 입력
    # 선택 입력
    pass  # TODO: 직접 구현해 보세요


class MemberResponse(BaseModel):
    """회원 정보 응답 (가입 결과, GET /members/me). password 필드가 없어 응답에서 자동 제외됩니다."""

    class Config:
        # ORM 객체(models.Member)를 그대로 반환해도 변환 가능
        pass  # TODO: 직접 구현해 보세요


class LoginRequest(BaseModel):
    """로그인 요청 바디 (POST /members/login)."""
    pass  # TODO: 직접 구현해 보세요


class TokenResponse(BaseModel):
    """로그인 성공 응답. 클라이언트는 이후 요청 헤더에 'Authorization: Bearer <access_token>' 으로 전달."""
    pass  # TODO: 직접 구현해 보세요


# ──────────────────────────── Product ───────────────────────────
class ProductCreate(BaseModel):
    """상품 등록 요청 바디 (POST /products). 등록자(member_id)는 토큰에서 가져오므로 입력받지 않습니다."""
    pass  # TODO: 직접 구현해 보세요


class ProductResponse(BaseModel):
    """상품 응답 (등록 결과, 목록 검색)."""

    class Config:
        pass  # TODO: 직접 구현해 보세요


# ──────────────────────────── Order ─────────────────────────────
class OrderCreate(BaseModel):
    """주문 생성 요청 바디 (POST /orders). 주문자는 토큰의 로그인 회원."""
    # 수업 TIP: 현재 0 이나 음수도 통과합니다. Field(gt=0) 등으로 검증을 추가해 보는 실습을 해볼 수 있습니다.
    pass  # TODO: 직접 구현해 보세요


class OrderResponse(BaseModel):
    """주문 응답 (생성 결과, GET /orders/me)."""

    class Config:
        pass  # TODO: 직접 구현해 보세요


# ──────────────────────────── Chat ──────────────────────────────
class ChatRequest(BaseModel):
    """챗봇 질의 요청 바디 (POST /chats, POST /chats/tunning)."""
    # 사용자 자연어 질문 예) "내 주문 내역 보여줘", "환불 정책 알려줘"
    pass  # TODO: 직접 구현해 보세요


class ChatResponse(BaseModel):
    """챗봇 응답 = 저장된 Chat 레코드 (질문 + 응답 + 시각)."""

    class Config:
        pass  # TODO: 직접 구현해 보세요


# ──────────────────────────── Document (RAG) ────────────────────
class DocumentCreate(BaseModel):
    """벡터DB 문장 저장 요청 (POST /documents). 예) {"texts": ["환불은 구매 후 7일 이내 가능합니다."]}"""
    pass  # TODO: 직접 구현해 보세요

class DocumentResponse(BaseModel):
    """문장 저장 결과: 추가된 문장 수."""
    pass  # TODO: 직접 구현해 보세요

class DocumentChunk(BaseModel):
    """벡터DB 의 청크 1건 (GET /documents 목록, PUT /documents/{id} 결과)."""
    # langchain_pg_embedding의 UUID
    # 청크 텍스트 내용
    pass  # TODO: 직접 구현해 보세요

class DocumentChunkUpdate(BaseModel):
    """청크 수정 요청 바디 (PUT /documents/{chunk_id})."""
    # 수정할 새 텍스트 (기존 청크를 삭제하고 재임베딩 후 저장)
    pass  # TODO: 직접 구현해 보세요
