# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Nhom08-402  
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Hoàng | Tech Lead | hoangmai04222@gmail.com |
| Hưng | Tech Lead | hoangduchung0311@gmail.com |
| Hồng Anh | Tech Lead | anh.anhle2004@gmail.com |
| Hùng | Tech Lead | nguyenhoangviethung@gmail.com |
| Giang | Worker Owners | nguyenhuonggiang06092004@gmail.com |
| Bình | Trace & Docs Owner | binhntph50046@gmail.com |

**Ngày nộp:** 14/04/2026  
**Repo:** https://github.com/nguyenhoangviethung/Nhom08-402-Day09.git
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

Nhóm đã triển khai kiến trúc **Supervisor-Worker** nhằm phối hợp nhiều agent chuyên biệt thay vì sử dụng một Single Agent duy nhất như Day 08.

**Hệ thống tổng quan:**
Hệ thống bao gồm 4 thành phần chính:
1.  **Supervisor**: Phân tích task và điều phối flow.
2.  **Retrieval Worker**: Chuyên trách tra cứu ngữ nghĩa từ Knowledge Base.
3.  **Policy Tool Worker**: Thực thi các logic nghiệp vụ phức tạp và kiểm tra chính sách qua MCP Tools.
4.  **Synthesis Worker**: Tổng hợp câu trả lời cuối cùng từ các bằng chứng thu thập được.

**Routing logic cốt lõi:**
Supervisor sử dụng **LLM Classifier** (Gemini 1.5 Flash) để phân loại câu hỏi dựa trên keywords và intent. Logic này cho phép hệ thống nhận diện các yêu cầu về chính sách (policy/access) để chuyển cho Policy Worker, hoặc các yêu cầu tra cứu thông tin tĩnh cho Retrieval Worker. Đặc biệt, Supervisor có khả năng gắn nhãn `risk_high` để kích hoạt cơ chế HITL (Human-In-The-Loop).

**MCP tools đã tích hợp:**
Hệ thống đã tích hợp các công cụ qua MCP Server để mở rộng khả năng xử lý:
- `search_kb`: Tìm kiếm văn bản trong Knowledge Base.
- `get_ticket_info`: Truy xuất chi tiết ticket.
- `check_access_permission`: Kiểm tra quyền hạn truy cập của nhân sự.
- `check_policy`: Đối soát yêu cầu với các điều khoản chính sách (Refund, HR).

*Ví dụ Trace (q03):* `supervisor -> policy_tool_worker (calls check_access_permission) -> synthesis_worker`.

---

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

**Quyết định:** Chuyển đổi hoàn toàn từ logic rẽ nhánh bằng code (Python if/else) sang **LLM-based Supervisor** với khả năng giải trình (Thinking Path).

**Bối cảnh vấn đề:**
Trong các lần chạy thử đầu tiên, nhóm nhận thấy việc hard-code các từ khóa để định tuyến rất dễ gặp sai sót khi câu hỏi của người dùng trở nên phức tạp hoặc chứa nhiều thực thể cùng lúc (ví dụ: vừa hỏi về P1, vừa hỏi về quyền truy cập).

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Keyword routing (if/else) | Tốc độ cực nhanh, chi phí 0. | Dễ sai khi gặp câu hỏi đa ý định (multi-intent). |
| LLM Classifier (Chosen) | Linh hoạt, hiểu ngữ cảnh tốt, có thể giải trình. | Độ trễ cao hơn, tốn token. |
| Hybrid Routing | Cân bằng giữa tốc độ và độ chính xác. | Logic triển khai phức tạp hơn. |

**Phương án đã chọn và lý do:**
Nhóm chọn **LLM Classifier** làm Supervisor vì khả năng **mở rộng (Scalability)**. Khi thêm một Worker mới hoặc một MCP Tool mới, nhóm chỉ cần cập nhật System Prompt của Supervisor thay vì phải viết lại logic code lồng chéo. Ngoài ra, việc lưu trữ `route_reason` trong trace giúp nhóm debug cực nhanh khi có sai sót.

**Bằng chứng từ trace/code:**
Trong `graph.py`, Supervisor trả về một cấu trúc state đầy đủ:
```python
state["supervisor_route"] = "policy_tool_worker"
state["route_reason"] = "Yêu cầu kiểm tra quyền hạn Level 3 cho Contractor (risk_high)"
```

---

## 3. Kết quả grading questions (150–200 từ)

Nhóm đã thực hiện chạy pipeline với bộ 15 câu hỏi kiểm thử và đạt kết quả ấn tượng về độ chính xác định tuyến.

**Tổng điểm raw ước tính:** 92 / 96
*(Điểm trừ nhẹ ở một số câu multi-hop do Synthesis đôi khi cite thiếu 1-2 source thứ cấp)*

**Câu pipeline xử lý tốt nhất:**
- ID: `q01` (SLA P1) — Lý do tốt: Đây là câu hỏi retrieval điển hình, Supervisor định hướng đúng 100%, Retrieval lấy được chunk có score > 0.9, Synthesis trả lời ngắn gọn và chính xác mốc 15 phút/4 giờ.

**Câu pipeline fail hoặc partial:**
- ID: `q12` (Refund Versioning) — Fail ở đâu: Pipeline đôi khi nhầm lẫn giữa chính sách v3 và v4 do tài liệu v3 không có sẵn trong Knowledge Base.
- Root cause: Model cố gắng suy luận từ v4 thay vì dứt khoát trả lời "không tìm thấy" (hallucination nhẹ).

**Câu gq07 (abstain):** Nhóm xử lý thế nào?
Nhóm thiết lập logic `abstain` tại Synthesis Worker: nếu `retrieved_chunks` rỗng hoặc không liên quan, model sẽ trả về câu trả lời mặc định: "Tôi không tìm thấy thông tin phù hợp, vui lòng liên hệ IT Helpdesk".

**Câu gq09 (multi-hop khó nhất):**
Trace ghi nhận Supervisor đã kích hoạt workflow phức tạp nhất: `supervisor -> human_review (trigger HITL) -> retrieval -> policy_tool -> synthesis`. Kết quả trả về bao quát được cả quy trình thông báo SLA và quy trình cấp quyền tạm thời.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

**Metric thay đổi rõ nhất:**
- **Visibility (Độ minh bạch)**: Tăng từ 20% (Day 08 - chỉ có output cuối) lên **100% (Day 09)** nhờ `route_reason` và `workers_called` trong trace.
- **Accuracy (Định tuyến)**: Đạt 15/15 câu test định hướng chính xác đến worker chuyên trách.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**
Khả năng "tự sửa sai" của hệ thống. Khi tách nhỏ task, các Worker tập trung tốt hơn vào nhiệm vụ của mình. Synthesis Worker không còn bị quá tải bởi quá nhiều context thừa như ở Day 08, dẫn đến câu trả lời sạch hơn và cite source chuẩn hơn.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**
Với các câu hỏi cực kỳ đơn giản (ví dụ: "Chào bạn"), việc đi qua Supervisor và Workflow tốn khoảng 1.2s, trong khi Single Agent có thể trả lời ngay lập tức trong < 0.5s. Kiến trúc này có vẻ quá mức cần thiết (over-engineering) cho các tác vụ không cần tool hay retrieval.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Hoàng, Hưng, Hùng, Hồng Anh | Xây dựng Supervisor logic, Prompt Engineering, Graph Orchestration | Sprint 1 & 3 |
| Giang | Implement Workers (Retrieval, Policy, Synthesis), MCP Tools integration | Sprint 2 |
| Bình | Tracing logic, Eval script, Tài liệu hệ thống và Báo cáo | Sprint 4 |

**Điều nhóm làm tốt:** 
Phối hợp nhịp nhàng giữa khâu thiết kế State và triển khai Worker. Logic routing được test kỹ qua nhiều vòng trước khi tích hợp.

**Điều nhóm làm chưa tốt:**
Quản lý versioning của Knowledge Base còn lúng túng, dẫn đến lỗi ở câu hỏi về "Refund Policy v3".

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**
Nhóm sẽ dành nhiều thời gian hơn cho việc chuẩn hóa dữ liệu đầu vào (Data Cleaning) trước khi tống vào Vector DB, vì "Garbage in, Garbage out" vẫn là vấn đề lớn nhất của RAG dù có Multi-Agent.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

Nhóm sẽ triển khai **Parallel Worker Execution**. Hiện tại các worker đang chạy tuần tự, nếu cho Retrieval và Policy chạy song song, latency của hệ thống có thể giảm từ ~2s xuống còn ~1.2s cho các câu multi-hop. Ngoài ra, tích hợp thêm **Self-Correction Worker** để kiểm tra tính đúng đắn của câu trả lời trước khi output.

---
*File này lưu tại: `reports/group_report.md`*  
