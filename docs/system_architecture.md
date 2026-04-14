# System Architecture — Lab Day 09

**Nhóm:** Nhom08-402  
**Ngày:** 14/04/2026  
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

> Mô tả ngắn hệ thống của nhóm: chọn pattern gì, gồm những thành phần nào.

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này (thay vì single agent):**

Kiến trúc này cho phép chuyên môn hóa từng thành phần, tăng tính minh bạch trong việc ra quyết định (routing) và dễ dàng mở rộng tính năng mới thông qua MCP Tools mà không làm ảnh hưởng đến logic lõi của hệ thống. Ngoài ra, nó cung cấp khả năng gỡ lỗi (debug) nhanh chóng nhờ các Trace ghi lại lý do điều hướng.

---

## 2. Sơ đồ Pipeline

> Vẽ sơ đồ pipeline dưới dạng text, Mermaid diagram, hoặc ASCII art.
> Yêu cầu tối thiểu: thể hiện rõ luồng từ input → supervisor → workers → output.

**Ví dụ (ASCII art):**
```
User Request
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← route_reason, risk_high, needs_tool
└──────┬───────┘
       │
   [route_decision]
       │
  ┌────┴────────────────────┐
  │                         │
  ▼                         ▼
Retrieval Worker     Policy Tool Worker
  (evidence)           (policy check + MCP)
  │                         │
  └─────────┬───────────────┘
            │
            ▼
      Synthesis Worker
        (answer + cite)
            │
            ▼
         Output
```

**Sơ đồ thực tế của nhóm:**

```
User Request
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← route_reason, risk_high, needs_tool
└──────┬───────┘
       │
   [route_decision]
       │
  ┌────┴────────────────────┐
  │                         │
  ▼                         ▼
Retrieval Worker     Policy Tool Worker
  (evidence)           (policy check + MCP)
  │                         │
  └─────────┬───────────────┘
            │
            ▼
      Synthesis Worker
        (answer + cite)
            │
            ▼
         Output
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Phân tích ý định (intent) của người dùng và điều phối tác vụ đến Worker phù hợp. |
| **Input** | Câu hỏi từ người dùng (task). |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | Sử dụng LLM Classifier để phân loại câu hỏi dựa trên mô tả nhiệm vụ và các ràng buộc về rủi ro. |
| **HITL condition** | Kích hoạt khi phát hiện mã lỗi lạ (unknown error code) hoặc yêu cầu có tính nhạy cảm cao (risk_high). |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Tìm kiếm ngữ nghĩa và trích xuất bằng chứng từ Knowledge Base. |
| **Embedding model** | text-embedding-004 |
| **Top-k** | 3 - 5 chunks |
| **Stateless?** | Yes |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Kiểm tra chính sách và thực thi các logic nghiệp vụ phức tạp thông qua MCP. |
| **MCP tools gọi** | search_kb, check_access_permission, get_ticket_info |
| **Exception cases xử lý** | Truy cập trái phép, yêu cầu ngoài khung giờ, hoặc thiếu thông tin định danh. |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | Gemini 1.5 Pro |
| **Temperature** | 0.1 |
| **Grounding strategy** | Chỉ sử dụng các chunks và kết quả tool đã được Worker cung cấp để tổng hợp câu trả lời. |
| **Abstain condition** | Khi dữ liệu từ các Worker trả về không chứa thông tin để giải quyết task. |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources |
| get_ticket_info | ticket_id | ticket details |
| check_access_permission | access_level, requester_role | can_grant, approvers |
| check_policy | policy_category | policy_details, constraints |

---

## 4. Shared State Schema

> Liệt kê các fields trong AgentState và ý nghĩa của từng field.

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| task | str | Câu hỏi đầu vào | supervisor đọc |
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| retrieved_chunks | list | Evidence từ retrieval | retrieval ghi, synthesis đọc |
| policy_result | dict | Kết quả kiểm tra policy | policy_tool ghi, synthesis đọc |
| mcp_tools_used | list | Tool calls đã thực hiện | policy_tool ghi |
| final_answer | str | Câu trả lời cuối | synthesis ghi |
| confidence | float | Mức tin cậy | synthesis ghi |
| risk_high | bool | Cảnh báo rủi ro cao | supervisor ghi, HITL đọc |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt | Thêm worker/MCP tool riêng |
| Routing visibility | Không có | Có route_reason trong trace |
| Tính giải trình | Thấp (Black box) | Cao (Clear reasoning path) |
| Tính an toàn | Thấp (Dễ bị ảo giác) | Cao (Có HITL cho rủi ro cao) |
| Tính mở rộng | Khó — phải sửa toàn prompt | Dễ — thêm worker/MCP tool riêng |
| Tính song song | Không có | Có thể chạy song song các worker |
| Tính linh hoạt | Thấp (Phải sửa toàn prompt) | Cao (Chỉ cần sửa worker tương ứng) |
| Tính dễ debug | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |

**Nhóm điền thêm quan sát từ thực tế lab:**

Trong quá trình test câu q09 về mã lỗi ERR-403-AUTH, hệ thống Multi-Agent đã nhận diện được đây là một "unknown code" và gán nhãn risk_high, giúp kích hoạt cơ chế kiểm duyệt thay vì cố gắng đưa ra một câu trả lời ảo giác như Single Agent.

---

## 6. Giới hạn và điểm cần cải tiến

> Nhóm mô tả những điểm hạn chế của kiến trúc hiện tại.

1. Độ trễ hệ thống (Latency): Do luồng xử lý phải đi qua nhiều bước trung gian, thời gian phản hồi tổng thể cao hơn so với việc gọi trực tiếp 1 LLM đơn lẻ.
2. Chi phí vận hành: Việc sử dụng nhiều lượt gọi LLM để điều phối và tổng hợp làm tăng lượng token tiêu thụ, dẫn đến chi phí vận hành cao hơn.
3. Sự phụ thuộc vào Supervisor: Nếu Supervisor phân loại sai ngay từ đầu, toàn bộ các bước sau sẽ không thể cho ra kết quả đúng. Cần cải tiến Prompt định tuyến hoặc sử dụng model mạnh hơn cho khâu này.
