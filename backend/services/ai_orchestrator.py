from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, List, Optional
import logging

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


def _provider_timeout_seconds() -> int:
    return int(os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "25"))


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


async def _invoke_claude(
    payload: dict,
    claude_key: str,
    retry_count: int = 0,
    correction: Optional[str] = None,
) -> AiRecommendation:
    client = AsyncAnthropic(api_key=claude_key)
    for _ in range(3):
        try:
            raw = await _call_claude(client, payload, correction)
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
                raise
            correction = (
                "The previous attempt failed before producing a valid "
                "recommendation. Return ONLY valid JSON matching the schema."
            )
            retry_count += 1
    raise RuntimeError("Anthropic failed to return a valid recommendation")


async def _invoke_gpt(
    payload: dict,
    openai_key: str,
    retry_count: int = 0,
    correction: Optional[str] = None,
) -> AiRecommendation:
    client = AsyncOpenAI(api_key=openai_key)
    for _ in range(3):
        try:
            raw = await _call_gpt4o(client, payload, correction)
            parsed = gate1_parse(raw, retry_count)
            rec = gate2_schema(parsed)
            violations = gate3_business_rules(payload, rec)
            rec = apply_business_rule_violations(rec, violations)
            rec.model_used = "gpt-4o"
            rec.source = "ai_gpt4o_fallback"
            rec.generated_at = datetime.now(timezone.utc).isoformat()
            return rec
        except RetryWithCorrectionError as exc:
            correction = exc.message
            retry_count += 1
        except Exception as exc:
            correction = (
                "The previous attempt failed before producing a valid "
                "recommendation. Return ONLY valid JSON matching the schema."
            )
            retry_count += 1
    raise RuntimeError("OpenAI failed to return a valid recommendation")


async def _invoke_grok(
    payload: dict,
    xai_key: str,
    retry_count: int = 0,
    correction: Optional[str] = None,
) -> AiRecommendation:
    client = AsyncOpenAI(
        api_key=xai_key,
        base_url=os.getenv("XAI_BASE_URL", "https://api.x.ai/v1"),
    )
    for _ in range(3):
        try:
            raw = await _call_grok(client, payload, correction)
            parsed = gate1_parse(raw, retry_count)
            rec = gate2_schema(parsed)
            violations = gate3_business_rules(payload, rec)
            rec = apply_business_rule_violations(rec, violations)
            rec.model_used = os.getenv("XAI_MODEL", "grok-2-latest")
            rec.source = "ai_grok_fallback"
            rec.generated_at = datetime.now(timezone.utc).isoformat()
            return rec
        except RetryWithCorrectionError as exc:
            correction = exc.message
            retry_count += 1
        except Exception:
            correction = (
                "The previous attempt failed before producing a valid "
                "recommendation. Return ONLY valid JSON matching the schema."
            )
            retry_count += 1
    raise RuntimeError("Grok failed to return a valid recommendation")


async def _run_single(
    payload: dict,
    claude_key: str | None,
    openai_key: str | None,
    xai_key: str | None,
) -> AiRecommendation:
    retry_count = 0
    correction: Optional[str] = None
    errors: list[str] = []
    timeout = _provider_timeout_seconds()

    if claude_key:
        try:
            return await asyncio.wait_for(
                _invoke_claude(payload, claude_key, retry_count, correction),
                timeout=timeout,
            )
        except Exception as exc:
            errors.append(f"anthropic: {exc}")
            logging.exception("Anthropic provider error for SKU %s: %s", payload.get("sku_id"), exc)

    if openai_key:
        try:
            return await asyncio.wait_for(
                _invoke_gpt(payload, openai_key, retry_count, correction),
                timeout=timeout,
            )
        except Exception as exc:
            errors.append(f"openai: {exc}")
            logging.exception("OpenAI provider error for SKU %s: %s", payload.get("sku_id"), exc)

    if xai_key:
        try:
            return await asyncio.wait_for(
                _invoke_grok(payload, xai_key, retry_count, correction),
                timeout=timeout,
            )
        except Exception as exc:
            errors.append(f"grok: {exc}")
            logging.exception("Grok provider error for SKU %s: %s", payload.get("sku_id"), exc)

    raise RuntimeError("No live AI provider succeeded for this SKU: " + " | ".join(errors))


async def run_parallel(
    payloads: List[dict],
    claude_key: str | None,
    openai_key: str | None,
    xai_key: str | None = None,
    max_concurrency: int = 3,
    timeout_seconds: int = 60,
    start_hook: Optional[Callable[[dict], None]] = None,
    progress_hook: Optional[Callable[[dict, AiRecommendation], None]] = None,
) -> List[AiRecommendation | None]:
    semaphore = asyncio.Semaphore(max_concurrency)

    async def _guarded(payload: dict) -> AiRecommendation | None:
        async with semaphore:
            try:
                if start_hook:
                    start_hook(payload)
                rec = await asyncio.wait_for(
                    _run_single(payload, claude_key, openai_key, xai_key),
                    timeout=timeout_seconds,
                )
            except asyncio.TimeoutError:
                logging.exception("Live AI request timed out for SKU %s", payload.get("sku_id"))
                return None
            except Exception:
                logging.exception("Live AI request failed for SKU %s", payload.get("sku_id"))
                return None
            if progress_hook:
                progress_hook(payload, rec)
            return rec

    tasks = [asyncio.create_task(_guarded(payload)) for payload in payloads]
    return await asyncio.gather(*tasks)
