from __future__ import annotations

import json
from pathlib import Path

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "pattern_synthesis_v1.0.txt"


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def synthesize_patterns(api_key: str, decisions: list[dict]) -> dict:
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = _read_prompt() + "\n\n" + json.dumps(decisions)
    response = model.generate_content(prompt)
    return json.loads(response.text)
