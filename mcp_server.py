"""
mcp_server.py — Mock MCP Server
Sprint 3: Implement HTTP Server cung cấp các công cụ (Tools) cho Agent.
"""

import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

# Đảm bảo đường dẫn gốc được nạp vào sys.path để uvicorn có thể import module 'workers'
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─────────────────────────────────────────────
# Tool Definitions (Schema Discovery)
# ─────────────────────────────────────────────

TOOL_SCHEMAS = {
    "search_kb": {
        "name": "search_kb",
        "description": "Tìm kiếm Knowledge Base nội bộ bằng semantic search. Trả về top-k chunks liên quan nhất.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Câu hỏi hoặc keyword cần tìm"},
                "top_k": {"type": "integer", "description": "Số chunks cần trả về", "default": 3},
            },
            "required": ["query"],
        },
    },
    "get_ticket_info": {
        "name": "get_ticket_info",
        "description": "Tra cứu thông tin ticket từ hệ thống Jira nội bộ.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "ID ticket (VD: IT-1234, P1-LATEST)"},
            },
            "required": ["ticket_id"],
        },
    },
    "check_access_permission": {
        "name": "check_access_permission",
        "description": "Kiểm tra điều kiện cấp quyền truy cập theo Access Control SOP.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "access_level": {"type": "integer", "description": "Level cần cấp (1, 2, hoặc 3)"},
                "requester_role": {"type": "string", "description": "Vai trò của người yêu cầu"},
                "is_emergency": {"type": "boolean", "description": "Có phải khẩn cấp không", "default": False},
            },
            "required": ["access_level", "requester_role"],
        },
    },
    "create_ticket": {
        "name": "create_ticket",
        "description": "Tạo ticket mới trong hệ thống Jira (MOCK).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "priority": {"type": "string", "enum": ["P1", "P2", "P3", "P4"]},
                "title": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["priority", "title"],
        },
    },
}

# ─────────────────────────────────────────────
# Tool Implementations
# ─────────────────────────────────────────────

def tool_search_kb(query: str, top_k: int = 3) -> dict:
    """Tìm kiếm vector database thực tế qua retrieval worker."""
    print(f"  [MCP Server] Đang thực thi 'search_kb' với query: '{query}'")
    try:
        from workers.retrieval import retrieve_hybrid
        # Gọi hàm retrieve_hybrid từ worker
        chunks = retrieve_hybrid(query, top_k=top_k)
        sources = list({c.get("source", "unknown") for c in chunks})
        print(f"  [MCP Server] -> Đã tìm thấy {len(chunks)} đoạn văn bản.")
        return {
            "chunks": chunks,
            "sources": sources,
            "total_found": len(chunks),
        }
    except Exception as e:
        print(f"  [MCP Server] ⚠️ Lỗi search_kb: {e}")
        return {
            "chunks": [],
            "sources": [],
            "total_found": 0,
            "error": str(e),
        }

# Mock ticket database
MOCK_TICKETS = {
    "P1-LATEST": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "title": "API Gateway down — toàn bộ người dùng không đăng nhập được",
        "status": "in_progress",
        "assignee": "nguyen.van.a@company.internal",
        "created_at": "2026-04-13T22:47:00",
        "sla_deadline": "2026-04-14T02:47:00",
        "escalated": True,
        "notifications_sent": ["slack:#incident-p1", "pagerduty:oncall"],
    },
    "IT-1234": {
        "ticket_id": "IT-1234",
        "priority": "P2",
        "title": "Feature login chậm cho một số user",
        "status": "open",
        "assignee": None,
        "created_at": "2026-04-13T09:15:00",
    },
}

def tool_get_ticket_info(ticket_id: str) -> dict:
    print(f"  [MCP Server] Đang thực thi 'get_ticket_info' cho ID: {ticket_id}")
    ticket = MOCK_TICKETS.get(ticket_id.upper())
    if ticket:
        return ticket
    return {"error": f"Ticket '{ticket_id}' không tìm thấy."}

ACCESS_RULES = {
    1: {"required_approvers": ["Line Manager"], "emergency_can_bypass": False},
    2: {"required_approvers": ["Line Manager", "IT Admin"], "emergency_can_bypass": True},
    3: {"required_approvers": ["Line Manager", "IT Admin", "IT Security"], "emergency_can_bypass": False},
}

def tool_check_access_permission(access_level: int, requester_role: str, is_emergency: bool = False) -> dict:
    print(f"  [MCP Server] Đang thực thi 'check_access_permission' (Level: {access_level}, Khẩn: {is_emergency})")
    rule = ACCESS_RULES.get(access_level)
    if not rule:
        return {"error": f"Access level {access_level} không hợp lệ."}

    notes = []
    if is_emergency and rule.get("emergency_can_bypass"):
        notes.append("Được phép bỏ qua quy trình duyệt vì lý do khẩn cấp.")
    elif is_emergency and not rule.get("emergency_can_bypass"):
        notes.append(f"CẢNH BÁO: Level {access_level} KHÔNG cho phép bỏ qua quy trình duyệt dù khẩn cấp.")

    return {
        "access_level": access_level,
        "can_grant": True,
        "required_approvers": rule["required_approvers"],
        "emergency_override": is_emergency and rule.get("emergency_can_bypass", False),
        "notes": notes,
    }

def tool_create_ticket(priority: str, title: str, description: str = "") -> dict:
    mock_id = f"IT-{9900 + hash(title) % 99}"
    print(f"  [MCP Server] Đang thực thi 'create_ticket': {mock_id} ({priority})")
    return {
        "ticket_id": mock_id,
        "priority": priority,
        "status": "open",
        "url": f"https://jira.company.internal/browse/{mock_id}",
    }

# ─────────────────────────────────────────────
# Dispatch Layer 
# ─────────────────────────────────────────────

TOOL_REGISTRY = {
    "search_kb": tool_search_kb,
    "get_ticket_info": tool_get_ticket_info,
    "check_access_permission": tool_check_access_permission,
    "create_ticket": tool_create_ticket,
}

def list_tools() -> list:
    return list(TOOL_SCHEMAS.values())

def dispatch_tool(tool_name: str, tool_input: dict) -> dict:
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Tool '{tool_name}' không tồn tại."}
    
    try:
        return TOOL_REGISTRY[tool_name](**tool_input)
    except Exception as e:
        return {"error": f"Tool '{tool_name}' execution failed: {e}"}

# ─────────────────────────────────────────────
# HTTP Server (FastAPI) 
# ─────────────────────────────────────────────

try:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(title="MCP HTTP Server", description="REST Server exposes tools")

    @app.get("/tools")
    def api_list_tools():
        return list_tools()

    @app.post("/tools/{tool_name}")
    async def api_dispatch_tool(tool_name: str, request: Request):
        try:
            tool_input = await request.json()
        except:
            tool_input = {}
            
        result = dispatch_tool(tool_name, tool_input)
        if isinstance(result, dict) and "error" in result:
            return JSONResponse(status_code=400, content=result)
        return result

except ImportError:
    app = None
    print("⚠️ FastAPI chưa được cài đặt. Chạy lệnh: pip install fastapi uvicorn")

if __name__ == "__main__":
    print("👉 Hãy chạy server bằng lệnh: uvicorn mcp_server:app --port 8000 --reload")