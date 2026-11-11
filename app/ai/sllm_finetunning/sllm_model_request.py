"""
[파일 역할]
  민감정보(회원 개인정보)가 포함된 데이터를 외부 API(OpenAI)로 보내지 않고,
  로컬 sLLM(Ollama, llama3.2:3b)으로 자연어 답변을 생성한다.

[연결 관계]
  - 호출: app/routers/chat.py → action == "get_my_profile" 분기
          generate_response_sllm(body.message, _format_profile(member))
  - 사용: 로컬 Ollama 서버(http://localhost:11434)

[핵심 개념]
  - 하이브리드 LLM 아키텍처: 일반 질문은 성능 좋은 클라우드 LLM, 민감 질문은 사내/로컬 sLLM.
    → 개인정보가 외부 서버로 전송되지 않아 개인정보보호(컴플라이언스) 측면에서 유리.
  - Ollama /api/generate 는 messages(역할 구분) 대신 단일 prompt 문자열을 받으므로
    system 지시 + 참고 데이터 + 질문을 하나의 텍스트로 구성한다.

[수업 포인트]
  - 같은 '근거 기반 답변' 프롬프트를 클라우드 LLM(generate_response)과 비교해 품질 차이 관찰.
  - 주의: 분류 단계(classify_message)에서는 '질문 원문'이 OpenAI 로 전송된다.
    개인정보 '데이터'만 로컬에서 처리된다는 점을 정확히 이해할 것.
"""


def generate_response_sllm(user_message: str, data: str) -> str:
    """
    로컬 sLLM 으로 참고 데이터 기반 답변을 생성한다.

    Args:
        user_message: 사용자 질문
        data: 회원정보를 포맷한 문자열(예: "- 회원번호: 1 / email: ... / 회원명: ... / age: ...")

    Returns:
        모델이 생성한 답변 원문(후처리 없음)

    Raises:
        requests.HTTPError / ConnectionError / Timeout: Ollama 오류·미실행·지연 시
        (호출부 chat.py 에 예외 처리가 없어 500 에러로 이어진다)

    # ⚠️ 개선 포인트:
    #   - URL/모델명 하드코딩 → 환경변수로 분리.
    #   - timeout=300 은 웹 응답 기준 과도함. 실패 시 대체 응답(fallback) 처리 필요.
    #   - .strip() 이 없어 앞뒤 공백/개행이 그대로 응답에 포함될 수 있다.
    """
        # 근거 데이터(개인정보) → 로컬에서만 처리

        # stream=False: 완성된 응답을 한 번에 받음 (True 면 줄 단위 JSON 스트림)
    pass  # TODO: 직접 구현해 보세요
