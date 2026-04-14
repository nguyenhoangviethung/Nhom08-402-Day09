# Goal

Mục tiêu của kế hoạch này là hoàn thành **Sprint 3 (60') — Thêm MCP**, nhắm đến điểm cộng (Bonus +2) bằng cách implement cấu trúc **MCP server thật** dưới dạng HTTP Server (sử dụng FastAPI và Uvicorn). Server sẽ cung cấp 2 tool là `search_kb` và `get_ticket_info` thay vì gọi mock/function call. 

Từ đó, file `workers/policy_tool.py` sẽ đóng vai trò MCP Client, gửi HTTP POST requests đến Server qua mạng cục bộ.

## User Review Required

> [!IMPORTANT]
> **Phương pháp thực hiện (HTTP Server thay vì mcp studio/sse):** 
> 
> Với hệ sinh thái Python, để tạo một server độc lập (real server), dùng **FastAPI** đóng role làm MCP tool provider là con đường ổn định và dễ debug bề mặt mạng nhất trong bối cảnh thực hành Lab. 
> Bạn có đồng ý dùng framework **FastAPI** + **Uvicorn** (được cung cấp sẵn trong `requirements.txt`) để thiết lập một REST HTTP Server cho 2 tools này không, hay bạn muốn sử dụng đặc tả JSON-RPC của package `mcp` tiêu chuẩn (cần dùng stdio hoặc Starlette SSE mapping phức tạp hơn chút)? Lựa chọn FastAPI hoàn toàn thỏa mãn "hoặc HTTP server" ở mức độ Advanced.

## Chuẩn bị (Prerequisites)
Để thực hiện được MCP real qua HTTP (Client - Server), chúng ta cần:
1. **Chạy 2 tiến trình (2 process):** 
   - Tiến trình 1: Chạy `mcp_server.py` bằng Uvicorn đứng chờ request gọi tools (ví dụ ở cổng 8000).
   - Tiến trình 2: Chạy `graph.py` để chạy pipeline. `policy_tool.py` sẽ gọi API sang localhost:8000.
2. **Thư viện:** Chắc chắn rằng các thư viện: `httpx`, `fastapi`, `uvicorn`, `pydantic` đã được cài theo `requirements.txt`. (Bạn đã chạy UV pip install rồi nên bước này có thể bỏ qua nếu `requirements.txt` của bạn đã uncomment phần thư viện MCP).

## Proposed Changes

---

### Real HTTP MCP Server

Kịch bản cho server là lắng nghe request từ cổng 8000 và tính toán trả về qua giao thức HTTP.

#### [MODIFY] [mcp_server.py](file:///home/anhle/vinuni/week_03/Nhom08-402-Day09/mcp_server.py)
Thay vì code giả lập hàm mock, tôi sẽ code file này thành một FastAPI app. File này sẽ có:
- Endpoint `POST /tools/search_kb`: Nhận body HTTP `{query: str, top_k: int}`, gọi kết nối tới `chroma_db` để truy xuất chunks, trả về JSON. Lúc này mcp_server sẽ import logic lấy từ ChromaDB tương tự quá trình retrieval.
- Endpoint `POST /tools/get_ticket_info`: Nhận body `{ticket_id: str}`, trả về JSON cấu trúc thông tin giả lập của ticket đó (như status, sla_impact, assignee...).

---

### Worker Integration

#### [MODIFY] [workers/policy_tool.py](file:///home/anhle/vinuni/week_03/Nhom08-402-Day09/workers/policy_tool.py)
Cập nhật function `_call_mcp_tool` để trở thành **HTTP Client** thực thụ:
- Dùng `httpx.post(f"http://127.0.0.1:8000/tools/{tool_name}", json=tool_input)` thay vì import hàm direct từ `mcp_server.py`.
- Lấy kết quả (`output`) từ Body trả về.
- Tạo construct gói lại thành định dạng trace MCP chuẩn quy định trong bài (`tool`, `input`, `output`, `timestamp`).

---

## Open Questions

> [!WARNING]
> Server ChromaDB lúc này sẽ được gọi từ `mcp_server.py` (cũng như `retrieval.py` trong graph). Hai file này cùng trỏ tới thư mục `./chroma_db`. Với ChromaDB (bản Persistent), việc nhiều process đọc từ 1 file DB có thể an toàn nếu chỉ Read. Kế hoạch này sẽ tập trung vào Read-only cho `search_kb`. Bạn thấy có vấn đề gì ở kiến trúc này không?

## Verification Plan

### Manual Verification
1. Sẽ yêu cầu bạn bật tab Terminal 1 và gõ: `uvicorn mcp_server:app --port 8000 --reload`
2. Tại Terminal 2, chạy command `python workers/policy_tool.py` để verify rằng Worker Client gọi được HTTP Server hoàn chỉnh.
3. Sau đó chạy tiếp `python graph.py` ở Terminal 2 để xem trace history được sinh ra có bao gồm block `mcp_tools_used` chuẩn chỉnh kèm log trace hay không.
