# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

- User/Agent: Khách hàng phản hồi chatbot vẫn báo thời hạn hoàn tiền là 14 ngày (thông tin cũ) thay vì 7 ngày.

- HR Query: Nhân viên hỏi về ngày phép năm, Agent trả lời 10 ngày (theo chính sách 2025) thay vì 12 ngày (2026).

- System: Retrieval bị "nhiễu" do xuất hiện các chunk dữ liệu chưa được làm sạch hoặc chưa được gán nhãn đúng.
---

## Detection

- Metric: quarantine_records trong manifest nhảy lên con số 4 (vượt ngưỡng cho phép của một đợt cập nhật nhỏ).

- Evaluation: Kết quả eval_retrieval.py báo hits_forbidden: yes cho câu hỏi q_leave_version.

- Freshness: latest_exported_at là 2026-04-10, trễ hơn 5 ngày so với thời điểm hiện tại (2026-04-15), vi phạm SLA 24h.

---

## Diagnosis

| Bước | Việc làm | Kết quả mong đợi |
|------|----------|--------------------------------------|
| 1 | Kiểm tra manifest.json | Thấy raw_records: 10 nhưng chỉ có 6 records được nạp. no_refund_fix: false cho thấy logic auto-fix chưa được thực thi triệt để. |
| 2 | Mở quarantine.csv | Phát hiện record #7 bị chặn do stale_hr_policy_effective_date (năm 2025) và record #9 bị chặn do unknown_doc_id. |
| 3 | Chạy python eval_retrieval.py | Kiểm tra top-k. Nếu policy_refund_v4 vẫn chứa text "14 ngày", chứng tỏ node Transform trong LangGraph bị skip hoặc lỗi regex. |

---

## Mitigation

- Manual Auto-fix: Chạy script transform_refund.py để ép toàn bộ chunk thuộc policy_refund_v4 có chứa "14 ngày" thành "7 ngày".

- Clear Stale Vectors: Xóa các vector có effective_date < 2026-01-01 trong collection day10_kb của ChromaDB.

- Rerun Pipeline: Trigger lại LangGraph với file policy_export_dirty.csv sau khi đã cập nhật allowed_doc_ids để bao gồm các catalog mới nếu cần.

- Banner: Tạm thời hiển thị thông báo "Dữ liệu đang được cập nhật" trên giao diện chatbot đối với các câu hỏi về chính sách nhân sự.
---

## Prevention

- Stricter Expectations: Thêm kiểm tra contains_no('14 ngày') vào node Contract_Validator đối với mọi tài liệu version 4.

- Alerting: Cấu hình Webhook gửi thông báo trực tiếp vào #alerts-data-quality ngay khi quarantine_records > 0.

- Day 11 Guardrails: Triển khai LLM-as-a-Judge ở bước cuối cùng để chặn các câu trả lời chứa thông tin "14 ngày" hoặc "2025" trước khi gửi tới User.

- Data Ownership: Yêu cầu Team CS cập nhật file policy_refund_v4.txt chuẩn lên Internal Knowledge Base để thay thế hoàn toàn file CSV export bị lỗi.
