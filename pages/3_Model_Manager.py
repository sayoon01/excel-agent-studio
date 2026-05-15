"""
Model Manager — Ollama / OpenAI / Google 모델 연결·다운로드·활성화
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Model Manager", page_icon="🧠", layout="wide")

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
st.caption("AI 모델 연결 · 다운로드 · 활성화 — 설정한 모델은 AI Prompt 페이지에서 자동으로 사용됩니다")

# ── 현재 활성 모델 배지 ──
ap = cfg.get("active_provider", "")
am = cfg.get("active_model", "")
if am:
    provider_label = {"openai": "OpenAI", "ollama": "Ollama", "google": "Google"}.get(ap, ap)
    st.markdown(
        f'<div style="display:inline-flex;align-items:center;gap:8px;'
        f'background:#d1fae5;color:#065f46;padding:6px 16px;border-radius:20px;'
        f'font-size:14px;font-weight:600;margin-bottom:12px">'
        f'<span style="font-size:10px">●</span> 활성 모델: {am} &nbsp;·&nbsp; {provider_label}'
        f'</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div style="display:inline-flex;align-items:center;gap:8px;'
        'background:#fef9c3;color:#854d0e;padding:6px 16px;border-radius:20px;'
        'font-size:14px;font-weight:600;margin-bottom:12px">'
        '⚠ 활성 모델 없음 — 아래에서 모델을 연결하고 "활성화" 버튼을 누르세요'
        '</div>',
        unsafe_allow_html=True,
    )

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

    # ── 설치된 모델 목록 ──
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
        cols = st.columns(3)
        for idx, m in enumerate(display_models):
            with cols[idx % 3]:
                is_active = (m == current_active and cfg.get("active_provider") == "ollama")
                if is_active:
                    st.markdown(
                        f'<div style="border:2px solid #10b981;border-radius:8px;'
                        f'padding:10px 14px;margin-bottom:8px;background:#f0fdf4">'
                        f'<div style="font-weight:600;font-size:13px">● {m}</div>'
                        f'<div style="font-size:11px;color:#059669;margin-top:2px">활성 모델</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="border:1px solid #e2e8f0;border-radius:8px;'
                        f'padding:10px 14px;margin-bottom:4px">'
                        f'<div style="font-weight:500;font-size:13px">{m}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    if st.button("활성화", key=f"act_{idx}", use_container_width=True):
                        cfg["ollama"]["host"]      = ollama_host
                        cfg["ollama"]["last_model"] = m
                        save_cfg(cfg)
                        set_active("ollama", m)
                        st.rerun()

    st.markdown("---")

    # ── 모델 다운로드 ──
    st.markdown("#### 모델 다운로드")

    POPULAR_MODELS = {
        "gemma2":             ("Google Gemma 2", "9B", "경량·빠름"),
        "gemma2:27b":         ("Google Gemma 2 27B", "27B", "고성능"),
        "llama3.1":           ("Meta Llama 3.1", "8B", "범용 대화"),
        "llama3.1:70b":       ("Meta Llama 3.1 70B", "70B", "최고 성능 (GPU 필요)"),
        "qwen2.5":            ("Alibaba Qwen 2.5", "7B", "다국어·한국어 우수"),
        "qwen2.5:14b":        ("Qwen 2.5 14B", "14B", "한국어 고성능"),
        "codellama":          ("Meta Code Llama", "7B", "코드 생성 특화"),
        "deepseek-coder-v2":  ("DeepSeek Coder V2", "16B", "코드 최고 성능"),
        "mistral":            ("Mistral 7B", "7B", "경량·고성능"),
        "phi3":               ("Microsoft Phi-3", "3.8B", "최소 리소스"),
        "mixtral":            ("Mistral Mixtral 8x7B", "8x7B", "MoE 아키텍처"),
    }

    # 카드 형태로 모델 표시
    model_names = list(POPULAR_MODELS.keys())
    grid = [model_names[i:i+3] for i in range(0, len(model_names), 3)]

    selected_model = st.session_state.get("selected_dl_model", model_names[0])

    for row in grid:
        cols = st.columns(3)
        for col, mname in zip(cols, row):
            with col:
                mfull, msize, mdesc = POPULAR_MODELS[mname]
                is_installed = mname in display_models
                is_selected  = (mname == selected_model)

                border = "2px solid #3b82f6" if is_selected else "1px solid #e2e8f0"
                bg     = "#eff6ff" if is_selected else "#fff"
                badge  = f'<span style="background:#d1fae5;color:#065f46;padding:1px 6px;border-radius:8px;font-size:10px">설치됨</span>' if is_installed else ""

                st.markdown(
                    f'<div style="border:{border};border-radius:8px;padding:10px 12px;'
                    f'background:{bg};margin-bottom:4px;cursor:pointer;min-height:80px">'
                    f'<div style="font-size:12px;font-weight:600">{mname} {badge}</div>'
                    f'<div style="font-size:11px;color:#64748b;margin-top:2px">{mfull}</div>'
                    f'<div style="font-size:11px;color:#94a3b8">{msize} · {mdesc}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                if st.button("선택" if not is_selected else "✓ 선택됨", key=f"sel_{mname}", use_container_width=True, type="secondary" if not is_selected else "primary"):
                    st.session_state["selected_dl_model"] = mname
                    st.rerun()

    st.markdown("")
    custom_model = st.text_input(
        "직접 입력 (예: llama3.1:8b-instruct-q4_0)",
        placeholder="ollama 모델명 직접 입력",
        key="custom_model_input",
    )

    dl_target = custom_model.strip() if custom_model.strip() else st.session_state.get("selected_dl_model", model_names[0])

    col_dl, col_info = st.columns([1, 2])
    with col_dl:
        if st.button(f"{dl_target} 다운로드", type="primary", use_container_width=True):
            if not ollama_ok:
                st.error("Ollama에 연결할 수 없습니다. 먼저 연결을 확인하세요.")
            else:
                try:
                    import requests
                    progress_bar = st.progress(0, text=f"'{dl_target}' 다운로드 중...")
                    # 스트리밍으로 진행상황 표시
                    with requests.post(
                        f"{ollama_host}/api/pull",
                        json={"name": dl_target, "stream": True},
                        stream=True,
                        timeout=600,
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
                                            pct = int(completed / total * 100) if total else 0
                                            progress_bar.progress(
                                                pct / 100,
                                                text=f"다운로드 중: {pct}% ({completed/1e9:.1f}/{total/1e9:.1f} GB)"
                                            )
                                        if data.get("status") == "success":
                                            break
                                    except Exception:
                                        pass
                        progress_bar.progress(1.0, text="완료!")
                    st.cache_data.clear()
                    # 모델 목록 갱신
                    _, new_models = check_ollama(ollama_host)
                    cfg["ollama"]["host"]   = ollama_host
                    cfg["ollama"]["models"] = new_models
                    save_cfg(cfg)
                    st.success(f"✅ '{dl_target}' 다운로드 완료!")
                    st.rerun()
                except Exception as e:
                    st.error(f"다운로드 실패: {e}")
                    st.info(f"터미널에서 직접 실행: `ollama pull {dl_target}`")

    with col_info:
        st.caption(f"다운로드할 모델: **{dl_target}**")
        if dl_target in POPULAR_MODELS:
            name, size, desc = POPULAR_MODELS[dl_target]
            st.caption(f"{name} | {size} | {desc}")


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

    oai_models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
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
    model_info = {
        "gpt-4o":       ("가장 강력한 멀티모달 모델", "빠름", "$$"),
        "gpt-4o-mini":  ("gpt-4o 경량화, 가성비 최고", "매우 빠름", "$"),
        "gpt-4-turbo":  ("128K context, 강력한 추론", "보통", "$$$"),
        "gpt-3.5-turbo":("경량·빠른 응답, 간단한 작업", "최고속", "$"),
    }
    cols = st.columns(4)
    for col, (name, (desc, speed, cost)) in zip(cols, model_info.items()):
        is_active = (cfg.get("active_model") == name and cfg.get("active_provider") == "openai")
        border = "2px solid #10b981" if is_active else "1px solid #e2e8f0"
        bg     = "#f0fdf4" if is_active else "#fff"
        col.markdown(
            f'<div style="border:{border};border-radius:8px;padding:12px;background:{bg}">'
            f'<div style="font-weight:600;font-size:13px">{name}</div>'
            f'<div style="font-size:11px;color:#64748b;margin-top:4px">{desc}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px">속도: {speed} | 비용: {cost}</div>'
            f'{"<div style=font-size:11px;color:#059669;margin-top:4px>● 활성 모델</div>" if is_active else ""}'
            f'</div>',
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
    g_info = {
        "gemini-2.0-flash": ("최신·빠른 응답, 코드·분석 최적화", "매우 빠름", "무료 티어 있음"),
        "gemini-1.5-pro":   ("1M token context, 문서 처리 최강", "보통", "유료"),
        "gemini-1.5-flash": ("1.5 Pro 경량화, 빠른 작업용", "빠름", "저렴"),
    }
    cols = st.columns(3)
    for col, (name, (desc, speed, cost)) in zip(cols, g_info.items()):
        is_active = (cfg.get("active_model") == name and cfg.get("active_provider") == "google")
        border = "2px solid #10b981" if is_active else "1px solid #e2e8f0"
        bg     = "#f0fdf4" if is_active else "#fff"
        col.markdown(
            f'<div style="border:{border};border-radius:8px;padding:12px;background:{bg}">'
            f'<div style="font-weight:600;font-size:13px">{name}</div>'
            f'<div style="font-size:11px;color:#64748b;margin-top:4px">{desc}</div>'
            f'<div style="font-size:11px;color:#94a3b8;margin-top:4px">속도: {speed} | {cost}</div>'
            f'{"<div style=font-size:11px;color:#059669;margin-top:4px>● 활성 모델</div>" if is_active else ""}'
            f'</div>',
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
