"""
[파일 역할]
  RAG(Retrieval-Augmented Generation)의 'R(검색)' 단계.
  사용자 질문과 관련된 정책 문장을 벡터 DB 에서 찾아 하나의 문자열로 반환한다.
  세 가지 검색 방식을 학습용으로 함께 담고 있다.
    방법1. Dense Search (임베딩 유사도)        ← 현재 실제 동작
    방법2. Sparse Search (BM25 키워드)         ← 설명
    방법3. Hybrid Search (Dense + BM25 → RRF)  ← 주석 처리된 고도화 코드

[연결 관계]
  - 사용: vector_store.vector_store (pgvector), app.database.engine (BM25 용 원문 조회)
  - 호출: app/routers/chat.py → get_policy(및 기타) 분기에서 search_policy(body.message)
  - 결과 전달: llm_calling_langchain.generate_response_langchain(data=검색결과)

[핵심 개념]
  - RAG: LLM 이 모르는 사내 문서를 '검색'해서 프롬프트에 넣어준 뒤 답변을 '생성'하게 하는 기법.
    → 모델 재학습 없이 최신/사내 지식 반영, 환각 감소, 근거 제시 가능.
  - relevance score: PGVector 는 기본적으로 코사인 '거리'를 계산하고,
    LangChain 이 이를 relevance = 1 - distance 로 바꿔 0~1 사이 '관련도'로 돌려준다
    (1 에 가까울수록 관련 높음).
  - Dense vs Sparse vs Hybrid (아래 각 방법 주석 참고)
  - RRF(Reciprocal Rank Fusion): 점수 체계가 서로 다른 검색 결과를 '순위'만으로 합치는 방법.
    score(d) = Σ 1 / (k + rank_i(d)),  k=60 (논문 권장값)
    이 코드는 rank 를 0부터 세므로 1/(rank + k) 로 구현되어 있다(1위 → 1/60).

[수업 포인트]
  - 임계값(SIMILARITY_THRESHOLD)으로 '관련 없는 문서'를 걸러야 엉뚱한 근거로 답하지 않는다.
  - top_k, threshold, 검색 방식은 데이터 규모/성격에 맞춰 실험으로 정한다.
"""


# 1에 가까울수록 엄격한 필터링
# relevance score(=1-코사인거리)가 0.4 미만인 문서는 '관련 없음'으로 간주하고 버린다.
# 너무 높으면 → 정답 문서도 놓침(재현율↓), 너무 낮으면 → 무관한 문서까지 포함(정밀도↓)

def search_policy(query: str) -> str | None:
    """
    사용자 질문과 관련된 정책 문장을 검색한다.

    Args:
        query: 사용자 질문 원문

    Returns:
        관련 문장들을 줄바꿈으로 이어붙인 문자열.
        임계값 이상인 문서가 하나도 없으면 None.

    # ⚠️ 개선 포인트:
    #   - 첫 번째 return 이후의 코드(방법2·3 설명 및 주석 코드)는 실행되지 않는 '도달 불가 코드'다.
    #     학습용으로 보존한 것이며, 하이브리드 검색을 쓰려면 방법1 블록을 주석 처리하고
    #     방법3 블록의 주석을 해제한다.
    #   - None 반환 시 호출부(chat.py)에서 별도 처리 없이 LLM 에 그대로 넘긴다.
    #     README 에 적힌 "적절한 정책이 없습니다." 응답은 실제로 구현되어 있지 않다.
    """
    # 방법1. Dense Search (의미 기반 벡터 검색)
    # query를 임베딩으로 변환한 뒤 pgvector에서 유사한 문서를 검색. 최대 3개까지만 가져옴(top_k)
    # 장점: 의미적으로 유사한 문서를 찾음. "반품 어떻게 해?"로 검색해도 "환불 정책"을 찾아냄
    # 단점: 정확한 키워드가 있어도 벡터 거리가 멀면 놓칠 수 있음
    # 반환 형태: [(Document(page_content=..., metadata=...), score), ...]  (관련도 높은 순)
        # 디버깅: 점수 분포를 보며 임계값 튜닝
    # 리스트 컴프리헨션으로 임계값 이상인 문서의 '본문 텍스트'만 추출
        # 관련 문서 없음 → 호출부에서 처리
    # 여러 문장을 하나의 '참고 데이터' 문자열로 합침
    pass  # TODO: 직접 구현해 보세요

    # ───────────── 아래는 도달 불가(학습용) 코드 ─────────────

    # 방법2. Sparse Search - BM25 (키워드 기반)
    # 예시)"환불은 언제 가능해?"라는 질문을 ["환불", "언제", "가능"] 등으로 분해
    # DB에 저장된 "환불은 구매 후 30일 이내에 가능합니다." 문장을 ["환불", "구매", "30일", "가능"] 등으로 분해하여 단어마나 빈도수 점수화
    # 장점: 정확한 단어가 있을 때 정확도 향상. 고유명사, 날짜, 상품코드 등에 강함
    # 단점: "반품"으로 검색하면 "환불"이 있는 문서를 못 찾음
    # (BM25 = TF(단어 빈도) × IDF(희귀 단어 가중치) + 문서 길이 보정. 임베딩 API 호출이 필요 없음)

    # # 방법3. Hybrid Search (Dense + Sparse 결합)
    # # RRF(Reciprocal Rank Fusion) 알고리즘으로 두 방식의 순위를 결합
    # # 장점: 의미 기반 + 키워드 기반의 단점을 상호 보완. 프로덕션 환경(대규모코퍼스)에서 권장
    # # 단점: 구현 복잡도

    # 방법3-1. BM25 - 키워드 기반 문장 3개 추출
    # bm25_results = _get_bm25_results(query)

    # 방법3-2. Dense retriever  - 유사도 기반 문장 3개 추출 후 임계값 이상만 필터링
    # dense_results_with_scores = vector_store.similarity_search_with_relevance_scores(query, k=3)
    # dense_results = [doc for doc, score in dense_results_with_scores if score >= SIMILARITY_THRESHOLD]

    # 방법3-3. RRF로 BM25(최대3개) + Dense(최대3개) 결과를 합산 후 rerank
    # fused = _reciprocal_rank_fusion([bm25_results, dense_results])
    # print(fused)
    # relevant = [item["doc"].page_content for item in fused[:3]]   # 상위 3개만 사용

    # if not relevant:
    #     return None
    # return "\n".join(relevant)


# BM25 알고리즘
def _get_bm25_results(query: str) -> list:
    """
    BM25(키워드 기반) 검색으로 상위 3개 문서를 반환한다. (함수명 앞 '_' = 모듈 내부용 관례)

    Args:
        query: 검색 질의

    Returns:
        LangChain Document 리스트(최대 3개). 저장된 문서가 없으면 빈 리스트.

    # ⚠️ 개선 포인트:
    #   - 요청마다 langchain_pg_embedding 의 '전체 문서'를 읽고 BM25 인덱스를 새로 만든다.
    #     문서가 많아지면 매우 느려지므로, 서버 시작 시/문서 변경 시에만 인덱스를 재생성해 캐싱해야 한다.
    #   - BM25Retriever 기본 전처리는 '공백 기준 분리'라서 한국어 조사("환불은", "환불이")를
    #     다른 단어로 취급한다. Kiwi/Okt 같은 형태소 분석기를 preprocess_func 로 지정하는 것을 권장.
    """
    # engine.connect(): ORM 세션 없이 원시 SQL 실행. with 블록이 끝나면 연결 자동 반환
        # 원문 텍스트만 리스트로
    # 메모리 내 BM25 인덱스 생성
    # 상위 3개 반환
    pass  # TODO: 직접 구현해 보세요


def _reciprocal_rank_fusion(results_lists: list, k: int = 60) -> list:
    """
    여러 검색기의 결과 리스트를 RRF 로 합쳐 재정렬(rerank)한다.

    Args:
        results_lists: [검색기1 결과(Document 리스트), 검색기2 결과, ...] (각 리스트는 순위 순)
        k: 상위 순위의 영향력을 완화하는 상수(기본 60)

    Returns:
        [{"score": float, "doc": Document}, ...] 를 score 내림차순으로 정렬한 리스트.

    예) 문서 A: BM25 1위(rank0) + Dense 2위(rank1) → 1/60 + 1/61 ≈ 0.0331
        문서 B: Dense 1위만                          → 1/60        ≈ 0.0167
        → 두 검색기 모두에서 상위인 A 가 최종 1위
    """
    # RRF 알고리즘: 각 retriever의 순위를 1/(rank+k) 점수로 변환 후 합산
    # k=60은 RRF 논문에서 권장하는 기본값
        # rank 는 0부터 시작
            # 같은 문장이면 같은 문서로 보고 점수 누적(중복 제거 효과)
    pass  # TODO: 직접 구현해 보세요
