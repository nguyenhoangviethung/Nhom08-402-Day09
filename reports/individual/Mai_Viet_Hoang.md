# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Mai Việt Hoàng  
**Vai trò trong nhóm:** Supervisor Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án Lab Day 09, tôi đảm nhận vai trò **Supervisor Owner** — người chịu trách nhiệm xây dựng "bộ não điều phối" của toàn hệ thống Multi-Agent trong Sprint 1.

**Module/file tôi chịu trách nhiệm:**
- Orchestrator chính: `graph.py` — bao gồm `AgentState`, `supervisor_node`, `route_decision`, `human_review_node`, và hàm `build_graph()`.

**Cách công việc của tôi kết nối với phần của thành viên khác:**  
`graph.py` là trung tâm kết nối toàn bộ hệ thống. Tôi định nghĩa `AgentState` — "hợp đồng dữ liệu" duy nhất xuyên suốt graph — để các Worker Owner (phụ trách Sprint 2) biết chính xác input/output nào họ cần đọc và ghi. Supervisor node chọn đúng worker để gọi, nên nếu logic routing sai thì toàn bộ pipeline bị ảnh hưởng.

**Bằng chứng:**
- File `graph.py` có `# Sprint 2+3: Kết nối đồ thị (Graph) với các Worker thực tế` trong docstring, thể hiện file này là nền tảng cho các sprint sau.
- Hàm `make_initial_state()` khởi tạo đầy đủ 16 trường của `AgentState`, đảm bảo contract không bị missing key khi worker khác truy cập.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Tách biệt hoàn toàn `route_decision()` khỏi `supervisor_node()` thành hai hàm riêng, thay vì gộp chung.

Khi thiết kế graph, cách đơn giản nhất là để `supervisor_node` vừa phân tích task vừa trả về route string trực tiếp. Tuy nhiên, LangGraph yêu cầu conditional edge phải là một hàm thuần túy nhận `state` và trả về tên node tiếp theo — không thể đồng thời cập nhật state. Nếu gộp chung, sẽ vi phạm nguyên tắc đơn trách nhiệm và gây lỗi khi compile graph.

**Lý do:**
1. **Đúng với LangGraph API:** `add_conditional_edges()` nhận một hàm `router` chỉ đọc state và trả về `Literal["retrieval_worker", "policy_tool_worker", "human_review"]`. Tách biệt `route_decision()` riêng giúp compiler không nhầm node với edge.
2. **Dễ mở rộng:** Sau này nếu cần thêm một worker mới, chỉ cần sửa hàm `route_decision()` và bảng routing trong `add_conditional_edges()`, không cần đụng vào `supervisor_node`.

**Trade-off đã chấp nhận:**  
Cần lưu `supervisor_route` vào `AgentState` như một trường trung gian để `route_decision` đọc lại. Điều này tạo ra một bước "write-then-read" bổ sung, nhưng đổi lại graph compile thành công và logic rõ ràng hơn.

**Bằng chứng từ code:**
```python
# supervisor_node ghi vào state
state["supervisor_route"] = route

# route_decision ĐỌC lại từ state (không ghi gì thêm)
def route_decision(state: AgentState) -> Literal[...]:
    return state.get("supervisor_route", "retrieval_worker")
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** `human_review_node` gây ra vòng lặp vô hạn (infinite loop) trong graph.

**Symptom (pipeline làm gì sai?):**  
Khi chạy một query chứa mã lỗi lạ (ví dụ `"ERR-403-AUTH"`), pipeline đi vào `human_review` đúng — nhưng sau đó bị kẹt. Graph cứ liên tục gọi lại `supervisor_node` thay vì tiếp tục sang `retrieval_worker`, khiến chương trình bị treo và phải Ctrl+C.

**Root cause:**  
Ban đầu tôi dùng `add_conditional_edges("human_review", route_decision, {...})` — tức là sau `human_review` thì lại qua `route_decision` để route tiếp. Nhưng bên trong `human_review_node`, tôi đặt `state["supervisor_route"] = "retrieval_worker"` với ý định sẽ đi đúng hướng. Vấn đề là conditional edge từ `human_review` thực chất đang map lại về `supervisor` vì bảng edges chưa khai báo đủ — dẫn đến vòng lặp.

**Cách sửa:**  
Thay `add_conditional_edges` bằng một **edge cố định** (fixed edge) từ `human_review` thẳng sang `retrieval_worker`:
```python
# Sai (gây loop):
# workflow.add_conditional_edges("human_review", route_decision)

# Đúng (fixed edge):
workflow.add_edge("human_review", "retrieval_worker")
```

**Bằng chứng trước/sau:**
- **Trước:** Query `"mã lỗi ERR-403-AUTH"` → terminal bị treo, phải kill process.
- **Sau:** Query tương tự → `[human_review] HITL triggered`, tự approve, đi tiếp sang `retrieval_worker` bình thường, in ra `final_answer` và lưu trace.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**  
Tôi làm tốt nhất ở việc thiết kế `AgentState` ngay từ đầu đủ đầy và nhất quán. 16 trường được khai báo với type rõ ràng, `make_initial_state()` đảm bảo không có `KeyError` khi workers truy cập. Điều này giúp Sprint 2 (workers) và Sprint 4 (trace) không phải quay lại sửa schema.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**  
Logic routing của tôi hiện dùng keyword matching đơn giản (check substring). Với câu hỏi tinh tế hơn như `"ai xử lý khi hệ thống sập lúc 3am?"`, hệ thống có thể route sai — cần LLM-based classification mới đáng tin cậy.

**Nhóm phụ thuộc vào tôi ở đâu?**  
Toàn bộ pipeline không thể chạy nếu `graph.py` chưa compile được. Worker Owner cần `AgentState` contract ổn định để viết `retrieval.py`, `policy_tool.py`, `synthesis.py`.

**Phần tôi phụ thuộc vào thành viên khác:**  
Tôi phụ thuộc vào Worker Owner để các hàm `retrieval_run`, `policy_tool_run`, `synthesis_run` trả đúng keys vào state. Nếu một worker ghi sai key name, graph sẽ fail silently.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ thay thế keyword matching bằng **LLM-based router**: thay vì check string `"hoàn tiền" in task`, tôi gọi một LLM với prompt phân loại ngắn, trả về JSON `{"route": "policy_tool_worker", "confidence": 0.92}`. Điều này giải quyết được các câu hỏi paraphrase phức tạp mà keyword cứng không nhận ra. Trace `q09` cho thấy một câu hỏi về contractor + emergency bị route về `retrieval` thay vì `policy_tool` — LLM router sẽ giải quyết đúng case này.

