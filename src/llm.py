"""LLM client — provider-agnostic, OpenAI-compatible chat completions over stdlib.

The project talks to any OpenAI-compatible endpoint, chosen entirely in .env:

  • Google Gemini (FREE tier):
        LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai
        LLM_API_KEY=<your Gemini key, starts with AIza...>
  • OpenRouter (paid, many models):
        LLM_BASE_URL=https://openrouter.ai/api/v1
        LLM_API_KEY=<your key, starts with sk-or-v1-...>

Swapping providers is a .env edit — no code change. We call the REST endpoint directly
with the stdlib, the same lightweight approach used by the streaming ingester.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")

_PLACEHOLDERS = {"", "sk-or-...", "sk-or-v1-...", "AIza...", "PASTE_YOUR_KEY_HERE"}


def _api_key() -> str:
    key = (os.getenv("LLM_API_KEY")
           or os.getenv("OPENROUTER_API_KEY")
           or os.getenv("GEMINI_API_KEY") or "").strip()
    if key in _PLACEHOLDERS:
        raise SystemExit(
            "No LLM API key set. Put your key on the LLM_API_KEY line in .env "
            "(Gemini key from your stock-digest project works, and it's free), then re-run."
        )
    return key


def chat(messages: list[dict], model: str, tools=None, tool_choice=None,
         max_tokens: int = 1024) -> dict:
    """POST a chat completion and return the parsed JSON response."""
    body: dict = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
    if tool_choice:
        body["tool_choice"] = tool_choice

    req = urllib.request.Request(
        f"{BASE_URL}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_api_key()}",
            "Content-Type": "application/json",
            # OpenRouter uses these for attribution; other providers ignore them.
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
        if e.code in (401, 403):
            raise SystemExit(f"LLM provider rejected the key ({e.code}). Check LLM_API_KEY in .env.")
        if e.code == 402:
            raise SystemExit("Insufficient credits (402). Use the free Gemini tier or top up.")
        if e.code == 429:
            raise SystemExit("Rate limited (429). Free tiers are slow — wait a bit or lower volume.")
        raise SystemExit(f"LLM error {e.code}: {detail[:400]}")


def text_of(response: dict) -> str:
    """Pull the assistant's text content from a chat response."""
    return response["choices"][0]["message"]["content"] or ""


def tool_args_of(response: dict) -> dict:
    """Pull the arguments of the first tool/function call, as a dict."""
    call = response["choices"][0]["message"]["tool_calls"][0]
    return json.loads(call["function"]["arguments"])
