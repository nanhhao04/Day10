# Kiến trúc pipeline — Lab Day 10

**Nhóm:** C401-Table-E1  
**Cập nhật:** 15/04/2026

---

## 1. Sơ đồ luồng (bắt buộc có 1 diagram: Mermaid / ASCII)

```
graph TD
    Start((Start)) --> Ingest[Node: Ingest_CSV_KB]
    Ingest --> Transform[Node: Text_Transformer]
    
    subgraph "LangGraph State Loop"
    Transform --> Validate{Node: Contract_Validator}
    Validate -- "Fail (Quarantine)" --> Q_Node[Node: Write_Quarantine]
    Validate -- "Pass" --> Embed_Node[Node: GitHub_Embedding]
    end

    Embed_Node --> Chroma[Node: Upsert_ChromaDB]
    Chroma --> End((End/Ready for Retrieval))

    %% Monitoring & Metadata
    M1[Freshness Monitor] -.->|Check timestamp| Embed_Node
    R1[Run_ID Tracker] -.->|Log state| Validate
```

> Vẽ thêm: điểm đo **freshness**, chỗ ghi **run_id**, và file **quarantine**.

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input | Output | Owner nhóm |
|------------|-------|--------|-------------|
| Ingest | policy_export_dirty.csv | State: raw_chunks | Data Analyst |
| Transform | raw_chunks | State: cleaned_chunks (Auto-fix 14d -> 7d) | Prototype Lead |
| Quality | cleaned_chunks | valid_chunks OR quarantine_record | Data Analyst |
| Embed | valid_chunks | Vectors (via GitHub Models API) | Prototype Lead |
| Monitor | Graph State | Alert #alerts-data-quality | Team Lead |

---

## 3. Idempotency & rerun

- Strategy: Hash-based Upsert.

- Mô tả: chunk_id được tạo bằng cách hash nội dung chunk_text kết hợp với doc_id.

- Cơ chế: Trong LangGraph, trước khi đẩy vào ChromaDB, một bước kiểm tra ID sẽ được thực hiện. Nếu chunk_id đã tồn tại và nội dung không đổi, node sẽ bỏ qua (skip) việc gọi API GitHub Models để tiết kiệm token và tránh duplicate vector.

- Rerun: Có thể rerun pipeline thoải mái với cùng một bộ data mà không sợ làm "rác" Vector DB.

---

## 4. Liên hệ Day 09

- Sự kết nối: Corpus sau khi được validate và embed qua pipeline này sẽ là nguồn dữ liệu duy nhất (Single Source of Truth) cho Agent ở Lab Day 09.

- Cải thiện: Thay vì để Agent tự đọc file .txt thô, ta cung cấp một Chroma Retriever đã qua lọc. Điều này đảm bảo khi người dùng hỏi về "Hoàn tiền", Agent luôn lấy được thông tin "7 ngày" (đã fix) thay vì "14 ngày" (stale) từ file dirty ban đầu.
---

## 5. Rủi ro đã biết

- GitHub Models Rate Limit: Do sử dụng mô hình qua API, nếu đẩy lượng lớn dữ liệu cùng lúc có thể bị giới hạn rate limit. Giải pháp: Implement cơ chế "Batching" trong node Embedding.

- State Complexity: LangGraph state có thể trở nên nặng nếu lưu quá nhiều chunk_text trong bộ nhớ. Giải pháp: Lưu trung gian qua file .parquet cho các tập dữ liệu lớn.

- Validation Strictness: Nếu rule trong data_contract.yaml quá chặt, tỷ lệ data rơi vào Quarantine sẽ cao, gây thiếu hụt tri thức cho Agent.
