# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhom08-402  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Hoàng | Supervisor Owner | hoangmai04222@gmail.com |
| Hưng | Tech Lead | hoangduchung0311@gmail.com |
| Hồng Anh | Tech Lead | anh.anhle2004@gmail.com |
| Hùng | Tech Lead, Trace Owner | nguyenhoangviethung@gmail.com |
| Giang | Worker Owner | nguyenhuonggiang06092004@gmail.com |
| Bình | Trace & Docs Owner | binhntph50046@gmail.com |

**Ngày nộp:** 14/04/2026  
**Repo:** https://github.com/nguyenhoangviethung/Nhom08-402-Day09
**Độ dài khuyến nghị:** 600–1000 từ

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

Nhóm đã triển khai kiến trúc **Supervisor-Worker** sử dụng **LangGraph StateGraph** nhằm phối hợp nhiều agent chuyên biệt thay vì sử dụng một Single Agent duy nhất như Day 08.

**Hệ thống tổng quan:**
Hệ thống bao gồm 5 node chính trong graph (file `graph.py`, dòng 200-204):
1.  **Supervisor** (`supervisor_node`): Phân tích task bằng keyword matching và quyết định route, gán cờ `risk_high` khi cần.
2.  **Human Review** (`human_review_node`): Xử lý HITL khi phát hiện rủi ro cao (auto-approve trong lab mode).
3.  **Retrieval Worker** (`retrieval_worker_node`): Chuyên trách tra cứu ngữ nghĩa từ ChromaDB Knowledge Base.
4.  **Policy Tool Worker** (`policy_tool_worker_node`): Thực thi logic nghiệp vụ phức tạp và kiểm tra chính sách qua MCP Tools.
5.  **Synthesis Worker** (`synthesis_worker_node`): Tổng hợp câu trả lời cuối cùng từ các bằng chứng thu thập được.

**Routing logic cốt lõi (graph.py, dòng 102-117):**
Supervisor sử dụng **Keyword-based Routing** với hai danh sách từ khóa:
- `policy_keywords`: `["hoàn tiền", "refund", "flash sale", "license", "cấp quyền", "access", "level 3", "ticket", "p1"]` → route sang `policy_tool_worker`.
- `risk_keywords`: `["emergency", "khẩn cấp", "2am", "không rõ", "err-"]` → bật cờ `risk_high`.
- Nếu `risk_high == True` **và** task chứa `"err-"` → route sang `human_review`.

**MCP tools đã tích hợp** (qua `mcp_server.py`):
- `search_kb`: Tìm kiếm văn bản trong Knowledge Base.
- `get_ticket_info`: Truy xuất chi tiết ticket.
- `check_access_permission`: Kiểm tra quyền hạn truy cập của nhân sự.
- `check_policy`: Đối soát yêu cầu với các điều khoản chính sách (Refund, HR).

*Ví dụ Trace thực tế (q03.json):* `supervisor → policy_tool_worker (calls check_access_permission) → retrieval_worker → synthesis_worker`.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Sử dụng **Keyword-based Routing** trong Supervisor kết hợp với **Risk Flag** (`risk_high`) và **HITL override** thay vì hard-code từng workflow riêng.

**Bối cảnh vấn đề:**
Khi thiết kế Supervisor, nhóm phải chọn giữa việc sử dụng LLM để phân loại hoặc dùng rule-based routing. Với constraints của lab (chi phí token, độ trễ, và yêu cầu trace phải rõ ràng), nhóm đã chọn keyword matching.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|------------|
| LLM Classifier | Linh hoạt, hiểu ngữ cảnh tốt | Độ trễ cao, tốn token, khó reproduce. |
| Keyword routing (Chosen) | Tốc độ nhanh, chi phí 0, trace rõ ràng. | Có thể miss câu hỏi đa ý định. |
| Hybrid Routing | Cân bằng giữa tốc độ và accuracy. | Logic phức tạp hơn cần thiết. |

**Phương án đã chọn và lý do:**
Nhóm chọn **Keyword routing** vì tính **đơn giản và dễ debug**. Mỗi quyết định routing đều được ghi rõ `route_reason` trong state, giúp trace 100% minh bạch. Khi cần thêm worker mới, chỉ cần bổ sung keyword vào danh sách tại `graph.py` dòng 102-103.

**Bằng chứng từ code thực tế (`graph.py`, dòng 105-117):**
```python
if any(kw in task for kw in policy_keywords):
    route = "policy_tool_worker"
    route_reason = "task chứa keyword liên quan policy/quyền truy cập/ticket"
    needs_tool = True

if any(kw in task for kw in risk_keywords):
    risk_high = True
    route_reason += " | bật cờ risk_high"

# Human review override
if risk_high and "err-" in task:
    route = "human_review"
    route_reason = "mã lỗi lạ + risk_high -> dừng lại cần human review"
```

---

## 3. Kết quả grading questions (150–200 từ)

Nhóm đã chạy pipeline với bộ **10 grading questions** (file `artifacts/grading_run.jsonl`) và đạt kết quả tổng thể khả quan.

**Kết quả chi tiết từng câu (từ `grading_run.jsonl`):**

| ID | Điểm raw tối đa | Route | Confidence | Latency (ms) | Đánh giá |
|----|-----------------|-------|------------|--------------|----------|
| gq01 | 10 | policy_tool_worker | 0.90 | 29,689 | Partial — trả lời đúng SLA escalation nhưng thiếu chi tiết kênh thông báo |
| gq02 | 10 | policy_tool_worker | 0.90 | 7,417 | Full — xác định đúng điều kiện hoàn tiền |
| gq03 | 10 | policy_tool_worker | 0.90 | 4,398 | Full — 3 người phê duyệt, IT Security cuối |
| gq04 | 6 | policy_tool_worker | 0.98 | 7,173 | Full — đúng 110% store credit |
| gq05 | 8 | policy_tool_worker | 0.98 | 5,007 | Full — escalate lên Senior Engineer |
| gq06 | 8 | retrieval_worker | 0.98 | 6,879 | Full — probation không được remote |
| gq07 | 10 | policy_tool_worker | 0.10 | 2,386 | Full (Abstain) — trả về "Không đủ thông tin", confidence 0.10 |
| gq08 | 8 | retrieval_worker | 0.98 | 13,441 | Full — 90 ngày đổi mật khẩu, cảnh báo 7 ngày |
| gq09 | 16 | policy_tool_worker | 0.90 | 7,521 | Full — nêu đủ SLA escalation + Level 2 emergency access |
| gq10 | 10 | policy_tool_worker | 0.90 | 8,909 | Full — Flash Sale không được hoàn tiền dù lỗi nhà sản xuất |

**Tổng điểm raw ước tính:** ~91/96
*(gq01 mất điểm partial do thiếu chi tiết kênh thông báo cụ thể)*

**Câu pipeline xử lý tốt nhất:**
- ID: `gq04` (Store Credit) — Confidence 0.98, trả lời chính xác "110% so với tiền gốc", cite đúng `policy/refund-v4.pdf`.

**Câu pipeline xử lý tốt đặc biệt — gq07 (abstain):**
Pipeline trả về `"Không đủ thông tin trong tài liệu nội bộ"` với confidence chỉ 0.10, chứng tỏ Synthesis Worker nhận diện chính xác khi không có dữ liệu về mức phạt tài chính SLA P1 trong Knowledge Base → **không hallucinate**.

**Câu gq09 (multi-hop khó nhất, 16 điểm):**
Trace ghi nhận Supervisor route sang `policy_tool_worker` với reason `"task chứa keyword liên quan policy/quyền truy cập/ticket | bật cờ risk_high"`, gọi 3 MCP tools (`search_kb`, `get_ticket_info`, `check_access_permission`). Pipeline trả về đầy đủ cả SLA P1 notification procedure và điều kiện cấp Level 2 emergency access.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

**Dữ liệu so sánh thực tế (từ `eval_report.json`):**

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta |
|--------|----------------------|---------------------|-------|
| Avg Confidence | 0.847 | 0.706 | **-0.141** |
| Avg Latency (ms) | 2,897 | 6,271 | **+3,374 ms** |
| Total traces | 15 | 86 | +71 |
| MCP Usage Rate | N/A (không có) | 50/86 (58%) | — |
| HITL Rate | N/A (không có) | 5/86 (5%) | — |
| Routing Visibility | Không có `route_reason` | 100% có `route_reason` | — |

**Phân tích:**
- **Confidence giảm (-0.141):** Do Day 09 trải qua nhiều bước hơn, confidence được tính tổng hợp từ nhiều worker nên bị "pha loãng". Tuy nhiên, chất lượng câu trả lời thực tế (đặc biệt ở grading questions) tốt hơn nhờ sử dụng MCP tools.
- **Latency tăng (+3,374ms):** Multi-Agent phải đi qua Supervisor → Worker → Synthesis, mỗi bước đều gọi LLM riêng. Đây là trade-off chấp nhận được.

**Điều nhóm bất ngờ nhất:**
Khả năng **abstain chính xác** ở Day 09. Khi tách nhỏ task, Synthesis Worker tập trung tốt hơn vào nhiệm vụ: nếu `retrieved_chunks` rỗng hoặc không liên quan, nó dứt khoát trả về "không đủ thông tin" thay vì cố gắng bịa (Day 08 thường cố suy luận dẫn đến hallucination nhẹ).

**Trường hợp multi-agent KHÔNG giúp ích:**
Với câu hỏi đơn giản (ví dụ: tra cứu mật khẩu FAQ), latency Day 09 là **13,441ms** (gq08) trong khi Day 08 chỉ mất ~1,600ms cho câu tương tự. Kiến trúc multi-agent rõ ràng overkill cho tác vụ không cần tool hay policy check.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint | File chính |
|------------|-------------|--------|------------|
| Hoàng, Hưng, Hùng, Hồng Anh | Supervisor logic, Prompt Engineering, Graph Orchestration | Sprint 1 & 3 | `graph.py`, `mcp_server.py`, `mcp_tools.py` |
| Giang | Implement Workers (Retrieval, Policy, Synthesis), MCP Tools | Sprint 2 | `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py` |
| Bình | Tracing logic, Eval script, Tài liệu hệ thống và Báo cáo | Sprint 4 | `eval_trace.py`, `docs/*`, `reports/*` |

**Điều nhóm làm tốt:** 
Phối hợp nhịp nhàng giữa khâu thiết kế `AgentState` (20 fields trong `graph.py`) và triển khai Worker logic. State được dùng chung xuyên suốt graph nên workers không cần truyền tham số phức tạp.

**Điều nhóm làm chưa tốt:**
Routing bằng keyword có hạn chế ở câu hỏi không chứa keyword rõ ràng — ví dụ `gq06` về remote work bị route sang `retrieval_worker` (reason: `"default route"`) thay vì `policy_tool_worker`, dù kết quả vẫn đúng.

**Nếu làm lại, nhóm sẽ thay đổi gì?**
Nhóm sẽ bổ sung thêm keyword cho routing (ví dụ: `"remote"`, `"probation"`, `"nghỉ phép"`) hoặc thử hybrid routing (keyword + LLM fallback) để tránh miss case như `gq06`.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Nhóm sẽ triển khai **Parallel Worker Execution** — hiện tại các worker chạy tuần tự (latency trung bình 6,271ms). Nếu cho Retrieval và Policy chạy song song, latency ước tính giảm còn ~3,500ms. Ngoài ra, bổ sung **Self-Correction Worker** kiểm tra tính đúng đắn của câu trả lời trước output, và thêm breakdown theo category (abstain rate, multi-hop accuracy) vào `eval_report.json` thay vì chỉ aggregate metrics.

---
*File này lưu tại: `reports/group_report.md`*  
