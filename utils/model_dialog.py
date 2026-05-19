"""
모델 설정 다이얼로그 — Workspace 사이드바 ⚙ 버튼에서 호출
"""
from __future__ import annotations
import json
import streamlit as st
from pathlib import Path

CONFIG = Path("model_config.json")

ROLES: dict[str, dict] = {
    "analysis":  {"label": "엑셀 분석",   "icon": "📊", "desc": "비교·집계·집행률·표 이해"},
    "code":      {"label": "코드 실행",   "icon": "⚙",  "desc": "Python·pandas·차트 생성"},
    "precision": {"label": "고정밀 분석", "icon": "🔬", "desc": "긴 보고서·복잡한 추론"},
    "embedding": {"label": "검색/RAG",   "icon": "🔍", "desc": "파일 유사도·문서 검색"},
}

_CLOUD_MODELS = [
    ("openai",  "gpt-4o"),
    ("openai",  "gpt-4o-mini"),
    ("openai",  "gpt-4-turbo"),
    ("openai",  "gpt-3.5-turbo"),
    ("google",  "gemini-2.0-flash"),
    ("google",  "gemini-1.5-pro"),
    ("google",  "gemini-1.5-flash"),
]


def _load() -> dict:
    if CONFIG.exists():
        try:
            return json.loads(CONFIG.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "active_provider": "", "active_model": "",
        "openai":  {"key": "", "model": "gpt-4o"},
        "ollama":  {"host": "http://localhost:11434", "models": []},
        "google":  {"key": "", "model": "gemini-1.5-pro"},
        "role_models": {},
    }


def _save(c: dict) -> None:
    CONFIG.write_text(json.dumps(c, indent=2, ensure_ascii=False), encoding="utf-8")


def _check_ollama(host: str) -> tuple[bool, list[str]]:
    try:
        import requests
        r = requests.get(f"{host}/api/tags", timeout=3)
        if r.status_code == 200:
            return True, [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return False, []


def _set_active(provider: str, model: str) -> None:
    c = _load()
    c["active_provider"] = provider
    c["active_model"] = model
    _save(c)
    if provider == "ollama":
        try:
            from utils.ollama_client import unload_all_except
            host = c.get("ollama", {}).get("host", "http://localhost:11434")
            dropped = unload_all_except(host, model)
            if dropped:
                st.toast(f"VRAM 정리: {', '.join(dropped)}", icon="🧹")
        except Exception:
            pass
    st.toast(f"✅ 활성 모델: {model}", icon="🟢")


@st.dialog("⚙ 모델 설정", width="large")
def model_settings_dialog() -> None:
    cfg = _load()
    active_model    = cfg.get("active_model", "")
    active_provider = cfg.get("active_provider", "")

    # 현재 모델 상태 배너
    if active_model:
        st.markdown(
            f'<div style="background:#d1fae5;color:#065f46;padding:8px 14px;'
            f'border-radius:8px;font-size:13px;font-weight:600;margin-bottom:12px">'
            f'● 현재 활성 모델: {active_model} <span style="font-weight:400;font-size:12px">'
            f'via {active_provider}</span></div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("활성 모델이 없습니다. 아래에서 모델을 연결하세요.")

    tab_ollama, tab_api, tab_roles = st.tabs(["🖥 Ollama", "☁ API 키", "🎯 역할 배정"])

    # ── Ollama 탭 ────────────────────────────────────────────
    with tab_ollama:
        host = cfg.get("ollama", {}).get("host", "http://localhost:11434")
        c1, c2 = st.columns([4, 1])
        new_host = c1.text_input("Ollama 서버 주소", value=host, label_visibility="collapsed",
                                 placeholder="http://localhost:11434")
        if c2.button("연결 확인", use_container_width=True):
            with st.spinner("연결 중…"):
                ok, models = _check_ollama(new_host)
            if ok:
                cfg["ollama"]["host"] = new_host
                cfg["ollama"]["models"] = models
                _save(cfg)
                st.success(f"✅ 연결 성공 — {len(models)}개 모델 감지")
                st.cache_data.clear()
                st.rerun()
            else:
                st.error("연결 실패. 주소를 확인하거나 Ollama를 실행하세요.")

        ok, installed = _check_ollama(cfg.get("ollama", {}).get("host", host))
        installed = installed or cfg.get("ollama", {}).get("models", [])

        if not installed:
            st.info("설치된 모델이 없습니다. Ollama에서 `ollama pull <모델명>`으로 설치하세요.")
        else:
            st.markdown(f"**설치된 모델 ({len(installed)}개)**")
            for m in installed:
                is_active = (m == active_model and active_provider == "ollama")
                mc, mb = st.columns([4, 1])
                if is_active:
                    mc.markdown(
                        f'<div style="padding:6px 10px;border:2px solid #10b981;border-radius:8px;'
                        f'background:#f0fdf4;font-size:13px;font-weight:600">● {m}</div>',
                        unsafe_allow_html=True,
                    )
                    mb.markdown(
                        '<div style="padding:6px 0;text-align:center;font-size:12px;color:#059669">'
                        '활성</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    mc.markdown(
                        f'<div style="padding:6px 10px;border:1px solid #e2e8f0;border-radius:8px;'
                        f'font-size:13px">{m}</div>',
                        unsafe_allow_html=True,
                    )
                    if mb.button("활성화", key=f"dlg_act_{m}", use_container_width=True):
                        cfg["ollama"]["host"] = new_host
                        cfg["ollama"]["last_model"] = m
                        _save(cfg)
                        _set_active("ollama", m)
                        st.rerun()

    # ── API 키 탭 ─────────────────────────────────────────────
    with tab_api:
        st.markdown("**OpenAI**")
        oai_key = st.text_input(
            "API 키", value=cfg.get("openai", {}).get("key", ""),
            type="password", key="dlg_oai_key", placeholder="sk-…",
        )
        oai_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        oai_model  = st.selectbox(
            "기본 모델", oai_models,
            index=oai_models.index(cfg.get("openai", {}).get("model", "gpt-4o"))
            if cfg.get("openai", {}).get("model", "gpt-4o") in oai_models else 0,
            key="dlg_oai_model",
        )
        if st.button("OpenAI 저장 & 활성화", key="dlg_oai_save", type="primary"):
            cfg.setdefault("openai", {})["key"]   = oai_key
            cfg.setdefault("openai", {})["model"]  = oai_model
            _save(cfg)
            _set_active("openai", oai_model)
            st.rerun()

        st.divider()
        st.markdown("**Google Gemini**")
        ggl_key = st.text_input(
            "API 키", value=cfg.get("google", {}).get("key", ""),
            type="password", key="dlg_ggl_key", placeholder="AIza…",
        )
        ggl_models = ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
        ggl_model  = st.selectbox(
            "기본 모델", ggl_models,
            index=ggl_models.index(cfg.get("google", {}).get("model", "gemini-1.5-pro"))
            if cfg.get("google", {}).get("model", "gemini-1.5-pro") in ggl_models else 0,
            key="dlg_ggl_model",
        )
        if st.button("Google 저장 & 활성화", key="dlg_ggl_save", type="primary"):
            cfg.setdefault("google", {})["key"]   = ggl_key
            cfg.setdefault("google", {})["model"]  = ggl_model
            _save(cfg)
            _set_active("google", ggl_model)
            st.rerun()

    # ── 역할 배정 탭 ──────────────────────────────────────────
    with tab_roles:
        st.caption("작업 유형별로 다른 모델을 지정하면 AI가 자동으로 최적 모델을 선택합니다.")

        ok_r, installed_r = _check_ollama(cfg.get("ollama", {}).get("host", "http://localhost:11434"))
        installed_r = installed_r or cfg.get("ollama", {}).get("models", [])

        all_choices = [("ollama", m) for m in installed_r] + _CLOUD_MODELS
        choice_labels = [f"[{p.capitalize()}] {m}" for p, m in all_choices]

        role_models = cfg.get("role_models", {})

        for rk, rmeta in ROLES.items():
            rm        = role_models.get(rk, {})
            cur_model = rm.get("model", "")
            cur_prov  = rm.get("provider", "")
            cur_label = f"[{cur_prov.capitalize()}] {cur_model}" if cur_model else ""

            rc1, rc2 = st.columns([1, 3])
            rc1.markdown(
                f'<div style="padding:8px 4px;font-size:13px">'
                f'{rmeta["icon"]} <b>{rmeta["label"]}</b>'
                f'<div style="font-size:11px;color:#64748b">{rmeta["desc"]}</div></div>',
                unsafe_allow_html=True,
            )
            sel_idx = choice_labels.index(cur_label) if cur_label in choice_labels else 0
            new_label = rc2.selectbox(
                "", ["(미설정)"] + choice_labels,
                index=sel_idx + 1 if cur_label in choice_labels else 0,
                key=f"dlg_role_{rk}",
                label_visibility="collapsed",
            )
            if new_label != "(미설정)" and new_label != cur_label:
                idx = choice_labels.index(new_label)
                prov, mod = all_choices[idx]
                c2 = _load()
                c2.setdefault("role_models", {})[rk] = {"provider": prov, "model": mod}
                if rk == "analysis":
                    c2["active_provider"] = prov
                    c2["active_model"]    = mod
                _save(c2)
                st.toast(f"✅ {rmeta['label']} → {mod}")
                st.rerun()
