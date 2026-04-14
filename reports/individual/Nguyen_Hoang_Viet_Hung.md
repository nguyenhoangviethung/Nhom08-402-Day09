# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Hoàng Việt Hùng  
**Vai trò trong nhóm:** Tech Lead, Trace Owner  
**Ngày nộp:** 14/04/2026  
**Độ dài yêu cầu:** 500–800 từ

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

Trong dự án Lab Day 09, tôi đảm nhận vai trò **Tech Lead & Workers Owner** — người chịu trách nhiệm review tất cả mã nguồn tất cả các thành viên, hỗ trợ các tech lead khác, xử lý conflict và match các component.

**Module/file tôi chịu trách nhiệm:**
- Orchestrator chính: `eval.py` (Day08), `eval_trace.py` (Hỗ trợ fix bug và match sau phần của Binh (một Trace Owner khác)), `artifacts/` bao gồm log, trace, baseline Day 08, *.json .
- _estimate_confidence để tính lại điểm cho retrieve_hybrid bới chương trình mới chỉ có source code cho retrieve_dense
**Cách công việc của tôi kết nối với phần của thành viên khác:**  
- Match tất cả thành phần với nhau, cùng với Bình chạy test_question và grading_question, tìm các bug bị lỗi vào sửa các logic trong graph.py
- Sửa lại đánh giá baseline cho single_agent cho có cùng thang đo đánh giá với multi_agent

**Bằng chứng:**
- Các file tôi đã thực hiện, các log tôi đã ghi đều có commit ghi lại
- Việc tôi có commit ở gần như tất cả các file kể cả module của người khác là do tôi là người review cuối cùng và chỉnh sửa lại những gì chưa hợp lý,
  chưa liên kết với nhau.
---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Viết lại hàm tính điểm confidence_score là quyết định của tôi, tôi dùng llm as judge.

Bởi dùng hybrid_search thì điểm confidence theo như origin code sẽ không thể vượt quá 0.5 (hoặc con số nào đó xấp xỉ)
**Lý do:**
1. **Đúng với thang điểm thực tế của hybird:** Sau khi sửa, chấm điểm của hybrid
2. **Dễ tận dụng mã nguồn**: không chỉ chấm confidence score cho hybrid mà còn của dense hay bất kì kĩ thuật retrieve nào đều có giống nhau, cùng 1 thang đo, dễ maintance. 

**Trade-off đã chấp nhận:**  
Tốn token mỗi lần sử dụng llm as judge và thời giang latency tăng.
**Bằng chứng từ code:**
```python
def _estimate_confidence(task: str, chunks: list, answer: str, policy_result: dict) -> float:
    """
    Sử dụng LLM-as-a-Judge để tự động chấm điểm độ tin cậy (Confidence Score).
    """
    # 1. Bắt các trường hợp rỗng hoặc từ chối trả lời
    if not chunks or "không đủ thông tin" in answer.lower():
        return 0.1

    # 2. Chuẩn bị dữ liệu cho Giám khảo LLM
    context_text = "\n".join([c.get("text", "") for c in chunks])
    if policy_result and policy_result.get("exceptions_found"):
        context_text += "\n[NGOẠI LỆ CHÍNH SÁCH]: " + str(policy_result.get("exceptions_found"))

    judge_prompt = f"""Bạn là một giám khảo độc lập (LLM-as-a-Judge).
    Nhiệm vụ: Đánh giá độ tin cậy (confidence score) của Câu trả lời so với Ngữ cảnh được cung cấp.

    Câu hỏi từ người dùng: {task}
    Ngữ cảnh có sẵn: {context_text}
    Câu trả lời cần chấm: {answer}

    Tiêu chí chấm điểm (0.0 đến 1.0):
    - 0.9 - 1.0: Câu trả lời chính xác, giải quyết trọn vẹn câu hỏi, được trích xuất hoàn toàn từ ngữ cảnh.
    - 0.7 - 0.89: Trả lời đúng phần lớn nhưng ngữ cảnh hỗ trợ hơi yếu hoặc thiếu một chút chi tiết.
    - 0.4 - 0.69: Trả lời chung chung, hoặc ngữ cảnh không thực sự sát với câu hỏi.
    - 0.1 - 0.39: Lạc đề, bịa đặt (hallucination), hoặc câu trả lời nói rằng không đủ thông tin.

    Trả về ĐÚNG định dạng JSON:
    {{
        "confidence": <float>,
        "reasoning": "<giải thích ngắn gọn 1 câu tại sao cho điểm này>"
    }}
    """

    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": judge_prompt}],
            temperature=0.0, # Nhiệt độ 0 để AI chấm điểm khách quan và ổn định nhất
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        conf = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")
        
        # In log ra màn hình để bạn dễ theo dõi AI đang "nghĩ" gì
        print(f"  [LLM Judge] Chấm: {conf} | Lý do: {reasoning}")

        # Vẫn phạt nhẹ nếu dính ngoại lệ chính sách (do tính chất phức tạp)
        penalty = 0.05 * len(policy_result.get("exceptions_found", []))
        final_conf = max(0.1, min(0.98, conf - penalty))
        
        return round(final_conf, 2)
        
    except Exception as e:
        print(f"  [LLM Judge] Lỗi khi chấm điểm: {e}. Fallback về mức 0.5")
        return 0.5
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** confidence score luôn trả về 0.75

**Symptom (pipeline làm gì sai?):**  
Đây là lỗi do graph.py quên gọi các hàm worker đúng.
**Root cause:**  
Ban đầu, graph khi thực thi đã hardcode confidence score là 0.75, đây là sự khập khiễng. Theo tôi, chương trình nên thiết kế để mỗi sprint khi nào hoàn thành 
không gây ảnh hưởng đến sprint trước đó.
**Cách sửa:**  
import _estimate_confidence mới thay vì hardcode
```python
# Sai:
def synthesis_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi synthesis worker."""
    # TODO Sprint 2: Thay bằng synthesis_run(state)
    state["workers_called"].append("synthesis_worker")
    state["history"].append("[synthesis_worker] called")

    # Placeholder output
    chunks = state.get("retrieved_chunks", [])
    sources = state.get("retrieved_sources", [])
    state["final_answer"] = f"[PLACEHOLDER] Câu trả lời được tổng hợp từ {len(chunks)} chunks."
    state["sources"] = sources
    state["confidence"] = 0.75
    state["history"].append(f"[synthesis_worker] answer generated, confidence={state['confidence']}")
    return state

# Đúng:
def synthesis_worker_node(state: AgentState) -> AgentState:
    """Wrapper gọi synthesis worker thực tế."""
    return synthesis_run(state)
```

**Bằng chứng trước/sau:**
- **Trước:** confidence_score = 0.75
- **Sau:** confidence_score được tính chính xác

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**  
Với vai trò như một lead, tôi quản lý mã nguồn của team không bị conflict với nhau. Hỗ trợ gần như tất cả component, tôi cảm thấy tôi làm tròn vai, có chút tốt.
**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**  
Chưa thể phát hiện sớm các bug, 1 phần do kinh nghiệm chưa phong phú, 1 phần do team còn vibe coding mất thời gian hiểu mã nguồn.
**Nhóm phụ thuộc vào tôi ở đâu?**  
Không có matching giữa các component thì không thể hoàn thành pipeline hay loop agent.
**Phần tôi phụ thuộc vào thành viên khác:**  
Không có
---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

- Tôi sẽ cố gắng hoàn thiện human-in-loop. Bình đã cố gắng hoàn thiện 1 phần tuy nhiên đó chưa thể đưa lên UX. Tôi muốn dựng thêm 1 vài MCP như đọc pdf, đọc scan
hay MCP chunk khác thay vì đơn giản theo header, hay thử các với các format khác thay vì phụ thuộc vào lab08.
- Thử các cách embedding khác với tiếng việt, thay vì embedding token như hiện tại có thể bị lỗi do phiên âm.
