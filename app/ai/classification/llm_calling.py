"""
[파일 역할]
  OpenAI 공식 Python SDK 를 "직접" 사용하여
    1) 사용자 질문의 의도를 분류하고 (classify_message)
    2) 참고 데이터를 바탕으로 자연어 답변을 생성한다 (generate_response)

[연결 관계]
  - 사용: classification_list.TOOLS (분류용 도구 목록), 환경변수 OPENAI_API_KEY
  - 호출: app/routers/chat.py
          · classify_message  → 모든 신규 질문의 1단계(의도 분류)
          · generate_response → get_my_orders 분기에서 주문 데이터를 자연어로 변환
  - 비교: rag/llm_calling_langchain.py 는 같은 기능을 LangChain 으로 구현한 버전

[핵심 개념]
  - Chat Completions API: messages(대화 목록)를 보내고 모델의 다음 메시지를 받는다.
    role 종류: system(행동 지침), user(사용자), assistant(모델 응답), tool(도구 결과)
  - temperature: 출력의 무작위성(창의성). 0 = 거의 결정적(같은 입력→같은 출력),
    높을수록 다양하지만 일관성이 떨어진다. 분류=0, 문장 생성=0.3 처럼 용도별로 다르게 설정.
  - tool_choice="auto": 모델이 도구를 호출할지 말지 스스로 판단.
    ("required" = 반드시 하나 호출, "none" = 호출 금지, 특정 함수 지정도 가능)

[수업 포인트]
  - "분류용 LLM 호출"과 "생성용 LLM 호출"을 분리하는 2-step 패턴.
  - 프롬프트에 참고 데이터를 주입하고 "없으면 응답불가"라고 지시 → 환각(hallucination) 억제.
"""
# 같은 패키지 내 상대 import

# 모듈이 import 되는 시점에 클라이언트를 1회 생성해 재사용(매 요청마다 생성하지 않음)
# main.py 에서 load_dotenv() 를 먼저 호출하므로 이 시점에 OPENAI_API_KEY 를 읽을 수 있다.


def classify_message(message: str) -> str:
    """
    사용자 메시지의 의도를 Function Calling 으로 분류한다.

    Args:
        message: 사용자가 입력한 질문 원문

    Returns:
        "get_my_orders" | "get_my_profile" | "get_policy" 중 하나(모델이 고른 함수 이름).
        모델이 어떤 도구도 고르지 않으면 "답변이 어려운 질문입니다." 문자열을 반환.

    # ⚠️ 개선 포인트:
    #   - 분류 실패 시 '안내 문구'를 action 값으로 반환한다. chat.py 는
    #     orders/profile 이 아니면 모두 else(RAG)로 보내므로, README 의
    #     "그 외 질문 → 답변이 어려운 질문입니다." 와 달리 실제로는 RAG 검색이 수행된다.
    #   - 상수(예: ACTION_UNKNOWN = "unknown")를 반환하고 호출부에서 명시적으로 처리하는 편이 안전.
    """
        # temperature는 분류 작업에 맞는 낮은 값으로 설정. 기본값은 1
        # 빠르고 저렴한 경량 모델 → 분류 작업에 적합
        # system 프롬프트 없이 사용자 질문만 전달. 분류 기준은 TOOLS 의 description 이 담당
        # 선택 가능한 함수 목록(메뉴판)
        # 도구 호출 여부를 모델이 판단 → 무관한 질문이면 호출 안 함
        # 분류는 "정답이 하나"인 작업 → 무작위성 제거
    # 응답 구조: response.choices[0].message.tool_calls = [ToolCall(function=Function(name=..., arguments=...)), ...]
        # 도구를 고르지 않음 = 3가지 의도 어디에도 해당하지 않는다고 판단한 경우
    # 여러 개를 고를 수도 있지만 첫 번째 선택만 사용
    pass  # TODO: 직접 구현해 보세요

def generate_response(user_message: str, data: str) -> str:
    """
    참고 데이터(data)를 근거로 사용자 질문에 대한 자연어 답변을 생성한다.

    Args:
        user_message: 사용자 질문 원문
        data: 서버가 조회한 근거 데이터(예: 주문 목록을 문자열로 포맷한 것)

    Returns:
        모델이 생성한 답변 문자열(앞뒤 공백 제거)
    """
                # system 메시지: 모델의 역할/규칙 + 근거 데이터 주입
                # → "근거 기반 답변(grounded answer)" 패턴. RAG 의 Generation 단계와 동일한 구조
        # 약간의 자연스러움은 허용하되 사실 왜곡은 최소화하는 낮은 값
    # 일반 텍스트 응답은 message.content 에 담긴다
    pass  # TODO: 직접 구현해 보세요
