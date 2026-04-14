# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Thị Hương Giang 
**Vai trò trong nhóm:** Worker Owner 
**Ngày nộp:** 14/4/2026 
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

> Trong mô hình Supervisor-Worker của nhóm, tôi tham gia vào thiết kế và lập trình bao gồm 3 file: retrieval.py và synthesis.py, policy_tool.py.


**Module/file tôi chịu trách nhiệm:**
- workers/retrieval.py: Chuyển đổi câu hỏi thành vector bằng model BKAI (vietnamese-bi-encoder) và truy vấn không gian Vector trên ChromaDB.
- workers/synthesis.py: Tổng hợp dữ liệu từ Retrieval và Policy, ép Agent sinh câu trả lời Grounded (chỉ dựa trên tài liệu) bằng gpt-4o-mini.

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Tôi tạo ra giao thức trạng thái, thành viên khác viết graph.py sẽ dựa vào các key như retrieved_chunks hoặc policy_result do các Worker của tôi trả về để quyết định bước tiếp theo trong Graph.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

Commit lịch sử chỉnh sửa các file trong thư mục workers/. Cụ thể là việc tôi viết lại hàm _build_context trong synthesis.py để ưu tiên hiển thị Exception Rule.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)


**Quyết định:** Áp dụng mô hình Hybrid 


**Lý do:**

Các mô hình ngôn ngữ (như gpt-4o-mini) rất giỏi đọc hiểu ngữ cảnh, nhưng lại dễ bị "ảo giác" (hallucination) với các quy định mang tính tuyệt đối (như: "Flash Sale thì không được hoàn tiền"). Nếu chỉ dùng LLM, tỷ lệ sai sót (False Positive) khi khách hàng cố tình dùng prompt lắt léo là khá cao. Do đó, tôi dùng LLM để phân tích mềm, nhưng dùng các câu lệnh if-else cứng để kiểm tra từ khóa "Flash sale" làm chốt chặn cuối cùng.

**Trade-off đã chấp nhận:**

việc bảo trì các quy tắc (Rule) cứng sẽ mất thời gian hơn so với việc chỉ viết một câu Prompt duy nhất cho LLM.

**Bằng chứng từ trace/code:**
```python
# Trích xuất từ workers/policy_tool.py
# 1. Gọi LLM để phân tích mềm (trả về JSON)
analysis = json.loads(response.choices[0].message.content)

# 2. Rule-based check (Bảo hiểm cho LLM)
if "flash sale" in task_lower and not any(ex['type'] == 'flash_sale' for ex in analysis.get('exceptions_found', [])):
    analysis['policy_applies'] = False
    analysis.setdefault('exceptions_found', []).append({
        "type": "flash_sale_hard_rule",
        "rule": "Đơn hàng Flash Sale tuyệt đối không hoàn tiền."
    })

```
---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Hệ thống gặp lỗi Silent Crash hoặc báo lỗi WinError 1114 khi chạy retrieval.py và index.py.

**Symptom (pipeline làm gì sai?):**

Khi chạy truy vấn, terminal hiện "Đang truy tìm dữ liệu..." rồi văng ra màn hình chờ hoặc báo lỗi DLL c10.dll của thư viện torch mà không trả về bất kỳ kết quả nào. Điều này làm nghẽn toàn bộ luồng RAG.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở xung đột phiên bản Python. Khi khởi tạo dự án, môi trường ảo vô tình sử dụng Python 3.14 (bản thử nghiệm chưa tương thích với thư viện lõi của PyTorch và ChromaDB). Ngoài ra, trên nền tảng Windows, hệ thống chặn khởi tạo file DLL tính toán nặng khi không ở chế độ High Performance.

**Cách sửa:**

Sử dụng conda

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

Trước khi sửa (Log Traceback): OSError: [WinError 1114] A dynamic link library (DLL) initialization routine failed. Error loading "...\torch\lib\c10.dll"

Sau khi sửa (Log Console): [retrieval_worker] Đang truy tìm dữ liệu cho: 'SLA ticket P1 là bao lâu?'...
  [Debug] Đang biến câu hỏi thành vector...
  [Debug] Kích thước vector truy vấn: 768
  retrieval_worker test done.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Xây dựng được các hàm cốt lõi cho chương trình.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi mất khá nhiều thời gian ở bước cài đặt Python và venv, khiến việc tối ưu hóa điểm số score của Vector Search bị thu hẹp thời gian.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nếu tôi chưa xây dựng xong Contract đầu ra của các Worker (Ví dụ: format [{"text", "source", "score"}]), thành vien khác sẽ không thể viết code cho Supervisor trong graph.py để nối luồng dữ liệu được

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc vào phần Indexing. Nếu dữ liệu trong chromadb bị trống hoặc lệch số chiều vector, retrieval.py của tôi dù viết đúng cũng sẽ trả về 0 chunks.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ tích hợp Hybrid Retrieval (Dense + BM25) trực tiếp vào retrieval.py. Hiện tại truy vấn chỉ dùng Dense Search (Cosine Similarity). Trace logs cho thấy các câu hỏi chứa mã lỗi cụ thể (ví dụ: "Lỗi ERR-403-AUTH") có điểm số Cosine rất thấp. Việc thêm thuật toán BM25 (Sparse Search) và gộp bằng Reciprocal Rank Fusion (RRF) như ở Lab 8 sẽ giải quyết triệt để điểm mù này.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
