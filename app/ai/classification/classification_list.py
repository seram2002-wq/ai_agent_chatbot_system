"""
[파일 역할]
  LLM 의 Function Calling(도구 호출) 기능에 넘겨줄 "도구(함수) 목록" 정의 파일.
  사용자의 질문을 3가지 의도(intent) 중 하나로 분류하기 위한 '선택지 메뉴판' 역할을 한다.

[연결 관계]
  - llm_calling.py           : OpenAI SDK 의 tools=TOOLS 로 전달
  - llm_calling_langchain.py : LangChain 의 llm.bind_tools(TOOLS) 로 전달
  - routers/chat.py          : 분류 결과(함수 이름)에 따라 분기 처리
                               get_my_orders  → 주문 조회 API + GPT 응답
                               get_my_profile → 회원정보 조회 + 로컬 sLLM 응답(민감정보)
                               get_policy     → RAG(벡터 검색) + GPT 응답

[핵심 개념] Function Calling / Tools
  - 개발자가 "이런 함수들이 있어"라고 JSON Schema 형태로 알려주면,
    LLM 은 질문을 읽고 "이 함수를 호출하는 게 좋겠다"는 결정(tool_calls)을 반환한다.
  - LLM 이 함수를 '직접 실행'하는 것이 아니다! 어떤 함수를 부를지 '선택'만 하고,
    실제 실행은 우리 서버 코드(chat.py)가 한다.
  - 이 프로젝트는 함수의 실행보다는 "어떤 함수를 골랐는가 = 의도 분류 결과"로 활용한다.

[수업 포인트]
  - description 이 분류 정확도를 좌우한다. 예시 문구('내 주문', '주문 내역')를
    넣어주면 LLM 이 더 정확히 고른다. → 프롬프트 엔지니어링의 일종.
  - parameters 가 비어있는 이유: 로그인 사용자 정보는 서버가 JWT 로 이미 알고 있어
    LLM 에게서 받을 인자가 없기 때문.
"""

# OpenAI Chat Completions API 의 tools 파라미터 형식
# 각 항목: {"type": "function", "function": {name, description, parameters(JSON Schema)}}
            # name: LLM 이 선택 시 반환하는 식별자 → chat.py 에서 if 분기의 기준값
            # description: LLM 이 "언제 이 함수를 골라야 하는지" 판단하는 근거(가장 중요)
            # parameters: 함수 인자 스키마. 인자가 없으므로 빈 object
            # 민감정보(개인정보) 질문 → chat.py 에서 외부 API 가 아닌 로컬 sLLM 으로 응답 생성
            # 비구조화 질문(정책 문서) → RAG 검색으로 처리
