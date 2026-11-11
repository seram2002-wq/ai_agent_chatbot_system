"""
[파일 역할]  ── 파인튜닝 파이프라인 1단계: 학습 데이터 생성
  sLLM(Llama 3.2 3B)을 '의도 분류기'로 파인튜닝하기 위한 지도학습(SFT) 데이터를 만들어
  train_classification.jsonl 파일로 저장한다.

[파이프라인 전체 흐름]  (GPU 가 필요해 RunPod 등 클라우드 GPU 환경에서 실행)
  1.sllm_pinetunnig_data.py  → 학습 데이터(JSONL) 생성          ← 현재 파일
  2.sllm_lora_learnning.py   → LoRA 학습 + 베이스 모델과 병합
  3.tunning_model_upload.py  → Hugging Face Hub 업로드
  4.tunning_model_test.py    → 튜닝 모델 vs 베이스 모델 비교 테스트
  Modelfile                  → 병합 모델을 Ollama 모델로 등록(ollama create)

[연결 관계]
  - 출력 파일 train_classification.jsonl 을 2단계(DATA_PATH)가 읽는다.

[핵심 개념]
  - JSONL(JSON Lines): 한 줄에 JSON 객체 하나. 대용량 데이터를 한 줄씩 스트리밍 처리하기 좋다.
      {"instruction": "내 주문 내역 보여줘", "response": "get_my_orders"}
  - instruction(입력) / response(정답) 쌍 → 지도학습(Supervised Fine-Tuning, SFT) 데이터 형식.
  - 클래스 균형: 레이블별 샘플 수가 비슷해야 특정 레이블로 쏠리지 않는다.
      get_my_orders 82개 / get_my_profile 82개 / get_policy 90개 = 고유 샘플 254개
      × 3회 반복 = 총 762줄  (원본 주석의 '약 250 * 3 = 750' 은 근사치이며 정확히는 762)

[수업 포인트]
  - 같은 의미를 다양한 표현(구어체, 영어 섞기, 짧은 명사형 등)으로 작성하는 것이 데이터 품질의 핵심.
  - 경계가 애매한 예시(예: "배송 중인 주문 알려줘" → orders, "배송 언제 돼?" → policy)가
    분류 기준을 모델에 가르치는 중요한 데이터다.

# ⚠️ 개선 포인트:
#   - 아래 '데이터 양 불리기'는 같은 문장을 3번 복제할 뿐 진짜 증강(augmentation)이 아니다.
#     새로운 정보가 없어 epoch 를 3배 늘린 것과 비슷하며 과적합(암기) 위험이 커진다.
#     → 동의어 치환, 어순 변경, LLM 으로 패러프레이즈 생성 등으로 '서로 다른' 문장을 만들 것.
#   - 검증(validation)/테스트 세트 분리가 없어 학습이 잘 됐는지 객관적으로 측정할 수 없다.
#   - 출력 파일이 상대경로라 '스크립트를 실행한 현재 폴더'에 저장된다.
#   - 3개 레이블 외의 '무관한 질문' 예시가 없어, 튜닝 모델은 어떤 질문이든 3개 중 하나로 답하게 된다.
"""

# 분류 레이블: get_my_orders / get_my_profile / get_policy
# instruction: 사용자 질문, response: 분류 결과
# 각 항목은 {"instruction": 입력 질문, "response": 정답 레이블} 형태의 dict
    # ── get_my_orders (82개) : 본인 주문/구매/결제/배송 '내역' 조회 ──────────

    # ── get_my_profile (82개) : 본인 회원정보(이메일·이름·나이·ID 등) 조회 → 민감정보 ──

    # ── get_policy (90개) : 환불·교환·반품·배송·결제취소 등 '일반 정책' 질문 ──────


# 데이터 양 불리기
# 고유 샘플 254개를 3번 이어 붙임 → 762줄. (⚠️ 단순 복제이므로 실제 '증강'은 아님 - 상단 설명 참고)
# 약 250 * 3 = 750 samples  (정확히는 254 * 3 = 762)

# "w": 덮어쓰기 모드, encoding="utf-8": 한글 깨짐 방지
        # ensure_ascii=False: 한글을 \uXXXX 로 이스케이프하지 않고 그대로 저장(가독성)
        # 끝에 "\n" → JSONL 형식(한 줄에 객체 하나)
