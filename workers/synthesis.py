import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

WORKER_NAME = "synthesis_worker"

# System Prompt ép Agent phải trung thực (Grounded Answer)
SYSTEM_PROMPT = """Bạn là trợ lý hỗ trợ nội bộ thông minh.
Nhiệm vụ: Tổng hợp câu trả lời từ Context và Policy.

QUY TẮC:
1. CHỈ dùng thông tin được cung cấp. Không tự bịa.
2. Nếu thiếu context -> nói "Không đủ thông tin trong tài liệu nội bộ".
3. Trích dẫn nguồn cuối mỗi đoạn: [tên_file].
4. Nêu rõ Ngoại lệ (Policy Exceptions) ngay đầu câu trả lời nếu có.
"""

def _call_llm(messages: list) -> str:
    """Gọi OpenAI GPT - Giữ nguyên như Lab 8 của Giang"""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[SYNTHESIS ERROR] Lỗi API: {str(e)}"

def _build_context(chunks: list, policy_result: dict) -> str:
    """Xây dựng context string từ chunks và policy result"""
    parts = []
    
    # Thêm phần Policy trước để AI ưu tiên
    if policy_result and policy_result.get("exceptions_found"):
        parts.append("=== POLICY EXCEPTIONS (QUAN TRỌNG) ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- {ex.get('rule', '')} (Nguồn: {ex.get('source', '')})")

    # Thêm các đoạn văn bản tìm được
    if chunks:
        parts.append("\n=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            parts.append(f"[{i}] Nguồn: {source}\n{text}")

    return "\n\n".join(parts) if parts else "(Không có context)"

def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    """
    Ước tính độ tin cậy dựa trên điểm số Retrieval và Policy
    """
    if not chunks or "không đủ thông tin" in answer.lower():
        return 0.1

    # Tính trung bình score từ các chunk
    avg_retrieval_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    
    # Nếu có exception từ policy_tool, giảm nhẹ confidence vì đây là trường hợp đặc biệt
    penalty = 0.05 * len(policy_result.get("exceptions_found", []))
    
    confidence = avg_retrieval_score - penalty
    return round(max(0.1, min(0.95, confidence)), 2)

def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    """
    Hàm tổng hợp chính (Internal Pipeline)
    """
    context = _build_context(chunks, policy_result)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Câu hỏi: {task}\n\nNgữ cảnh:\n{context}\n\nHãy trả lời dựa trên tài liệu."}
    ]

    answer = _call_llm(messages)
    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {
        "answer": answer,
        "sources": sources,
        "confidence": confidence,
    }

def run(state: dict) -> dict:
    """
    Worker entry point - Điểm tiếp nhận chính từ Graph
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    # Ghi log lịch sử gọi worker
    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])

    try:
        # Gọi hàm xử lý logic
        result = synthesize(task, chunks, policy_result)
        
        # Cập nhật kết quả vào State chung
        state["final_answer"] = result["answer"]
        state["retrieved_sources"] = result["sources"] # Đồng bộ với các worker khác
        state["confidence"] = result["confidence"]
        
        state["history"].append(f"[{WORKER_NAME}] Đã tạo câu trả lời. Confidence: {result['confidence']}")

    except Exception as e:
        state["final_answer"] = f"Lỗi tổng hợp: {str(e)}"
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    return state

# --- Test độc lập ---
if __name__ == "__main__":
    print("--- Testing Synthesis Worker ---")
    test_state = {
        "task": "SLA P1 là bao lâu?",
        "retrieved_chunks": [{"text": "SLA cho P1 là 4 giờ làm việc.", "source": "sla_2026.txt", "score": 0.9}],
        "policy_result": {}
    }
    res = run(test_state)
    print(f"Answer: {res['final_answer']}")
    print(f"Confidence: {res['confidence']}")