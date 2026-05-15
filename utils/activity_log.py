"""활동 로그: 세션 상태 + ``activity_log.json`` 영속화 (페이지 간 공유)."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

LOG_PATH = Path("activity_log.json")
_MAX_SESSION = 20
_MAX_FILE = 500

# 대시보드 «Processed»·주간 차트에 집계할 성공 상태
PROCESS_SUCCESS_STATUSES = frozenset({"merged", "analyzed", "executed"})


def normalize_entry(e: dict) -> dict:
    """구형 키(``file``, ``time``)와 신형 키를 통일합니다."""
    if not isinstance(e, dict):
        return {}
    out = dict(e)
    out["filename"] = out.get("filename") or out.get("file") or ""
    out["timestamp"] = out.get("timestamp") or out.get("time") or ""
    return out


def load_entries(limit: int | None = None) -> list[dict]:
    """디스크에 저장된 로그를 읽어 정규화된 목록으로 반환합니다."""
    if not LOG_PATH.exists():
        return []
    try:
        raw = json.loads(LOG_PATH.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            return []
        normalized = [normalize_entry(x) for x in raw if isinstance(x, dict)]
        if limit is not None:
            return normalized[:limit]
        return normalized
    except Exception:
        return []


def count_processed_success(entries: list[dict] | None = None) -> int:
    """성공 처리 건수(merged / analyzed / executed)."""
    data = entries if entries is not None else load_entries()
    return sum(1 for e in data if e.get("status") in PROCESS_SUCCESS_STATUSES)


def weekly_processing_dataframe(days: int = 7) -> pd.DataFrame:
    """최근 ``days``일, 성공 처리만 날짜별 건수 (행 순서 = 시간순)."""
    today = datetime.now().date()
    day_list = [today - timedelta(days=days - 1 - i) for i in range(days)]
    counts = {d: 0 for d in day_list}
    for e in load_entries():
        if e.get("status") not in PROCESS_SUCCESS_STATUSES:
            continue
        ts_s = e.get("timestamp") or ""
        if not ts_s:
            continue
        try:
            ts_norm = ts_s.replace("Z", "+00:00") if ts_s.endswith("Z") else ts_s
            d = datetime.fromisoformat(ts_norm).date()
            if d in counts:
                counts[d] += 1
        except Exception:
            continue
    week_kr = ["월", "화", "수", "목", "금", "토", "일"]
    labels = [f"{d.month}/{d.day} ({week_kr[d.weekday()]})" for d in day_list]
    return pd.DataFrame({"요일": labels, "건수": [counts[d] for d in day_list]})


def add_entry(action: str, filename: str, status: str, detail: str = "") -> None:
    """세션 맨 앞에 넣고 ``activity_log.json``에도 동일 스키마로 저장합니다."""
    row = {
        "action": action,
        "filename": filename,
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if detail:
        row["detail"] = detail

    if "activity_log" not in st.session_state:
        st.session_state.activity_log = []
    st.session_state.activity_log.insert(0, row)
    st.session_state.activity_log = st.session_state.activity_log[:_MAX_SESSION]

    prev = load_entries()
    merged = [row] + prev
    merged = merged[:_MAX_FILE]
    try:
        LOG_PATH.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass
