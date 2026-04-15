# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Anh Hào

**Vai trò:** Ingestion Owner / Data Contract Specialist

**Ngày nộp:** 2026-04-15

**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

Tôi phụ trách chính phần Ingestion và thiết lập Data Contract cho quy trình ETL của nhóm. Cụ thể, tôi đã thực hiện cập nhật các file:
- `contracts/data_contract.yaml`: Định nghĩa chủ sở hữu, SLA và các quy tắc kiểm soát chất lượng dữ liệu.
- `docs/data_contract.md`: Tài liệu hóa Source Map và Schema cho hệ thống.
- Thực hiện chạy pipeline lần đầu tiên với `run-id=sprint1`.

**Kết nối với thành viên khác:**

Tôi thiết lập contract dữ liệu để các thành viên phụ trách Cleaning Rules và Embedding có thể dựa vào đó để xây dựng logic chính xác, đảm bảo tất cả `doc_id` đều nằm trong allowlist đã thống nhất.

**Bằng chứng (commit / comment trong code):**

Tôi đã cập nhật `owner_team: "AI Platform - Data Engineering"` và `alert_channel: "#alerts-data-quality"` trong file `data_contract.yaml` để kích hoạt cơ chế giám sát.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Trong Sprint 1, tôi đã quyết định thiết lập mức độ nghiêm trọng **"halt"** cho các lỗi liên quan đến chính sách hoàn tiền stale_refund_window và định dạng ngày tháng effective_date_iso_yyyy_mm_dd. 

Quyết định này dựa trên thực tế rằng nếu Agent sử dụng nhầm dữ liệu về chính sách hoàn tiền cũ (14 ngày thay vì 7 ngày), nó sẽ trực tiếp ảnh hưởng đến quyền lợi của công ty và gây ra các khiếu nại pháp lý. Thay vì chỉ cảnh báo (`warn`), việc dừng pipeline (`halt`) buộc đội ngũ kỹ thuật phải xử lý sạch dữ liệu thô trước khi cho phép dữ liệu lọt vào Vector Database. Điều này đảm bảo tính "Source of Truth" tuyệt đối cho hệ thống RAG mà nhóm xây dựng từ Day 09.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Khi chạy `python etl_pipeline.py run --run-id sprint1`, tôi đã phát hiện một Anomaly lớn về tính Freshness của dữ liệu. Cụ thể, log báo:
`freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 118.958, "sla_hours": 24.0}`.

Dữ liệu nguồn được export từ ngày 10/04, dẫn đến độ trễ gần 119 giờ, vượt xa mức SLA 24 giờ mà tôi đã quy định trong `data_contract.yaml`. Điều này cho thấy hệ thống export dữ liệu từ hệ nguồn (Source System) đang gặp tình trạng "stale" (dữ liệu cũ). Tôi đã ghi nhận lỗi này vào manifest để báo cáo cho đội ngũ Data Engineer sửa đổi script export. Ngoài ra, pipeline cũng phát hiện 4 bản ghi bị đẩy vào `quarantine` do các lỗi về định dạng ngày (DD/MM/YYYY) và doc_id lạ.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Dưới đây là kết quả từ manifest của phiên chạy `sprint1`:
```json
"raw_records": 10,
"cleaned_records": 6,
"quarantine_records": 4,
"latest_exported_at": "2026-04-10T08:00:00"
```
Trước khi có pipeline, toàn bộ 10 bản ghi (bao gồm cả 4 bản ghi lỗi) sẽ được đưa vào Agent. Sau khi tôi thiết lập Ingestion layer, 4 bản ghi bẩn đã bị lọc ra. Cụ thể trong file `quarantine_sprint1.csv`, dòng có `chunk_id: 10` bị cách ly vì lý do `invalid_effective_date_format` (giá trị thô: `01/02/2026`).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tự động hóa việc đồng bộ giữa file `data_contract.yaml` và `data_contract.md`. Hiện tại việc cập nhật cả hai file vẫn làm thủ công, dễ dẫn đến sai lệch. Tôi sẽ viết một đoạn script nhỏ để tự động sinh file Markdown từ file YAML để đảm bảo tính nhất quán (Single Source of Truth) cho tài liệu kỹ thuật của nhóm.
