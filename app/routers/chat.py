"""
[파일 역할]
- AI 챗봇 API 의 "오케스트레이터(지휘자)" 입니다. 이 프로젝트의 핵심 파일.
- 사용자 질문 1건을 받아 ① 시맨틱 캐시 조회 → ② 의도 분류 → ③ 의도별 처리(API / sLLM / RAG)
  → ④ 캐시 저장 → ⑤ 대화 이력 DB 저장 순으로 응답을 만듭니다.

[엔드포인트]
    POST /chats          → 201, ChatResponse  (Bearer 토큰 필요) : 메인 챗봇
    POST /chats/tunning  → 200, {"action": ...} (Bearer 토큰 필요) : 파인튜닝 sLLM 분류기 테스트용

[처리 흐름]
    질문 ──▶ semantic_cache.search() ──HIT──▶ 캐시 응답 사용
                    │MISS
                    ▼
            classify_message() (OpenAI Function Calling)
              ├─ get_my_orders  → my_orders() → _format_orders() → generate_response() (OpenAI)
              ├─ get_my_profile → my_page()   → _format_profile() → generate_response_sllm() (로컬 Ollama)
              └─ 그 외(get_policy 포함) → search_policy() (pgvector RAG) → generate_response_langchain()
                    │
                    ▼
            semantic_cache.store()  →  Chat 테이블 저장 → 응답

[연결되는 곳]
- app/ai/classification/llm_calling.py   : classify_message, generate_response (OpenAI SDK 직접 사용)
- app/ai/rag/llm_calling_langchain.py    : LangChain 버전 분류/응답 (+ 메모리 버전)
- app/ai/rag/retriever.py                : search_policy (벡터 검색)
- app/ai/rag/memory.py                   : load_chat_history (최근 N턴 대화)
- app/ai/rag/semantic_cache.py           : Redis 기반 의미 유사도 캐시
- app/ai/sllm_pinetunning/*.py           : 로컬 sLLM(Ollama llama3.2) 응답/분류
- app/routers/order.py, member.py        : my_orders, my_page 를 함수로 재사용

[핵심 개념]
- Tool/Function Calling 기반 "의도 분류(Intent Classification)" → 라우팅
- RAG(Retrieval-Augmented Generation): 검색한 문서를 프롬프트에 넣어 환각(hallucination) 감소
- Semantic Cache: 문자열이 아닌 "의미"가 비슷한 질문이면 이전 응답 재사용 → 토큰 비용/지연 감소
- 민감정보 분리 처리: 개인정보는 외부 LLM API 로 보내지 않고 로컬 sLLM 으로 응답 생성

[수업 포인트]
- 주석 처리된 대안 코드(# action = classify_message_langchain ...)를 번갈아 켜 보며
  OpenAI SDK 직접 호출 vs LangChain, 단일턴 vs 멀티턴(메모리)을 비교 실습할 수 있습니다.
"""


# [의도 분류 + 응답 생성] OpenAI Python SDK 를 직접 사용하는 버전
# [RAG 검색] pgvector 유사도 검색으로 정책 문장 조회
# [LangChain 버전] 같은 기능을 LangChain(LCEL)으로 구현 — 비교용
# [대화 메모리] 최근 N턴 대화를 HumanMessage/AIMessage 리스트로 변환
# 다른 라우터의 엔드포인트 함수를 "일반 파이썬 함수"로 재사용

# [시맨틱 캐시] Redis Stack 벡터 검색 기반 캐시 (싱글톤)
# [sLLM 응답] 로컬 Ollama(llama3.2:3b) 서버에 요청 — 민감정보 응답용


@router.post("", response_model=schemas.ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_member: models.Member = Depends(get_current_member),
):
    """
    챗봇 질의 처리 (메인 엔드포인트).

    HTTP: POST /chats → 201 Created
    Args:
        body: ChatRequest (message: 사용자 질문)
        db  : DB 세션
        current_member: 로그인 회원 (캐시 분리, 주문/프로필 조회, 대화 저장에 사용)
    Returns:
        저장된 Chat 레코드 (id, member_id, request, response, created_at)
    Raises:
        HTTPException(401/403): 인증 실패
        (500): OpenAI/Ollama 호출 실패 등 처리되지 않은 예외
    """
    # 같은질문에 대한 캐싱 : redis stack에 같은 질문이 이력이 있는지 검색
    # 왜 분류보다 "먼저" 캐시를 볼까? → 캐시 HIT 시 분류 LLM 호출 + 응답 LLM 호출(최대 2회)을 모두 생략해
    #                               토큰 비용과 응답 지연을 크게 줄일 수 있기 때문입니다.
    #                               (단, 캐시 조회용 임베딩 API 호출 1회는 발생)
    # member_id 로 캐시를 분리 → A 회원의 "내 주문" 답변이 B 회원에게 나가는 사고를 방지
    # 히트 시: redis에 저장된 값으로 즉시 응답
    # 미스 시: 아래 else 분기 처리로 진행

        # ① 의도 분류: "get_my_orders" / "get_my_profile" / "get_policy" / "답변이 어려운 질문입니다." 중 하나
        # action = classify_message_langchain(body.message)   # ← LangChain 버전으로 교체 실습
        # ⚠️ 개선 포인트: 디버깅용 print 대신 logging 모듈(logger.info/debug)을 사용해야
        #               레벨별 출력 제어, 파일 저장, 운영 환경 로그 수집이 가능합니다.
            # ② -1 [일반 질문] 내 주문 조회
            # 라우터 함수를 직접 호출: FastAPI 를 거치지 않으므로 Depends 가 동작하지 않습니다.
            # → db, current_member 를 "명시적으로" 인자로 넘겨 의존성 주입을 우회(재사용)합니다.
            # ORM 객체 리스트 → LLM 이 읽기 쉬운 텍스트로 변환
            # 조회한 데이터를 "참고 데이터"로 넣어 OpenAI 가 자연어 답변 생성
            # response_text = generate_response_langchain(body.message, data)
        # 민감정보의 경우 sLLM을 통해 응답생성
            # ② -2 [민감 질문] 내 회원정보 조회
            # 설계 의도: 이메일/이름/나이 같은 개인정보를 외부 LLM API(OpenAI)로 전송하지 않고,
            #           로컬에서 실행되는 sLLM(Ollama) 으로 응답을 생성해 개인정보 외부 유출 위험을 줄입니다.
            #           (질문 문장 자체는 분류를 위해 OpenAI 로 전송된다는 점은 함께 짚어 주세요)
            # ② -3 [비구조화 질문] 정책(환불/교환/배송) → RAG
            # ⚠️ 개선 포인트: classify_message 가 "답변이 어려운 질문입니다."(분류 실패)를 반환해도 이 else 로 흘러와
            #               RAG 검색을 수행합니다. README 의 "그외 질문 → '답변이 어려운 질문입니다.'" 규칙과 불일치합니다.
            #               `elif action == "get_policy":` 로 분기하고, 마지막 else 에서 고정 문구를 반환하도록 개선할 수 있습니다.
            # ⚠️ 개선 포인트: search_policy 는 유사도 임계값을 넘는 문장이 없으면 None 을 반환합니다.
            #               그대로 프롬프트에 넣으면 "[참고 데이터]\nNone" 이라는 문자열이 들어갑니다.
            #               README 대로라면 `if context is None: response_text = "적절한 정책이 없습니다."` 처리가 필요합니다.
            # response_text = generate_response(body.message, context)
            # # 최근대화고려 작업(Window Memory): 응답시 최근 5턴 대화 기록을 함께 전달
            # history = load_chat_history(current_member.id, db)
            # response_text = generate_response_langchain_memory(body.message, context, history)

        # redis stack에 질문/응답을 저장
        # store: member_id 포함 (flush_by_member로 사용자별 선택 삭제 가능)
        # (캐시 MISS 일 때만 저장 → HIT 응답을 다시 중복 저장하지 않음)


    # ⑤ 대화 이력 저장 (캐시 HIT/MISS 모두 저장) → memory.py 의 멀티턴 대화, 이력 조회에 사용

    # response_model=ChatResponse 로 직렬화
    pass  # TODO: 직접 구현해 보세요


def _format_orders(orders: list) -> str:
    """
    주문 ORM 객체 리스트를 LLM 프롬프트용 텍스트로 변환합니다. (앞의 _ 는 "모듈 내부용" 관례)

    Args:
        orders: models.Order 리스트
    Returns:
        str: "- 주문번호: 1 / 상품ID: 3 / 수량: 2 / 주문일: 2026-01-01" 형식의 줄들. 없으면 안내 문구
    """
    # 수업 TIP: 상품ID 대신 o.product.name(relationship)을 쓰면 LLM 이 더 자연스러운 답변을 만들 수 있습니다.
    pass  # TODO: 직접 구현해 보세요


def _format_profile(member: list) -> str:
    """
    회원 ORM 객체를 sLLM 프롬프트용 텍스트로 변환합니다.

    Args:
        member: models.Member 객체
    Returns:
        str: "- 회원번호: 1 / email: ... / 회원명: ... / age: ..." 형식
    """
    # ⚠️ 개선 포인트: 타입힌트가 `list` 로 되어 있지만 실제로는 models.Member "단일 객체"가 들어옵니다.
    #               `member: models.Member` 로 수정하는 것이 정확합니다.
    pass  # TODO: 직접 구현해 보세요


# ──────────────────────────────────────────────────────────────────────
# [실험용] 파인튜닝(LoRA) sLLM 분류기 테스트 엔드포인트
# - 응답 생성 없이 "분류 결과(action)"만 반환합니다. GPT 분류기(classify_message)와 결과를 비교하는 용도.
# ⚠️ 개선 포인트: import 문이 파일 중간에 위치합니다. PEP 8 에 따라 파일 상단으로 옮기는 것이 좋습니다.
# ──────────────────────────────────────────────────────────────────────
@router.post("/tunning")
def create_chat_tunning(
    body: schemas.ChatRequest,
    db: Session = Depends(get_db),                                # 현재 미사용 (확장 대비)
    current_member: models.Member = Depends(get_current_member),  # 인증만 강제
):
    """
    sLLM 분류기 단독 테스트.

    HTTP: POST /chats/tunning → 200 OK
    Returns:
        {"action": "get_my_orders" | "get_my_profile" | "get_policy" | "응답불가합니다"}
    """
    # tunning 분류기 (로컬 Ollama 의 llama3.2:3b 호출)
    pass  # TODO: 직접 구현해 보세요
