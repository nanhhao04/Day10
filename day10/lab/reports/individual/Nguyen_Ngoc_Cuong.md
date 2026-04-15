# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Ngọc Cường  
**Vai trò:** Sprint 3 (60') — Inject corruption & before/after 
**Ngày nộp:** 15/4/2026  

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
artifacts/eval/eval_after.csv, artifacts/eval/before_eval.csv artifacts/eval/after_eval.csv
- …

**Kết nối với thành viên khác:**
Kết nối với các thành viên làm ở Sprint 4 (60') — Monitoring + docs + báo cáo: Cung cấp thông tin log vừa có về kết quả chạy trước và sau eval, lấy kết quả của 2 bước trên để so sánh
_________________

**Bằng chứng (commit / comment trong code):**

Các commit ở trong folder eval, folder cleaned ở 2 trong 3 file có tên có cụm là "2026-04-15T09..."
cleaned_2026-04-15T08-16Z.csv
cleaned_2026-04-15T08-27Z.csv
---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Cố tình chọn thêm data nhiễu và data bị trùng lặp. data nhiễu thì chọn các file có chứa các ký tự đặc biệt, data bị trùng lặp thì chọn thêm data thông tin sai hoặc phiên bản cũ hơn thêm vào

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

Khi chạy trước eval, tôi đã bỏ sót thông tin về _impact_metrics_quarantine_breakdown:
Phát hiện sau khi chạy sau khi eval, dùng lệnh python etl_pipeline.py run --no-refund-fix --skip-validate để phát hiện là log trước khi eval thì không có thông tin này
fix: dùng python etl_pipeline.py run --no-refund-fix --skip-validate  khi chạy trước eval và cho kết quả trực quan hơn

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

cleaned_2026-04-15T08-27Z.csv: trước khi làm sạch
cleaned_2026-04-15T08-16Z.csv: sau khi làm sạch

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

TÔi sẽ thêm  data nhiễu và data chính xác và metric về quy định loại dữ liệu chứa gì để đánh giá cho 2 loại data này có bị bỏ sót hay lọai nhầm không. Về mettric thì tôi sẽ thêm quy định bản cũ hơn sẽ là loại nếu câu hỏi không đề cập thời gian (mặc định là hỏi thông tin phiên bản mới nhất)
