"""
[파일 역할]  ── 파인튜닝 파이프라인 3단계: Hugging Face Hub 업로드
  2단계에서 만든 LoRA 어댑터와 병합 모델을 Hugging Face Hub 저장소에 업로드한다.
  → GPU 서버(RunPod)에서 학습한 결과물을 로컬 PC 로 옮기기 위한 '중간 저장소' 역할.

[연결 관계]
  - 입력: ./llama32-3b-style-lora, ./llama32-3b-style-merged (2단계 결과)
  - 다음: 4단계(4.tunning_model_test.py)가 merged 저장소를 from_pretrained 로 다운로드해 테스트

[핵심 개념]
  - Hugging Face Hub: 모델/데이터셋을 Git 기반으로 저장·공유하는 플랫폼(모델계의 GitHub).
  - HfApi.create_repo(exist_ok=True): 저장소가 없으면 생성, 있으면 그대로 사용.
  - upload_folder: 폴더 전체를 업로드(대용량 파일은 내부적으로 LFS/Xet 처리).

[수업 포인트]
  - 어댑터(가벼움, 백업·재학습용) vs 병합 모델(무거움, 바로 실행용)을 '둘 다' 올리는 이유.
  - 업로드 전 `huggingface-cli login` 또는 HF_TOKEN(쓰기 권한) 설정이 필요하다.

# ⚠️ 개선 포인트:
#   - HF_ID 가 특정 개인 계정으로 하드코딩되어 있다 → 수강생은 본인 ID 로 변경하거나 환경변수로 분리.
#   - 쓰기 권한 토큰이 필요하다(로그인 안 되어 있으면 create_repo 단계에서 401 오류).
#   - create_repo 기본값은 public 저장소 → 사내 데이터로 학습한 모델이면 private=True 를 고려.
#   - import os 는 사용되지 않는다.
"""

# 로그인된 토큰(캐시 또는 HF_TOKEN)을 자동으로 사용
# 허깅페이스 ID

# 1. LoRA 어댑터(Adapter) 업로드 - 백업 및 재학습용
# 저장소 ID 형식: "사용자명/저장소명"

    # SFTTrainer 가 epoch 마다 저장한 중간 체크포인트·로그는 용량만 크고 불필요 → 제외
    # 불필요한 파일 제외

# 2. 병합 모델(Full Model) 업로드 - 로컬 CPU PC 테스트용
