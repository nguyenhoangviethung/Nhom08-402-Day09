"""
workers/policy_tool.py — Policy & Tool Worker
Sử dụng LLM (OpenAI) để phân tích ngoại lệ chính sách một cách thông minh dựa trên chunks.
"""

import os
import json
from datetime import datetime
from openai import OpenAI

WORKER_NAME = "policy_tool_worker"

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """Mock/Real MCP call."""
    try:
        from mcp_server import dispatch_tool
        result = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name, "input": tool_input, "output": result, 
            "error": None, "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "tool": tool_name, "input": tool_input, "output": None, 
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "timestamp": datetime.now().isoformat()
        }

def analyze_policy(task: str, chunks: list) -> dict:
    """Gọi LLM để phân tích policy và tìm exceptions thay vì if-else cứng."""
    if not chunks:
        return {"policy_applies": True, "exceptions_found": [], "policy_name": "unknown", "explanation": "No context provided."}

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    context_text = "\n---\n".join([c.get("text", "") for c in chunks])
    
    prompt = f"""Bạn là một chuyên gia phân tích chính sách công ty.
    Dựa vào ngữ cảnh (Context) bên dưới, hãy đánh giá yêu cầu (Task) của người dùng.
    Xác định xem có chính sách nào áp dụng không, và có ngoại lệ (exception/từ chối) nào bị vi phạm không.

    Task: {task}
    Context: 
    {context_text}

    Trả về đúng định dạng JSON:
    {{
        "policy_applies": boolean,  // True nếu không vi phạm ngoại lệ nào
        "policy_name": "Tên chính sách (vd: Policy v4)",
        "exceptions_found": [
            {{"type": "tên ngoại lệ", "rule": "Trích dẫn luật", "source": "Nguồn luật"}}
        ],
        "explanation": "Giải thích ngắn gọn"
    }}
    """

    try:
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        
        # Merge các sources thực tế
        result["source"] = list({c.get("source", "unknown") for c in chunks})
        return result
    except Exception as e:
        print(f"⚠️ Policy LLM Analysis failed: {e}")
        return {
            "policy_applies": True, "exceptions_found": [],
            "source": list({c.get("source", "unknown") for c in chunks}),
            "error": str(e)
        }

def run(state: dict) -> dict:
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", []).append(WORKER_NAME)
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    worker_io = {
        "worker": WORKER_NAME,
        "input": {"task": task, "chunks_count": len(chunks), "needs_tool": needs_tool},
        "output": None, "error": None,
    }

    try:
        # 1. Fallback search (nếu retrieval chunk rỗng nhưng cần tool)
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")
            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # 2. Phân tích bằng LLM
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # 3. Tool mở rộng (vd JIRA tickets)
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result.get("policy_applies", True),
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(f"[{WORKER_NAME}] policy_applies={policy_result.get('policy_applies')}, exceptions={len(policy_result.get('exceptions_found', []))}")

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state