# Quality report — Lab Day 10 (nhóm)

**run_id:** `2026-04-15T09-00Z` (Trước) / `2026-04-15T08-27Z` (Sau)  
**Ngày:** 15/4/2026

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước | Sau | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 13 | Sau đổi mới tăng thêm dữ liệu (có lỗi) |
| cleaned_records | 6 | 6 | Không đổi |
| quarantine_records | 4 | 7 | Tăng do pipeline bắt nhiều lỗi mới hơn |
| Expectation halt? | Fail 1 ở refund_no_stale_14d_window | Fail 1 ở refund_no_stale_14d_window | Đều dùng cờ `--skip-validate` để tiếp tục |

---

## 2. Before / after retrieval (bắt buộc)

> Đính kèm hoặc dẫn link tới `artifacts/eval/before_after_eval.csv` (hoặc 2 file before/after).
*Đã chạy pipeline để generate `artifacts/eval/eval_after.csv`*.

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước (Lỗi dữ liệu - corrupted pipeline):** 
```csv
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,"Yêu cầu hoàn tiền được chấp nhận trong vòng 14 ngày làm việc kể từ khi xác nhận đơn hàng.",no,yes,,3
```
Đoạn trích (chunk) bị lọt tệp bản cũ (`policy-v3`) lỗi chứa thời hạn "14 ngày" vào top retrieval.

**Sau (Quá trình cleanup cải thiện):**
```csv
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,yes,yes,,3
```
Top-k trả về văn bản của rule 7 ngày mới nhất, có chứa thông tin kỳ vọng (`contains_expected`: yes). Tuy nhiên Expectation vẫn fail tại rule `refund` do vẫn đang override `--no-refund-fix`.

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

---

## 3. Freshness & monitor

> Kết quả `freshness_check` (PASS/WARN/FAIL) và giải thích SLA bạn chọn.
Kết quả `freshness_check` = FAIL 
Log: `{"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 120.465, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}`

**Giải thích:** SLA ở đây được đặt là 24.0 giờ, có nghĩa là dữ liệu không được phép cũ/đình trệ quá 1 ngày. Tuy nhiên, `latest_exported_at` thu được trong database lại là `2026-04-10T08:00:00`, tổng cộng là hơn 120 giờ cũ đi (`age_hours: 120.465`). Vì lỗi vi phạm ngưỡng `sla_hours`, `freshness_check` sẽ trả về `FAIL`.

---

## 4. Corruption inject (Sprint 3)

> Mô tả cố ý làm hỏng dữ liệu kiểu gì (duplicate / stale / sai format) và cách phát hiện.

Qua các file metrics của log phân loại (`_impact_metrics_quarantine_breakdown`), chúng ta có thể thấy dữ liệu đã bị tiêm (inject) các kiểu hỏng (corruption) như sau:
- **Duplicate:** Lỗi `duplicate_chunk_text`.
- **Missing Data:** Lỗi `missing_effective_date`.
- **Stale:** Ngày trễ quy định, thể hiện ở các lỗi `stale_hr_policy_effective_date` và Expectation Halt fail tại rule `refund_no_stale_14d_window`.
- **Invalid ID:** Lỗi `unknown_doc_id`.
- **Format Errors (đã inject ở "Sau"):** Lỗi `hidden_char_in_chunk_text`, `chunk_text_too_short`, `sla_p1_response_too_long`.

**Cách phát hiện:** 
Pipeline đã cài cắm danh sách các `Expectations` (luật kiểm duyệt chất lượng dựa theo các expectation rules). Hệ thống sẽ chặn hoặc cảnh báo lại khi bản ghi không qua rule để tiến hành gắn cờ cách ly (vào nhóm `quarantine_records`).

---

## 5. Hạn chế & việc chưa làm

- Chưa thu thập và đánh giá được dữ liệu thực tế top-k của Retrieve (Do phần Before / After Retrieval đang chờ để chạy script và copy paste dữ liệu đánh giá).
- Quá nhiều records bị quarantine (7/13 sau Retrieval chạy), pipeline đang phải phụ thuộc vào cờ cảnh báo rủi ro `--skip-validate` báo lỗi tiếp tục embed tạm qua mặt. Cần dùng script để sửa chữa dữ liệu như `--refund-fix` để làm sạch và nâng tỷ lệ Cleaned records lên.
