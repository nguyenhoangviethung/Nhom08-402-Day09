"""
workers/synthesis.py — Synthesis Worker
Tạo câu trả lời cuối cùng dựa trên context và policy analysis. Áp dụng Strict Prompting từ OpenAI.
"""

import os
from openai import OpenAI

WORKER_NAME = "synthesis_worker"

SYSTEM_PROMPT = """Bạn là trợ lý IT/CS Helpdesk nội bộ.

Quy tắc nghiêm ngặt:
1. CHỈ trả lời dựa vào context được cung cấp. KHÔNG dùng kiến thức ngoài.
2. Nếu context không đủ để trả lời → nói rõ "Không đủ thông tin trong tài liệu nội bộ".
3. Trích dẫn nguồn (ví dụ: [policy_v4.txt]) khi đưa ra thông tin quan trọng.
4. Trả lời súc tích, cấu trúc rõ ràng (bullet points nếu cần).
5. Nếu Policy Exceptions có tồn tại, PHẢI nêu rõ ngoại lệ này ở ngay đầu câu trả lời.
"""

def _call_llm(messages: list) -> str:
    """Gọi LLM (OpenAI) để tổng hợp câu trả lời."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=messages,
            temperature=0.1,  # Low temp để grounded
            max_tokens=512,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[SYNTHESIS ERROR] Không thể gọi LLM. Chi tiết lỗi: {e}"

def _build_context(chunks: list, policy_result: dict) -> str:
    """Đóng gói context block tương tự build_context_block trong rag_answer."""
    parts = []

    if chunks:
        parts.append("=== TÀI LIỆU THAM KHẢO ===")
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            score = chunk.get("score", 0)
            parts.append(f"[{i}] Nguồn: {source} (score: {score})\n{text}")

    if policy_result and policy_result.get("exceptions_found"):
        parts.append("\n=== POLICY EXCEPTIONS ĐÃ PHÁT HIỆN ===")
        for ex in policy_result["exceptions_found"]:
            parts.append(f"- Ngoại lệ: {ex.get('type')} -> {ex.get('rule')}")

    if not parts:
        return "(Không có context nào được tìm thấy)"

    return "\n\n".join(parts)

def _estimate_confidence(chunks: list, answer: str, policy_result: dict) -> float:
    """Tính toán logic confidence score."""
    if not chunks:
        return 0.1

    if "Không đủ thông tin" in answer or "không có trong tài liệu" in answer.lower() or "không biết" in answer.lower():
        return 0.2

    # Lấy điểm trung bình của top chunks
    avg_score = sum(c.get("score", 0) for c in chunks) / len(chunks)
    
    # Policy exception làm phức tạp vấn đề, trừ một chút confidence
    exception_penalty = 0.05 * len(policy_result.get("exceptions_found", []))
    
    confidence = min(0.98, avg_score - exception_penalty)
    return round(max(0.1, confidence), 2)

def synthesize(task: str, chunks: list, policy_result: dict) -> dict:
    context = _build_context(chunks, policy_result)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Câu hỏi: {task}\n\n{context}\n\nAnswer:"}
    ]

    answer = _call_llm(messages)
    sources = list({c.get("source", "unknown") for c in chunks})
    confidence = _estimate_confidence(chunks, answer, policy_result)

    return {"answer": answer, "sources": sources, "confidence": confidence}

def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    policy_result = state.get("policy_result", {})

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks), "has_policy": bool(policy_result)},
        "output": None, "error": None,
    }

    try:
        result = synthesize(task, chunks, policy_result)
        state["final_answer"] = result["answer"]
        state["sources"] = result["sources"]
        state["confidence"] = result["confidence"]

        worker_io["output"] = {
            "answer_length": len(result["answer"]),
            "sources": result["sources"],
            "confidence": result["confidence"],
        }
        state["history"].append(f"[{WORKER_NAME}] confidence={result['confidence']}, sources={result['sources']}")

    except Exception as e:
        worker_io["error"] = {"code": "SYNTHESIS_FAILED", "reason": str(e)}
        state["final_answer"] = f"SYNTHESIS_ERROR: {e}"
        state["confidence"] = 0.0
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state