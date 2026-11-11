"""
[파일 역할]
  로컬에서 실행 중인 sLLM(small LLM, Llama 3.2 3B)을 Ollama 로 호출해
  사용자 질문을 3가지 레이블 중 하나로 분류한다.
  OpenAI Function Calling 분류기(llm_calling.classify_message)의 '로컬/저비용 대안'.

[연결 관계]
  - 호출: app/routers/chat.py 의 POST /chats/tunning 엔드포인트 (분류 결과만 반환하는 실험용)
  - 사용: 로컬 Ollama 서버(http://localhost:11434), 모델 llama3.2:3b
  - 관련: pinetunning/ 폴더의 LoRA 학습 결과를 Ollama 모델로 등록하면 이 분류기의 정확도가 향상된다.

[핵심 개념]
  - sLLM: 수십억(B) 파라미터 수준의 작은 언어 모델. 로컬/사내 서버에서 실행 가능
    → 데이터가 외부로 나가지 않음(보안), API 비용 없음, 대신 성능은 대형 모델보다 낮음.
  - Ollama: 로컬 LLM 실행 도구. REST API 제공
      POST /api/generate  {"model", "prompt", "stream"}
      stream=False → 토큰을 조금씩 보내지 않고 완성된 답변을 한 번에 JSON 으로 반환
  - Function Calling 미지원 모델은 '프롬프트로 출력 형식을 강제'하고 '후처리로 검증'한다.

[수업 포인트]
  - 작은 모델은 지시를 잘 안 따르므로(설명을 덧붙이는 등) 문자열 포함 여부로 레이블을 추출하는 후처리가 필수.
  - 이 한계를 해결하기 위한 것이 pinetunning/ 의 LoRA 파인튜닝.
"""

# 허용되는 출력 레이블(classification_list.TOOLS 의 함수 이름과 동일하게 맞춤)


def sllm_classifier(user_message: str) -> str:
    """
    Ollama 의 sLLM 으로 질문 의도를 분류한다.

    Args:
        user_message: 사용자 질문

    Returns:
        VALID_LABELS 중 하나. 모델 출력에서 레이블을 찾지 못하면 "응답불가합니다".

    Raises:
        requests.HTTPError: Ollama 가 4xx/5xx 를 반환한 경우(raise_for_status)
        requests.ConnectionError / Timeout: Ollama 서버 미실행 또는 응답 지연

    # ⚠️ 개선 포인트:
    #   - URL·모델명이 하드코딩되어 있다 → 환경변수(OLLAMA_URL, OLLAMA_MODEL)로 분리 권장.
    #   - "llama3.2:3b" 는 튜닝 전 '기본 모델'이다. LoRA 튜닝 효과를 보려면
    #     Modelfile 로 `ollama create <이름> -f Modelfile` 한 모델 이름으로 바꿔야 한다.
    #   - timeout=300(5분)은 웹 요청 기준으로 매우 길다. 사용자 대기/워커 점유 문제.
    #   - 동기 requests 호출이라 응답 대기 중 해당 워커가 블로킹된다.
    """
    # Few-shot 없이 '선택지 + 엄격한 출력 지시'만 주는 Zero-shot 분류 프롬프트
        # 모델이 이 뒤에 바로 레이블을 이어 쓰도록 유도

        # Ollama 기본 포트 11434
        # CPU 환경에서 첫 로딩/추론이 느릴 수 있어 넉넉히 설정
    # HTTP 오류면 예외 발생
    # Ollama 응답 JSON 의 생성 텍스트 필드
    # 후처리: 유효한 레이블 포함 여부 확인
    # 예) 모델이 "정답은 get_policy 입니다" 처럼 말해도 레이블을 추출할 수 있다
    pass  # TODO: 직접 구현해 보세요
