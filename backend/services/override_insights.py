from __future__ import annotations

import json
from pathlib import Path

from anthropic import AsyncAnthropic

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "override_insight_v1.0.txt"


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


async def extract_override_insight(api_key: str, payload: dict) -> dict:
    client = AsyncAnthropic(api_key=api_key)
    response = await client.messages.create(
        model="claude-haiku-3-5-20241022",
        temperature=0,
        max_tokens=250,
        system=_read_prompt(),
        messages=[{"role": "user", "content": json.dumps(payload)}],
    )
    return json.loads(response.content[0].text)
