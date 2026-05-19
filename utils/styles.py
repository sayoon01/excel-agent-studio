"""
공통 스타일 유틸리티 — 모든 페이지에서 import해서 사용
"""

GLOBAL_CSS = """<style>
/* ═══════════════════════════════════════
   1. Design Tokens
═══════════════════════════════════════ */
:root {
    --c-primary:    #2563eb;
    --c-primary-h:  #1d4ed8;
    --c-surface:    #f8fafc;
    --c-surface-2:  #f1f5f9;
    --c-elevated:   #ffffff;
    --c-border:     #e2e8f0;
    --c-border-s:   #cbd5e1;
    --c-text:       #0f172a;
    --c-muted:      #64748b;
    --c-muted-2:    #94a3b8;
    --c-success:    #065f46;
    --c-success-bg: #d1fae5;
    --c-active:     #059669;
    --c-active-bg:  #d1fae5;
    --c-info:       #1d4ed8;
    --c-info-bg:    #eff6ff;
    --c-info-border:#bfdbfe;
    --c-error:      #dc2626;
    --c-error-bg:   #fee2e2;
    --c-warn-bg:    #fef3c7;
    --c-warn:       #92400e;
    --r-sm:   8px;
    --r-md:   12px;
    --r-lg:   16px;
    --r-pill: 999px;
    --shadow-xs: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-sm: 0 2px 8px rgba(0,0,0,0.07);
    --shadow-md: 0 4px 20px rgba(0,0,0,0.10);
    --t: 0.18s ease;
}

/* ═══════════════════════════════════════
   2. Streamlit 기본 UI 정리
═══════════════════════════════════════ */
footer { visibility: hidden; }
#MainMenu { visibility: hidden; }
[data-testid="stDecoration"] { display: none !important; }
[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
}
[data-testid="stToolbar"] {
    background: transparent !important;
    padding: 0 !important;
    min-height: 0 !important;
}
[data-testid="stToolbarActionButton"] { display: none !important; }
[data-testid="stAppViewContainer"] > .main { padding-top: 1.5rem !important; }

/* 사이드바 열기 버튼 */
[data-testid="stExpandSidebarButton"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    position: fixed !important;
    left: 0.5rem !important;
    top: 0.5rem !important;
    z-index: 99999 !important;
}
[data-testid="stSidebarContent"] { padding-top: 0.5rem !important; }

/* ═══════════════════════════════════════
   3. 폰트 · 타이포그래피
═══════════════════════════════════════ */
* {
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
h1 {
    font-size: clamp(1.3rem, 2.5vw, 1.75rem) !important;
    font-weight: 700 !important;
    letter-spacing: -0.025em !important;
    color: var(--c-text) !important;
}
h2, h3 {
    font-size: clamp(1rem, 2vw, 1.25rem) !important;
    font-weight: 650 !important;
    letter-spacing: -0.02em !important;
    color: var(--c-text) !important;
}

/* ═══════════════════════════════════════
   4. 레이아웃
═══════════════════════════════════════ */
[data-testid="stHorizontalBlock"] { align-items: center; }

/* ═══════════════════════════════════════
   5. 사이드바 브랜딩 영역
═══════════════════════════════════════ */
.sidebar-brand {
    padding: 14px 4px 18px;
    border-bottom: 1px solid var(--c-border);
    margin-bottom: 14px;
}
.sidebar-brand-title {
    font-size: 15px;
    font-weight: 700;
    color: var(--c-text);
    letter-spacing: -0.02em;
}
.sidebar-brand-sub {
    font-size: 11px;
    color: var(--c-muted-2);
    margin-top: 2px;
}

/* ═══════════════════════════════════════
   6. 메트릭 카드
═══════════════════════════════════════ */
div[data-testid="stMetric"] {
    background: var(--c-elevated) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: var(--r-md) !important;
    padding: 16px 20px !important;
    box-shadow: var(--shadow-xs) !important;
    transition: box-shadow var(--t) !important;
}
div[data-testid="stMetric"]:hover {
    box-shadow: var(--shadow-sm) !important;
}
div[data-testid="stMetric"] label {
    font-size: 11px !important;
    color: var(--c-muted) !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 26px !important;
    font-weight: 700 !important;
    color: var(--c-text) !important;
    letter-spacing: -0.02em !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 12px !important;
}

/* ═══════════════════════════════════════
   7. Expander
═══════════════════════════════════════ */
[data-testid="stExpander"] {
    border: 1px solid var(--c-border) !important;
    border-radius: var(--r-md) !important;
    overflow: hidden !important;
    background: var(--c-elevated) !important;
    transition: box-shadow var(--t) !important;
}
[data-testid="stExpander"]:hover {
    box-shadow: var(--shadow-xs) !important;
}
[data-testid="stExpander"] summary {
    font-size: 13px !important;
    font-weight: 600 !important;
    padding: 10px 14px !important;
    color: #334155 !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--c-surface) !important;
}

/* ═══════════════════════════════════════
   8. Status 블록
═══════════════════════════════════════ */
[data-testid="stStatusWidget"] {
    border: 1px solid var(--c-border) !important;
    border-radius: var(--r-md) !important;
    background: var(--c-surface) !important;
    padding: 4px !important;
}

/* ═══════════════════════════════════════
   9. 버튼 포커스
═══════════════════════════════════════ */
button:focus-visible {
    outline: 2px solid var(--c-primary) !important;
    outline-offset: 2px !important;
}

/* ═══════════════════════════════════════
   10. 채팅 입력창
═══════════════════════════════════════ */
[data-testid="stChatInput"] textarea {
    border: 2px solid var(--c-border) !important;
    border-radius: var(--r-md) !important;
    background: var(--c-elevated) !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
    transition: border-color var(--t), box-shadow var(--t) !important;
    resize: none !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: var(--c-primary) !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
    outline: none !important;
}

/* ═══════════════════════════════════════
   11. 채팅 버블
═══════════════════════════════════════ */
[data-testid="stChatMessage"] {
    padding: 4px 0;
    gap: 10px;
    background: transparent !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
[data-testid="stChatMessageContent"] {
    background: #eff6ff !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 16px 4px 16px 16px !important;
    padding: 10px 16px !important;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
[data-testid="stChatMessageContent"] {
    background: var(--c-elevated) !important;
    border: 1px solid var(--c-border) !important;
    border-radius: 4px 16px 16px 16px !important;
    box-shadow: var(--shadow-sm) !important;
    padding: 12px 16px !important;
}

/* ═══════════════════════════════════════
   12. 코드 블록
═══════════════════════════════════════ */
[data-testid="stCodeBlock"] pre, .stCodeBlock pre {
    background: #1e293b !important;
    border-radius: var(--r-sm) !important;
    border: none !important;
    padding: 14px 16px !important;
}
[data-testid="stCodeBlock"] code, .stCodeBlock code {
    color: #e2e8f0 !important;
    font-size: 12.5px !important;
}

/* ═══════════════════════════════════════
   13. Divider · Toast · Select
═══════════════════════════════════════ */
hr[data-testid="stDivider"] {
    border-color: var(--c-surface-2) !important;
    margin: 16px 0 !important;
}
[data-testid="stToast"] {
    border-radius: var(--r-md) !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    border-radius: var(--r-sm) !important;
    border-color: var(--c-border) !important;
}

/* ═══════════════════════════════════════
   14. 파일 칩 (선택된 파일 태그)
═══════════════════════════════════════ */
.file-chip {
    display: inline-block;
    background: var(--c-info-bg);
    border: 1px solid var(--c-info-border);
    color: var(--c-info);
    padding: 2px 10px;
    border-radius: var(--r-pill);
    font-size: 12px;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 4px;
    cursor: default;
    white-space: nowrap;
}

/* ═══════════════════════════════════════
   15. 바운싱 로딩 도트
═══════════════════════════════════════ */
@keyframes bounce-dot {
    0%, 80%, 100% { transform: translateY(0);    opacity: 0.4; }
    40%           { transform: translateY(-6px); opacity: 1;   }
}
.loading-dots {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 8px 4px;
}
.loading-dots span {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--c-primary);
    animation: bounce-dot 0.95s ease-in-out infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.12s; }
.loading-dots span:nth-child(3) { animation-delay: 0.24s; }

/* ═══════════════════════════════════════
   16. 스크롤바
═══════════════════════════════════════ */
::-webkit-scrollbar       { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--c-border-s); border-radius: var(--r-pill); }
::-webkit-scrollbar-thumb:hover { background: var(--c-muted-2); }

/* ═══════════════════════════════════════
   17. 접근성 - 모션 감소
═══════════════════════════════════════ */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
</style>"""


def apply_global_css(extra: str = "") -> None:
    """모든 페이지 set_page_config 직후에 호출. extra는 페이지별 추가 CSS."""
    import streamlit as st

    extra_body = extra.strip()
    if extra_body.startswith("<style>"):
        extra_body = extra_body[len("<style>"):]
    if extra_body.endswith("</style>"):
        extra_body = extra_body[:-len("</style>")]
    extra_body = extra_body.strip()

    if extra_body:
        css = GLOBAL_CSS.replace("</style>", f"\n{extra_body}\n</style>", 1)
    else:
        css = GLOBAL_CSS

    st.markdown(css, unsafe_allow_html=True)


def sidebar_brand(title: str = "AI Prompt Platform", subtitle: str = "Excel × AI") -> None:
    """사이드바 상단 브랜딩 블록."""
    import streamlit as st
    st.markdown(
        f'<div class="sidebar-brand">'
        f'<div class="sidebar-brand-title">{title}</div>'
        f'<div class="sidebar-brand-sub">{subtitle}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def loading_dots() -> str:
    """바운싱 로딩 도트 HTML — st.markdown으로 출력."""
    return '<div class="loading-dots"><span></span><span></span><span></span></div>'


def empty_state(icon: str, title: str, subtitle: str = "") -> str:
    """빈 상태 표시용 HTML."""
    sub = (
        f'<div style="font-size:13px;color:var(--c-muted-2);margin-top:8px;'
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
