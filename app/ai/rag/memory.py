"""
[파일 역할]
  DB(chats 테이블)에 저장된 사용자의 최근 대화 N턴을 불러와
  LangChain 메시지 객체 리스트(HumanMessage/AIMessage)로 변환한다.
  → LLM 이 "이전 대화 문맥"을 이해하도록 돕는 '대화 메모리' 기능.

[연결 관계]
  - 사용: app/models.Chat (request=사용자 질문, response=AI 답변 저장 테이블)
  - 호출: app/routers/chat.py (현재 주석 처리, 메모리 실습 시 해제)
  - 결과 전달: llm_calling_langchain.generate_response_langchain_memory(history=...)

[핵심 개념]
  - LLM 은 기본적으로 Stateless(무상태): 이전 요청을 기억하지 못한다.
    → 이전 대화를 매 요청마다 프롬프트에 '다시 넣어줘야' 기억하는 것처럼 동작한다.
  - Window Memory(슬라이딩 윈도우 메모리): 전체 대화가 아닌 "최근 N턴"만 유지.
    · 전체 기록 → 토큰 비용 증가 + 컨텍스트 길이 초과 위험
    · 너무 적게 → 문맥 손실
  - 다른 방식: Summary Memory(오래된 대화를 요약), Vector Memory(관련 대화만 검색) 등.

[수업 포인트]
  - DB 를 메모리 저장소로 사용 → 서버 재시작/다중 서버에서도 대화 기록 유지.
  - 최신순으로 N개 가져온 뒤 reversed() 로 '시간순'으로 되돌리는 이유.
"""


# Window Memory 크기: 최근 N턴의 대화만 유지
# 너무 크면 토큰 비용 증가, 너무 작으면 문맥 손실
# 1턴 = 질문 1개 + 답변 1개 → 5턴이면 메시지 10개가 프롬프트에 추가됨


def load_chat_history(member_id: int, db: Session, limit: int = MEMORY_WINDOW) -> list:
    """
    특정 사용자의 최근 대화 기록을 LangChain 메시지 리스트로 반환한다.

    Args:
        member_id: 대화 기록을 조회할 회원 ID (다른 사용자의 대화가 섞이지 않도록 필터)
        db: SQLAlchemy 세션
        limit: 가져올 최대 턴 수 (기본 MEMORY_WINDOW=5)

    Returns:
        [HumanMessage, AIMessage, HumanMessage, AIMessage, ...] (오래된 → 최신 순)
        대화 기록이 없으면 빈 리스트.
    """

    # 테이블에서 특정 사용자의 최근 대화 기록 최신순으로 5개 조회
    # SQL: SELECT * FROM chats WHERE member_id=? ORDER BY created_at DESC LIMIT 5
        # 최신순 정렬해야 '최근' N개를 자를 수 있음

    # 반환값: [HumanMessage, AIMessage, HumanMessage, AIMessage] 형태의 리스트로 변환
    # 앞의 5개 중 오래된 것부터
        # 명확한 응답을 위해 두 주체의 대화의 구분이 필요
        # HumanMessage : 사용자가 보낸 메시지, AIMessage : AI(LLM)가 응답했던 메시지
        # → OpenAI API 로 전송될 때 각각 role="user", role="assistant" 로 변환된다
    pass  # TODO: 직접 구현해 보세요
