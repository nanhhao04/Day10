# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** C401-Table-E1 
**Thành viên:**
| Tên | Vai trò (Day 10) | Email |
|-----|------------------|-------|
| Hào | Ingestion / Raw Owner | haovladimir01@gmail.com |
| Hải, Mạnh | Cleaning & Quality Owner | Hải: ingssconan123@gmail.com; Mạnh: manh.nd223720@sis.hust.edu.vn |
| Cường | Embed & Idempotency Owner | ngoccuong6a@gmail.com |
| An | Monitoring / Docs Owner | lehaan050504@gmail.com |

**Ngày nộp:** 15/04/2026
**Repo:** https://github.com/nanhhao04/Day10  
**Độ dài khuyến nghị:** 600–1000 từ

---

---

## 1. Pipeline tổng quan (150–200 từ)

Hệ thống được thiết kế dưới dạng một State Graph sử dụng LangGraph để điều phối dòng chảy dữ liệu từ nguồn thô đến Vector Database (ChromaDB). Nguồn dữ liệu thô (Raw) bao gồm tệp policy_export_dirty.csv (chứa các lỗi migration thực tế) và các tệp văn bản từ Internal Knowledge Base.

Tóm tắt luồng:

Ingestion: Node này chịu trách nhiệm nạp dữ liệu và gán nhãn run_id cùng timestamp.

Transformation: Thực hiện làm sạch cơ bản và áp dụng logic "auto-fix" cho các chính sách hoàn tiền (chuyển đổi chuỗi "14 ngày" sang "7 ngày").

Quality Gate (Validation): Kiểm tra dữ liệu dựa trên Data Contract. Nếu vi phạm các rule nghiêm trọng (Halt), bản ghi sẽ bị đẩy vào quarantine_records.

Embedding: Sử dụng mô hình từ GitHub Models API để chuyển đổi văn bản thành vector.

Persistence: Thực hiện Upsert vào ChromaDB dựa trên chunk_id (hash-based) để đảm bảo tính Idempotency.


---

## 2. Cleaning & expectation (150–200 từ)

> Baseline đã có nhiều rule (allowlist, ngày ISO, HR stale, refund, dedupe…). Nhóm thêm **≥3 rule mới** + **≥2 expectation mới**. Khai báo expectation nào **halt**.

### 2a. Bảng metric_impact (bắt buộc — chống trivial)

Auto-fix Refund: Tự động chuẩn hóa cửa sổ hoàn tiền về 7 ngày cho policy_refund_v4.

HR Cutoff: Loại bỏ mọi chính sách nhân sự có effective_date trước 2026-01-01.

Deduplication: Loại bỏ các chunk trùng lặp nội dung dựa trên giá trị hash.

Ví dụ expectation fail: Bản ghi số #5 thiếu effective_date. Hệ thống đã kích hoạt rule null_date_halt, dừng việc xử lý bản ghi này và đẩy vào artifacts/quarantine/. Điều này ngăn chặn việc chatbot cung cấp thông tin chính sách mà không rõ ngày hiệu lực.
---

## 3. Before / after ảnh hưởng retrieval hoặc agent (200–250 từ)

-Nhóm đã thực hiện Corruption Inject bằng cách đưa vào dữ liệu cũ của năm 2025 và các bản ghi trùng lặp có nội dung mâu thuẫn.

-Kịch bản inject:
Chèn bản ghi hr_leave_policy năm 2025 (10 ngày phép) song song với bản 2026 (12 ngày phép). Đồng thời inject dòng refund v3 (14 ngày) vào file export của v4.

-Kết quả định lượng:
Dựa trên eval_after.csv:

-q_refund_window: Hệ thống đạt contains_expected: yes (trả về 7 ngày). Tuy nhiên, ghi nhận hits_forbidden: yes do trong top-k vẫn xuất hiện bản ghi cũ chưa được purge triệt để khỏi collection (cần xử lý trong Mitigation).

-q_leave_version: Thành công tuyệt đối. contains_expected: yes (12 ngày) và hits_forbidden: no. Rule lọc ngày hiệu lực đã chặn đứng thông tin 10 ngày phép của năm 2025.

-Tỷ lệ chính xác (Pass rate): Tăng từ 40% (trước clean) lên 85% (sau clean).

---


## 4. Freshness & monitoring (100–150 từ)

Nhóm áp dụng SLA 24 giờ cho tính tươi mới của dữ liệu (Freshness).

PASS: Khi current_time - latest_exported_at < 24h.

WARN: Khi khoảng cách từ 24h - 48h.

FAIL: Khi dữ liệu cũ hơn 48h hoặc quarantine_records > 20% tổng lượng raw.

Trong run_id hiện tại, hệ thống báo WARN vì latest_exported_at là 2026-04-10, trong khi ngày chạy là 15/04. Điều này cảnh báo Team Data cần thực hiện một đợt sync mới từ hệ thống CMS của Teki.

---

## 5. Liên hệ Day 09 (50–100 từ)

Dữ liệu sau khi embed được đẩy vào collection day10_kb. Collection này trực tiếp thay thế corpus thô được dùng trong Lab Day 09. Nhờ việc tích hợp này, Multi-agent hỗ trợ phụ huynh sẽ không còn tình trạng trả lời sai chính sách hoàn tiền 14 ngày, giúp giảm tỷ lệ ticket khiếu nại do AI cung cấp thông tin sai lệch.

---

## 6. Rủi ro còn lại & việc chưa làm

-Xử lý tồn dư (Residual Stale Data): Như đã thấy ở q_refund_window, top-k vẫn còn dính dữ liệu lỗi. Cần cơ chế Hard Delete thay vì chỉ Upsert khi thay đổi logic contract.

-Tối ưu hóa Token: Chưa có cơ chế tóm tắt (summarization) trước khi embed cho các chunk quá dài (>1000 tokens), dẫn đến tốn chi phí API GitHub Models.
