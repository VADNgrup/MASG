"""
Centralized LLM utility — direct HTTP calls via httpx.

Import llm_extension ONCE here so patches apply globally.
All agents import chat() / achat() from this module.
"""
import llm_extension  # noqa: F401 — patches openai & langchain_openai on import

import asyncio
import json
from typing import Optional

import httpx

from llm_extension.llm_config import llm_config


def chat(
    model: str,
    messages: list,
    temperature: float = 0.3,
    max_tokens: Optional[int] = None,
) -> str:
    """
    Synchronous chat completion via direct HTTP request.

    Returns the content string from the first choice.
    """
    url = f"{llm_config.BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {llm_config.API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    with httpx.Client(timeout=llm_config.DEFAULT_TIMEOUT) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        try:
            data = response.json()
        except Exception as exc:
            raise ValueError(
                f"LLM API returned non-JSON response "
                f"(status {response.status_code}): {response.text!r}"
            ) from exc

    return data["choices"][0]["message"]["content"]


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
