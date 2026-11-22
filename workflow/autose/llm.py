"""LLM client interface wrapping Google Gemini for AutoSE agents with automatic fallback."""
from __future__ import annotations

import os
import time
from typing import Any
from google import genai
from google.genai import types

FALLBACK_MODELS = [
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
]

def get_client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is required.")
    return genai.Client(api_key=api_key)

def call_gemini(
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_retries: int = 3,
) -> str:
    """Call Google Gemini with retries, exponential backoff, and model fallback on 429."""
    client = get_client()
    contents = f"{system_prompt}\n\n---\n\n{user_prompt}"

    candidate_models = [model] + [m for m in FALLBACK_MODELS if m != model]

    last_err = None
    for cand_model in candidate_models:
        for attempt in range(1, max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=cand_model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        temperature=temperature,
                    )
                )
                return response.text or ""
            except Exception as e:
                last_err = e
                err_str = str(e).lower()
                if "429" in err_str or "resource_exhausted" in err_str or "quota" in err_str:
                    print(f"[autose-llm] Quota limit reached on {cand_model}, falling back to next available model...")
                    break  # Fall back immediately to next candidate model
                time.sleep(2 ** attempt)

    raise RuntimeError(f"All Gemini models exhausted. Last error: {last_err}")
