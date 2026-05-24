from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "pattern_synthesis_v1.0.txt"
)


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _extract_json_text(text: str) -> str:
    """
    Gemini often returns:
      - raw JSON
      - JSON wrapped in markdown fences
        
```json
        ...
        
```
      - JSON with leading/trailing prose

    This tries hard to isolate the JSON payload.
    """
    if not isinstance(text, str):
        raise ValueError("Model response text was not a string")

    s = text.strip()

    # Strip common markdown code fences
    if s.startswith("```"):
        # Remove first fence line
        newline_idx = s.find("\n")
        s = s[newline_idx + 1 :] if newline_idx != -1 else ""
        if s.endswith("```"):
            s = s[: -len("```")].strip()

    # If it looks like a JSON array/object within larger text, extract by
    # delimiters.
    first_curly = s.find("{")
    first_square = s.find("[")

    candidates = []  # type: list[tuple[int, str]]
    if first_curly != -1:
        candidates.append((first_curly, "{"))
    if first_square != -1:
        candidates.append((first_square, "["))

    if not candidates:
        raise ValueError(
            "Could not find a JSON object/array start in model response"
        )

    start_index, start_char = min(candidates, key=lambda x: x[0])
    s = s[start_index:]

    if start_char == "{":
        last_index = s.rfind("}")
        if last_index == -1:
            raise ValueError("Could not find closing '}' for JSON object")
        return s[: last_index + 1].strip()

    last_index = s.rfind("]")
    if last_index == -1:
        raise ValueError("Could not find closing ']' for JSON array")
    return s[: last_index + 1].strip()


def synthesize_patterns(api_key: str, decisions: list[dict]) -> dict:
    import google.generativeai as genai

    if not isinstance(decisions, list):
        raise ValueError("decisions must be a list of objects")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-pro")
    prompt = _read_prompt() + "\n\n" + json.dumps(decisions)

    response = model.generate_content(prompt)
    raw_text = getattr(response, "text", None)
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Gemini returned an empty response")

    json_text = _extract_json_text(raw_text)

    try:
        parsed: Any = json.loads(json_text)
    except json.JSONDecodeError as exc:
        preview = raw_text[:500].replace("\n", " ")
        raise ValueError(
            f"Failed to parse Gemini JSON output: {exc}. "
            f"Raw preview: {preview}"
        ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("Expected Gemini to return a JSON object (dict)")

    return parsed
