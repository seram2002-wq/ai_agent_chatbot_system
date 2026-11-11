"""
[파일 역할]
  llm_calling.py(OpenAI SDK 직접 호출)와 같은 기능을 LangChain 프레임워크로 구현한 버전.
    - classify_message_langchain         : bind_tools 를 이용한 의도 분류
    - generate_response_langchain        : 프롬프트 템플릿 + LCEL 체인으로 답변 생성
    - generate_response_langchain_memory : 이전 대화(history)를 함께 넣어 답변 생성

[연결 관계]
  - 사용: classification_list.TOOLS, 환경변수 OPENAI_API_KEY
  - 호출: app/routers/chat.py
          · generate_response_langchain → get_policy(RAG) 분기에서 현재 사용 중
          · generate_response_langchain_memory → 주석 처리(대화 메모리 실습용)
          · classify_message_langchain → 주석 처리(대안 분류기)
  - 연계: rag/memory.py 의 load_chat_history() 결과가 history 로 들어온다.

[핵심 개념]
  - LangChain: LLM 앱을 만들 때 모델/프롬프트/파서/검색기 등을 '부품'처럼 조립하는 프레임워크.
    모델 공급자(OpenAI, Anthropic, Google ...)를 바꿔도 나머지 코드는 거의 그대로 유지된다.
  - ChatPromptTemplate: {변수} 자리표시자가 있는 메시지 템플릿.
  - LCEL(LangChain Expression Language): `prompt | llm | parser` 처럼 파이프(|)로
    컴포넌트를 연결. 앞 단계의 출력이 다음 단계의 입력이 된다(유닉스 파이프와 유사).
  - StrOutputParser: 모델 응답 객체(AIMessage)에서 텍스트(content)만 꺼내 str 로 변환.
  - MessagesPlaceholder: 프롬프트 중간에 "메시지 리스트"를 통째로 끼워 넣는 자리.
    대화 기록(Human/AI 메시지 여러 개)을 넣을 때 사용.

[수업 포인트]
  - 같은 기능을 SDK 직접 호출 vs 프레임워크로 비교해 보며 장단점 토론.
  - 분류용 LLM(temperature=0)과 응답용 LLM(temperature=0.3)을 객체로 분리한 설계.
"""

# 분류 전용 모델: 결정적 출력을 위해 temperature=0

# 응답 생성 전용 모델: 약간의 자연스러움 허용(0.3)

# langchain에서는 아래와 같이 모델만 변경하면 쉽게 코드 리팩토링 가능
# llm_classify = ChatGoogleGenerativeAI(model="gemini-1.5-pro")
# llm_classify = ChatAnthropic(model="claude-opus-4-5")
# 모델이 바뀌어도 bind_tools(), invoke(), StrOutputParser() 등 나머지 코드는 그대로 사용 가능

# bind_tools: 모델에 도구 목록을 '묶어둔' 새 Runnable 을 만든다.
# 이후 invoke 할 때마다 tools 파라미터가 자동으로 함께 전송됨 (OpenAI SDK 의 tools=TOOLS 와 동일)


def classify_message_langchain(message: str) -> str:
    """
    LangChain bind_tools 로 사용자 질문의 의도를 분류한다.

    Args:
        message: 사용자 질문

    Returns:
        선택된 도구 이름(get_my_orders / get_my_profile / get_policy),
        도구를 고르지 않으면 "답변이 어려운 질문입니다."

    # ⚠️ 개선 포인트:
    #   - 현재 chat.py 에서는 주석 처리되어 사용되지 않는다(대안 구현 비교용).
    #   - 실패 시 안내 문구를 action 으로 반환하는 문제는 llm_calling.classify_message 와 동일.
    """
    # 문자열을 넣으면 LangChain 이 자동으로 HumanMessage 로 감싸서 전송
    # LangChain 은 공급자와 무관하게 표준화된 형태로 제공: [{"name": ..., "args": {...}, "id": ...}]
    # dict 접근(SDK 의 .function.name 과 비교)
    pass  # TODO: 직접 구현해 보세요


def generate_response_langchain(user_message: str, data: str) -> str:
    """
    참고 데이터 기반 답변을 LCEL 체인으로 생성한다. (RAG 의 Generation 단계)

    Args:
        user_message: 사용자 질문
        data: 검색된 정책 문장 등 참고 데이터
              (retriever.search_policy 가 관련 문서가 없으면 None 을 반환 → 프롬프트에 "None" 이 들어감)

    Returns:
        생성된 답변 문자열

    # ⚠️ 개선 포인트:
    #   - 호출할 때마다 ChatPromptTemplate 과 chain 을 새로 생성한다.
    #     템플릿은 고정이므로 모듈 레벨에서 1회만 만들어 재사용하는 것이 효율적.
    #   - data 가 None 일 때의 처리(예: "적절한 정책이 없습니다." 즉시 반환)가 없다.
    """
        # {data}, {user_message} 는 invoke 시 딕셔너리로 채워질 자리표시자
    #  LCEL(LangChain Expression Language)
    #  파이프 연산자로 컴포넌트를 연결하는 방식
    #  dict → prompt(메시지 리스트) → llm_response(AIMessage) → StrOutputParser(str)
    pass  # TODO: 직접 구현해 보세요


# history(메모리)와 함께 llm응답 생성
def generate_response_langchain_memory(user_message: str, data: str, history: list = None) -> str:
    """
    이전 대화 기록(history)까지 고려하여 답변을 생성한다. (Window Memory 실습용)

    Args:
        user_message: 현재 사용자 질문
        data: 참고 데이터(검색 결과). None 가능
        history: [HumanMessage, AIMessage, ...] 형태의 최근 대화 리스트(memory.load_chat_history 결과)

    Returns:
        생성된 답변 문자열

    예) 이전 턴: "환불은 며칠 이내야?" → "7일 이내입니다."
        현재 턴: "그럼 교환은?"  ← '그럼'이 무엇을 가리키는지 history 가 있어야 이해 가능
    """
    # 디버깅용 로그
            # 문자열 리터럴이 나란히 있으면 파이썬이 자동으로 이어 붙인다(암묵적 문자열 연결)
        # history : 이전 대화 기록을 system과 현재 질문 사이에 삽입
        # load_chat_history()로 가져온 HumanMessage/AIMessage 리스트 데이터
        # 최종 메시지 순서: system → (과거 user/ai 반복) → 현재 user
        # None이면 빈 문자열로 폴백
        # None이면 빈 리스트로 폴백
    pass  # TODO: 직접 구현해 보세요
