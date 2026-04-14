# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Nhom08-402  
**Ngày:** 14/04/2026

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.86 | 0.75 | -0.11 | Multi-agent đánh giá khắt khe hơn |
| Avg latency (ms) | 0 | 0 | 0 | Môi trường Lab chạy quá nhanh |
| Abstain rate (%) | 10% | 0% | -10% | Multi-agent tìm kiếm sâu hơn qua các worker |
| Multi-hop accuracy | 0% | 80% | +80% | Nhờ sự phối hợp giữa các chuyên gia |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Điểm cải tiến lớn nhất về minh bạch |
| Debug time (estimate) | 30 phút | 5 phút | -25 phút | Tìm ra lỗi nhanh nhờ Trace chi tiết |
| HITL Trigger rate | 0% | 6.6% | +6.6% | Cơ chế an toàn bảo vệ hệ thống |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Cao (95%) | Cao (95%) |
| Latency | Thấp | Trung bình |
| Observation | Trả lời trực tiếp nhanh | Phải đi qua Supervisor nên tốn thêm 1 bước |

**Kết luận:** Multi-agent không làm tăng độ chính xác của câu hỏi dễ nhưng giúp hệ thống "giải trình" được lý do tại sao lại chọn nguồn tài liệu đó.

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Thấp (Hay bị quên context) | Cao (Phối hợp tốt) |
| Routing visible? | ✗ | ✓ |
| Observation | Dễ xảy ra hiện tượng ảo giác | Supervisor chia nhỏ task giúp Agent tập trung |

**Kết luận:** Multi-agent vượt trội hoàn toàn khi xử lý các câu hỏi phức tạp (như câu q15) nhờ quy trình chia để trị.

### 2.3 Câu hỏi cần abstain (Dữ liệu không có trong hệ thống)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 10% | 0% |
| Hallucination cases | Có (Khi cố trả lời lỗi lạ) | Không (Nhờ có HITL) |
| Observation | Agent cũ hay "đoán mò" | Agent mới biết chuyển cho người kiểm duyệt |

**Kết luận:** Cơ chế chuyển hướng sang HITL khi gặp rủi ro cao giúp Day 09 an toàn hơn hẳn cho doanh nghiệp.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: 30 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: 5 phút
```
**Câu cụ thể nhóm đã debug:** Câu q09 (ERR-403-AUTH). Nhờ nhìn vào Trace, nhóm phát hiện Supervisor đã gán nhãn `risk_high` và đưa vào quy trình Duyệt (HITL) thay vì trả lời sai, giúp nhóm hiểu rõ luồng xử lý an toàn.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn bộ Prompt hệ thống | Chỉ cần thêm MCP tool và update route rule |
| Thêm 1 domain mới | Phải viết lại Large Prompt | Thêm 1 Worker mới chuyên trách |
| Thay đổi retrieval strategy | Sửa trực tiếp trong lõi pipeline | Chỉ sửa retrieval_worker, không động vào supervisor |
| A/B test một phần | Khó — phải clone toàn bộ hệ thống | Dễ — chỉ cần thay thế worker cụ thể |

**Nhận xét:** Day 09 cho phép phát triển kiểu module. Team có 7 người có thể mỗi người làm 1 worker mà không bao giờ bị xung đột code (conflict git).

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 LLM call | 3 LLM calls |
| Complex query | 1 LLM call | 5 LLM calls |
| MCP tool call | N/A | +1 call cho tool use |

**Nhận xét về cost-benefit:** Tuy tốn token hơn và độ trễ cao hơn một chút, nhưng sự đánh đổi này là xứng đáng để có được độ chính xác cao và khả năng giải trình (Explainability).

---

## 6. Kết luận

**Multi-agent tốt hơn single agent ở điểm nào?**
1. Khả năng gỡ lỗi (Debug) cực nhanh nhờ Trace và Routing visibility.
2. Tính an toàn vượt trội nhờ cơ chế HITL cho các trường hợp rủi ro cao.

**Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**
1. Chi phí vận hành (Token) cao hơn do phải gọi LLM nhiều lần để điều phối.

**Khi nào KHÔNG nên dùng multi-agent?**
Khi hệ thống chỉ có một tệp dữ liệu duy nhất và yêu cầu phản hồi tức thì với chi phí rẻ nhất có thể.

**Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**
1. Thêm bộ nhớ (Memory) cho Supervisor để tối ưu hóa việc định tuyến dựa trên lịch sử.
2. Tối ưu hóa Parallel processing để các Worker chạy song song thay vì tuần tự nhằm giảm Latency.
