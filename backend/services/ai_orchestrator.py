from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

from models.recommendation import AiRecommendation
from services.validation import (
    RetryWithCorrectionError,
    apply_business_rule_violations,
    gate1_parse,
    gate2_schema,
    gate3_business_rules,
)

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "sku_recommendation_v1.0.txt"
)


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_user_message(
    payload: dict,
    correction: Optional[str] = None,
) -> str:
    base = (
        "Analyze this SKU and return your recommendation as JSON:\n"
        f"{json.dumps(payload)}"
    )
    if correction:
        return f"{correction}\n{base}"
    return base


async def _call_claude(
    client: AsyncAnthropic,
    payload: dict,
    correction: Optional[str] = None,
) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        temperature=0,
        max_tokens=600,
        system=_read_prompt(),
        messages=[
            {
                "role": "user",
                "content": _build_user_message(payload, correction),
            },
        ],
    )
    return response.content[0].text


async def _call_gpt4o(
    client: AsyncOpenAI,
    payload: dict,
    correction: Optional[str] = None,
) -> str:
    response = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        max_tokens=600,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _read_prompt()},
            {
                "role": "user",
                "content": _build_user_message(payload, correction),
            },
        ],
    )
    return response.choices[0].message.content or ""


async def _call_grok(
    client: AsyncOpenAI,
    payload: dict,
    correction: Optional[str] = None,
) -> str:
    response = await client.chat.completions.create(
        model=os.getenv("XAI_MODEL", "grok-2-latest"),
        temperature=0,
        max_tokens=600,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _read_prompt()},
            {
                "role": "user",
                "content": _build_user_message(payload, correction),
            },
        ],
    )
    return response.choices[0].message.content or ""


async def _run_single(
    payload: dict,
    claude_key: str | None,
    openai_key: str | None,
    xai_key: str | None,
) -> AiRecommendation:
    claude = AsyncAnthropic(api_key=claude_key) if claude_key else None
    gpt = AsyncOpenAI(api_key=openai_key) if openai_key else None
    grok = (
        AsyncOpenAI(
            api_key=xai_key,
            base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
        )
        if xai_key
        else None
    )

    retry_count = 0
    correction = None

    if claude:
        for _ in range(2):
            try:
                raw = await _call_claude(claude, payload, correction)
                parsed = gate1_parse(raw, retry_count)
                rec = gate2_schema(parsed)
                violations = gate3_business_rules(payload, rec)
                rec = apply_business_rule_violations(rec, violations)
                rec.model_used = "claude-sonnet-4-20250514"
                rec.source = "ai_claude_sonnet"
                rec.generated_at = datetime.now(timezone.utc).isoformat()
                return rec
            except RetryWithCorrectionError as exc:
                correction = exc.message
                retry_count += 1
            except Exception as exc:
                if "credit balance is too low" in str(exc).lower():
                    break
                correction = (
                    "The previous attempt failed before producing a valid "
                    "recommendation. Return ONLY valid JSON matching the "
                    "schema."
                )
                retry_count += 1

    if gpt:
        try:
            raw = await _call_gpt4o(gpt, payload, correction)
            parsed = gate1_parse(raw, retry_count)
            rec = gate2_schema(parsed)
            violations = gate3_business_rules(payload, rec)
            rec = apply_business_rule_violations(rec, violations)
            rec.model_used = "gpt-4o"
            rec.source = "ai_gpt4o_fallback"
            rec.generated_at = datetime.now(timezone.utc).isoformat()
            return rec
        except Exception:
            pass

    if grok:
        try:
            raw = await _call_grok(grok, payload, correction)
            parsed = gate1_parse(raw, retry_count)
            rec = gate2_schema(parsed)
            violations = gate3_business_rules(payload, rec)
            rec = apply_business_rule_violations(rec, violations)
            rec.model_used = os.getenv("XAI_MODEL", "grok-2-latest")
            rec.source = "ai_grok_fallback"
            rec.generated_at = datetime.now(timezone.utc).isoformat()
            return rec
        except Exception:
            pass

    raise RuntimeError("No live AI provider succeeded for this SKU")


async def run_parallel(
    payloads: List[dict],
    claude_key: str | None,
    openai_key: str | None,
    xai_key: str | None = None,
    max_concurrency: int = 3,
    timeout_seconds: int = 60,
    progress_hook: Optional[Callable[[dict, AiRecommendation], None]] = None,
) -> List[AiRecommendation]:
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _guarded(payload: dict) -> AiRecommendation:
        async with semaphore:
            try:
                rec = await asyncio.wait_for(
                    _run_single(
                        payload,
                        claude_key,
                        openai_key,
                        xai_key,
                    ),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                raise RuntimeError("Live AI request timed out")
            if progress_hook:
                progress_hook(payload, rec)
            return rec

    tasks = [asyncio.create_task(_guarded(payload)) for payload in payloads]
    return await asyncio.gather(*tasks)
