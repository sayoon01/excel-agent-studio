"""공유 AI 호출 유틸리티 — File Manager, Dashboard 등에서 재사용."""
import json
from pathlib import Path

CONFIG_FILE = Path("model_config.json")


def load_active_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def call_ai_simple(prompt: str, system: str = "", timeout: int = 120) -> str:
    """활성 모델 설정으로 단순 1회 AI 호출. 오류는 문자열로 반환."""
    cfg      = load_active_config()
    provider = cfg.get("active_provider", "")
    model    = cfg.get("active_model", "")

    if not provider or not model:
        return "⚠️ 모델이 설정되지 않았습니다. **Model Manager**에서 모델을 먼저 활성화하세요."

    msgs = ([{"role": "system", "content": system}] if system else []) + \
           [{"role": "user", "content": prompt}]

    if provider == "openai":
        key = cfg.get("openai", {}).get("key", "")
        if not key:
            return "⚠️ OpenAI API 키가 없습니다. Model Manager에서 입력하세요."
        try:
            import openai
            resp = openai.OpenAI(api_key=key).chat.completions.create(
                model=model, messages=msgs, temperature=0.3, max_tokens=1500,
            )
            return resp.choices[0].message.content
        except Exception as e:
            return f"⚠️ OpenAI 오류: {e}"

    elif provider == "ollama":
        from utils.ollama_client import chat as ollama_chat

        host = cfg.get("ollama", {}).get("host", "http://localhost:11434")
        try:
            resp = ollama_chat(host, model, msgs, stream=False, timeout=timeout)
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "응답 파싱 실패")
            return f"⚠️ Ollama 오류 (HTTP {resp.status_code})"
        except Exception as e:
            return f"⚠️ Ollama 연결 실패: {e}"

    elif provider == "google":
        key = cfg.get("google", {}).get("key", "")
        if not key:
            return "⚠️ Google API 키가 없습니다. Model Manager에서 입력하세요."
        try:
            import google.generativeai as genai
            genai.configure(api_key=key)
            full = (system + "\n\n" + prompt) if system else prompt
            return genai.GenerativeModel(model).generate_content(full).text
        except Exception as e:
            return f"⚠️ Google AI 오류: {e}"

    return f"⚠️ 지원하지 않는 provider: {provider}"
