"""
작업 유형 분류 → 모델 자동 선택 → LLM 호출.

사용자는 모델을 고르지 않습니다. Model Manager의 role_models / Ollama 풀에서
작업에 맞는 모델을 자동으로 골라 호출합니다.
"""
from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIG_FILE = Path("model_config.json")

TASK_TYPES = (
    "visualization",
    "code_generation",
    "long_form_report",
    "data_analysis",
    "quick_qa",
)

TASK_LABELS: dict[str, str] = {
    "visualization": "차트·시각화",
    "code_generation": "코드 생성",
    "long_form_report": "장문 보고서",
    "data_analysis": "데이터 분석",
    "quick_qa": "빠른 질의",
}

# README / Model Manager 역할과 정렬
TASK_TO_ROLE: dict[str, str] = {
    "visualization": "analysis",
    "code_generation": "code",
    "long_form_report": "precision",
    "data_analysis": "analysis",
    "quick_qa": "analysis",
}

DEFAULT_TASK_MODELS: dict[str, dict[str, Any]] = {
    "visualization": {
        "provider": "ollama",
        "model": "qwen3:14b",
        "fallbacks": ["qwen3", "qwen2.5:14b", "gemma3:12b"],
    },
    "code_generation": {
        "provider": "ollama",
        "model": "qwen2.5-coder:14b",
        "fallbacks": ["qwen2.5-coder", "deepseek-coder-v2", "codellama"],
    },
    "long_form_report": {
        "provider": "ollama",
        "model": "gemma3:27b",
        "fallbacks": ["gemma2:27b", "gemma3:12b", "llama3.1:70b"],
    },
    "data_analysis": {
        "provider": "ollama",
        "model": "qwen2.5:14b",
        "fallbacks": ["qwen3:14b", "qwen3", "qwen2.5"],
    },
    "quick_qa": {
        "provider": "ollama",
        "model": "gemma2",
        "fallbacks": ["phi3", "qwen2.5", "llama3.1"],
    },
}

CLOUD_FALLBACK: dict[str, dict[str, str]] = {
    "visualization": {"provider": "openai", "model": "gpt-4o-mini"},
    "code_generation": {"provider": "openai", "model": "gpt-4o"},
    "long_form_report": {"provider": "openai", "model": "gpt-4o"},
    "data_analysis": {"provider": "openai", "model": "gpt-4o-mini"},
    "quick_qa": {"provider": "google", "model": "gemini-2.0-flash"},
}

_ROLE_TO_TASK: dict[str, str] = {
    "analysis": "data_analysis",
    "code": "code_generation",
    "precision": "long_form_report",
    "embedding": "quick_qa",
}

_KEYWORDS: list[tuple[str, list[str], int]] = [
    ("code_generation", [
        "python", "코드", "스크립트", "script", "pandas", "exec", "함수 작성",
        "프로그램", "자동화 코드", "코딩",
    ], 3),
    ("visualization", [
        "차트", "그래프", "chart", "graph", "plot", "시각화", "막대", "선 그래프",
        "파이", "히스토그램", "bar chart", "visualize", "그려",
    ], 3),
    ("long_form_report", [
        "보고서", "리포트", "report", "요약본", "전체 요약", "인사이트 정리",
        "장문", "상세 분석", "종합 분석", "브리핑",
    ], 2),
    ("quick_qa", [
        "몇 행", "몇 열", "컬럼이 뭐", "열이 뭐", "what column", "how many row",
        "행 수", "열 수", "뭐야?", "알려줘", "간단히",
    ], 2),
    ("data_analysis", [
        "집행률", "집계", "합계", "비교", "필터", "분석", "aggregate", "compare",
        "합쳐", "통합", "정렬", "집계", "diff", "증감", "평균",
    ], 1),
]


@dataclass
class RouteResult:
    task_type: str
    task_label: str
    provider: str
    model: str
    api_base: str | None
    api_key: str | None
    role: str

    @property
    def display(self) -> str:
        prov = {"ollama": "Ollama", "openai": "OpenAI", "google": "Gemini"}.get(
            self.provider, self.provider
        )
        return f"{self.model} ({prov})"


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "active_provider": "",
        "active_model": "",
        "openai": {"key": "", "model": "gpt-4o"},
        "ollama": {"host": "http://localhost:11434", "models": []},
        "google": {"key": "", "model": "gemini-1.5-pro"},
        "role_models": {},
    }


def _normalize_model_name(name: str) -> str:
    return name.split(":")[0] if name and ":" not in name.split("/")[-1] else name


def _model_available(name: str, installed: list[str]) -> bool:
    if not installed:
        return True
    base = _normalize_model_name(name)
    for inst in installed:
        if inst == name or inst.startswith(base + ":") or inst == base:
            return True
    return False


def _pick_from_candidates(
    candidates: list[str],
    installed: list[str],
    provider: str,
) -> str | None:
    for c in candidates:
        if provider != "ollama" or _model_available(c, installed):
            return c
    return None


def get_ollama_installed(cfg: dict | None = None) -> list[str]:
    cfg = cfg or load_config()
    saved = cfg.get("ollama", {}).get("models") or []
    if saved:
        return saved
    host = cfg.get("ollama", {}).get("host", "http://localhost:11434")
    try:
        import requests

        r = requests.get(f"{host.rstrip('/')}/api/tags", timeout=3)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", []) if m.get("name")]
    except Exception:
        pass
    return []


def has_model_pool(cfg: dict | None = None) -> bool:
    cfg = cfg or load_config()
    if cfg.get("role_models"):
        return True
    if get_ollama_installed(cfg):
        return True
    if cfg.get("openai", {}).get("key"):
        return True
    if cfg.get("google", {}).get("key"):
        return True
    if cfg.get("active_provider") and cfg.get("active_model"):
        return True
    return False


def classify_task(prompt: str) -> str:
    """사용자 자연어 → 작업 유형."""
    text = prompt.lower().strip()
    if not text:
        return "data_analysis"

    scores: dict[str, int] = {t: 0 for t in TASK_TYPES}
    for task_type, keywords, weight in _KEYWORDS:
        for kw in keywords:
            if kw.lower() in text:
                scores[task_type] += weight

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return "data_analysis"


def task_type_from_role(role: str) -> str:
    return _ROLE_TO_TASK.get(role, "data_analysis")


def resolve_route(
    task_type: str,
    cfg: dict | None = None,
) -> RouteResult | None:
    """작업 유형 → provider + model."""
    cfg = cfg or load_config()
    installed = get_ollama_installed(cfg)
    role = TASK_TO_ROLE.get(task_type, "analysis")

    provider, model = "", ""

    # 1) role_models (Model Manager에서 설정)
    rm = cfg.get("role_models", {}).get(role, {})
    if rm.get("provider") and rm.get("model"):
        provider = rm["provider"]
        model = rm["model"]
        if provider == "ollama" and installed:
            if not _model_available(model, installed):
                picked = _pick_from_candidates(
                    [model] + DEFAULT_TASK_MODELS.get(task_type, {}).get("fallbacks", []),
                    installed,
                    "ollama",
                )
                if picked:
                    model = picked
                else:
                    provider, model = "", ""

    # 2) task_models (config 직접 지정)
    if not model:
        tm = cfg.get("task_models", {}).get(task_type, {})
        if tm.get("provider") and tm.get("model"):
            provider = tm["provider"]
            model = tm["model"]

    # 3) 기본 Ollama 매핑
    if not model:
        defaults = DEFAULT_TASK_MODELS.get(task_type, DEFAULT_TASK_MODELS["data_analysis"])
        provider = defaults["provider"]
        candidates = [defaults["model"]] + list(defaults.get("fallbacks", []))
        model = _pick_from_candidates(candidates, installed, "ollama") or defaults["model"]

    # 4) Ollama 미설치 시 클라우드 폴백
    if provider == "ollama" and installed and not _model_available(model, installed):
        cloud = CLOUD_FALLBACK.get(task_type)
        if cloud and cfg.get(cloud["provider"], {}).get("key"):
            provider, model = cloud["provider"], cloud["model"]
        else:
            picked = _pick_from_candidates(
                [m for m in installed],
                installed,
                "ollama",
            )
            if picked:
                model = picked
            elif cfg.get("openai", {}).get("key"):
                cloud = CLOUD_FALLBACK.get(task_type, CLOUD_FALLBACK["data_analysis"])
                provider, model = cloud["provider"], cloud["model"]
            else:
                return None

    if not provider and cfg.get("active_provider") and cfg.get("active_model"):
        provider = cfg["active_provider"]
        model = cfg["active_model"]

    if not provider or not model:
        if cfg.get("openai", {}).get("key"):
            cloud = CLOUD_FALLBACK.get(task_type, CLOUD_FALLBACK["data_analysis"])
            provider, model = cloud["provider"], cloud["model"]
        else:
            return None

    api_base: str | None = None
    api_key: str | None = None
    if provider == "ollama":
        api_base = cfg.get("ollama", {}).get("host", "http://localhost:11434")
    elif provider == "openai":
        api_key = cfg.get("openai", {}).get("key", "")
        if not api_key:
            return None
    elif provider == "google":
        api_key = cfg.get("google", {}).get("key", "")
        if not api_key:
            return None
    else:
        return None

    return RouteResult(
        task_type=task_type,
        task_label=TASK_LABELS.get(task_type, task_type),
        provider=provider,
        model=model,
        api_base=api_base,
        api_key=api_key,
        role=role,
    )


def route_for_prompt(prompt: str, cfg: dict | None = None) -> RouteResult | None:
    task_type = classify_task(prompt)
    return resolve_route(task_type, cfg)


def route_for_role(role: str, prompt: str = "", cfg: dict | None = None) -> RouteResult | None:
    task_type = classify_task(prompt) if prompt else task_type_from_role(role)
    if role in _ROLE_TO_TASK:
        task_type = task_type_from_role(role)
    return resolve_route(task_type, cfg)


def _full_messages(messages: list, system: str) -> list:
    return ([{"role": "system", "content": system}] if system else []) + messages


def call_with_route(
    messages: list,
    route: RouteResult,
    *,
    system: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    timeout: int = 180,
) -> str:
    full_msgs = _full_messages(messages, system)

    if route.provider == "openai":
        if not route.api_key:
            return "⚠️ OpenAI API 키가 없습니다. Model Manager에서 입력하세요."
        try:
            import openai

            resp = openai.OpenAI(api_key=route.api_key).chat.completions.create(
                model=route.model,
                messages=full_msgs,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            return f"⚠️ OpenAI 오류: {e}"

    if route.provider == "ollama":
        try:
            from utils.ollama_client import chat as ollama_chat

            resp = ollama_chat(
                route.api_base or "http://localhost:11434",
                route.model,
                full_msgs,
                stream=False,
                timeout=timeout,
            )
            if resp.status_code == 200:
                return resp.json().get("message", {}).get("content", "응답 파싱 실패")
            return f"⚠️ Ollama 오류 (HTTP {resp.status_code})"
        except Exception as e:
            return f"⚠️ Ollama 연결 실패: {e}"

    if route.provider == "google":
        if not route.api_key:
            return "⚠️ Google API 키가 없습니다. Model Manager에서 입력하세요."
        try:
            import google.generativeai as genai

            genai.configure(api_key=route.api_key)
            chat_text = (system + "\n\n" if system else "") + "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in messages
            )
            return genai.GenerativeModel(route.model).generate_content(chat_text).text
        except Exception as e:
            return f"⚠️ Google AI 오류: {e}"

    return "⚠️ 지원하지 않는 provider입니다."


def stream_with_route(
    messages: list,
    route: RouteResult,
    *,
    system: str = "",
    timeout: int = 180,
) -> Iterator[str]:
    full_msgs = _full_messages(messages, system)

    if route.provider == "ollama":
        try:
            from utils.ollama_client import iter_chat

            yield from iter_chat(
                route.api_base or "http://localhost:11434",
                route.model,
                full_msgs,
                timeout=timeout,
            )
            return
        except Exception as e:
            yield f"⚠️ Ollama 연결 실패: {e}"
            return

    yield call_with_route(messages, route, system=system, timeout=timeout)
