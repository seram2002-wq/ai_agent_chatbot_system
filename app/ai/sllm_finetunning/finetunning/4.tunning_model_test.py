"""
[파일 역할]  ── 파인튜닝 파이프라인 4단계: 튜닝 모델 vs 베이스 모델 비교 테스트
  같은 질문을
    (1) LoRA 튜닝·병합 모델(Hugging Face 에서 다운로드, transformers 로 직접 추론)
    (2) 튜닝 전 베이스 모델(로컬 Ollama 의 llama3.2:3b)
  에 각각 넣고 분류 결과를 비교해 파인튜닝 효과를 확인한다.

[연결 관계]
  - 입력: HF Hub 의 병합 모델(3단계 업로드 결과), 로컬 Ollama 서버
  - 비교 대상 함수 구조는 app/ai/sllm_pinetunning/sllm_classification.py 와 동일

[핵심 개념]
  - transformers 직접 추론 흐름:
      apply_chat_template(add_generation_prompt=True) → 토큰 ID 텐서
      → model.generate() → 새로 생성된 토큰만 decode
  - do_sample=False: 탐욕적(greedy) 디코딩 → 매번 확률이 가장 높은 토큰 선택(결정적, 분류에 적합)
  - torch.no_grad(): 추론 시 기울기 계산을 꺼서 메모리·속도 절약
  - model.eval(): 드롭아웃 등 학습 전용 동작 비활성화

[수업 포인트]
  - 테스트 질문 "세금계산서 발행 가능해?" 는 학습 데이터에 get_policy 로 들어있는 문장이다.
    → 베이스 모델은 틀리기 쉬운 애매한 질문이 튜닝 후 맞게 분류되는지 확인.
    (단, 학습에 쓴 문장으로 테스트하면 '암기' 여부만 확인될 뿐이므로, 학습에 없던 문장으로도 꼭 테스트할 것)

# ⚠️ 개선 포인트:
#   - from_pretrained 의 torch_dtype 인자는 최신 transformers 에서 dtype 으로 이름이 바뀌었다
#     (2단계 파일은 dtype 사용 → 일관성 위해 dtype 권장).
#   - 튜닝 모델은 학습 때 '질문만'(instruction) 입력으로 학습했는데, 테스트에서는 지시문이 포함된
#     긴 프롬프트를 넣는다. 학습/추론 입력 형식이 다르면 튜닝 효과가 제대로 측정되지 않는다.
#   - BASE_MODEL_ID 는 정의만 되고 사용되지 않는다.
#   - Ollama 호출에 timeout 이 없어 서버가 응답하지 않으면 무한 대기할 수 있다.
#   - 질문 1개로만 비교 → 여러 문장으로 정확도(accuracy)를 계산하는 평가 스크립트로 확장 권장.
"""

# 3단계에서 업로드한 병합 모델 저장소

# GPU/CPU 분기

# 모델 로드 (Merged Model)
# 병합 모델이므로 PEFT 없이 일반 모델처럼 바로 로드 가능 (최초 실행 시 수 GB 다운로드 후 캐시)
    # GPU: fp16 으로 메모리 절반 / CPU: fp16 연산 지원이 약하므로 float32
    # 모델 전체("")를 지정한 디바이스에 올림
# 추론 모드

# 병합(lora) 모델 답변 생성하기
def tunning_model_classify_message(user_message: str) -> str:
    """
    튜닝·병합 모델로 질문을 분류한다(transformers 직접 추론).

    Args:
        user_message: 테스트 질문

    Returns:
        VALID_LABELS 중 하나, 찾지 못하면 "응답불가합니다"
    """

        # 끝에 "assistant 차례" 헤더를 붙여 모델이 답변을 시작하게 함
        # PyTorch 텐서로 반환

    # 만약 encoded가 딕셔너리(BatchEncoding)라면 .input_ids를 쓰고, 아니면 그대로 사용
    # (transformers 버전에 따라 반환 타입이 달라 양쪽 모두 대응하는 방어 코드)

            # 레이블은 짧으므로 최대 32토큰만 생성
            # greedy 디코딩 → 결정적 출력
            # pad 토큰 미설정 경고 방지

    # outputs[0] 에는 '입력 프롬프트 + 생성 토큰'이 모두 들어있으므로
    # 입력 길이(input_tensor.shape[-1]) 이후의 새 토큰만 잘라서 디코딩
    pass  # TODO: 직접 구현해 보세요


# 튜닝 전 베이스 모델(ollama pull llama3.2:3b)
def base_model_classify_message(user_message: str) -> str:
    """
    튜닝 전 베이스 모델(Ollama)로 같은 프롬프트를 분류한다(비교 기준선, baseline).

    Returns:
        VALID_LABELS 중 하나, 찾지 못하면 "응답불가합니다"
    """
        # 완성된 응답을 한 번에 받음
    # 키가 없으면 빈 문자열(방어 코드)
    pass  # TODO: 직접 구현해 보세요


    # 같은 질문으로 두 모델의 결과를 나란히 비교 (정답: get_policy)
