"""
Results — 결과 파일 관리 및 대화 저장
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.activity_log import add_entry
from utils.styles import apply_global_css, empty_state

st.set_page_config(page_title="Results", page_icon="📝", layout="wide")

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# ── CSS ──
apply_global_css("""<style>
/* ── 헤더 액션 버튼 (Chat 저장 / 작성) ── */
[data-testid="stBaseButton-secondary"] {
    height: 34px !important;
    min-height: 34px !important;
    padding: 0 14px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    white-space: nowrap !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
    box-sizing: border-box !important;
}
/* ── 미리보기 버튼 — 파란색 계열 ── */
[data-testid="stColumn"]:has(.rpv-zone) button {
    height: 30px !important; min-height: 30px !important; max-height: 30px !important;
    padding: 0 !important; font-size: 15px !important; border-radius: 8px !important;
    background: #eff6ff !important; color: #1d4ed8 !important;
    border: 1px solid #bfdbfe !important;
    display: flex !important; align-items: center !important;
    justify-content: center !important; width: 100% !important;
    box-sizing: border-box !important; transition: background 0.15s !important;
}
[data-testid="stColumn"]:has(.rpv-zone) button:hover {
    background: #dbeafe !important; border-color: #93c5fd !important;
}
/* ── 다운로드 버튼 — 초록색 계열 ── */
[data-testid="stDownloadButton"] > button {
    height: 30px !important; min-height: 30px !important; max-height: 30px !important;
    padding: 0 !important; font-size: 15px !important; border-radius: 8px !important;
    background: #f0fdf4 !important; color: #16a34a !important;
    border: 1px solid #bbf7d0 !important;
    display: flex !important; align-items: center !important;
    justify-content: center !important; width: 100% !important;
    box-sizing: border-box !important; transition: background 0.15s !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #dcfce7 !important; border-color: #86efac !important;
}
/* ── 삭제 버튼 — 빨간색 계열 ── */
[data-testid="stColumn"]:has(.rdel-zone) button {
    height: 30px !important; min-height: 30px !important; max-height: 30px !important;
    padding: 0 !important; font-size: 15px !important; border-radius: 8px !important;
    background: #fff1f2 !important; color: #dc2626 !important;
    border: 1px solid #fecaca !important;
    display: flex !important; align-items: center !important;
    justify-content: center !important; width: 100% !important;
    box-sizing: border-box !important; transition: background 0.15s !important;
}
[data-testid="stColumn"]:has(.rdel-zone) button:hover {
    background: #fee2e2 !important; border-color: #f87171 !important;
}
</style>""")

# ── 헤더 ──
hl, hb1, hb2 = st.columns([4.2, 1.3, 1.0])
hl.markdown("## Results")

# ── 대화 → MD 저장 다이얼로그 ──
@st.dialog("대화 저장")
def save_chat_dialog():
    title = st.text_input("파일 제목", value="AI Chat Report")
    msgs = st.session_state.get("messages", [])
    st.caption(f"{len(msgs)}개 메시지")
    if st.button("저장", type="primary", use_container_width=True):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
        fname = f"{safe}_{ts}.md"
        content = f"# {title}\n\n> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n"
        for msg in msgs:
            role = "User" if msg["role"] == "user" else "AI"
            content += f"### {role}\n\n{msg['content']}\n\n"
            if msg.get("code_output"):
                content += f"```\n{msg['code_output']}\n```\n\n"
            content += "---\n\n"
        (OUTPUT_DIR / fname).write_text(content, encoding="utf-8")
        add_entry("저장", fname, "saved")
        st.success(f"✅ {fname}")
        st.rerun()


@st.dialog("Markdown 작성")
def new_md_dialog():
    title = st.text_input("제목")
    body = st.text_area("내용 (Markdown)", height=220, placeholder="# Heading\n\nYour content...")
    if st.button("저장", type="primary", use_container_width=True):
        if title.strip():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = "".join(c if c.isalnum() or c in "-_ " else "_" for c in title)
            fname = f"{safe}_{ts}.md"
            (OUTPUT_DIR / fname).write_text(
                f"# {title}\n\n> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n---\n\n{body}\n",
                encoding="utf-8",
            )
            add_entry("저장", fname, "saved")
            st.success(f"✅ {fname}")
            st.rerun()
        else:
            st.warning("제목을 입력하세요.")


# ── 상단 액션 버튼 ──
has_msgs = bool(st.session_state.get("messages"))

with hb1:
    st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
    if st.button("Chat 저장", help="대화 내용을 Markdown으로 저장",
                 disabled=not has_msgs, use_container_width=True):
        save_chat_dialog()
    st.markdown("</div>", unsafe_allow_html=True)

with hb2:
    st.markdown("<div style='padding-top:8px'>", unsafe_allow_html=True)
    if st.button("✏️ 작성", help="새 Markdown 파일 작성", use_container_width=True):
        new_md_dialog()
    st.markdown("</div>", unsafe_allow_html=True)

if not has_msgs:
    st.caption("대화 저장: AI Prompt에서 대화 후 'Chat 저장' 버튼을 누르세요")

st.divider()

# ── 출력 파일 목록 ──
st.markdown("#### Output files")

out_files = sorted(
    [f for f in OUTPUT_DIR.glob("*") if f.name != ".gitkeep"],
    key=lambda f: f.stat().st_mtime, reverse=True,
)

if not out_files:
    st.markdown(empty_state("📄", "결과 파일이 없습니다", "AI Prompt에서 분석하거나 대화를 저장하면 여기에 표시됩니다"), unsafe_allow_html=True)
    st.stop()

# 컬럼 헤더
st.markdown(
    '<div style="display:flex;gap:12px;padding:4px 14px;font-size:11px;'
    'color:#94a3b8;font-weight:600;letter-spacing:.04em;margin-top:4px">'
    '<span style="flex:1">파일명</span>'
    '<span style="width:80px">유형</span>'
    '<span style="width:90px">날짜·크기</span>'
    '<span style="width:60px;text-align:center">미리보기</span>'
    '<span style="width:60px;text-align:center">다운로드</span>'
    '<span style="width:32px;text-align:center">삭제</span>'
    '</div>',
    unsafe_allow_html=True,
)

if "res_preview_idx" not in st.session_state:
    st.session_state["res_preview_idx"] = None

BADGE = {
    ".md":   ("#dbeafe", "#1e40af", "markdown", "📄"),
    ".xlsx": ("#d1fae5", "#065f46", "excel",    "📊"),
    ".xls":  ("#d1fae5", "#065f46", "excel",    "📊"),
    ".csv":  ("#fef3c7", "#92400e", "csv",      "📋"),
}

for i, fp in enumerate(out_files):
    ext  = fp.suffix.lower()
    stat = fp.stat()
    age  = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).total_seconds()
    time_str = (
        "방금"           if age < 60    else
        f"{int(age//60)}분 전"   if age < 3600  else
        f"{int(age//3600)}시간 전" if age < 86400 else
        f"{int(age//86400)}일 전"
    )
    size_str = (f"{stat.st_size/1024:.0f} KB" if stat.st_size < 1_048_576
                else f"{stat.st_size/1_048_576:.1f} MB")

    bg, fg, badge_txt, icon = BADGE.get(ext, ("#f3f4f6", "#374151", ext.lstrip("."), "📁"))

    cn, cb, ct, cp, cd, cdel = st.columns([3.5, 0.9, 1.1, 0.5, 0.5, 0.3])

    cn.markdown(
        f"<span style='font-weight:500;font-size:13px'>{icon} {fp.name}</span>",
        unsafe_allow_html=True,
    )
    cb.markdown(
        f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:12px;'
        f'font-size:11px;font-weight:600">{badge_txt}</span>',
        unsafe_allow_html=True,
    )
    ct.markdown(
        f"<span style='color:#94a3b8;font-size:12px'>{size_str} · {time_str}</span>",
        unsafe_allow_html=True,
    )

    is_open = (st.session_state["res_preview_idx"] == i)
    cp.markdown('<span class="rpv-zone" style="display:none"></span>', unsafe_allow_html=True)
    if cp.button("✕" if is_open else "◉", key=f"rpv_{i}", use_container_width=True,
                 help="미리보기"):
        st.session_state["res_preview_idx"] = None if is_open else i
        st.rerun()

    with open(fp, "rb") as fh:
        cd.download_button("⬇", data=fh.read(), file_name=fp.name,
                           key=f"rdl_{i}", use_container_width=True)

    cdel.markdown('<span class="rdel-zone" style="display:none"></span>', unsafe_allow_html=True)
    if cdel.button("🗑", key=f"rdel_{i}"):
        add_entry("삭제", fp.name, "deleted")
        fp.unlink()
        if st.session_state["res_preview_idx"] == i:
            st.session_state["res_preview_idx"] = None
        st.toast(f"'{fp.name}' 삭제됨")
        st.rerun()

    # ── 미리보기 패널 ──
    if not is_open:
        continue

    with st.container():
        st.markdown(
            '<div style="border:1px solid #cbd5e1;border-radius:8px;'
            'padding:12px 16px;margin:4px 0 10px;background:#f8fafc">',
            unsafe_allow_html=True,
        )
        if ext == ".md":
            st.markdown(fp.read_text(encoding="utf-8"))
        elif ext in (".xlsx", ".xls"):
            try:
                df = pd.read_excel(fp)
                st.dataframe(df.head(50), use_container_width=True, height=300)
                if len(df) > 50:
                    st.caption(f"처음 50행 / 전체 {len(df):,}행")
            except Exception as e:
                st.error(str(e))
        elif ext == ".csv":
            try:
                df = pd.read_csv(fp)
                st.dataframe(df.head(50), use_container_width=True, height=300)
                if len(df) > 50:
                    st.caption(f"처음 50행 / 전체 {len(df):,}행")
            except Exception as e:
                st.error(str(e))
        else:
            st.info("미리보기를 지원하지 않는 파일 형식입니다.")
        st.markdown("</div>", unsafe_allow_html=True)
