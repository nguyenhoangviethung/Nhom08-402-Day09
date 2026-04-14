"""
workers/retrieval.py — Retrieval Worker
Tích hợp Dense, Sparse, Hybrid, Rerank và Query Transformation.
Sử dụng bkai-foundation-models/vietnamese-bi-encoder để khớp với DB đã index.
"""

import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv

import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder, SentenceTransformer

load_dotenv()

# =============================================================================
# CẤU HÌNH WORKER & DATABASE
# =============================================================================

WORKER_NAME = "retrieval_worker"
DEFAULT_TOP_K_SEARCH = 10
DEFAULT_TOP_K_SELECT = 3

CHROMA_DB_DIR = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "day09_docs")

# Cache embedding model để không bị load lại mỗi lần query
_embedding_model = None

def get_embedding(text: str) -> list:
    """Sử dụng đúng model local đã dùng ở file index.py"""
    global _embedding_model
    if _embedding_model is None:
        model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "bkai-foundation-models/vietnamese-bi-encoder")
        print(f"  [Retrieval] Đang load model embedding: {model_name}...")
        _embedding_model = SentenceTransformer(model_name)
    return _embedding_model.encode(text).tolist()


# =============================================================================
# CÁC CHIẾN LƯỢC TRUY XUẤT (RETRIEVAL)
# =============================================================================

def transform_query(query: str, strategy: str = "expansion") -> List[str]:
    """Biến đổi query để tăng recall bằng cách dùng LLM sinh ra các cách hỏi khác."""
    if strategy != "expansion":
        return [query]

    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        prompt = f"Given the Vietnamese query: '{query}', generate 2 alternative phrasings in Vietnamese. Output as JSON array of strings: [\"q1\", \"q2\"]"
        
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        # Lấy mảng kết quả từ JSON, nếu không có trả về list rỗng
        expanded = next((v for v in data.values() if isinstance(v, list)), [])
        return [query] + expanded
    except Exception as e:
        print(f"⚠️ Transform query failed: {e}")
        return [query]


def retrieve_dense(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Dense retrieval: So sánh cosine similarity của vector embedding."""
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    
    query_embedding = get_embedding(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "source": results["metadatas"][0][i].get("source", "unknown"),
                "score": round(1 - results["distances"][0][i], 4) # Distance trong Chroma là cosine distance
            })
    return chunks


def retrieve_sparse(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Sparse retrieval: Tìm kiếm theo keyword bằng thuật toán BM25."""
    client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    collection = client.get_collection(COLLECTION_NAME)
    all_data = collection.get(include=["documents", "metadatas"])
    
    if not all_data.get("documents"): 
        return []

    corpus = all_data["documents"]
    tokenized_corpus = [doc.lower().split() for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)
    
    tokenized_query = query.lower().split()
    doc_scores = bm25.get_scores(tokenized_query)
    
    top_indices = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
    
    return [{
        "text": corpus[i],
        "metadata": all_data["metadatas"][i],
        "source": all_data["metadatas"][i].get("source", "unknown"),
        "score": float(doc_scores[i])
    } for i in top_indices]


def retrieve_hybrid(query: str, top_k: int) -> List[Dict[str, Any]]:
    """Hybrid retrieval: Kết hợp Dense và Sparse bằng Reciprocal Rank Fusion (RRF)."""
    dense_results = retrieve_dense(query, top_k=top_k)
    sparse_results = retrieve_sparse(query, top_k=top_k)
    
    rrf_scores = {}
    
    # Tính điểm RRF cho Dense
    for rank, doc in enumerate(dense_results):
        rrf_scores[doc["text"]] = rrf_scores.get(doc["text"], 0) + 1.0 / (60 + rank)
        
    # Tính điểm RRF cho Sparse
    for rank, doc in enumerate(sparse_results):
        rrf_scores[doc["text"]] = rrf_scores.get(doc["text"], 0) + 1.0 / (60 + rank)
        
    # Sắp xếp lại dựa trên tổng điểm RRF
    sorted_texts = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    all_results = dense_results + sparse_results
    final_results = []
    for text, score in sorted_texts:
        match = next(d for d in all_results if d["text"] == text)
        match["score"] = round(score, 4) # Update score thành RRF score để theo dõi
        final_results.append(match)
        
    return final_results


def rerank(query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """Rerank bằng Cross-Encoder để chấm điểm Relevance chính xác hơn."""
    if not candidates: 
        return []
    
    try:
        # CrossEncoder chuyên dụng cho tiếng Việt/Đa ngôn ngữ
        model = CrossEncoder("BAAI/bge-reranker-v2-m3")
        pairs = [[query, c["text"]] for c in candidates]
        scores = model.predict(pairs)
        
        for i, chunk in enumerate(candidates):
            chunk["score"] = float(scores[i]) # Ghi đè score cũ bằng rerank score
        
        candidates = sorted(candidates, key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]
    except Exception as e:
        print(f"⚠️ Rerank failed: {e}. Đang trả về danh sách candidates ban đầu.")
        return candidates[:top_k]


# =============================================================================
# WORKER ENTRY POINT (Sử dụng bởi Graph)
# =============================================================================

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ Agent workflow.
    """
    task = state.get("task", "")
    
    # Lấy config cấu hình Pipeline
    retrieval_mode = state.get("retrieval_mode", "dense") # "dense", "sparse", "hybrid"
    use_rerank = state.get("use_rerank", False)
    use_transform = state.get("use_transform", False)
    top_k_search = state.get("top_k_search", DEFAULT_TOP_K_SEARCH)
    top_k_select = state.get("top_k_select", DEFAULT_TOP_K_SELECT)

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task, 
            "mode": retrieval_mode, 
            "rerank": use_rerank, 
            "transform": use_transform
        },
        "output": None,
        "error": None,
    }

    try:
        # 1. Transform Query
        queries = transform_query(task) if use_transform else [task]
        
        # 2. Retrieve (Search rộng)
        all_candidates = []
        for q in queries:
            if retrieval_mode == "dense":
                all_candidates.extend(retrieve_dense(q, top_k_search))
            elif retrieval_mode == "sparse":
                all_candidates.extend(retrieve_sparse(q, top_k_search))
            elif retrieval_mode == "hybrid":
                all_candidates.extend(retrieve_hybrid(q, top_k_search))
            else:
                raise ValueError(f"retrieval_mode không hợp lệ: {retrieval_mode}")

        # Khử trùng lặp (nếu Transform Query sinh ra nhiều cụm từ tìm ra cùng 1 text)
        seen = set()
        unique_candidates = []
        for c in all_candidates:
            if c["text"] not in seen:
                unique_candidates.append(c)
                seen.add(c["text"])

        # 3. Rerank & Select
        if use_rerank:
            chunks = rerank(task, unique_candidates, top_k_select)
        else:
            chunks = unique_candidates[:top_k_select]

        sources = list({c["source"] for c in chunks})

        # Cập nhật State
        state["retrieved_chunks"] = chunks
        state["retrieved_sources"] = sources

        worker_io["output"] = {
            "chunks_count": len(chunks), 
            "sources": sources
        }
        state["history"].append(
            f"[{WORKER_NAME}] mode={retrieval_mode}, retrieved {len(chunks)} chunks from {sources}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "RETRIEVAL_FAILED", "reason": str(e)}
        state["retrieved_chunks"] = []
        state["retrieved_sources"] = []
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# =============================================================================
# CHẠY TEST ĐỘC LẬP
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Retrieval Worker — Standalone Test")
    print("=" * 60)

    # Đảm bảo đã cài đủ thư viện nếu chạy test
    # pip install chromadb sentence-transformers rank-bm25 openai python-dotenv

    test_state = {
        "task": "SLA xử lý ticket P1 là bao lâu?",
        "retrieval_mode": "dense",  # Thử đổi thành "hybrid" hoặc "sparse"
        "use_rerank": False,        # Thử bật True nếu máy mạnh / có internet tải model rerank
        "use_transform": False,
        "top_k_search": 10,
        "top_k_select": 3
    }

    print(f"\n▶ Đang chạy test với cấu hình: {test_state}")
    
    result = run(test_state)
    
    chunks = result.get("retrieved_chunks", [])
    print(f"\n✅ Đã lấy ra {len(chunks)} chunks:")
    
    for idx, c in enumerate(chunks, 1):
        print(f"\n  [{idx}] Nguồn: {c['source']} | Score: {c['score']}")
        print(f"      Text: {c['text'][:150]}...")
        
    print(f"\n📄 Nguồn tài liệu: {result.get('retrieved_sources', [])}")