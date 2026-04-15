# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Lê Hà An
**Vai trò:** Ingestion / Cleaning / Embed / Monitoring — Monitoring / Docs Owner
**Ngày nộp:** 15/04/2026  
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

-File / module:

-contracts/data_contract.yaml: Thiết kế bộ quy tắc kiểm soát chất lượng và định nghĩa schema cho pipeline.

-manifest.json: Xây dựng cấu trúc tệp quan sát (observability) để ghi lại trạng thái của mỗi lần chạy (run).

-Runbook.md: Soạn thảo quy trình xử lý sự cố khi hệ thống phát hiện dữ liệu rơi vào phân vùng Quarantine.

-Kết nối với thành viên khác:
-Tôi đóng vai trò là "điểm cuối" của thông tin. Tôi tiếp nhận kết quả định lượng từ Ingestion (số lượng records), logic từ Cleaning (các bản ghi bị loại biên), và trạng thái lưu trữ từ Embed để tổng hợp thành một bức tranh toàn cảnh về sức khỏe dữ liệu (Data Health).

-Bằng chứng:

-Commit: "feat: initialize manifest tracker and data contract schema v1.1"

-Code snippet: self.manifest['quarantine_records'] = len(quarantine_df) trong module MonitorNode.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi đã quyết định thiết lập cơ chế Halt (Dừng) đối với các vi phạm về effective_date (ngày hiệu lực) nhưng chỉ để mức Warn (Cảnh báo) đối với vi phạm Freshness (SLA 24h).

Lý do: Một bản ghi thiếu ngày hiệu lực hoặc sai format ISO (như bản ghi #5 trong quarantine.csv) sẽ gây lỗi logic nghiêm trọng cho hệ thống RAG khi cần so sánh phiên bản chính sách. Tuy nhiên, nếu dữ liệu chỉ hơi "cũ" (ví dụ trễ 30 giờ so với SLA 24 giờ), việc dừng toàn bộ pipeline là không cần thiết vì dữ liệu hiện tại vẫn có thể sử dụng được. Quyết định này giúp cân bằng giữa tính chính xác tuyệt đối và tính sẵn sàng của hệ thống (High Availability). Tôi cũng định dạng tệp quarantine.csv bao gồm cả cột reason để hỗ trợ Data Quality Owner điều tra lỗi nhanh nhất mà không cần đọc mã nguồn.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong đợt chạy run_id: 2026-04-15T07-36Z, tôi phát hiện chỉ số quarantine_records vọt lên mức 4 (chiếm 40% tổng dữ liệu đầu vào).

Phát hiện: Qua việc kiểm tra manifest.json, tôi thấy no_refund_fix: false và quarantine_records: 4. Tôi ngay lập tức truy xuất tệp quarantine.csv.
Triệu chứng: Dòng CSV số 9 báo lỗi unknown_doc_id cho tài liệu legacy_catalog_xyz_zzz.
Xử lý: Tôi xác định đây là lỗi do danh sách allowed_doc_ids trong Data Contract chưa được cập nhật kịp thời với các mã tài liệu mới từ phía đối tác. Tôi đã thực hiện cập nhật Allowlist trong file YAML và hướng dẫn team rerun pipeline. Đồng thời, tôi bổ sung một bước kiểm tra trong Runbook để phân biệt rõ giữa lỗi "Dữ liệu rác" và lỗi "Thiếu cấu hình" nhằm rút ngắn thời gian chẩn đoán sau này.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Dưới đây là minh chứng cho việc hệ thống đã lọc sạch dữ liệu cũ thông qua quá trình Monitoring và Validation tại run_id: 2026-04-15T07-36Z:

Dòng log từ quarantine.csv (Dữ liệu bị chặn):
7,hr_leave_policy,"Nhân viên dưới 3 năm kinh nghiệm được 10 ngày phép năm (bản HR 2025).",2025-01-01,2026-04-10T08:00:00,stale_hr_policy_effective_date

Dòng kết quả từ eval_after.csv (Dữ liệu đã sạch):
q_leave_version,"Theo chính sách nghỉ phép...",hr_leave_policy,"...được 12 ngày phép năm theo chính sách 2026.",yes,no,yes,3

Việc hits_forbidden là no và top1_doc_expected là yes chứng minh hệ thống đã truy xuất đúng phiên bản 2026.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp Slack Webhook API vào node Monitoring. Thay vì phải kiểm tra tệp manifest thủ công, hệ thống sẽ tự động gửi thông báo trực tiếp kèm link dẫn tới file Quarantine ngay khi tỷ lệ lỗi vượt quá 10%. Điều này giúp biến quá trình giám sát từ thụ động sang chủ động (Proactive Monitoring).
_________________
