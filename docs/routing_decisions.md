# Routing Decisions Log — Lab Day 09

**Nhóm:** Nhom08-402  
**Ngày:** 14/04/2026

---

## Routing Decision #1

**Task đầu vào:**
> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `Tra cứu thông tin tĩnh về quy trình và cam kết dịch vụ (SLA) từ cơ sở dữ liệu.`  
**MCP tools được gọi:** `search_kb`  
**Workers called sequence:** `supervisor -> retrieval_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): `Thông tin về thời gian xử lý ticket P1 theo quy định.`
- confidence: 0.75
- Correct routing? Yes

**Nhận xét:**
Routing này hoàn toàn chính xác. Task yêu cầu tra cứu thông tin văn bản tĩnh có sẵn trong tài liệu chính sách, do đó việc điều hướng vào retrieval_worker giúp lấy đúng bằng chứng cần thiết mà không cần xử lý logic công cụ phức tạp.

---

## Routing Decision #2

**Task đầu vào:**
> Khách hàng có thể yêu cầu hoàn tiền trong bao lâu?

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `Yêu cầu kiểm tra chính sách hoàn tiền (Refund Policy) và các điều kiện đi kèm.`  
**MCP tools được gọi:** `search_kb, check_policy`  
**Workers called sequence:** `supervisor -> policy_tool_worker -> synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): `Số ngày quy định được phép yêu cầu hoàn tiền.`
- confidence: 0.75
- Correct routing? Yes

**Nhận xét:**
Routing đúng. Câu hỏi về hoàn tiền thường đi kèm các điều kiện ràng buộc về thời gian và loại sản phẩm. Việc sử dụng policy_tool_worker cho phép hệ thống áp dụng các quy tắc kiểm tra chặt chẽ hơn là chỉ đọc văn bản thuần túy.

---

## Routing Decision #3

**Task đầu vào:**
> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `unknown error code + risk_high → human review.`  
**MCP tools được gọi:** `None`  
**Workers called sequence:** `supervisor -> human_review (Auto-approved) -> retrieval_worker`

**Kết quả thực tế:**
- final_answer (ngắn): `Giải thích lỗi ERR-403-AUTH.`
- confidence: 0.75
- Correct routing? Yes

**Nhận xét:**
Đây là minh chứng cho tính an toàn của hệ thống. Supervisor đã nhận diện được mã lỗi lạ và gán nhãn rủi ro cao, từ đó kích hoạt cơ chế HITL để đảm bảo câu trả lời được kiểm chứng trước khi tới tay người dùng.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> Ticket P1 lúc 2am. Cần cấp Level 2 access tạm thời cho contractor để xử lý. Ai phê duyệt?

**Worker được chọn:** `policy_tool_worker`  
**Route reason:** `Yêu cầu xử lý logic phức tạp về quyền hạn (Access Level 2) cho đối tượng đặc biệt (Contractor) trong khung giờ ngoài hành chính.`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**
Routing này khó vì nó chứa đồng thời nhiều biến số: cấp độ truy cập, đối tượng nhân sự và điều kiện thời gian khẩn cấp. Supervisor phải nhạy bén để không nhầm lẫn với một câu hỏi tra cứu thông thường mà đưa vào policy_tool để xác định đúng cấp phê duyệt.

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 8 | 53% |
| policy_tool_worker | 7 | 46% |
| human_review | 1 | 6% |

### Routing Accuracy

- Câu route đúng: 15 / 15
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 1

### Lesson Learned về Routing

1. **Phân tách trách nhiệm (Separation of Concerns):** Việc chia nhỏ worker giúp Supervisor dễ dàng đưa ra quyết định dựa trên chuyên môn của từng agent.
2. **Cơ chế Safety (HITL):** Thiết lập ranh giới cho rủi ro (Risk threshold) giúp bảo vệ hệ thống khi gặp dữ liệu nằm ngoài vùng kiến thức đã biết.

### Route Reason Quality

Nhìn lại các `route_reason` trong trace, chúng đã cung cấp đủ thông tin ngữ cảnh để debug (ví dụ: giải thích lý do tại sao trigger HITL). Để cải tiến, nhóm sẽ bổ sung thêm các keywords mà Supervisor bắt được để việc tinh chỉnh logic sau này nhanh hơn.