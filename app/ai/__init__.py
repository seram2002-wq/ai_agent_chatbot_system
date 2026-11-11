"""
[파일 역할]
  app.ai 패키지의 진입점(__init__.py).
  `from app.ai import classify_message, generate_response` 처럼 짧은 경로로
  자주 쓰는 함수를 꺼내 쓸 수 있도록 하위 모듈의 함수를 다시 내보낸다(re-export).

[연결 관계]
  - 사용: app/ai/classification/llm_calling.py 의 classify_message, generate_response
  - 참고: 현재 app/routers/chat.py 는 이 경로가 아닌 전체 경로
          (app.ai.classification.llm_calling)로 직접 import 하고 있다.

[핵심 개념]
  - 파이썬 패키지: 폴더 안에 __init__.py 가 있으면 그 폴더를 패키지로 인식한다.
  - __init__.py 는 패키지가 처음 import 될 때 '한 번' 실행된다.

[수업 포인트]
  - __init__.py 에서 import 를 하면 "패키지만 import 해도" 하위 모듈 코드가 실행된다는 점.

# ⚠️ 개선 포인트:
#   - 이 import 때문에 app.ai 하위의 어떤 모듈(예: app.ai.rag.retriever)을 import 해도
#     먼저 llm_calling.py 가 실행되어 OpenAI 클라이언트가 생성되는 부작용이 생긴다.
#     (OPENAI_API_KEY 가 없는 테스트 환경에서 의도치 않은 초기화/에러 가능)
#   - 필요하지 않다면 비워두거나, 지연 import(함수 안에서 import)를 고려한다.
"""

# 하위 모듈의 함수를 패키지 레벨로 끌어올림(re-export)
