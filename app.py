"""
Dashboard — AI Prompt Platform 메인 화면
"""
import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path
from datetime import datetime
import json

from utils.activity_log import (
    count_processed_success,
    load_entries,
    weekly_processing_dataframe,
)
from utils.styles import apply_global_css, empty_state

st.set_page_config(
    page_title="AI Prompt Platform",
    page_icon="🤖",
    layout="wide",
)

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 세션 초기화 ──
for key, val in [("messages", []), ("tokens_used", 0)]:
    if key not in st.session_state:
        st.session_state[key] = val

# ── CSS ──
apply_global_css("""<style>
.activity-row {
    display: flex;
    align-items: center;
    flex-wrap: nowrap;
    gap: 10px;
    padding: 9px 12px;
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    margin-bottom: 6px;
    font-size: 13px;
    min-width: 0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    transition: box-shadow 0.15s;
}
.activity-row:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
.activity-name {
    flex: 1 1 auto;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 220px;
    min-width: 0;
}
.activity-time {
    flex: 0 0 auto;
    color: #94a3b8;
    font-size: 11px;
    white-space: nowrap;
    min-width: 5.5rem;
    text-align: right;
}
.badge {
    flex: 0 0 auto;
    padding: 2px 9px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    white-space: nowrap;
}
</style>""")


# ── 모델 설정 로드 (항상 기본값 보장) ──
def load_model_cfg() -> dict:
    cfg_path = Path("model_config.json")
    if cfg_path.exists():
        try:
            return json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"active_provider": "", "active_model": "", "openai": {}, "ollama": {}, "google": {}}

model_cfg      = load_model_cfg()
active_model   = model_cfg.get("active_model", "")
active_provider = model_cfg.get("active_provider", "")
provider_label = {"openai": "OpenAI", "ollama": "Ollama", "google": "Google"}.get(active_provider, "")

# ── 파일 수 계산 ──
def count_files(d: Path, exts: set) -> int:
    return sum(1 for f in d.glob("*") if f.suffix.lower() in exts and f.name != ".gitkeep")

upload_count = count_files(UPLOAD_DIR, {".xlsx", ".xls", ".csv"})
output_count = count_files(OUTPUT_DIR, {".xlsx", ".xls", ".csv", ".md"})

def get_processed_count() -> int:
    """AI Prompt가 ``activity_log.json``에 남긴 성공 처리 건수."""
    return count_processed_success()


# ── 헤더 ──
header_l, header_r = st.columns([5, 1])
with header_l:
    st.markdown("## Dashboard")
    st.caption("AI 프롬프트 플랫폼 — 파일 업로드 → AI 처리 → 결과 저장")
with header_r:
    st.markdown("<br>", unsafe_allow_html=True)
    if active_model:
        st.markdown(
            f'<div style="text-align:right">'
            f'<span style="background:#d1fae5;color:#065f46;padding:5px 12px;'
            f'border-radius:20px;font-size:12px;font-weight:600">● {active_model}</span>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:3px;text-align:right">via {provider_label}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="text-align:right">'
            '<span style="background:#fef9c3;color:#854d0e;padding:5px 12px;'
            'border-radius:20px;font-size:12px;font-weight:600">⚙ 모델 미설정</span>'
            '<div style="font-size:11px;color:#94a3b8;margin-top:3px;text-align:right">'
            'Model Manager에서 연결하세요</div>'
            '</div>',
            unsafe_allow_html=True,
        )

# ── 메트릭 카드 4개 ──
m1, m2, m3, m4 = st.columns(4)
m1.metric("Uploaded files",  f"{upload_count}개",   delta=None)
m2.metric("Processed",       f"{get_processed_count()}건", delta=None)
m3.metric("Active model",    active_model or "—",   delta=provider_label or None)
m4.metric("Tokens used",     f"{st.session_state.tokens_used:,}")

# 모델이 설정되지 않은 경우 안내 배너
if not active_model:
    st.info(
        "**모델이 연결되지 않았습니다.** "
        "왼쪽 사이드바에서 **Model Manager**를 열고 Ollama / OpenAI / Google 중 하나를 연결하세요. "
        "Ollama는 무료로 로컬에서 실행할 수 있습니다."
    )

st.divider()

# ── 두 패널: 최근 활동 + 처리 통계 ──
panel_l, panel_r = st.columns(2)

# ── 왼쪽: 최근 활동 ──
with panel_l:
    st.markdown("#### Recent activity")

    # activity_log.json 우선, 없으면 파일 기반 fallback
    activity_items = []
    for entry in load_entries(limit=8):
        fn = entry.get("filename") or ""
        if not fn:
            continue
        activity_items.append({
            "name":   fn,
            "status": entry.get("status", "saved"),
            "ts":     entry.get("timestamp", ""),
        })

    if not activity_items:
        all_files = sorted(
            [f for f in list(UPLOAD_DIR.glob("*")) + list(OUTPUT_DIR.glob("*"))
             if f.name != ".gitkeep"],
            key=lambda f: f.stat().st_mtime, reverse=True,
        )[:6]
        for f in all_files:
            loc = "outputs" if "outputs" in str(f.parent) else "uploads"
            status = "processed" if loc == "outputs" and f.suffix != ".md" else \
                     "saved"     if f.suffix == ".md" else "uploaded"
            activity_items.append({
                "name":   f.name,
                "status": status,
                "ts":     datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })

    STATUS_STYLE = {
        "merged":   ("#d1fae5", "#065f46"),
        "analyzed": ("#dbeafe", "#1e40af"),
        "executed": ("#d1fae5", "#065f46"),
        "saved":    ("#fef3c7", "#92400e"),
        "uploaded": ("#ede9fe", "#5b21b6"),
        "deleted":  ("#f3f4f6", "#374151"),
        "processed":("#d1fae5", "#065f46"),
        "error":    ("#fee2e2", "#991b1b"),
    }

    if activity_items:
        for item in activity_items:
            fname   = item["name"]
            status  = item["status"]
            ts_str  = item["ts"]
            bg, fg  = STATUS_STYLE.get(status, ("#f3f4f6", "#374151"))
            icon    = "📊" if fname.endswith((".xlsx", ".xls")) else "📋" if fname.endswith(".csv") else "📄"

            try:
                age  = datetime.now() - datetime.fromisoformat(ts_str)
                secs = age.total_seconds()
                time_str = (
                    "방금"          if secs < 60    else
                    f"{int(secs//60)}분 전"  if secs < 3600  else
                    f"{int(secs//3600)}시간 전" if secs < 86400 else
                    f"{int(age.days)}일 전"
                )
            except Exception:
                time_str = ""

            st.markdown(
                f'<div class="activity-row">'
                f'<span>{icon}</span>'
                f'<span class="activity-name" title="{fname}">{fname}</span>'
                f'<span class="badge" style="background:{bg};color:{fg}">{status}</span>'
                f'<span class="activity-time">{time_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(empty_state("📋", "아직 활동이 없습니다", "파일 업로드 또는 AI Prompt 사용 후 표시됩니다"), unsafe_allow_html=True)

# ── 오른쪽: 주간 통계 차트 ──
with panel_r:
    st.markdown("#### Processing stats (7 days)")

    df_chart = weekly_processing_dataframe(days=7)

    if df_chart["건수"].sum() == 0:
        st.markdown(empty_state("📊", "처리 기록 없음", "AI Prompt에서 작업하면 통계가 표시됩니다"), unsafe_allow_html=True)
    else:
        day_order = list(df_chart["요일"])
        chart = (
            alt.Chart(df_chart)
            .mark_bar(color="#60a5fa")
            .encode(
                x=alt.X("요일:N", sort=day_order, title=None, axis=alt.Axis(labelAngle=-35)),
                y=alt.Y("건수:Q", title="처리 건수"),
            )
            .properties(height=220)
        )
        st.altair_chart(chart, use_container_width=True)

st.divider()

# ── 빠른 시작 ──
st.markdown("#### 빠른 시작")

if not active_model:
    # 모델 미설정: 단계별 안내
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown("""
        **1. 모델 연결** `필수`

        Model Manager에서 Ollama 또는 OpenAI/Google API를 연결합니다.
        Ollama는 로컬에서 무료 실행 가능.
        """)
    with s2:
        st.markdown("""
        **2. 파일 업로드**

        File Manager에서 엑셀/CSV 파일을 업로드합니다.
        """)
    with s3:
        st.markdown("""
        **3. AI 대화**

        AI Prompt에서 자연어로 작업을 지시합니다.
        """)
    with s4:
        st.markdown("""
        **4. 결과 저장**

        Results에서 결과 파일을 확인하고 다운로드합니다.
        """)
else:
    # 모델 설정됨: 프롬프트 예시
    st.caption("AI Prompt 페이지에서 이런 것들을 할 수 있습니다:")
    examples = [
        "5개 파일을 1개로 통합하고 동일 항목은 평균값으로 계산해줘",
        "B열 기준 내림차순 정렬해줘",
        "매출 상위 10개만 추출해서 새 파일로 저장해줘",
        "각 파일의 3번째 시트만 모아서 합쳐줘",
        "빈 셀을 0으로 채우고 중복 행 제거해줘",
        "월별 합계 차트로 보여줘",
    ]
    cols = st.columns(2)
    for i, ex in enumerate(examples):
        cols[i % 2].code(ex, language=None)
