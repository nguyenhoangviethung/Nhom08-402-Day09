# Single Agent vs Multi-Agent Comparison - Lab Day 09

**Nhom:** 08  
**Ngay cap nhat:** 2026-04-14  
**Nguon du lieu:** summary comparison duoc tao luc `2026-04-14T17:31:57.251544`

> Ghi chu:
> - Day 08 baseline da duoc load thanh cong.
> - Day 09 da co `86` trace de tong hop.
> - JSON tong hop hien tai chua co breakdown theo tung loai cau hoi, vi vay cac muc `abstain rate`, `multi-hop accuracy`, va phan tich chi tiet theo category van duoc ghi `N/A` neu chua suy ra duoc mot cach an toan.

---

## 1. Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chu |
|--------|------------------------|----------------------|-------|---------|
| So luong run/traces | N/A | 86 | N/A | JSON tong hop chi cho biet Day 09 co 86 trace |
| Avg confidence | 0.847 | 0.706 | -0.141 | Day 08 cao hon ve do tin cay trung binh |
| Avg latency (ms) | 2897 | 6271 | +3374 | Multi-agent cham hon do route worker va goi tool |
| Abstain rate (%) | N/A | N/A | N/A | Chua co breakdown abstain trong JSON tong hop |
| Multi-hop accuracy | N/A | N/A | N/A | Chua co metric accuracy theo nhom multi-hop |
| Routing visibility | Khong co route_reason | Co `route_reason` | N/A | Day 09 debug de hon ro ret |
| MCP usage rate | N/A | 50/86 (58%) | N/A | Day 08 khong co external tool orchestration tuong ung |
| HITL rate | N/A | 5/86 (5%) | N/A | Day 09 co co che human-in-the-loop |

**Nhan xet nhanh:** Day 09 hy sinh do tre va mot phan confidence trung binh de doi lay kha nang dieu phoi worker, goi external tools, va quan sat luong xu ly tot hon.

---

## 2. Phan tich theo loai cau hoi

### 2.1 Cau hoi don gian (single-document)

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | N/A |
| Latency | Co xu huong nhanh hon | Co xu huong cham hon |
| Observation | Kien truc don gian hon, it buoc xu ly hon | Van phai qua supervisor/worker nen ton overhead |

**Ket luan:** Voi cau hoi don gian, single-agent nhieu kha nang co loi ve toc do. Day 09 khong duoc cho thay loi the ve latency o snapshot hien tai.

### 2.2 Cau hoi multi-hop (cross-document)

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | N/A | N/A |
| Routing visible? | Khong | Co |
| Observation | Kho biet cau tra loi sai vi retrieve sai hay tong hop sai | Co route, co workers, co MCP usage, nen de truy nguyen luong xu ly hon |

**Ket luan:** Chua co so lieu accuracy de ket luan Day 09 dung hon, nhung Day 09 tot hon ro o kha nang quan sat va debug voi bai toan phuc tap.

### 2.3 Cau hoi can abstain

| Nhan xet | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | N/A | N/A |
| Hallucination cases | N/A | N/A |
| Observation | Chua co so lieu chi tiet | Chua co so lieu chi tiet |

**Ket luan:** Can them raw results hoac breakdown theo category de dien phan nay.

---

## 3. Debuggability Analysis

### Day 08 - Debug workflow

```text
Khi answer sai -> thuong phai doc lai pipeline retrieve + generate
-> kho biet loi nam o truy xuat, prompt, hay tong hop
-> khong co route_reason de truy vet
```

### Day 09 - Debug workflow

```text
Khi answer sai -> doc trace
-> xem supervisor_route + route_reason
-> xem worker nao da duoc goi
-> xem co MCP tool nao duoc goi hay khong
-> khoanh vung loi nhanh hon o routing, worker, hay tool
```

**Nhan xet:** Day 09 ro rang de debug hon Day 08 vi trace cho thay duoc luong di cua tung query. Day 08 co the nhanh hon, nhung Day 09 minh bach hon rat nhieu khi can dieu tra loi.

---

## 4. Extensibility Analysis

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Them 1 tool/API moi | Thuong phai chen truc tiep vao pipeline | Them tool va noi vao worker/MCP |
| Them 1 domain moi | De bi phinh prompt hoac logic | Co the them worker hoac them route rule |
| Thay doi retrieval strategy | Sua trong mot pipeline lien khoi | Sua retrieval layer rieng |
| A/B test mot phan | Kho tach rieng | De hon vi co the swap worker |

**Nhan xet:** Day 09 vuot troi ve extensibility. Con so `50/86 (58%)` cau co dung MCP cho thay kien truc nay da thuc su bat dau khai thac external capability thay vi chi tra loi trong mot pipeline dong.

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | Thuong it buoc hon | Thuong them buoc supervisor + worker |
| Complex query | Gioi han hon trong kha nang phan tach nhiem vu | Co the goi nhieu worker/tool hon |
| MCP tool call | N/A | 50/86 (58%) query co dung MCP |

**Nhan xet ve cost-benefit:**

- Day 09 cham hon Day 08 trung binh `3374 ms`.
- Day 09 co confidence trung binh thap hon `0.141` diem o snapshot hien tai.
- Doi lai, Day 09 co kha nang goi tool ben ngoai o `58%` so cau hoi va co HITL o `5%` so cau hoi.
- Dieu nay cho thay multi-agent phu hop hon cho bai toan can orchestration, trace, va mo rong capability; khong phai bai toan toi uu do tre.

---

## 6. Ket luan

**Multi-agent tot hon single agent o diem nao?**

1. De debug hon nho co `supervisor_route`, `route_reason`, va trace tung buoc.
2. De mo rong hon nho co worker architecture va MCP integration.
3. Xu ly bai toan can tool ben ngoai tot hon, the hien qua `50/86 (58%)` query co dung MCP.

**Multi-agent kem hon hoac khong khac biet o diem nao?**

1. Latency trung binh cao hon: `6271 ms` so voi `2897 ms`.
2. Confidence trung binh thap hon trong snapshot nay: `0.706` so voi `0.847`.

**Khi nao KHONG nen dung multi-agent?**

Khi bai toan chu yeu la hoi dap don gian, tai lieu it, khong can tool ben ngoai, khong can HITL, va uu tien quan trong nhat la toc do phan hoi.

**Neu tiep tuc phat trien he thong nay, nhom se them gi?**

1. Bo sung breakdown theo category de do `abstain rate` va `multi-hop accuracy`.
2. Luu them metrics chi phi nhu `llm_calls`, `prompt_tokens`, `completion_tokens`, va so tool call moi query.
3. Toi uu routing de giam latency cho cac cau hoi don gian, chi dung multi-agent day du khi query that su can.
