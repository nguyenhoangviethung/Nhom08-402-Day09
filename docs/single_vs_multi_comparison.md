# Single Agent vs Multi-Agent Comparison - Lab Day 09

**Nhom:** 08  
**Ngay cap nhat:** 2026-04-14  
**Nguon du lieu thuc te dung de dien file nay:** `artifacts/traces/*.json` trong repo hien tai

> Ghi chu quan trong:
> - Repo hien tai khong co ket qua Day 08, vi vay cac cot `Day 08` duoc ghi `N/A` neu khong co so lieu thuc te.
> - Day 09 moi co 5 trace mau, va ca 5 deu la cung 1 cau hoi: "Can cap quyen Level 3 de khac phuc P1 khan cap. Quy trinh la gi?"
> - Trace Day 09 hien phan anh graph dang chay voi placeholder outputs trong `graph.py`, chua phai bo danh gia day du 15 cau hoi.

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chu |
|--------|------------------------|----------------------|-------|---------|
| So trace co trong repo | N/A | 5 | N/A | 5 trace deu duoc tao ngay 2026-04-14 |
| Avg confidence | N/A | 0.75 | N/A | Lay trung binh tu 5 file trace |
| Avg latency (ms) | N/A | 0.8 ms | N/A | Trung binh tu 5 trace: `0, 1, 3, 0, 0` |
| Abstain rate (%) | N/A | N/A | N/A | Khong co trace thuoc nhom abstain |
| Multi-hop accuracy | N/A | N/A | N/A | Khong co bo cham dung/sai cho cau multi-hop |
| Routing visibility | Khong co so lieu | Co `supervisor_route` va `route_reason` | N/A | Day 09 debug duoc theo tung buoc |
| MCP usage rate | N/A | 0/5 (0%) | N/A | Tat ca trace deu co `mcp_tools_used = []` |
| HITL rate | N/A | 0/5 (0%) | N/A | Tat ca trace deu co `hitl_triggered = false` |
| Avg workers called | N/A | 3 | N/A | Moi trace goi `policy_tool_worker`, `retrieval_worker`, `synthesis_worker` |

**Nhan xet nhanh:** Day 09 co uu diem ro rang nhat o kha nang quan sat luong xu ly. Tuy nhien, du lieu hien tai chua du de ket luan Day 09 tot hon Day 08 ve accuracy hay abstain quality.

---

## 2. Phan tich theo loai cau hoi

### 2.1 Cau hoi don gian (single-document)

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | N/A |
| Latency | N/A | N/A |
| Observation | Khong co ket qua Day 08 trong repo | Chua co trace cho nhom cau hoi single-document; 5 trace hien co deu la mot cau hoi policy + access + P1 |

**Ket luan:** Chua du so lieu thuc te de so sanh.

### 2.2 Cau hoi multi-hop (cross-document)

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | N/A |
| Routing visible? | N/A | Co |
| Observation | Khong co baseline Day 08 | Cac trace Day 09 cho thay supervisor route ve `policy_tool_worker`, sau do moi qua retrieval va synthesis |

**Ket luan:** Day 09 da cho thay route va chuoi worker duoc log ro, nhung chua co tap ket qua de tinh multi-hop accuracy.

### 2.3 Cau hoi can abstain

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | N/A | N/A |
| Hallucination cases | N/A | 5/5 trace hien co van la placeholder answer |
| Observation | Khong co ket qua Day 08 | `final_answer` trong 5 trace deu la chuoi `[PLACEHOLDER] ...`, nen chua danh gia duoc kha nang abstain that |

**Ket luan:** Day 09 hien chua dat muc co the danh gia abstain vi graph van dung output gia lap.

---

## 3. Debuggability Analysis

### Day 08 - Debug workflow

```text
Khong co trace Day 08 trong repo hien tai.
Vi vay khong do duoc thoi gian debug thuc te.
```

### Day 09 - Debug workflow

```text
Khi answer sai -> mo file trace JSON
-> xem supervisor_route + route_reason
-> xem workers_called
-> doi chieu voi graph.py
-> xac dinh ngay duoc loi dang nam o placeholder wrappers
```

**Mot lan debug thuc te co the chi ra tu trace hien co:**

- Cau hoi la ve `Level 3 access` va `P1 khan cap`, nhung `retrieved_sources` lai chi co `sla_p1_2026.txt`.
- `policy_result.policy_name` trong 5 trace deu la `refund_policy_v4`, khong khop voi bai toan access control.
- `final_answer` van la `[PLACEHOLDER] ...`.
- Doi chieu voi [graph.py](/c:/Users/hoang/Documents/Nhom08-402-Day09/graph.py) cho thay `retrieval_worker_node`, `policy_tool_worker_node`, va `synthesis_worker_node` dang hard-code output thay vi goi `workers/*.py`.

**Ket luan debug:** Day 09 de khoanh vung loi hon Day 08 vi trace chi ra rat nhanh rang van de nam o orchestration wrappers, khong phai do kho truy vet toan pipeline.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Them 1 tool/API moi | N/A trong repo hien tai | Kien truc ho tro tot hon: co `mcp_tools_used`, `needs_tool`, `policy_tool_worker` |
| Them 1 domain moi | N/A | Co the tach them worker moi ma khong can sua tat ca thanh phan |
| Thay doi retrieval strategy | N/A | Co the sua rieng [workers/retrieval.py](/c:/Users/hoang/Documents/Nhom08-402-Day09/workers/retrieval.py) |
| A/B test mot phan | N/A | De hon vi moi worker co contract rieng |

**Nhan xet:** Ve mat thiet ke, Day 09 mo rong tot hon. Ve mat thuc thi, repo hien tai van chua noi `graph.py` sang worker implementation that, nen tinh mo rong moi dung o muc kien truc.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | N/A | N/A |
| Complex query | N/A | N/A |
| MCP tool call | N/A | 0 trong 5 trace hien co |

**Nhan xet ve cost-benefit:**

- Tu trace hien co, Day 09 goi trung binh 3 worker cho moi cau hoi.
- Tuy nhien, trace khong log so LLM calls thuc te.
- Doi chieu ma nguon cho thay `graph.py` dang dung placeholder wrappers, nen 5 trace hien tai chua chung minh duoc chi phi LLM/MCP that.
- Vi vay, nhom chi nen ket luan chac chan rang Day 09 tang chi phi dieu phoi worker, con chi phi model that can phai do lai sau khi graph goi truc tiep `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`.

---

## 6. Ket luan

**Multi-agent tot hon single agent o diem nao?**

1. Quan sat va debug tot hon nho co `supervisor_route`, `route_reason`, `workers_called`.
2. De tach nhiem vu va mo rong kien truc hon, vi retrieval, policy, synthesis duoc tach thanh module rieng.

**Multi-agent kem hon hoac chua khac biet o diem nao?**

1. Chua co bang chung thuc nghiem trong repo de noi tot hon ve accuracy, abstain, hay multi-hop.
2. Overhead dieu phoi cao hon: moi trace Day 09 hien goi 3 workers cho 1 query.

**Khi nao KHONG nen dung multi-agent?**

Khi bai toan chi la hoi dap don gian, khong can route, khong can tool, khong can trace chi tiet, va uu tien lon nhat la do tre thap va pipeline gon nhe.

**Neu tiep tuc phat trien he thong nay, nhom se them gi?**

1. Noi `graph.py` sang worker implementations that thay vi placeholder outputs.
2. Chay du 15 test questions trong `data/test_questions.json` de co metrics that cho abstain va multi-hop.
3. Luu them `llm_calls`, `prompt_tokens`, `completion_tokens`, `mcp_count` vao trace de so sanh chi phi ro rang hon voi Day 08.
