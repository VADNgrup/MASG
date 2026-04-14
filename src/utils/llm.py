import asyncio
import base64
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

from src.utils.config import Config

_LOG_PATH = Path("logs/llm_calls.jsonl")


def _write_log(model: str, token_usage: dict, elapsed: float) -> None:
    """Append a single JSON line to the LLM call log file."""
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "token_usage": token_usage,
        "elapsed_s": round(elapsed, 3),
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

_MAX_RETRIES = 6

def chat(
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Synchronous chat completion via direct HTTP request.
    Retries up to _MAX_RETRIES times with exponential backoff on transient errors.

    ``base_url`` and ``api_key`` override ``Config.LLM_BASE_URL`` /
    ``Config.OPENAI_API_KEY`` when provided (e.g. for the eval endpoint).

    Returns the content string from the first choice.
    """
    resolved_base = (base_url or Config.LLM_BASE_URL).rstrip("/")
    resolved_key = api_key or Config.OPENAI_API_KEY
    url = f"{resolved_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    last_exc: Exception = RuntimeError("No attempts made")

    t0 = time.monotonic()
    for attempt in range(_MAX_RETRIES):
        try:
            with httpx.Client(timeout=120) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                try:
                    data = response.json()
                except Exception as exc:
                    raise ValueError(
                        f"LLM API returned non-JSON response "
                        f"(status {response.status_code}): {response.text!r}"
                    ) from exc

            content = data["choices"][0]["message"]["content"]
            _write_log(model, data.get("usage", {}), time.monotonic() - t0)
            return _strip_think(content)

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_exc = exc
            wait = min(2 ** attempt, 30)
            print(f"[llm] Attempt {attempt + 1}/{_MAX_RETRIES} failed: {exc}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"LLM request failed after {_MAX_RETRIES} attempts") from last_exc


def _strip_think(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


async def achat(
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Async chat completion — runs the sync chat() in a thread executor
    so it does not block the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: chat(model, messages, temperature, max_tokens),
    )

def _vlm_config() -> tuple[str, str, str]:
    """Return (base_url, api_key, model) for the VLM endpoint from app config."""
    base = Config.VLM_BASE_URL.rstrip("/")
    if not base.endswith("/v1"):
        base = f"{base}/v1"
    return base, Config.VLM_API_KEY, Config.VLM_MODEL_NAME


def b64_image(image_bytes: bytes, mime: str = "image/png") -> dict:
    """
    Build an OpenAI-compatible ``image_url`` content item from raw bytes.

    Usage inside a messages list::

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image."},
                    b64_image(raw_png_bytes),
                ],
            }
        ]
    """
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime};base64,{encoded}"},
    }


def vision_chat(
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """
    Synchronous multimodal chat via the VLM endpoint (Config.VLM_BASE_URL).

    ``messages`` follow the OpenAI format and may contain mixed content items,
    e.g. text + image_url (use the ``b64_image()`` helper to build image items).
    Retries up to _MAX_RETRIES times with exponential backoff.

    ``base_url`` and ``api_key`` override the VLM defaults when provided
    (e.g. for the eval endpoint).

    Returns the content string from the first choice (think-tags stripped).
    """
    vlm_base, vlm_key, default_model = _vlm_config()
    resolved_base = (base_url or vlm_base).rstrip("/")
    resolved_key = api_key or vlm_key
    url = f"{resolved_base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model or default_model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    last_exc: Exception = RuntimeError("No attempts made")

    t0 = time.monotonic()
    for attempt in range(_MAX_RETRIES):
        try:
            with httpx.Client(timeout=120) as client:
                response = client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                try:
                    data = response.json()
                except Exception as exc:
                    raise ValueError(
                        f"VLM API returned non-JSON response "
                        f"(status {response.status_code}): {response.text!r}"
                    ) from exc

            content = data["choices"][0]["message"]["content"]
            _write_log(payload["model"], data.get("usage", {}), time.monotonic() - t0)
            return _strip_think(content)

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_exc = exc
            wait = min(2 ** attempt, 30)
            print(f"[vlm] Attempt {attempt + 1}/{_MAX_RETRIES} failed: {exc}. Retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError(f"VLM request failed after {_MAX_RETRIES} attempts") from last_exc


async def avision_chat(
    messages: list,
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Async multimodal chat — runs the sync vision_chat() in a thread executor
    so it does not block the event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        None,
        lambda: vision_chat(messages, model, temperature, max_tokens),
    )

