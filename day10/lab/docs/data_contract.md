# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| policy_export_dirty.csv | ETL Pipeline (CSV/Python) | Stale policy (14d refund), Duplicate text, Invalid Date | Quarantine count > 0 |
| Internal Knowledge Base | Manual Upload / Sync | Missing fields, Legacy Doc IDs | Freshness > 24h |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | ID ổn định sau clean (hash hoặc doc_id + seq) |
| doc_id | string | Có | Khóa logic tài liệu nguồn (vd: policy_refund_v4) |
| chunk_text | string | Có | Nội dung văn bản (min 8 chars) |
| effective_date | date | Có | Ngày hiệu lực (ISO YYYY-MM-DD) |
| exported_at | datetime | Có | Thời điểm export dữ liệu |

---

## 3. Quy tắc quarantine vs drop

- **Quarantine**: Mọi bản ghi không vượt qua baseline rules (unknown doc_id, sai format ngày, stale HR policy) sẽ được đẩy vào `artifacts/quarantine/`.
- **Drop**: Các bản ghi trùng lặp nội dung (`duplicate_chunk_text`) sẽ bị loại bỏ hoàn toàn, chỉ giữ lại bản ghi đầu tiên được tìm thấy.
- **Approval**: Data Quality Owner (AI Platform Team) sẽ review file quarantine định kỳ. Bản ghi chỉ được merge lại sau khi nguồn dữ liệu gốc được sửa chữa hoặc rules được cập nhật.

---

## 4. Phiên bản & canonical

- **Source of truth cho policy refund**: Tài liệu `data/docs/policy_refund_v4.txt`. Mọi chunk có nội dung "14 ngày làm việc" sẽ bị tự động sửa thành "7 ngày làm việc" trong pipeline.
- **HR Policy**: Chỉ chấp nhận các phiên bản có `effective_date` từ `2026-01-01` trở về sau.
- **IT Helpdesk**: Dựa trên `it_helpdesk_faq.txt` là bản mới nhất năm 2026.
