# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Mạnh

**Vai trò:** Cleaning & Quality

**Ngày nộp:** 2026-04-15

**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/Nguyen_Duc_Manh.md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

Tôi phụ trách phần **Cleaning** và **Quality** — cụ thể là triển khai ba cleaning rule mới (Rule 7–9) trong `transform/cleaning_rules.py` và ba expectation tương ứng (E7–E9) trong `quality/expectations.py`.

- **Rule 7** (`hidden_char_in_chunk_text`): quarantine chunk chứa BOM (`\ufeff`) hoặc null byte (`\x00`).
- **Rule 8** (`chunk_text_too_short`): quarantine chunk_text có độ dài < 20 ký tự sau strip.
- **Rule 9** (`sla_p1_response_too_long`): quarantine chunk `sla_p1_2026` mô tả SLA phản hồi > 60 phút — dữ liệu migration lỗi.

**Kết nối với thành viên khác:**

Output `cleaned_csv` của tôi được đăng ký trong manifest (`cleaned_csv` key) và log `cleaned_records` — là input trực tiếp cho Embed Owner (Lê Hà An / Lê Ngọc Hải) sử dụng trong `etl_pipeline.py`.

**Bằng chứng (commit / comment trong code):**

Docstring `Rule mới Sprint 2 (Nguyễn Đức Mạnh)` ở đầu `cleaning_rules.py` (dòng 7–23) và comment `# ── Rule 7/8/9` trong hàm `clean_rows()` (dòng 147–186). Expectation E7–E9 tương ứng trong `quality/expectations.py` (dòng 115–172).

---

## 2. Một quyết định kỹ thuật (100–150 từ)

**Halt vs warn cho E7 và E9 / warn cho E8:**

Tôi chọn **halt** cho E7 (`no_hidden_chars_in_chunk_text`) và E9 (`sla_p1_no_response_over_60_min`) vì nếu ký tự BOM lọt vào Vector DB, embedding bị nhiễu semantic không phát hiện được ở inference. Tương tự, chunk SLA sai (120 phút thay vì 15 phút) sẽ làm Agent trả lời sai cam kết P1 cho khách hàng — sai lệch nghiêm trọng về SLA contract. Hai trường hợp này → **quarantine + ban bản ghi hoàn toàn**, không để vào `cleaned_csv`.

E8 (`chunk_min_length_20`) tôi chọn **warn** thay vì halt: chunk quá ngắn thường là lỗi dữ liệu phụ (ví dụ "N/A", "OK"), không ảnh hưởng trực tiếp đến retrieval quality nếu rule 8 đã quarantine chúng từ cleaning layer. Severity warn cho phép pipeline publish và log backlog xử lý sau.

**Idempotency trong prune vector:**

Tôi ủng hộ việc prune vector ID không còn trong batch hiện tại (logic `prev_ids - set(ids)` tại `etl_pipeline.py` dòng 178–184): nếu không prune, vector cũ chứa "14 ngày" vẫn nằm trong Chroma và top-k trả về "mồi cũ" dù `cleaned_csv` đã sạch.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Khi thử bỏ prune (comment dòng `col.delete(ids=drop)` trong `etl_pipeline.py`), kết quả `grading_run.jsonl` vẫn báo `hits_forbidden=true` cho câu hỏi hoàn tiền — dù `cleaned_grading-ready.csv` không còn dòng nào chứa "14 ngày làm việc".

**Check nào phát hiện:** Expectation E3 (`refund_no_stale_14d_window`) log `OK (halt)` sau run chuẩn — nhưng khi chạy `--no-refund-fix --skip-validate` rồi query Chroma, top-1 vẫn trả về chunk cũ từ run trước. Đây là dấu hiệu vector index chứa "mồi cũ".

**Fix:** Khôi phục logic prune trong `cmd_embed_internal()`:
```python
drop = sorted(prev_ids - set(ids))
if drop:
    col.delete(ids=drop)
    log(f"embed_prune_removed={len(drop)}")
```
Sau fix, `grading_run.jsonl` (run `grading-ready`) xác nhận `hits_forbidden=false` cho cả 3 câu hỏi grading, kể cả `gq_d10_01` (hoàn tiền 7 ngày).

---

## 4. Bằng chứng trước / sau (80–120 từ)

**Run `grading-ready`** (manifest: `artifacts/manifests/manifest_grading-ready.json`):

```
raw_records=13 | cleaned_records=6 | quarantine_records=7
quarantine_breakdown:
  hidden_char_in_chunk_text=1   ← Rule 7 (BOM)
  chunk_text_too_short=1        ← Rule 8 ("OK")
  sla_p1_response_too_long=1    ← Rule 9 ("120 phút")
```

**Log expectation** (run chuẩn sau fix prune):
```
expectation[refund_no_stale_14d_window] OK (halt) :: violations=0
expectation[no_hidden_chars_in_chunk_text] OK (halt) :: hidden_char_violations=0
expectation[sla_p1_no_response_over_60_min] OK (halt) :: sla_violations=0
```

**grading_run.jsonl:** `gq_d10_01 → hits_forbidden=false, contains_expected=true` — xác nhận pipeline sạch end-to-end. Trước khi có Rule 7–9, `quarantine_records` chỉ là 4; sau khi thêm ba rule, tăng lên 7 (thêm 3 bản ghi bị bắt đúng chủ đích).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ đọc ngưỡng cutoff HR (`2026-01-01`) trực tiếp từ `contracts/data_contract.yaml` thay vì hard-code trong `cleaning_rules.py`. Cụ thể: đọc key `env_vars.hr_leave_min_effective_date` trong YAML khi module load — nếu contract thay đổi cutoff, rule 3 tự cập nhật mà không cần sửa Python. Đây là hướng **Distinction d** (config-driven rules) giúp pipeline decoupled khỏi logic business cứng. Sau đó push lên `main` để nhóm đồng bộ.
