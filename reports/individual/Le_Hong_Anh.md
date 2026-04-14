# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Lê Hồng Anh  
**Vai trò trong nhóm:** MCP Owner
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

**Module/file tôi chịu trách nhiệm:**
- File chính: `mcp_server.py`
- Functions tôi implement: `list_tools()`, `dispatch_tool()`, và đặc biệt là các router/endpoint HTTP trong FastAPI như `api_list_tools()` và `api_dispatch_tool()`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi đảm nhận xây dựng **Advanced MCP Server** (để đạt tiêu chí Bonus +2) bằng HTTP Server kết hợp với FastAPI. Công việc của tôi cung cấp RESTful endpoints độc lập tại cổng 8000 cho Policy Worker của các thành viên khác trong nhóm. Thay vì để hệ thống sử dụng Mock MCP class trong Python và gọi qua function call cục bộ, Worker Agent giờ đây tách biệt với Tools. Agent gọi `/tools` (GET) để tự động hóa danh sách schemas, và gọi `/tools/{tool_name}` (POST) để chạy các công cụ cụ thể như `search_kb`, `check_access_permission`, v.v.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
- Commit Hash: `c1daa69a2b4a1f23868c472b204a0f03302b9e1b` thuộc nhánh `feat/mcp_server`.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tôi quyết định triển khai MCP server như một nền tảng dịch vụ REST API sống (live HTTP server) sử dụng thư viện `FastAPI`, không dùng class giả lập (Mock class) gọi qua Python function.

**Lý do:** 
- Tuân thủ đúng kiến trúc Client-Server chuẩn, cung cấp nền tảng thật giống Model Context Protocol, qua đó hoàn thành yêu cầu Advanced MCP Server để kiếm chặng điểm Bonus +2.
- Giúp hệ thống Agent dễ dàng mở rộng, không bị trói buộc ngữ cảnh bộ nhớ (Decoupling). Worker ở port khác hoặc server khác vẫn có thể tương tác với `TOOL_REGISTRY`. 
- Tận dụng `FastAPI` giúp các endpoint được cung cấp sẵn Document và có thể chạy xử lý bất đồng bộ (async).

**Trade-off đã chấp nhận:**
Giao tiếp HTTP có overhead so với in-memory code-call. Bắt buộc nhóm phải thêm logic về timeout, retry cũng như setup riêng `uvicorn mcp_server:app --port 8000` để chạy song song hai component của dự án. 

**Bằng chứng từ trace/code:**
```python
    app = FastAPI(title="MCP HTTP Server", description="REST server exposing MCP-like tools")

    @app.get("/tools")
    def api_list_tools():
        return list_tools()

    @app.post("/tools/{tool_name}")
    async def api_dispatch_tool(tool_name: str, request: Request):
        try:
            tool_input = await request.json()
        except Exception:
            tool_input = {}
        ...
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** API Endpoint `/tools/{tool_name}` bị crash hoặc trả về 500 lỗi do không parse được tham số JSON lúc Client (Worker) gửi request thiếu body.

**Symptom (pipeline làm gì sai?):**
Khi Policy Worker gọi tới một Tool không yêu cầu đầu vào hoặc đầu vào là tham số rỗng (None), Request POST không chứa Body chuẩn. FastAPI gọi trực tiếp `await request.json()` sẽ throw Exception `JSONDecodeError`, đánh sập một nhịp tương tác và làm pipeline Multi-Agent trả về lỗi Error.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Lỗi nằm ở quá trình parser trong routing logic ở `mcp_server.py`. Tôi mặc định tin tưởng data đầu vào và không có Error handling cho request từ các Agent Worker.

**Cách sửa:**
Bọc method parse body vào trong `try-except` block. Khi một tool thực thi mà request format không xác định được nội dung, biến tham số gọi tools `tool_input` sẽ tự fallback thành dictionary rỗng `{}` giúp code trong Tool Registry an toàn thực thi báo format lỗi một cách đúng tiêu chuẩn (thay vì làm server sập). 

**Bằng chứng trước/sau:**
```python
# Lỗi cũ:
tool_input = await request.json()
result = dispatch_tool(tool_name, tool_input)

# Đoạn code sửa lỗi ổn định mới trong mcp_server.py:
        try:
            tool_input = await request.json()
        except Exception:
            tool_input = {}

        result = dispatch_tool(tool_name, tool_input)
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã implement thành công một **Advanced MCP module** hoàn chỉnh giúp team đạt mục tiêu Bonus. Schema các tools (`search_kb`, `get_ticket_info`) và logic HTTP FastAPI được map rất rõ ràng, cách ly được các dependencies nội bộ giúp cho RAG Worker gọn nhẹ hơn. 

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Đôi khi check lỗi JSON cho các schema input (`inputSchema`) vẫn còn xử lý manual. Tính năng validation của Pydantic (built-in của FastAPI) có thể linh động hơn nhưng tôi chưa ứng dụng vì thời gian hạn chế.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Nếu tôi không start server này thành công, các thành viên xử lý Agent/Worker sẽ mất endpoint để route tool. Họ sẽ không thể lấy ticket info từ Jira Mock hay policy chunk trong database.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Tôi cần các thành viên viết logic core trong file `mcp_tools.py` chuẩn xác (logic chroma db hay logic ticket) để tích hợp vào Registry của mình.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Nếu có thêm thời gian, tôi sẽ trực tiếp apply `Pydantic BaseModel` tự sinh cho từng properties trong `TOOL_SCHEMAS`. Hiện tại, request được lấy một loạt dưới dạng `dict()` và chuyển tới `dispatch_tool`, dẫn đến việc các tools phải tự check type tham số đầu vào. Sử dụng sức mạnh FastAPI schema-validation sẽ đẩy bớt code check type khỏi các tools, nâng cao độ bền của kiến trúc.
