"""Gemini client tuned for free-tier limits with exact token accounting.

* Per-minute 429s are temporary: wait the delay Google asks for, then retry the SAME model.
* Daily-quota 429s are not: fall back to the next model, and remember that this one is spent.
* 5xx (overloaded) errors: back off and retry.
"""
from __future__ import annotations

import os
import re
import time
from typing import Callable

from google import genai
from google.genai import types

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
]
MAX_WAIT_SECONDS = 90          # longer than this means a daily cap, not a per-minute one
_exhausted: set[str] = set()   # models whose daily quota is gone in this process
_token_hook: Callable[[int, int], None] | None = None


def set_token_hook(hook: Callable[[int, int], None] | None) -> None:
    global _token_hook
    _token_hook = hook


def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    return genai.Client(api_key=api_key)


def _retry_delay(err: str) -> float | None:
    m = re.search(r"retry in (?:(\d+)h)?(?:(\d+)m)?([\d.]+)s", err)
    if m:
        h, mi, s = (float(x) if x else 0.0 for x in m.groups())
        return h * 3600 + mi * 60 + s
    m = re.search(r"'retryDelay': '(\d+)s'", err)
    return float(m.group(1)) if m else None


def call_gemini(model: str, system_prompt: str, user_prompt: str,
                temperature: float = 0.2, max_retries: int = 6) -> str:
    client = get_client()
    contents = f"{system_prompt}\n\n---\n\n{user_prompt}"
    candidates = [m for m in [model] + FALLBACK_MODELS if m not in _exhausted]
    candidates = list(dict.fromkeys(candidates))
    last_err: Exception | None = None

    for cand in candidates:
        for attempt in range(1, max_retries + 1):
            try:
                resp = client.models.generate_content(
                    model=cand, contents=contents,
                    config=types.GenerateContentConfig(temperature=temperature))
                usage = getattr(resp, "usage_metadata", None)
                if usage and _token_hook:
                    inp = getattr(usage, "prompt_token_count", 0) or 0
                    out = getattr(usage, "candidates_token_count", 0) or 0
                    _token_hook(int(inp), int(out))
                    print(f"[autose-llm] model={cand} tokens={int(inp)}+{int(out)}", flush=True)
                else:
                    print(f"[autose-llm] model={cand}", flush=True)
                time.sleep(2)  # gentle pacing for free-tier RPM limits
                return resp.text or ""
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                low = msg.lower()
                if "429" in low or "resource_exhausted" in low:
                    delay = _retry_delay(msg)
                    if delay is not None and delay <= MAX_WAIT_SECONDS:
                        wait_s = delay + 3
                        print(f"[autose-llm] {cand}: rate limited, waiting {wait_s:.0f}s", flush=True)
                        time.sleep(wait_s)
                        continue
                    print(f"[autose-llm] {cand}: daily quota spent, trying next model", flush=True)
                    _exhausted.add(cand)
                    break
                if "503" in low or "500" in low or "unavailable" in low or "overloaded" in low:
                    wait_s = min(10 * attempt, 60)
                    print(f"[autose-llm] {cand}: transient {wait_s}s backoff ({type(e).__name__})", flush=True)
                    time.sleep(wait_s)
                    continue
                if "404" in low or "not_found" in low:
                    _exhausted.add(cand)
                    break
                raise
    raise RuntimeError(f"All Gemini models exhausted or unavailable. Last error: {last_err}")
