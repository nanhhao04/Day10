"""
Cleaning rules — raw export → cleaned rows + quarantine.

Baseline gồm các failure mode mở rộng (allowlist doc_id, parse ngày, HR stale version).
Sinh viên thêm ≥3 rule mới: mỗi rule phải ghi `metric_impact` (xem README — chống trivial).

Rule mới Sprint 2 (Nguyễn Đức Mạnh):
  Rule 7 — BOM / hidden-character quarantine:
    metric_impact: Khi inject chunk có ký tự BOM (\ufeff) hoặc null byte,
    `quarantine_records` tăng thêm mỗi chunk bị nhiễm. Test: thêm 1 dòng BOM
    vào CSV → quarantine_records tăng 1, cleaned_records giảm 1.

  Rule 8 — chunk_text quá ngắn (<20 ký tự sau strip ký tự ẩn):
    metric_impact: Quarantine row có nội dung thực sự quá ngắn để có ý nghĩa
    semantic (ví dụ chỉ có "OK" hay "N/A"). Test: inject 1 dòng chunk_text="OK"
    → quarantine_records tăng 1. Baseline CSV đã có dòng chunk_text rỗng bị bắt
    ở rule 4; rule 8 bắt thêm trường hợp ngắn nhưng không rỗng.

  Rule 9 — SLA P1 response time sanity (>60 phút là corrupt):
    metric_impact: Quarantine chunk `sla_p1_2026` nào mô tả SLA phản hồi > 60 phút
    (dữ liệu không hợp lý với P1 SLA). Test: inject dòng nói "120 phút" →
    quarantine_records tăng 1. Rule này phát hiện lỗi migration policy SLA cũ.
"""

from __future__ import annotations

import csv
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ── Rule 9 -- SLA P1: phản hồi ban đầu hợp lệ phải ≤ 60 phút.
_SLA_RESPONSE_MINUTES = re.compile(r"(\d+)\s*phút", re.IGNORECASE)
_SLA_MAX_RESPONSE_MINUTES = 60

# Khớp export hợp lệ trong lab (mở rộng khi nhóm thêm doc mới — phải đồng bộ contract).
ALLOWED_DOC_IDS = frozenset(
    {
        "policy_refund_v4",
        "sla_p1_2026",
        "it_helpdesk_faq",
        "hr_leave_policy",
    }
)

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DMY_SLASH = re.compile(r"^(\d{2})/(\d{2})/(\d{4})$")


def _norm_text(s: str) -> str:
    return " ".join((s or "").strip().split()).lower()


def _stable_chunk_id(doc_id: str, chunk_text: str, seq: int) -> str:
    h = hashlib.sha256(f"{doc_id}|{chunk_text}|{seq}".encode("utf-8")).hexdigest()[:16]
    return f"{doc_id}_{seq}_{h}"


def _normalize_effective_date(raw: str) -> Tuple[str, str]:
    """
    Trả về (iso_date, error_reason).
    iso_date rỗng nếu không parse được.
    """
    s = (raw or "").strip()
    if not s:
        return "", "empty_effective_date"
    if _ISO_DATE.match(s):
        return s, ""
    m = _DMY_SLASH.match(s)
    if m:
        dd, mm, yyyy = m.group(1), m.group(2), m.group(3)
        return f"{yyyy}-{mm}-{dd}", ""
    return "", "invalid_effective_date_format"


def load_raw_csv(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({k: (v or "").strip() for k, v in r.items()})
    return rows


def clean_rows(
    rows: List[Dict[str, str]],
    *,
    apply_refund_window_fix: bool = True,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Trả về (cleaned, quarantine).

    Baseline (mở rộng theo narrative Day 10):
    1) Quarantine: doc_id không thuộc allowlist (export lạ / catalog sai).
    2) Chuẩn hoá effective_date sang YYYY-MM-DD; quarantine nếu không parse được.
    3) Quarantine: chunk hr_leave_policy có effective_date < 2026-01-01 (bản HR cũ / conflict version).
    4) Quarantine: chunk_text rỗng hoặc effective_date rỗng sau chuẩn hoá.
    5) Loại trùng nội dung chunk_text (giữ bản đầu).
    6) Fix stale refund: policy_refund_v4 chứa '14 ngày làm việc' → 7 ngày.

    Sprint 2 — rule mới:
    7) Quarantine: chunk_text chứa BOM (\ufeff) hoặc null byte (\x00).
       metric_impact: inject 1 dòng BOM → quarantine_records +1.
    8) Quarantine: chunk_text (sau strip ký tự ẩn) ngắn hơn 20 ký tự.
       metric_impact: inject dòng "OK" → quarantine_records +1.
    9) Quarantine: sla_p1_2026 chunk mô tả SLA phản hồi > 60 phút (dữ liệu không hợp lý).
       metric_impact: inject dòng "120 phút" → quarantine_records +1.
    """
    quarantine: List[Dict[str, Any]] = []
    seen_text: set[str] = set()
    cleaned: List[Dict[str, Any]] = []
    seq = 0

    for raw in rows:
        doc_id = raw.get("doc_id", "")
        text = raw.get("chunk_text", "")
        eff_raw = raw.get("effective_date", "")
        exported_at = raw.get("exported_at", "")

        if doc_id not in ALLOWED_DOC_IDS:
            quarantine.append({**raw, "reason": "unknown_doc_id"})
            continue

        eff_norm, eff_err = _normalize_effective_date(eff_raw)
        if eff_err == "empty_effective_date":
            quarantine.append({**raw, "reason": "missing_effective_date"})
            continue
        if eff_err == "invalid_effective_date_format":
            quarantine.append({**raw, "reason": eff_err, "effective_date_raw": eff_raw})
            continue

        if doc_id == "hr_leave_policy" and eff_norm < "2026-01-01":
            quarantine.append(
                {
                    **raw,
                    "reason": "stale_hr_policy_effective_date",
                    "effective_date_normalized": eff_norm,
                }
            )
            continue

        if not text:
            quarantine.append({**raw, "reason": "missing_chunk_text"})
            continue

        # ── Rule 7: BOM / hidden-character quarantine ─────────────────────────
        # metric_impact: inject dòng BOM → quarantine_records tăng 1.
        if "\ufeff" in text or "\x00" in text:
            quarantine.append(
                {
                    **raw,
                    "reason": "hidden_char_in_chunk_text",
                    "detail": "contains BOM or null byte",
                }
            )
            continue

        # ── Rule 8: chunk_text quá ngắn (<20 ký tự) ──────────────────────────
        # metric_impact: inject dòng "OK" → quarantine_records tăng 1.
        if len(text.strip()) < 20:
            quarantine.append(
                {
                    **raw,
                    "reason": "chunk_text_too_short",
                    "detail": f"len={len(text.strip())} < 20",
                }
            )
            continue

        # ── Rule 9: SLA P1 response time sanity ──────────────────────────────
        # metric_impact: inject dòng nói "120 phút" → quarantine_records tăng 1.
        if doc_id == "sla_p1_2026":
            matches = _SLA_RESPONSE_MINUTES.findall(text)
            # chunk được phép có nhiều số; ta chọn số phút nhỏ nhất (response SLA)
            if matches:
                min_minutes = min(int(m) for m in matches)
                if min_minutes > _SLA_MAX_RESPONSE_MINUTES:
                    quarantine.append(
                        {
                            **raw,
                            "reason": "sla_p1_response_too_long",
                            "detail": f"min_response_minutes={min_minutes} > {_SLA_MAX_RESPONSE_MINUTES}",
                        }
                    )
                    continue

        key = _norm_text(text)
        if key in seen_text:
            quarantine.append({**raw, "reason": "duplicate_chunk_text"})
            continue
        seen_text.add(key)

        fixed_text = text
        if apply_refund_window_fix and doc_id == "policy_refund_v4":
            if "14 ngày làm việc" in fixed_text:
                fixed_text = fixed_text.replace(
                    "14 ngày làm việc",
                    "7 ngày làm việc",
                )
                fixed_text += " [cleaned: stale_refund_window]"

        seq += 1
        cleaned.append(
            {
                "chunk_id": _stable_chunk_id(doc_id, fixed_text, seq),
                "doc_id": doc_id,
                "chunk_text": fixed_text,
                "effective_date": eff_norm,
                "exported_at": exported_at or "",
            }
        )

    return cleaned, quarantine


def write_cleaned_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at\n", encoding="utf-8")
        return
    fieldnames = ["chunk_id", "doc_id", "chunk_text", "effective_date", "exported_at"]
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_quarantine_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("chunk_id,doc_id,chunk_text,effective_date,exported_at,reason\n", encoding="utf-8")
        return
    keys: List[str] = []
    seen_k: set[str] = set()
    for r in rows:
        for k in r.keys():
            if k not in seen_k:
                seen_k.add(k)
                keys.append(k)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore", restval="")
        w.writeheader()
        for r in rows:
            w.writerow(r)
