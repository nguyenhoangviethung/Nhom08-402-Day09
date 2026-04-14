# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Hoàng Đức Hưng  
**Vai trò trong nhóm:** Tech Lead  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong Lab Day 09, tôi phụ trách các phần việc thiên về hạ tầng orchestration và tài liệu, kỹ thuật: tách phần MCP thành `mcp_server.py` và `mcp_tools.py`, xử lý lỗi worker liên quan đến thiếu thư viện, và viết hai tài liệu phân tích `docs/routing_decisions.md` cùng `docs/single_vs_multi_comparison.md`.

Phần tôi làm kết nối trực tiếp với các thành viên khác ở chỗ: worker muốn gọi được tool thì phải có một lớp server/dispatch ổn định; còn khi nhóm cần giải thích vì sao hệ thống route như vậy hoặc Multi-Agent khác gì Single Agent thì phải có tài liệu tổng hợp số liệu và case thực tế. Nói cách khác, tôi không chỉ làm phần chạy được, mà còn làm phần để cả nhóm nhìn rõ hệ thống đang hoạt động như thế nào.

**Bằng chứng cụ thể:**
- Commit `856afb3` với mô tả `tách function` tác động trực tiếp lên `mcp_server.py` và tạo `mcp_tools.py`.
- `mcp_server.py` giữ vai trò khai báo tool schemas, registry, dispatch và lớp HTTP cho MCP server.
- `mcp_tools.py` tách riêng phần triển khai tool như `tool_search_kb`, `tool_get_ticket_info`, `tool_check_access_permission`, `tool_create_ticket`.
- `docs/routing_decisions.md` tổng hợp 4 tình huống route tiêu biểu và thống kê `15/15` route đúng.
- `docs/single_vs_multi_comparison.md` tổng hợp snapshot `86` trace của Day 09 để so sánh với Day 08.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

Quyết định kỹ thuật quan trọng nhất tôi muốn nhấn mạnh trong phần mình tham gia là **tách phần MCP thành hai lớp rõ ràng**: `mcp_server.py` phụ trách giao diện server/HTTP và `mcp_tools.py` phụ trách logic thực thi tool. Tôi chọn hướng này thay vì dồn tất cả vào một file vì trong bối cảnh lab, nhóm cần code vừa dễ test bằng tay, vừa dễ sửa khi thêm tool mới.

Cụ thể, sau khi tách, `mcp_server.py` tập trung vào `TOOL_SCHEMAS`, `TOOL_REGISTRY`, `dispatch_tool()` và các endpoint `/tools`, còn `mcp_tools.py` chứa phần implementation thật của từng tool. Ví dụ, `tool_search_kb()` gọi `retrieve_hybrid()` để truy vấn KB, còn `tool_get_ticket_info()` và `tool_check_access_permission()` xử lý dữ liệu mock theo từng nghiệp vụ. Cách tách này làm ranh giới trách nhiệm rõ hơn: sửa contract hoặc endpoint thì nhìn vào server, còn sửa logic tool thì nhìn vào file tools.

Trade-off của quyết định này là số file tăng lên và người đọc phải theo dõi qua hai nơi thay vì một. Tuy nhiên, tôi chấp nhận đánh đổi vì lợi ích lớn hơn là dễ debug, dễ test endpoint, và phù hợp với định hướng multi-agent có tool orchestration của nhóm.

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

Lỗi tôi xử lý là tình huống worker bị lỗi khi môi trường chưa đủ thư viện. Trong thực tế làm lab, đây là lỗi rất dễ xảy ra: code có thể chạy trên máy người này nhưng fail trên máy khác chỉ vì thiếu `sentence-transformers`, `chromadb`, `fastapi` hoặc `uvicorn`.

Tôi tiếp cận lỗi này theo hai hướng. Thứ nhất là làm cho worker bớt “giòn” hơn trước sự thiếu hụt dependency. Ở `workers/retrieval.py:45-84`, luồng embedding được thiết kế fallback theo thứ tự: thử `SentenceTransformer`, nếu không được thì thử OpenAI embeddings, cuối cùng mới dùng random embedding để debug luồng code. Cách này giúp worker không đổ vỡ ngay từ bước import khi thiếu thư viện cục bộ. Thứ hai là đồng bộ lại phần khai báo môi trường trong `requirements.txt`, nơi đã liệt kê các thư viện quan trọng như `chromadb`, `sentence-transformers`, `fastapi`, `uvicorn` để nhóm cài đặt nhất quán hơn.

Với `mcp_server.py`, tôi cũng xử lý thêm trường hợp thiếu `FastAPI` bằng warning có hướng dẫn cài đặt cụ thể (`mcp_server.py:128-130`). Điểm tôi rút ra là trong hệ multi-agent, một lỗi dependency nhỏ ở worker có thể làm gãy cả pipeline; vì vậy sửa lỗi không chỉ là “cài cho chạy”, mà là làm cho hệ thống thất bại theo cách dễ hiểu và dễ khôi phục hơn.

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

Điểm tôi làm tốt nhất là biến phần kỹ thuật của nhóm thành thứ có thể vận hành và có thể giải thích. Ở `docs/routing_decisions.md`, tôi chốt lại được các case route quan trọng như câu SLA đi vào `retrieval_worker`, câu refund đi vào `policy_tool_worker`, và case `ERR-403-AUTH` phải kích hoạt `human_review`. Ở phần so sánh Day 08 và Day 09, tôi không mô tả cảm tính mà dựa vào số liệu cụ thể: `86` trace, `58%` query có dùng MCP, `5%` query có HITL, latency trung bình tăng từ `2897 ms` lên `6271 ms`.

Điểm tôi còn làm chưa tốt là phần breakdown theo từng loại câu hỏi trong tài liệu so sánh vẫn còn `N/A` ở một số mục như `abstain rate` hay `multi-hop accuracy`, vì dữ liệu snapshot hiện tại chưa đủ sạch để suy luận an toàn. Nếu có thêm thời gian, tôi sẽ làm tiếp phần này để báo cáo thuyết phục hơn.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Nếu có thêm 2 giờ, tôi sẽ tách riêng phần trace summary thành một script tạo báo cáo tự động thay vì cập nhật tay trong Markdown. Mục tiêu là mỗi lần chạy eval xong, nhóm có thể sinh ngay bảng so sánh mới cho `routing accuracy`, `MCP usage`, `HITL rate`, `latency`, và breakdown theo category. Làm vậy sẽ giúp `single_vs_multi_comparison.md` bớt thủ công, đồng thời hỗ trợ nhóm debug nhanh hơn khi tiếp tục tinh chỉnh supervisor và worker.


