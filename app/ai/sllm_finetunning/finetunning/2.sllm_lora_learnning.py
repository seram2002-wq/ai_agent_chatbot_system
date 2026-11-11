"""
[파일 역할]  ── 파인튜닝 파이프라인 2단계: LoRA 학습 + 병합
  Llama-3.2-3B-Instruct 를 1단계에서 만든 분류 데이터로 LoRA 파인튜닝하고,
  학습된 어댑터를 베이스 모델에 병합(merge)해 단독 실행 가능한 모델로 저장한다.

[연결 관계]
  - 입력: train_classification.jsonl (1단계 결과)
  - 출력: ./llama32-3b-style-lora   (LoRA 어댑터: 수십~수백 MB)
          ./llama32-3b-style-merged (병합된 전체 모델: 수 GB)
  - 다음 단계: 3단계 업로드, Modelfile(FROM ./llama32-3b-style-merged)로 Ollama 등록

[핵심 개념]
  - 파인튜닝(Fine-tuning): 사전학습된 모델을 특정 작업 데이터로 추가 학습.
  - SFT(Supervised Fine-Tuning): (입력, 정답) 쌍으로 "이런 질문엔 이렇게 답해"를 가르치는 지도학습.
  - LoRA(Low-Rank Adaptation): 원본 가중치 W 는 얼려두고(freeze),
    옆에 작은 행렬 두 개(A: d×r, B: r×d)만 학습해 ΔW = B·A 를 더하는 방식.
      W' = W + (alpha / r) · B·A
    → 학습 파라미터 수가 전체의 1% 미만, GPU 메모리·시간 대폭 절감.
  - Chat Template: 모델마다 대화를 표현하는 특수 토큰 형식이 다르다(Llama 3 는 <|start_header_id|> 등).
    학습/추론 모두 같은 템플릿을 써야 모델이 제대로 이해한다.
  - Adapter vs Merged:
      Adapter = 변경분만 저장(가벼움, 베이스 모델이 별도로 필요, 재학습/백업용)
      Merged  = 베이스 + 어댑터를 합친 완성본(무거움, 단독 실행, Ollama/배포용)

[수업 포인트]
  - LoraConfig = "어디를/얼마나 크게 고칠지", SFTConfig = "어떻게/얼마나 오래 학습할지".
  - GPU 메모리 절약 기법: bf16, gradient checkpointing, gradient accumulation.

# ⚠️ 개선 포인트:
#   - CPU 분기(DTYPE=float32)가 있지만 SFTConfig 는 bf16=True 로 고정 → CPU 에서 실행하면 실패할 수 있다.
#     bf16=(DEVICE == "cuda") 처럼 조건부로 설정하는 것이 일관적이다.
#   - 폴더명 'style'(…-style-lora/merged)은 문체 학습 예제에서 가져온 이름으로, '분류' 작업과 맞지 않는다.
#   - eval_strategy="no" → 검증 데이터가 없어 과적합 여부를 확인할 수 없다(1단계의 단순 복제와 결합되면 위험).
#   - num_train_epochs=10 + 데이터 3배 복제 = 같은 문장을 사실상 30번 학습.
"""
# 가비지 컬렉터: 큰 모델 객체 삭제 후 메모리 즉시 회수
# Hugging Face 데이터셋 로더
# 토크나이저/언어모델 자동 로더
# PEFT: LoRA 등 경량 파인튜닝 라이브러리
# TRL: SFT 학습을 간편하게 해주는 트레이너

# 0. 기본 환경 설정
# Llama 3.2 는 Meta 의 'gated' 모델 → HF 사이트에서 사용 승인 + 토큰 로그인 필요

# LoRA 어댑터 저장 경로
# 병합 모델 저장 경로

# 모델 가중치를 메모리에 저장할 때 쓰는 데이터타입.
# GPU는 bfloat16 연산을 하드웨어에서 직접 지원하기 때문에 빠르고 메모리도 절약
# (bf16: 16비트지만 float32 와 같은 지수 범위 → fp16 보다 오버플로에 강해 학습이 안정적. 메모리는 float32 의 절반)
# CPU환경일때, 스레드 수 제한
# CPU가 1코어면 min(8, 1) → 1이 되는 거고, 만약 16코어면 min(8, 16) → 8로 제한


# 1. HF 로그인
def hf_login():
    """환경변수 HF_TOKEN 으로 Hugging Face 에 로그인한다(gated 모델 다운로드에 필요). 없으면 경고만 출력."""
    pass  # TODO: 직접 구현해 보세요

# 2-1). 모델 / 토크나이저 로드 : 텍스트를 모델이 이해할 수 있는 숫자(토큰 ID)로 변환하는 도구
def load_tokenizer():
    """
    베이스 모델의 토크나이저를 불러오고 패딩 설정을 보정한다.

    Returns:
        설정이 완료된 토크나이저
    """
    # Rust 기반 고속 토크나이저

    # pad_token 미설정 방지
    # 배치 학습 시 길이가 다른 문장을 같은 길이로 맞추려면 패딩 토큰이 필요한데,
    # Llama 는 기본 pad_token 이 없으므로 문장 끝 토큰(eos)을 패딩으로 재사용한다.

    # 학습 시에는 오른쪽 패딩이 일반적(생성/추론 배치에서는 왼쪽 패딩을 주로 사용)
    pass  # TODO: 직접 구현해 보세요


# 2-2). 기본 모델 불러오기
def load_base_model():
    """
    학습용 베이스 모델을 로드하고 메모리 절약 옵션을 켠다.

    Returns:
        AutoModelForCausalLM (다음 토큰 예측 = 텍스트 생성 모델)
    """
        # bf16(GPU) / float32(CPU)
        # 로딩 시 CPU RAM 사용량 최소화

    # use_cache: 추론 시 이전 토큰의 Key/Value 를 저장해 속도를 높이는 기능.
    # 학습 중에는 필요 없고, gradient checkpointing 과 충돌하므로 끈다.
    # Gradient Checkpointing: 중간 활성값을 모두 저장하지 않고 역전파 때 다시 계산
    # → GPU 메모리를 크게 절약하는 대신 학습 속도는 약 20~30% 느려짐(메모리 ↔ 시간 트레이드오프)
    pass  # TODO: 직접 구현해 보세요


# 2-3) 데이터 전처리 : 원본 컬럼(instruction, response) 제거 및 구조 변경
def load_and_prepare_dataset(tokenizer):
    """
    JSONL 을 읽어 각 샘플을 chat template 이 적용된 단일 'text' 컬럼으로 변환한다.

    Returns:
        datasets.Dataset (컬럼: text)
    """
    # load_dataset("json") 은 기본적으로 "train" split 하나를 만든다
        # 샘플 하나씩 변환
        # 기존 instruction/response 컬럼 제거 → text 만 남김
    pass  # TODO: 직접 구현해 보세요

def build_text(example, tokenizer):
    """
    (instruction, response) 한 쌍을 Llama 3 대화 형식 문자열로 변환한다.

    예) {"instruction": "내 정보 보여줘", "response": "get_my_profile"}
     → "<|begin_of_text|><|start_header_id|>user<|end_header_id|>\n\n내 정보 보여줘<|eot_id|>
        <|start_header_id|>assistant<|end_header_id|>\n\nget_my_profile<|eot_id|>" (개념적 예시)
    """

        # 토큰 ID 가 아닌 문자열로 반환(토큰화는 SFTTrainer 가 수행)
        # 정답(assistant)까지 이미 포함되어 있으므로 생성 프롬프트 불필요
    pass  # TODO: 직접 구현해 보세요

# 2. LoRA 학습
def train_lora():
    """토크나이저·모델·데이터를 준비하고 LoRA SFT 학습을 수행한 뒤 어댑터를 저장한다."""


    # 아래 LoraConfig와 SFTConfig는 대표적인 하이퍼파라미터(모델학습을 위해 개발자가 지정하는 값)

    # 어디(레이어)를 학습시킬지에 대한 설정
        # rank: 저차원 행렬의 크기. 클수록 표현력↑, 파라미터·메모리↑ (보통 8~64)
        # 스케일링 계수. 실제 반영 배율 = alpha / r = 128 / 32 = 4
        # LoRA 층에 5% 드롭아웃 → 과적합 완화
        # bias 파라미터는 학습하지 않음
        # 다음 토큰 예측(생성형) 작업
        # LoRA 를 붙일 레이어: 어텐션(q/k/v/o) + MLP(gate/up/down) 전부 → 효과는 크지만 학습량↑
        # (최소 구성은 q_proj, v_proj 만 대상으로 하기도 함)

    # 어느정도(얼마나)로, 어떤 방식으로 학습할지
        #몇 번 반복해서 학습할지 결정
        # GPU 1장이 한 번에 처리하는 샘플 수
        # 4번 모아서 1번 업데이트 → 유효 배치 = 4 × 4 = 16
        #입력데이터 최대 길이
        # A4500 (Ampere 아키텍처)은 bf16 지원
        # 데이터 로딩 병렬 프로세스 수
        # 여러 짧은 샘플을 한 시퀀스로 묶지 않음(분류 데이터는 짧아 단순하게)
        # LoRA 는 일반 전체 파인튜닝(1e-5 수준)보다 큰 학습률을 주로 사용
        # 매 스텝 loss 출력
        # epoch 마다 체크포인트 저장
        # 검증 없음 (⚠️ 상단 개선 포인트 참고)
        # AdamW 옵티마이저
        # 학습률을 코사인 곡선으로 서서히 감소 → 후반 미세 조정 안정
        # 처음 3% 스텝 동안 학습률을 0→2e-4 로 서서히 증가(초반 폭주 방지)
        # wandb 등 외부 로깅 비활성

    # SFTTrainer: 토큰화 + LoRA 적용(peft_config) + 학습 루프를 한 번에 처리
        # 이 설정으로 모델에 LoRA 어댑터를 자동 부착, 원본 가중치는 freeze
        # (구버전의 tokenizer= 인자에 해당)


    # LoRA 어댑터 가중치 저장
    # (전체 모델이 아니라 학습된 A·B 행렬만 저장 → adapter_model.safetensors, adapter_config.json)
    # 토크나이저 설정 저장 : 어뎁터를 다시 불러다 쓸때 같은 토크나이저 필요


    # 메모리 정리
    # 병합 단계에서 베이스 모델을 다시 올려야 하므로 학습 모델을 해제해 메모리 확보
    pass  # TODO: 직접 구현해 보세요


# 6. LoRA 병합
def merge_lora_to_base():
    """
    깨끗한 베이스 모델 위에 학습된 어댑터를 얹고 가중치를 합쳐(merge) 단독 모델로 저장한다.
    병합 후에는 PEFT 라이브러리 없이 일반 모델처럼 로드/서빙(Ollama, vLLM 등) 가능.
    """

    # 베이스 모델 + 어댑터를 결합한 PeftModel (아직은 W 와 B·A 가 분리된 상태)

    # merge_and_unload(): W' = W + (alpha/r)·B·A 를 실제로 계산해 가중치에 더하고 LoRA 층 제거
    # → 추론 시 추가 연산 없음

    # 폴더가 이미 있어도 오류 없이 진행

    # safe_serialization=True → .safetensors 형식으로 저장
    # (pickle 기반 .bin 과 달리 로딩 시 임의 코드 실행 위험이 없고 로딩도 빠름)

    # 병합 폴더 안에 tokenizer도 저장. 이후 해당 모델 실행시킬때 같은 토크나이저 사용

    # 메모리 정리
    pass  # TODO: 직접 구현해 보세요

# 0. 메인
def main():
    """전체 실행 순서: 로그인 → LoRA 학습 → 병합"""
    pass  # TODO: 직접 구현해 보세요

# 이 파일을 직접 실행할 때만 main() 수행(다른 파일에서 import 할 때는 실행 안 됨)
