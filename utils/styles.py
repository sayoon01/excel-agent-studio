"""
공통 스타일 유틸리티 — 모든 페이지에서 import해서 사용
"""

GLOBAL_CSS = """<style>
/* ═══════════════════════════════════════
   Streamlit 기본 UI 제거
═══════════════════════════════════════ */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
[data-testid="stDecoration"] { display: none !important; }
/* 헤더: 투명 배경, 테두리 제거 */
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}
[data-testid="stToolbar"] {
    background: transparent !important;
    padding: 0 !important;
    min-height: 0 !important;
}
/* 사이드바 열기 버튼은 보이게 유지, 나머지 툴바 요소 숨김 */
[data-testid="stToolbarActionButton"] { display: none !important; }
[data-testid="stAppViewContainer"] > .main { padding-top: 1.5rem !important; }
[data-testid="stSidebarContent"] { padding-top: 1rem !important; }

/* ═══════════════════════════════════════
   폰트·렌더링
═══════════════════════════════════════ */
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* ═══════════════════════════════════════
   레이아웃 유틸
═══════════════════════════════════════ */
[data-testid="stHorizontalBlock"] { align-items: center; }

/* ═══════════════════════════════════════
   메트릭 카드
═══════════════════════════════════════ */
div[data-testid="stMetric"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.05) !important;
}
div[data-testid="stMetric"] label {
    font-size: 12px !important;
    color: #64748b !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ═══════════════════════════════════════
   Expander
═══════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    background: #ffffff !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    color: #334155 !important;
}
[data-testid="stExpander"] summary:hover {
    background: #f8fafc !important;
}

/* ═══════════════════════════════════════
   Status 블록 (AI 처리 중)
═══════════════════════════════════════ */
[data-testid="stStatusWidget"] {
    border: 1px solid #e2e8f0 !important;
    border-radius: 10px !important;
    background: #f8fafc !important;
    padding: 4px !important;
}

/* ═══════════════════════════════════════
   버튼 포커스 링
═══════════════════════════════════════ */
button:focus-visible {
    outline: 2px solid #2563eb !important;
    outline-offset: 2px !important;
}

/* ═══════════════════════════════════════
   채팅 입력창
═══════════════════════════════════════ */
[data-testid="stChatInput"] textarea {
    border: 2px solid #e2e8f0 !important;
    border-radius: 12px !important;
    background: #ffffff !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    outline: none !important;
}

/* ═══════════════════════════════════════
   채팅 버블
═══════════════════════════════════════ */
[data-testid="stChatMessage"] {
    padding: 4px 0;
    gap: 10px;
    background: transparent !important;
}

/* 사용자 메시지 버블 */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
[data-testid="stChatMessageContent"] {
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 16px 4px 16px 16px !important;
    padding: 10px 16px !important;
}

/* AI 메시지 버블 */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
[data-testid="stChatMessageContent"] {
    background: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 4px 16px 16px 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    padding: 12px 16px !important;
}

/* ═══════════════════════════════════════
   코드 블록 다크 테마
═══════════════════════════════════════ */
[data-testid="stCodeBlock"] pre,
.stCodeBlock pre {
    background: #1e293b !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 14px 16px !important;
}
[data-testid="stCodeBlock"] code,
.stCodeBlock code {
    color: #e2e8f0 !important;
    font-size: 12.5px !important;
}

/* ═══════════════════════════════════════
   Divider
═══════════════════════════════════════ */
hr[data-testid="stDivider"] {
    border-color: #f1f5f9 !important;
    margin: 16px 0 !important;
}

/* ═══════════════════════════════════════
   Toast 알림
═══════════════════════════════════════ */
[data-testid="stToast"] {
    border-radius: 10px !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}

/* ═══════════════════════════════════════
   Select box / Multiselect
═══════════════════════════════════════ */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    border-radius: 8px !important;
    border-color: #e2e8f0 !important;
}
</style>"""


def apply_global_css(extra: str = "") -> None:
    """모든 페이지 set_page_config 직후에 호출. extra는 페이지별 추가 CSS."""
    import streamlit as st

    extra_body = extra.strip()
    if extra_body.startswith("<style>"):
        extra_body = extra_body[len("<style>") :]
    if extra_body.endswith("</style>"):
        extra_body = extra_body[: -len("</style>")]
    extra_body = extra_body.strip()

    if extra_body:
        # Streamlit은 markdown 1회당 <style> 블록 1개만 적용함.
        # 두 번째 <style>…</style>은 태그가 제거되고 내용만 텍스트로 노출됨.
        css = GLOBAL_CSS.replace("</style>", f"\n{extra_body}\n</style>", 1)
    else:
        css = GLOBAL_CSS

    st.markdown(css, unsafe_allow_html=True)


def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    """빈 상태 표시용 HTML. st.markdown(..., unsafe_allow_html=True)로 출력."""
    sub = (
        f'<div style="font-size:13px;color:#94a3b8;margin-top:8px;'
        f'max-width:320px;line-height:1.6">{subtitle}</div>'
        if subtitle else ""
    )
    return (
        f'<div style="display:flex;flex-direction:column;align-items:center;'
        f'justify-content:center;padding:72px 0;text-align:center">'
        f'<div style="font-size:52px;margin-bottom:16px;opacity:0.65">{icon}</div>'
        f'<div style="font-size:15px;font-weight:700;color:#334155;letter-spacing:-0.01em">{title}</div>'
        f'{sub}</div>'
    )
