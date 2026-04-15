# Báo cáo cá nhân — mẫu GV (reference)

**Họ và tên:** Lê Ngọc Hải  
**Vai trò:** Cleaning & Quality  
**Độ dài:** ~450 từ (mẫu)

---

## 1. Phụ trách

Tôi triển khai `transform/cleaning_rules.py` (rule 7–9 + duplicate detection), `quality/expectations.py` (E7–E9), và **impact metrics tracking** trong `etl_pipeline.py`. Chi tiết:

- **Rule 7–9:** quarantine BOM/hidden-char, chunk quá ngắn (<20 ký tự), SLA P1 sanity (>60 phút)
- **Duplicate detection:** `_norm_text()` normalize (lowercase + collapse spaces) → `seen_text` set → quarantine duplicates, giữ bản đầu (idempotent)
- **Impact metrics:** breakdown từng quarantine reason (Counter), quality ratio (cleaned/raw %), persist vào manifest JSON

Kết nối với embed owner qua manifest `cleaned_csv`, log `cleaned_records`, và `_impact_metrics` object.

**Bằng chứng:** 
- `etl_pipeline.py` dòng 88–102 (log breakdown), dòng 119–125 (manifest metrics)
- `transform/cleaning_rules.py` dòng 140–146 (duplicate logic)
- Logs tại `artifacts/logs/run_*.log` và `artifacts/manifests/manifest_*.json`

---

## 2. Quyết định kỹ thuật

**Duplicate detection — normalize + set:**
- `_norm_text(text)` → strip, lowercase, collapse spaces → phát hiện "Policy  Refund" vs "policy refund" cùng chunk
- Giữ bản đầu (first-seen wins) → idempotent replay, không bị stale vectors trong top-k
- Quarantine (không drop im lặng) → audit trail: SRE biết duplicate ở đâu, bao nhiêu, để debug root cause

**Impact metrics — measure & monitor:**
- Breakdown từng quarantine reason (Counter) → phát hiện anomaly nhanh (duplicate tăng đột ngột = upstream issue)
- Quality ratio = cleaned/raw % → tracking trend qua time series → alert nếu pass_rate < threshold
- Persist vào manifest JSON → replay history, backtrack nếu quality giảm

**Halt vs warn:** `exported_at` sai format → **quarantine + cleaning** (không để vào cleaned) thay vì warn, vì sai clock làm sai freshness downstream. Còn `exported_at` rỗng trên cleaned → **warn** (E9): vẫn cho publish nhưng log để backlog.

**Vector idempotency:** ủng hộ prune vector id không còn trong batch — tránh top-k còn "14 ngày" sau inject.

---

## 3. Sự cố / anomaly

**Vector remanence issue:** Khi thử bỏ prune, `grading_run.jsonl` báo `hits_forbidden=true` dù cleaned đã sạch — nguyên nhân vector cũ. Fix: prune trong `etl_pipeline.py` sau khi so sánh `prev_ids` vs `ids`.

**Duplicate metric spike:** Nếu `quarantine_breakdown["duplicate_chunk_text"]` tăng đột ngột → check:
- Upstream export có lặp lại dòng?
- Data contract thay đổi? → thêm allowlist doc_id chưa handle duplicate?
- Signal: duplicate nhiều = payload issue, trigger escalation

---

## 4. Before/after

**Log (impact metrics):**
```
_impact_metrics_quarantine_breakdown:
  unknown_doc_id=2
  duplicate_chunk_text=3
  chunk_text_too_short=1
_impact_metrics_quality_ratio:cleaned_to_raw=94%
```

**Manifest metrics:**
```json
"_impact_metrics": {
  "quality_pass_rate": 94.5,
  "quarantine_breakdown": {
    "duplicate_chunk_text": 3,
    "chunk_text_too_short": 1,
    "unknown_doc_id": 2
  }
}
```

**Expectation:** `expectation[refund_no_stale_14d_window] OK (halt)` sau run chuẩn; trước đó với `--no-refund-fix` expectation FAIL.

**Eval CSV:** dòng `q_refund_window` có `hits_forbidden=no` trong `artifacts/eval/before_after_eval.csv`.

---

## 5. Cải tiến thêm 2 giờ

**Config externalization (Distinction d):** Đọc cutoff HR `2026-01-01` từ `contracts/data_contract.yaml` thay vì hard-code trong Python → schema-driven, audit trail.

**Metrics dashboard hook:** `_impact_metrics` trong manifest ready for Grafana/DataDog ingest → SLA monitoring, quality trend alert.
