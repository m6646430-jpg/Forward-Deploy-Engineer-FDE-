"""LLM client — talks to OpenRouter's OpenAI-compatible API.

OpenRouter (https://openrouter.ai) is a single API in front of many providers (Anthropic,
Google, OpenAI, ...). We use it so the project runs on your OpenRouter credits and you can
swap models by changing one string in .env — no code change.

We call the REST endpoint directly with the stdlib (no extra dependency), the same
lightweight approach used by the streaming ingester.

Requires OPENROUTER_API_KEY in .env (a key that starts with `sk-or-v1-...`).
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key or key.startswith("sk-or-..."):
        raise SystemExit(
            "OPENROUTER_API_KEY is not set. Paste your OpenRouter key (sk-or-v1-...) "
            "into the .env file, then re-run."
        )
    return key


def chat(messages: list[dict], model: str, tools=None, tool_choice=None,
         max_tokens: int = 1024) -> dict:
    """POST a chat completion to OpenRouter and return the parsed JSON response."""
    body: dict = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
    if tool_choice:
        body["tool_choice"] = tool_choice

    req = urllib.request.Request(
        OPENROUTER_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            # Optional but recommended by OpenRouter for attribution:
            "HTTP-Referer": "https://github.com/m6646430-jpg/Forward-Deploy-Engineer-FDE-",
            "X-Title": "Review Intelligence",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        if e.code == 401:
            raise SystemExit("OpenRouter rejected the key (401). Check OPENROUTER_API_KEY in .env.")
        if e.code == 402:
            raise SystemExit("OpenRouter says insufficient credits (402). Top up at openrouter.ai.")
        raise SystemExit(f"OpenRouter error {e.code}: {detail[:400]}")


def text_of(response: dict) -> str:
    """Pull the assistant's text content from a chat response."""
    return response["choices"][0]["message"]["content"] or ""


def tool_args_of(response: dict) -> dict:
    """Pull the arguments of the first tool/function call, as a dict."""
    call = response["choices"][0]["message"]["tool_calls"][0]
    return json.loads(call["function"]["arguments"])
