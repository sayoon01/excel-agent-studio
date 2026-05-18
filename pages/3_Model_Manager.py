"""
Model Manager — 작업 목적별 모델 추천 + 연결·활성화
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from utils.styles import apply_global_css

# ══════════════════════════════════════════════
# 모델 메타데이터 (용도·속도·메모리)
# ══════════════════════════════════════════════

OLLAMA_MODELS: dict[str, dict] = {
    # ── Qwen 계열 (Alibaba) ──
    "qwen3:14b": {
        "full": "Alibaba Qwen 3 14B", "size": "14B", "role": "analysis",
        "purpose": ["한국어 엑셀 분석", "실무형", "추천"],
        "speed": "보통", "mem_gb": 10, "desc": "한국어 엑셀 분석 최강 — 상아 앱 메인 추천",
    },
    "qwen3": {
        "full": "Alibaba Qwen 3 8B", "size": "8B", "role": "analysis",
        "purpose": ["한국어", "엑셀 분석", "범용"],
        "speed": "빠름", "mem_gb": 6, "desc": "Qwen 3 경량 버전, 빠른 한국어 분석",
    },
    "qwen2.5:14b": {
        "full": "Qwen 2.5 14B", "size": "14B", "role": "analysis",
        "purpose": ["한국어 고성능", "엑셀 분석"],
        "speed": "보통", "mem_gb": 10, "desc": "한국어 정확도 최우선",
    },
    "qwen2.5": {
        "full": "Alibaba Qwen 2.5 7B", "size": "7B", "role": "analysis",
        "purpose": ["한국어", "엑셀 분석", "다국어"],
        "speed": "빠름", "mem_gb": 5, "desc": "한국어 엑셀 분석 경량 추천",
    },
    "qwen2.5-coder:14b": {
        "full": "Qwen 2.5 Coder 14B", "size": "14B", "role": "code",
        "purpose": ["Python", "pandas", "코드 생성"],
        "speed": "보통", "mem_gb": 10, "desc": "pandas·openpyxl·차트 생성 특화 — 코드 역할 추천",
    },
    "qwen2.5-coder": {
        "full": "Qwen 2.5 Coder 7B", "size": "7B", "role": "code",
        "purpose": ["코드 생성", "Python"],
        "speed": "빠름", "mem_gb": 5, "desc": "경량 코드 생성 모델",
    },
    # ── Gemma 계열 (Google DeepMind) ──
    "gemma3:12b": {
        "full": "Google Gemma 3 12B", "size": "12B", "role": "analysis",
        "purpose": ["엑셀 분석", "로컬 추천", "표 이해"],
        "speed": "보통", "mem_gb": 8, "desc": "Gemini 기술 기반 로컬 실전 모델",
    },
    "gemma3:27b": {
        "full": "Google Gemma 3 27B", "size": "27B", "role": "precision",
        "purpose": ["고정밀 분석", "복잡한 추론", "긴 보고서"],
        "speed": "느림", "mem_gb": 18, "desc": "복잡한 회계표·긴 보고서 고정밀 분석",
    },
    "gemma2": {
        "full": "Google Gemma 2 9B", "size": "9B", "role": "analysis",
        "purpose": ["엑셀 분석", "빠른 응답"],
        "speed": "빠름", "mem_gb": 6, "desc": "경량·범용 분석",
    },
    "gemma2:27b": {
        "full": "Google Gemma 2 27B", "size": "27B", "role": "precision",
        "purpose": ["고성능 분석", "복잡한 추론"],
        "speed": "보통", "mem_gb": 18, "desc": "복잡한 다단계 분석",
    },
    # ── 코드 특화 ──
    "deepseek-coder-v2": {
        "full": "DeepSeek Coder V2", "size": "16B", "role": "code",
        "purpose": ["코드 생성", "고급 ETL", "고성능"],
        "speed": "보통", "mem_gb": 12, "desc": "복잡한 데이터 처리·ETL 코드 특화",
    },
    "codellama": {
        "full": "Meta Code Llama", "size": "7B", "role": "code",
        "purpose": ["코드 생성"],
        "speed": "빠름", "mem_gb": 5, "desc": "코드 생성 경량 모델",
    },
    # ── 임베딩/RAG ──
    "nomic-embed-text": {
        "full": "Nomic Embed Text", "size": "0.1B", "role": "embedding",
        "purpose": ["임베딩", "RAG", "파일 검색"],
        "speed": "매우 빠름", "mem_gb": 1, "desc": "파일 유사도 검색·RAG 전용 임베딩 모델",
    },
    # ── 범용 ──
    "llama3.1": {
        "full": "Meta Llama 3.1 8B", "size": "8B", "role": "analysis",
        "purpose": ["범용 대화", "문서 이해"],
        "speed": "빠름", "mem_gb": 6, "desc": "균형 잡힌 범용 모델",
    },
    "llama3.1:70b": {
        "full": "Meta Llama 3.1 70B", "size": "70B", "role": "precision",
        "purpose": ["최고 성능", "복잡한 추론"],
        "speed": "느림", "mem_gb": 48, "desc": "최고 품질, 고사양 GPU 필요",
    },
    "mistral": {
        "full": "Mistral 7B", "size": "7B", "role": "analysis",
        "purpose": ["범용", "경량"],
        "speed": "빠름", "mem_gb": 5, "desc": "경량·고성능 균형",
    },
    "phi3": {
        "full": "Microsoft Phi-3", "size": "3.8B", "role": "analysis",
        "purpose": ["최소 리소스", "빠른 응답"],
        "speed": "매우 빠름", "mem_gb": 3, "desc": "RAM 8GB 이하 환경용",
    },
    "mixtral": {
        "full": "Mistral Mixtral 8x7B", "size": "8x7B", "role": "precision",
        "purpose": ["범용 고성능", "MoE"],
        "speed": "보통", "mem_gb": 28, "desc": "MoE 아키텍처, 높은 품질",
    },
}

ROLES: dict[str, dict] = {
    "analysis":  {"label": "엑셀 분석",   "icon": "📊", "desc": "비교·집계·집행률·표 이해",     "tools": ["aggregate","compare_files","calculate_ratio","filter_rows"]},
    "code":      {"label": "코드 실행",   "icon": "⚙",  "desc": "Python·pandas·차트 생성",      "tools": ["visualize"]},
    "precision": {"label": "고정밀 분석", "icon": "🔬", "desc": "긴 보고서·복잡한 추론·대용량", "tools": []},
    "embedding": {"label": "검색/RAG",   "icon": "🔍", "desc": "파일 유사도·문서 검색 전용",    "tools": []},
}

OPENAI_MODELS: dict[str, dict] = {
    "gpt-5-mini":    {"desc": "GPT-5 경량화 — 빠르고 저렴한 메인 추천", "speed": "매우 빠름", "cost": "$",   "purpose": ["엑셀 분석", "AI Prompt 메인", "추천"], "role": "analysis"},
    "gpt-5":         {"desc": "최신 GPT-5 — 복잡한 분석·긴 리포트",      "speed": "빠름",     "cost": "$$$", "purpose": ["고정밀 분석", "복잡한 추론"],           "role": "precision"},
    "gpt-4o":        {"desc": "강력한 멀티모달, 표 이해 우수",            "speed": "빠름",     "cost": "$$",  "purpose": ["복잡한 분석", "멀티모달"],               "role": "analysis"},
    "gpt-4o-mini":   {"desc": "gpt-4o 경량화, 가성비 최고",              "speed": "매우 빠름", "cost": "$",  "purpose": ["엑셀 분석", "빠른 응답", "가성비"],      "role": "analysis"},
    "gpt-4-turbo":   {"desc": "128K context, 강력한 추론",               "speed": "보통",     "cost": "$$$", "purpose": ["긴 문서", "복잡한 추론"],               "role": "precision"},
    "gpt-3.5-turbo": {"desc": "경량·빠른 응답, 최저 비용",                "speed": "최고속",   "cost": "$",   "purpose": ["간단한 작업", "최저 비용"],             "role": "analysis"},
}

GOOGLE_MODELS: dict[str, dict] = {
    "gemini-2.0-flash": {"desc": "최신·빠른 응답, 분석 최적화",  "speed": "매우 빠름", "cost": "무료 티어", "purpose": ["엑셀 분석", "빠른 응답"]},
    "gemini-1.5-pro":   {"desc": "1M token context, 문서 처리 최강", "speed": "보통",  "cost": "유료",    "purpose": ["대용량 문서", "정확도"]},
    "gemini-1.5-flash": {"desc": "1.5 Pro 경량화, 빠른 작업용",     "speed": "빠름",  "cost": "저렴",    "purpose": ["빠른 응답", "가성비"]},
}


st.set_page_config(page_title="Model Manager", page_icon="🧠", layout="wide")
apply_global_css()

CONFIG = Path("model_config.json")

# ── config 로드/저장 ──
def load_cfg() -> dict:
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "active_provider": "",
        "active_model": "",
        "openai":  {"key": "", "model": "gpt-4o"},
        "ollama":  {"host": "http://localhost:11434", "models": []},
        "google":  {"key": "", "model": "gemini-1.5-pro"},
        "servers": [],
    }

def save_cfg(c: dict):
    CONFIG.write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")

def set_active(provider: str, model: str):
    c = load_cfg()
    c["active_provider"] = provider
    c["active_model"]    = model
    save_cfg(c)
    if provider == "ollama":
        from utils.ollama_client import unload_all_except

        host = c.get("ollama", {}).get("host", "http://localhost:11434")
        dropped = unload_all_except(host, model)
        if dropped:
            st.toast(f"VRAM 정리: {', '.join(dropped)} 내림", icon="🧹")
    st.toast(f"✅ 활성 모델: {model}", icon="🟢")

def save_role(role: str, provider: str, model: str):
    c = load_cfg()
    c.setdefault("role_models", {})[role] = {"provider": provider, "model": model}
    if role == "analysis":
        c["active_provider"] = provider
        c["active_model"]    = model
    save_cfg(c)

cfg = load_cfg()

# ── Ollama 자동 감지 (페이지 로드시 localhost 체크) ──
@st.cache_data(ttl=30)
def check_ollama(host: str):
    try:
        import requests
        r = requests.get(f"{host}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return True, models
        return False, []
    except Exception:
        return False, []

# ── 헤더 ──
st.markdown("## Model Manager")
st.caption("작업 목적에 맞는 AI 모델 자동 선택 — 역할별 모델을 설정하면 AI Prompt가 자동으로 라우팅합니다")

# ── 역할 기반 모델 할당 카드 ──
ollama_ok_pre, detected_pre = check_ollama(cfg["ollama"].get("host", "http://localhost:11434"))
installed_pre = detected_pre or cfg["ollama"].get("models", [])

_cloud_opts = [
    ("openai", "gpt-4o"), ("openai", "gpt-4o-mini"), ("openai", "gpt-4-turbo"),
    ("google", "gemini-2.0-flash"), ("google", "gemini-1.5-pro"), ("google", "gemini-1.5-flash"),
]

role_models = cfg.get("role_models", {})
role_cols = st.columns(4)
for _ci, (_rk, _rmeta) in enumerate(ROLES.items()):
    _rm = role_models.get(_rk, {})
    _cur_model    = _rm.get("model", "") if _rm else ""
    _cur_provider = _rm.get("provider", "") if _rm else ""
    with role_cols[_ci]:
        _bg     = "#f0fdf4" if _cur_model else "#fef9c3"
        _border = "2px solid #10b981" if _cur_model else "1px solid #fbbf24"
        _prov_tag = (
            f'<span style="font-size:10px;background:#eff6ff;color:#1e40af;'
            f'padding:1px 6px;border-radius:8px;display:inline-block;margin-top:2px">'
            f'{_cur_provider}</span>' if _cur_provider else ""
        )
        _model_line = (
            f'<div style="font-weight:600;font-size:12px;color:#1e293b;margin-top:4px">'
            f'{_cur_model}</div>{_prov_tag}'
        ) if _cur_model else (
            '<div style="font-size:12px;color:#b45309;margin-top:4px">미설정</div>'
        )
        st.markdown(
            f'<div style="border:{_border};border-radius:10px;padding:12px 14px;'
            f'background:{_bg};margin-bottom:8px;min-height:112px;box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
            f'<div style="font-size:22px;margin-bottom:2px">{_rmeta["icon"]}</div>'
            f'<div style="font-weight:700;font-size:14px">{_rmeta["label"]}</div>'
            f'<div style="font-size:11px;color:#64748b;margin:2px 0 4px">{_rmeta["desc"]}</div>'
            f'{_model_line}</div>',
            unsafe_allow_html=True,
        )
        if st.button("변경", key=f"edit_role_{_rk}", use_container_width=True):
            if st.session_state.get("editing_role") == _rk:
                st.session_state.pop("editing_role", None)
            else:
                st.session_state["editing_role"] = _rk
            st.rerun()

# ── 역할 편집 패널 ──
_editing = st.session_state.get("editing_role")
if _editing and _editing in ROLES:
    _emeta = ROLES[_editing]
    st.markdown(f"**{_emeta['icon']} {_emeta['label']} — 모델 선택**")
    _model_choices: list[tuple[str, str, str]] = [(f"[Ollama] {m}", "ollama", m) for m in installed_pre]
    for _prov, _mname in _cloud_opts:
        _model_choices.append((f"[{_prov.capitalize()}] {_mname}", _prov, _mname))
    if not _model_choices:
        st.warning("연결된 모델이 없습니다. Ollama를 연결하거나 아래 탭에서 API 키를 설정하세요.")
    else:
        _choice_labels = [c[0] for c in _model_choices]
        _rm_cur = cfg.get("role_models", {}).get(_editing, {})
        _cur_label = (
            f"[{_rm_cur.get('provider','').capitalize()}] {_rm_cur.get('model','')}"
            if _rm_cur.get("model") else ""
        )
        _def_idx = next(
            (i for i, c in enumerate(_model_choices) if c[0] == _cur_label), 0
        ) if _cur_label else 0
        _sel = st.selectbox(
            "모델", _choice_labels, index=_def_idx, key=f"sel_{_editing}",
            label_visibility="collapsed",
        )
        _sel_info = _model_choices[_choice_labels.index(_sel)]
        _acol1, _acol2 = st.columns([1, 5])
        if _acol1.button("적용", type="primary", key=f"apply_{_editing}"):
            save_role(_editing, _sel_info[1], _sel_info[2])
            st.session_state.pop("editing_role", None)
            st.toast(f"✅ {_emeta['label']} → {_sel_info[2]}", icon="🟢")
            st.rerun()
        if _acol2.button("취소", key=f"cancel_{_editing}"):
            st.session_state.pop("editing_role", None)
            st.rerun()

st.markdown("")

tab_ollama, tab_openai, tab_google, tab_servers = st.tabs(
    ["Ollama", "OpenAI", "Google Gemini", "원격 서버"]
)

# ═══════════════════════════════════════════════════
# OLLAMA 탭
# ═══════════════════════════════════════════════════
with tab_ollama:

    col_host, col_test = st.columns([3, 1])
    ollama_host = col_host.text_input(
        "Ollama 서버 주소",
        value=cfg["ollama"].get("host", "http://localhost:11434"),
        help="로컬: http://localhost:11434 | 원격: http://서버IP:11434",
    )

    # 연결 테스트
    if col_test.button("연결 확인", use_container_width=True):
        st.cache_data.clear()
        with st.spinner("연결 중..."):
            ok, models = check_ollama(ollama_host)
        if ok:
            cfg["ollama"]["host"]   = ollama_host
            cfg["ollama"]["models"] = models
            save_cfg(cfg)
            st.success(f"✅ 연결 성공! {len(models)}개 모델 발견")
            st.rerun()
        else:
            st.error("❌ 연결 실패 — Ollama가 실행 중인지 확인하세요")
            with st.expander("Ollama 설치 및 실행 방법"):
                st.code("""\
# macOS / Linux 설치
curl -fsSL https://ollama.com/install.sh | sh

# 실행 (백그라운드)
ollama serve &

# 또는 systemctl
sudo systemctl start ollama""", language="bash")

    # 자동 감지
    ollama_ok, detected_models = check_ollama(ollama_host)

    # ── VRAM에 올라간 모델 (활성 모델만 유지) ──
    if ollama_ok:
        from utils.ollama_client import list_loaded_models, unload_all_except

        loaded = list_loaded_models(ollama_host)
        active_ollama = (
            cfg.get("active_model", "")
            if cfg.get("active_provider") == "ollama"
            else ""
        )
        if loaded:
            st.markdown("#### VRAM 사용 중")
            for name in loaded:
                tag = "활성" if name == active_ollama else "대기"
                st.caption(f"• `{name}` — {tag}")
            if active_ollama and len(loaded) > 1:
                if st.button("활성 모델만 남기고 VRAM 정리", key="ollama_vram_clean"):
                    dropped = unload_all_except(ollama_host, active_ollama)
                    if dropped:
                        st.success(f"내림: {', '.join(dropped)}")
                    else:
                        st.info("정리할 모델이 없습니다.")
                    st.rerun()
            elif not active_ollama and loaded:
                st.caption("활성 모델을 선택하면 다른 모델은 자동으로 VRAM에서 내려갑니다.")

    st.markdown("---")

    # ── 설치된 모델 목록 (역할별 그룹) ──
    st.markdown("#### 설치된 모델")

    saved_models = cfg["ollama"].get("models", [])
    display_models = detected_models if detected_models else saved_models

    if ollama_ok and not detected_models:
        st.info("Ollama가 실행 중이지만 설치된 모델이 없습니다. 아래에서 모델을 다운로드하세요.")
    elif not ollama_ok:
        st.warning(
            "Ollama에 연결할 수 없습니다. "
            f"`{ollama_host}` 에서 실행 중인지 확인하거나 '연결 확인' 버튼을 눌러주세요."
        )
        if saved_models:
            st.caption(f"마지막으로 저장된 모델 목록: {', '.join(saved_models)}")

    if display_models:
        current_active = cfg.get("active_model", "")

        def _get_meta(m: str) -> dict:
            return OLLAMA_MODELS.get(m, OLLAMA_MODELS.get(m.split(":")[0], {}))

        _role_label_map = {
            "analysis":  ("📊 엑셀 분석",   "#eff6ff", "#1e40af"),
            "code":      ("⚙ 코드 생성",    "#f5f3ff", "#5b21b6"),
            "precision": ("🔬 고정밀 분석", "#fff7ed", "#9a3412"),
            "embedding": ("🔍 검색/RAG",    "#f0fdf4", "#065f46"),
        }

        # 역할별로 분류
        _grouped: dict[str, list] = {"analysis": [], "code": [], "precision": [], "embedding": [], "_other": []}
        for m in display_models:
            role = _get_meta(m).get("role", "_other")
            _grouped.setdefault(role, []).append(m)

        _model_idx = 0
        for _grp_role in ["analysis", "code", "precision", "embedding", "_other"]:
            _grp_models = _grouped.get(_grp_role, [])
            if not _grp_models:
                continue
            _rl, _rl_bg, _rl_fg = _role_label_map.get(_grp_role, ("기타", "#f1f5f9", "#374151"))
            st.markdown(
                f'<div style="font-size:11px;font-weight:700;color:{_rl_fg};background:{_rl_bg};'
                f'display:inline-block;padding:2px 10px;border-radius:8px;margin:8px 0 6px">{_rl}</div>',
                unsafe_allow_html=True,
            )
            _cols = st.columns(3)
            for _ci, m in enumerate(_grp_models):
                meta      = _get_meta(m)
                is_active = (m == current_active and cfg.get("active_provider") == "ollama")
                purpose_tags = "".join(
                    f'<span style="font-size:10px;background:{_rl_bg};color:{_rl_fg};'
                    f'padding:1px 5px;border-radius:6px;margin-right:2px">{t}</span>'
                    for t in meta.get("purpose", [])[:2]
                )
                speed_txt = meta.get("speed", "")
                mem_txt   = f'{meta.get("mem_gb", "")}GB' if meta.get("mem_gb") else ""
                with _cols[_ci % 3]:
                    if is_active:
                        st.markdown(
                            f'<div style="border:2px solid #10b981;border-radius:8px;'
                            f'padding:10px 14px;margin-bottom:8px;background:#f0fdf4;box-shadow:0 1px 4px rgba(0,0,0,0.06)">'
                            f'<div style="font-weight:600;font-size:13px">● {m}</div>'
                            f'<div style="margin:4px 0 2px">{purpose_tags}</div>'
                            f'<div style="font-size:11px;color:#64748b">{speed_txt} {("· "+mem_txt) if mem_txt else ""}</div>'
                            f'<div style="font-size:11px;color:#059669;margin-top:2px">활성 모델</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f'<div style="border:1px solid #e2e8f0;border-radius:8px;'
                            f'padding:10px 14px;margin-bottom:4px;box-shadow:0 1px 4px rgba(0,0,0,0.04)">'
                            f'<div style="font-weight:500;font-size:13px">{m}</div>'
                            f'<div style="margin:4px 0 2px">{purpose_tags}</div>'
                            f'<div style="font-size:11px;color:#94a3b8">{speed_txt} {("· "+mem_txt) if mem_txt else ""}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button("활성화", key=f"act_{_model_idx}", use_container_width=True):
                            cfg["ollama"]["host"]       = ollama_host
                            cfg["ollama"]["last_model"] = m
                            save_cfg(cfg)
                            set_active("ollama", m)
                            st.rerun()
                _model_idx += 1

    st.markdown("---")

    # ── 고급 설정: 모델 다운로드 (기본 접힘) ──
    with st.expander("고급 설정 — 모델 다운로드 / 직접 입력", expanded=False):
        st.caption("설치되지 않은 모델을 다운로드합니다. Ollama 연결이 필요합니다.")

        dl_model_names = list(OLLAMA_MODELS.keys())
        selected_model = st.session_state.get("selected_dl_model", dl_model_names[0])

        grid = [dl_model_names[i:i+3] for i in range(0, len(dl_model_names), 3)]
        for row in grid:
            cols = st.columns(3)
            for col, mname in zip(cols, row):
                with col:
                    meta         = OLLAMA_MODELS[mname]
                    is_installed = mname in display_models
                    is_selected  = (mname == selected_model)
                    border = "2px solid #3b82f6" if is_selected else "1px solid #e2e8f0"
                    bg     = "#eff6ff" if is_selected else "#fff"
                    inst_badge = (
                        '<span style="background:#d1fae5;color:#065f46;padding:1px 6px;'
                        'border-radius:8px;font-size:10px">설치됨</span>' if is_installed else ""
                    )
                    purpose_html = "".join(
                        f'<span style="font-size:10px;background:#f1f5f9;color:#475569;'
                        f'padding:1px 5px;border-radius:6px;margin-right:2px">{t}</span>'
                        for t in meta.get("purpose", [])[:2]
                    )
                    st.markdown(
                        f'<div style="border:{border};border-radius:8px;padding:10px 12px;'
                        f'background:{bg};margin-bottom:4px;min-height:90px">'
                        f'<div style="font-size:12px;font-weight:600">{mname} {inst_badge}</div>'
                        f'<div style="margin:3px 0">{purpose_html}</div>'
                        f'<div style="font-size:11px;color:#64748b">{meta["size"]} · {meta["speed"]} · {meta["mem_gb"]}GB</div>'
                        f'<div style="font-size:11px;color:#94a3b8;margin-top:1px">{meta["desc"]}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button(
                        "선택" if not is_selected else "✓ 선택됨",
                        key=f"sel_{mname}", use_container_width=True,
                        type="secondary" if not is_selected else "primary",
                    ):
                        st.session_state["selected_dl_model"] = mname
                        st.rerun()

        st.markdown("")
        # 직접 입력은 고급 설정 내부로 이동
        custom_model = st.text_input(
            "직접 입력 (예: llama3.1:8b-instruct-q4_0)",
            placeholder="ollama pull 모델명 직접 입력",
            key="custom_model_input",
        )
        dl_target = custom_model.strip() if custom_model.strip() else st.session_state.get("selected_dl_model", dl_model_names[0])

        col_dl, col_info = st.columns([1, 2])
        with col_dl:
            if st.button(f"{dl_target} 다운로드", type="primary", use_container_width=True):
                if not ollama_ok:
                    st.error("Ollama에 연결할 수 없습니다. 먼저 연결을 확인하세요.")
                else:
                    try:
                        import requests
                        progress_bar = st.progress(0, text=f"'{dl_target}' 다운로드 중...")
                        with requests.post(
                            f"{ollama_host}/api/pull",
                            json={"name": dl_target, "stream": True},
                            stream=True, timeout=600,
                        ) as resp:
                            if resp.status_code == 200:
                                total, completed = 0, 0
                                for line in resp.iter_lines():
                                    if line:
                                        try:
                                            data = json.loads(line)
                                            if data.get("total"):
                                                total     = data["total"]
                                                completed = data.get("completed", 0)
                                                pct       = int(completed / total * 100) if total else 0
                                                progress_bar.progress(
                                                    pct / 100,
                                                    text=f"다운로드: {pct}% ({completed/1e9:.1f}/{total/1e9:.1f} GB)",
                                                )
                                            if data.get("status") == "success":
                                                break
                                        except Exception:
                                            pass
                            progress_bar.progress(1.0, text="완료!")
                        st.cache_data.clear()
                        _, new_models = check_ollama(ollama_host)
                        cfg["ollama"]["host"]   = ollama_host
                        cfg["ollama"]["models"] = new_models
                        save_cfg(cfg)
                        st.success(f"✅ '{dl_target}' 다운로드 완료!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"다운로드 실패: {e}")
                        st.info(f"터미널 직접 실행: `ollama pull {dl_target}`")

        with col_info:
            st.caption(f"다운로드 대상: **{dl_target}**")
            if dl_target in OLLAMA_MODELS:
                m = OLLAMA_MODELS[dl_target]
                st.caption(f"{m['full']} | {m['size']} | {m['desc']}")


# ═══════════════════════════════════════════════════
# OPENAI 탭
# ═══════════════════════════════════════════════════
with tab_openai:
    st.markdown("#### OpenAI API 연결")

    oai_key = st.text_input(
        "API Key",
        value=cfg["openai"].get("key", ""),
        type="password",
        help="platform.openai.com → API keys 에서 발급",
    )

    oai_models = ["gpt-5-mini", "gpt-5", "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
    saved_oai_m = cfg["openai"].get("model", "gpt-4o")
    oai_model   = st.selectbox(
        "모델 선택",
        oai_models,
        index=oai_models.index(saved_oai_m) if saved_oai_m in oai_models else 0,
    )

    col_save, col_test = st.columns(2)

    if col_save.button("저장 및 활성화", type="primary", use_container_width=True):
        if not oai_key.strip():
            st.warning("API 키를 입력해주세요.")
        else:
            cfg["openai"] = {"key": oai_key, "model": oai_model}
            save_cfg(cfg)
            set_active("openai", oai_model)
            st.rerun()

    if col_test.button("연결 테스트", use_container_width=True):
        if not oai_key.strip():
            st.warning("API 키를 먼저 입력하세요.")
        else:
            with st.spinner("OpenAI API 연결 중..."):
                try:
                    import openai
                    client = openai.OpenAI(api_key=oai_key)
                    models = [m.id for m in client.models.list().data if "gpt" in m.id]
                    st.success(f"✅ 연결 성공! 사용 가능한 GPT 모델 {len(models)}개")
                except Exception as e:
                    st.error(f"❌ 연결 실패: {e}")

    st.markdown("---")
    st.markdown("#### 모델별 특징")
    _oai_rows = [list(OPENAI_MODELS.items())[i:i+3] for i in range(0, len(OPENAI_MODELS), 3)]
    for _oai_row in _oai_rows:
      cols = st.columns(3)
      for col, (name, meta) in zip(cols, _oai_row):
        is_active = (cfg.get("active_model") == name and cfg.get("active_provider") == "openai")
        border = "2px solid #10b981" if is_active else "1px solid #e2e8f0"
        bg     = "#f0fdf4" if is_active else "#fff"
        purpose_html = "".join(
            f'<span style="font-size:10px;background:#f5f3ff;color:#5b21b6;'
            f'padding:1px 5px;border-radius:6px;margin-right:2px">{t}</span>'
            for t in meta.get("purpose", [])[:2]
        )
        act_div = '<div style="font-size:11px;color:#059669;margin-top:4px">● 활성 모델</div>' if is_active else ""
        col.markdown(
            f'<div style="border:{border};border-radius:8px;padding:12px;background:{bg}">'
            f'<div style="font-weight:600;font-size:13px">{name}</div>'
            f'<div style="margin:4px 0">{purpose_html}</div>'
            f'<div style="font-size:11px;color:#64748b">{meta["desc"]}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px">속도: {meta["speed"]} | 비용: {meta["cost"]}</div>'
            f'{act_div}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════
# GOOGLE GEMINI 탭
# ═══════════════════════════════════════════════════
with tab_google:
    st.markdown("#### Google Gemini API 연결")

    g_key = st.text_input(
        "API Key",
        value=cfg["google"].get("key", ""),
        type="password",
        help="aistudio.google.com → Get API key 에서 무료 발급 가능",
    )

    g_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
    saved_gm = cfg["google"].get("model", "gemini-2.0-flash")
    g_model  = st.selectbox(
        "모델 선택",
        g_models,
        index=g_models.index(saved_gm) if saved_gm in g_models else 0,
    )

    col_gsave, col_gtest = st.columns(2)

    if col_gsave.button("저장 및 활성화", type="primary", use_container_width=True, key="gsave"):
        if not g_key.strip():
            st.warning("API 키를 입력해주세요.")
        else:
            cfg["google"] = {"key": g_key, "model": g_model}
            save_cfg(cfg)
            set_active("google", g_model)
            st.rerun()

    if col_gtest.button("연결 테스트", use_container_width=True, key="gtest"):
        if not g_key.strip():
            st.warning("API 키를 먼저 입력하세요.")
        else:
            with st.spinner("Google API 연결 중..."):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=g_key)
                    m = genai.GenerativeModel(g_model)
                    m.generate_content("Hello")
                    st.success("✅ 연결 성공!")
                except Exception as e:
                    st.error(f"❌ 연결 실패: {e}")

    st.markdown("---")
    st.markdown("#### 모델별 특징")
    cols = st.columns(len(GOOGLE_MODELS))
    for col, (name, meta) in zip(cols, GOOGLE_MODELS.items()):
        is_active = (cfg.get("active_model") == name and cfg.get("active_provider") == "google")
        border = "2px solid #10b981" if is_active else "1px solid #e2e8f0"
        bg     = "#f0fdf4" if is_active else "#fff"
        purpose_html = "".join(
            f'<span style="font-size:10px;background:#fff7ed;color:#9a3412;'
            f'padding:1px 5px;border-radius:6px;margin-right:2px">{t}</span>'
            for t in meta.get("purpose", [])[:2]
        )
        act_div = '<div style="font-size:11px;color:#059669;margin-top:4px">● 활성 모델</div>' if is_active else ""
        col.markdown(
            f'<div style="border:{border};border-radius:8px;padding:12px;background:{bg}">'
            f'<div style="font-weight:600;font-size:13px">{name}</div>'
            f'<div style="margin:4px 0">{purpose_html}</div>'
            f'<div style="font-size:11px;color:#64748b">{meta["desc"]}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px">속도: {meta["speed"]} | {meta["cost"]}</div>'
            f'{act_div}</div>',
            unsafe_allow_html=True,
        )


# ═══════════════════════════════════════════════════
# 원격 서버 탭
# ═══════════════════════════════════════════════════
with tab_servers:
    st.markdown("#### 등록된 원격 서버")

    if cfg["servers"]:
        for i, srv in enumerate(cfg["servers"]):
            c1, c2, c3 = st.columns([4, 1, 0.5])
            c1.write(f"**{srv['name']}** — `{srv['host']}:{srv['port']}` | {srv.get('gpu','')}")
            if c2.button("연결 테스트", key=f"tsrv_{i}"):
                try:
                    import requests
                    r = requests.get(f"{srv['url']}/api/tags", timeout=5)
                    if r.status_code == 200:
                        models = [m["name"] for m in r.json().get("models", [])]
                        st.success(f"✅ 연결됨 — 모델: {', '.join(models)}")
                    else:
                        st.error("❌ 응답 오류")
                except Exception:
                    st.error("❌ 연결 불가")
            if c3.button("🗑️", key=f"dsrv_{i}"):
                cfg["servers"].pop(i)
                save_cfg(cfg)
                st.rerun()
    else:
        st.info("등록된 원격 서버가 없습니다.")

    with st.expander("서버 추가"):
        with st.form("add_srv"):
            c1, c2, c3 = st.columns(3)
            s_name = c1.text_input("이름", placeholder="RTX 5090 Server")
            s_host = c2.text_input("Host", placeholder="192.168.1.100")
            s_port = c3.number_input("Port", value=11434, min_value=1, max_value=65535)
            s_gpu  = st.text_input("GPU 정보", placeholder="NVIDIA RTX 5090 24GB")
            if st.form_submit_button("추가", type="primary"):
                if s_name and s_host:
                    cfg["servers"].append({
                        "name": s_name, "host": s_host, "port": int(s_port),
                        "gpu":  s_gpu,  "url":  f"http://{s_host}:{s_port}",
                        "added": datetime.now().isoformat(),
                    })
                    save_cfg(cfg)
                    st.success(f"✅ '{s_name}' 추가됨")
                    st.rerun()

    with st.expander("원격 Ollama 설정 가이드"):
        st.code("""\
# 1. 원격 서버에 Ollama 설치
curl -fsSL https://ollama.com/install.sh | sh

# 2. 외부 접속 허용 (systemd 환경)
sudo systemctl edit ollama
# 아래 내용 추가:
# [Service]
# Environment="OLLAMA_HOST=0.0.0.0:11434"

# 3. Ollama 재시작 + 모델 다운로드
sudo systemctl restart ollama
ollama pull qwen2.5

# 4. 방화벽 열기
sudo ufw allow 11434/tcp""", language="bash")
