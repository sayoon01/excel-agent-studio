"""공유 AI 호출 유틸리티 — 작업 유형별 자동 모델 라우팅."""
import json
from pathlib import Path

from utils.task_router import (
    RouteResult,
    call_with_route,
    classify_task,
    has_model_pool,
    load_config,
    route_for_prompt,
    route_for_role,
)

CONFIG_FILE = Path("model_config.json")


def load_active_config() -> dict:
    return load_config()


def call_ai_simple(
    prompt: str,
    system: str = "",
    timeout: int = 120,
    task_type: str | None = None,
) -> str:
    """작업 유형에 맞는 모델로 단순 1회 호출."""
    cfg = load_config()
    if not has_model_pool(cfg):
        return "⚠️ 모델 풀이 비어 있습니다. **Model Manager**에서 Ollama 모델을 연결하세요."

    tt = task_type or classify_task(prompt)
    route = resolve_route_safe(tt, prompt, cfg)
    if route is None:
        return "⚠️ 사용 가능한 모델이 없습니다. Model Manager에서 모델을 등록하세요."

    msgs = ([{"role": "system", "content": system}] if system else []) + [
        {"role": "user", "content": prompt}
    ]
    return call_with_route(msgs, route, system="", temperature=0.3, max_tokens=1500, timeout=timeout)


def resolve_route_safe(task_type: str, prompt: str, cfg: dict) -> RouteResult | None:
    route = route_for_prompt(prompt, cfg) if prompt else None
    if route and route.task_type == task_type:
        return route
    from utils.task_router import resolve_route

    return resolve_route(task_type, cfg)


def call_ai_for_task(
    messages: list,
    *,
    prompt: str = "",
    task_type: str | None = None,
    role: str | None = None,
    system: str = "",
    temperature: float = 0.1,
    max_tokens: int = 2000,
    timeout: int = 180,
) -> tuple[str, RouteResult | None]:
    """메시지 목록 + 작업 힌트로 자동 라우팅 후 호출."""
    cfg = load_config()
    if not has_model_pool(cfg):
        return "⚠️ 모델 풀이 비어 있습니다. **Model Manager**에서 모델을 연결하세요.", None

    if role:
        route = route_for_role(role, prompt, cfg)
    elif task_type:
        from utils.task_router import resolve_route

        route = resolve_route(task_type, cfg)
    else:
        user_text = prompt or next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
        )
        route = route_for_prompt(user_text, cfg)

    if route is None:
        return "⚠️ 사용 가능한 모델이 없습니다. Model Manager에서 모델을 등록하세요.", None

    text = call_with_route(
        messages,
        route,
        system=system,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    return text, route
