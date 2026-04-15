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

3.1. Drop Rules (Loại bỏ)
drop_duplicate_chunk_text: Nếu phát hiện trùng lặp nội dung hoàn toàn (chunk_text), pipeline chỉ giữ lại bản ghi đầu tiên và loại bỏ các bản ghi sau.

3.2. Quarantine Rules (Cách ly để Review)
Các bản ghi sau sẽ được đẩy vào artifacts/quarantine/ và không được đưa vào production:

unknown_doc_id: doc_id không nằm trong danh sách Allowlist (ví dụ: legacy_catalog_xyz).

hr_policy_freshness_cutoff: Các tài liệu HR (hr_leave_policy) có effective_date trước ngày 2026-01-01.

invalid_format: Sai định dạng ngày hoặc thiếu các trường bắt buộc (missing_effective_date).

3.3. Auto-fix Logic (Halt/Transform)
no_stale_refund_window: Nếu doc_id là policy_refund_v4 và nội dung chứa "14 ngày làm việc", pipeline phải tự động chuyển đổi (transform) thành "7 ngày làm việc" để đồng bộ với phiên bản mới nhất.

---

## 4. Phiên bản & canonical

| Doc ID | Path tài liệu gốc | Version |
|--------|------------------|----------|
| policy_refund_v4 | data/docs/policy_refund_v4.txt | 4.0 |
| it_helpdesk_faq | data/docs/it_helpdesk_faq.txt | 2026 |
| hr_leave_policy | data/docs/hr_leave_policy.txt | >= 2026 |
| sla_p1_2026 | data/docs/sla_p1_2026.txt | 2026 |