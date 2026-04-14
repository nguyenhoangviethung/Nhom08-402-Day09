# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyen Thanh Binh  
**Vai trò trong nhóm:** Trace & Docs Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án Lab Day 09, tôi đảm nhận vai trò **Trace & Docs Owner**. Nhiệm vụ chính của tôi là xây dựng hệ thống đánh giá pipeline và hoàn thiện toàn bộ tài liệu kỹ thuật.

**Module/file tôi chịu trách nhiệm:**
- **Tool đánh giá & Trace:** `eval_trace.py` (379 dòng) — chứa 6 hàm chính: `run_test_questions()`, `run_grading_questions()`, `analyze_traces()`, `compare_single_vs_multi()`, `save_eval_report()`, và `print_metrics()`.
- **Hệ thống tài liệu:** `docs/system_architecture.md`, `docs/routing_decisions.md`, `docs/single_vs_multi_comparison.md`.
- **Kết quả đánh giá:** `artifacts/eval_report.json` — file tổng hợp metrics so sánh Day 08 vs Day 09.
- **Báo cáo nhóm:** `reports/group_report.md`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Công việc của tôi là bước cuối cùng trong pipeline phát triển. Khi Workers (Giang) hoàn thành logic xử lý và Supervisor (Hoàng, Hưng, Hùng, Hồng Anh) hoàn thành routing, tôi sử dụng `eval_trace.py` để chạy 15 câu test và 10 câu grading, từ đó tạo ra 86 trace files trong `artifacts/traces/`. Nếu routing sai, tôi cung cấp `route_reason` từ trace giúp nhóm điều chỉnh danh sách keyword trong `graph.py` dòng 102-103.

**Bằng chứng:**
- File `eval_trace.py` chứa hàm `analyze_traces()` (dòng 180-249) tính toán `routing_distribution`, `avg_confidence`, `avg_latency_ms`, `mcp_usage_rate`, `hitl_rate`.
- Tài liệu `docs/routing_decisions.md` phân tích chi tiết 4 quyết định routing từ trace thực tế, kết quả 15/15 câu test route chính xác.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thiết kế hàm `compare_single_vs_multi()` trong `eval_trace.py` (dòng 259-299) để tự động so sánh Day 08 baseline với Day 09 multi-agent, và lưu `route_reason` cùng `risk_high` flag vào `AgentState`.

**Bối cảnh:**
Trong ngày Day 08, hệ thống chỉ có output cuối cùng (answer + confidence), không có bất kỳ trace nào cho thấy tại sao AI chọn cách trả lời đó. Khi chuyển sang Day 09, tôi đã đề xuất cơ chế bắt buộc Supervisor phải ghi `route_reason` và gán `risk_high` flag trước khi chuyển task cho Worker.

**Lý do chọn:**
1. **Tính giải trình (Transparency):** `route_reason` giúp debug nhanh — ví dụ, tra câu q09 trong trace thấy rõ: `"unknown error code + risk_high → human review | human approved → retrieval"`.
2. **An toàn (Safety):** Flag `risk_high` cho phép chặn yêu cầu có mã lỗi lạ `ERR-403-AUTH` để kích hoạt HITL. Trong 86 traces thực tế, có 5 lần HITL được trigger (5%).

**Trade-off đã chấp nhận:**
Hàm `compare_single_vs_multi()` phải đọc toàn bộ 86 trace files mỗi lần chạy, tốn I/O. Tuy nhiên, đây chỉ chạy offline nên không ảnh hưởng performance pipeline.

**Bằng chứng từ code (`graph.py`, dòng 114-117):**
```python
if risk_high and "err-" in task:
    route = "human_review"
    route_reason = "mã lỗi lạ + risk_high -> dừng lại cần human review"
```
Trace thực tế tại `artifacts/traces/q09.json`:
```json
{
  "route_reason": "unknown error code + risk_high → human review | human approved → retrieval",
  "hitl_triggered": true,
  "workers_called": ["human_review", "retrieval_worker", "synthesis_worker"]
}
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `latency_ms` luôn trả về `0` trong tất cả 15 trace files ban đầu (`q01.json` → `q15.json`).

**Symptom:**
Khi chạy `python eval_trace.py`, tất cả trace files ghi `"latency_ms": 0` và history ghi `"[graph] completed in 0ms"`. Điều này khiến `avg_latency_ms` trong `eval_report.json` cũng bằng 0, làm vô nghĩa việc so sánh hiệu năng Day 08 vs Day 09.

**Root cause:**
Lỗi nằm trong hàm `build_graph()` tại `graph.py` (dòng 241-250). Biến `start` được lấy bằng `time.time()`, nhưng trong giai đoạn Sprint 1 khi workers chỉ là placeholder (chạy sync, không có I/O thật), thời gian xử lý quá nhỏ (~microseconds). Kiểu `int()` làm tròn xuống 0:
```python
final_state["latency_ms"] = int((time.time() - start) * 1000)  # → 0ms khi chạy placeholder
```

**Cách sửa:**
Khi Workers thật được tích hợp (Sprint 3+), mỗi Worker gọi API Gemini nên latency tự nhiên tăng lên hàng nghìn ms. Tôi cũng cập nhật `analyze_traces()` trong `eval_trace.py` (dòng 225-227) để chỉ tính latency khi giá trị > 0:
```python
lat = t.get("latency_ms")
if lat:
    latencies.append(lat)
```

**Bằng chứng trước/sau:**
- **Trước (q01.json placeholder):** `"latency_ms": 0`, `"[graph] completed in 0ms"`
- **Sau (grading_run.jsonl — pipeline thật):** `gq01: 29,689ms`, `gq04: 7,173ms`, `gq07: 2,386ms`
- **Avg latency Day 09 (eval_report.json):** `6,271 ms` (tính từ 86 traces có latency > 0)

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Hệ thống hóa dữ liệu đánh giá. File `eval_report.json` tôi tạo ra chứa đầy đủ 7 metrics quan trọng: `total_traces` (86), `routing_distribution` (72% policy, 27% retrieval), `avg_confidence` (0.706), `avg_latency_ms` (6,271), `mcp_usage_rate` (58%), `hitl_rate` (5%), và `top_sources`. Tài liệu `docs/single_vs_multi_comparison.md` có bảng so sánh chi tiết 6 metrics giữa Day 08 và Day 09 với số liệu thực.

**Tôi làm chưa tốt:**
15 trace files ban đầu (q01-q15) vẫn chứa `final_answer` dạng `"[PLACEHOLDER]"` vì được tạo trước khi Workers thật hoàn thành. Tôi nên chạy lại các trace này sau Sprint 3 để có dữ liệu nhất quán.

**Nhóm phụ thuộc vào tôi ở đâu?**
Nếu không có `eval_trace.py` và `eval_report.json`, nhóm không có bằng chứng định lượng để chứng minh Multi-Agent tốt hơn Day 08 ở khía cạnh nào, không tính được score ước tính cho grading.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi phụ thuộc hoàn toàn vào Workers (Giang) và Supervisor (Hoàng, Hưng, Hùng, Hồng Anh). Nếu Workers trả về kết quả sai, trace file sẽ ghi nhận kết quả sai nhưng tôi không thể tự sửa logic business.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ bổ sung **breakdown theo category** vào `eval_report.json`: tách riêng `abstain_accuracy`, `multi_hop_accuracy`, và `simple_query_accuracy`. Hiện tại `eval_report.json` chỉ có aggregate metrics, dẫn đến `docs/single_vs_multi_comparison.md` phải ghi `N/A` ở mục abstain rate và multi-hop accuracy (dòng 21-22). Ngoài ra, tôi sẽ chạy lại 15 trace files (q01-q15) với Workers thật để xóa bỏ các `[PLACEHOLDER]` answer.

---
*Lưu file này với tên: `reports/individual/Nguyen_Thanh_Binh.md`*  
