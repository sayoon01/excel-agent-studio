"""Ollama VRAM 관리 — 활성 모델만 메모리에 유지."""
from __future__ import annotations

import json
from collections.abc import Iterator

import requests

DEFAULT_KEEP_ALIVE = "30m"


def _same_model(a: str, b: str) -> bool:
    """Ollama ``/api/ps`` 이름과 활성 모델명이 동일한지 비교."""
    return bool(a and b and a == b)


def list_loaded_models(host: str, timeout: int = 5) -> list[str]:
    try:
        r = requests.get(f"{host.rstrip('/')}/api/ps", timeout=timeout)
        if r.status_code != 200:
            return []
        return [m.get("name", "") for m in r.json().get("models", []) if m.get("name")]
    except Exception:
        return []


def unload_model(host: str, model: str, timeout: int = 30) -> bool:
    """VRAM에서 모델을 내립니다 (``keep_alive: 0``)."""
    try:
        r = requests.post(
            f"{host.rstrip('/')}/api/generate",
            json={"model": model, "prompt": "", "keep_alive": 0},
            timeout=timeout,
        )
        return r.status_code == 200
    except Exception:
        return False


def unload_all_except(host: str, keep_model: str) -> list[str]:
    """``keep_model`` 외 VRAM에 올라간 모델을 모두 내립니다. 반환: 내린 모델명 목록."""
    unloaded: list[str] = []
    for name in list_loaded_models(host):
        if _same_model(name, keep_model):
            continue
        if unload_model(host, name):
            unloaded.append(name)
    return unloaded


def chat(
    host: str,
    model: str,
    messages: list,
    *,
    stream: bool = False,
    keep_alive: str = DEFAULT_KEEP_ALIVE,
    unload_others: bool = True,
    timeout: int = 180,
) -> requests.Response:
    """Ollama ``/api/chat`` — 필요 시 다른 모델을 먼저 내린 뒤 호출."""
    host = host.rstrip("/")
    if unload_others:
        unload_all_except(host, model)
    return requests.post(
        f"{host}/api/chat",
        json={
            "model": model,
            "messages": messages,
            "stream": stream,
            "keep_alive": keep_alive,
        },
        timeout=timeout,
    )


def iter_chat(
    host: str,
    model: str,
    messages: list,
    *,
    keep_alive: str = DEFAULT_KEEP_ALIVE,
    unload_others: bool = True,
    timeout: int = 180,
) -> Iterator[str]:
    """Ollama ``/api/chat`` 스트리밍 — 토큰(청크) 단위로 ``content``를 yield."""
    host = host.rstrip("/")
    if unload_others:
        unload_all_except(host, model)
    try:
        with requests.post(
            f"{host}/api/chat",
            json={
                "model": model,
                "messages": messages,
                "stream": True,
                "keep_alive": keep_alive,
            },
            stream=True,
            timeout=timeout,
        ) as resp:
            if resp.status_code != 200:
                yield f"⚠️ Ollama 오류 (HTTP {resp.status_code})"
                return
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if chunk.get("done"):
                    break
                part = chunk.get("message", {}).get("content") or ""
                if part:
                    yield part
    except Exception as e:
        yield f"⚠️ Ollama 연결 실패: {e}"
