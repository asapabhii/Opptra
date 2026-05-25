from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import List

from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "cluster_formation_v1.0.txt"
)


def _read_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_cluster_payload(recommendations: List[dict]) -> dict:
    return {"recommendations_summary": recommendations}


def _summarize_recommendation(rec: dict) -> dict:
    return {
        "sku_id": rec["sku_id"],
        "sku_name": rec["sku_name"],
        "brand": rec["brand"],
        "sub_category": rec["sub_category"],
        "buy_box_state_6": rec["buy_box_state_6"],
        "action_type": rec["action_type"],
        "confidence": rec["confidence"],
        "competitor_classification": rec["competitor_classification"],
        "temporal_persistence": rec["temporal_persistence"],
        "doc_urgency": rec["doc_urgency"],
        "revenue_at_risk_7d": rec["revenue_at_risk_7d"],
        "working_capital_at_risk": rec["working_capital_at_risk"],
        "impact_score": rec["impact_score"],
        "flags": rec["flags"],
    }


def _rule_based_clusters(recommendations: List[dict]) -> List[dict]:
    clusters: dict[tuple[str, str], dict] = {}
    for rec in recommendations:
        key = (rec["action_type"], rec["competitor_classification"])
        cluster_name = (
            f"{rec['action_type'].replace('_', ' ').title()} - "
            f"{rec['competitor_classification']}"
        )
        root_cause = (
            "mixed_escalation"
            if rec["action_type"] == "escalate_to_human"
            else "grey_market_flooding"
        )
        clusters.setdefault(
            key,
            {
                "cluster_name": cluster_name,
                "root_cause": root_cause,
                "action_type": rec["action_type"],
                "sku_ids": [],
                "sku_count": 0,
                "combined_gmv_at_risk_inr": 0.0,
                "combined_working_capital_inr": 0.0,
                "headline": "",
                "impact_score": 0.0,
            },
        )
        cluster = clusters[key]
        cluster["sku_ids"].append(rec["sku_id"])
        cluster["sku_count"] += 1
        cluster["combined_gmv_at_risk_inr"] += rec["revenue_at_risk_7d"]
        cluster["combined_working_capital_inr"] += rec[
            "working_capital_at_risk"
        ]
        cluster["impact_score"] += rec["impact_score"]

    result = []
    for cluster in clusters.values():
        cluster["headline"] = (
            f"{cluster['sku_count']} SKUs grouped for "
            f"{cluster['action_type'].replace('_', ' ')}. "
            f"Combined GMV at risk: {cluster['combined_gmv_at_risk_inr']:.0f}."
        )
        result.append(cluster)
    return result


def build_rule_based_clusters(recommendations: List[dict]) -> List[dict]:
    return _rule_based_clusters(recommendations)


def _cluster_prompt_content(recommendations: List[dict]) -> str:
    summaries = [_summarize_recommendation(r) for r in recommendations]
    payload = _build_cluster_payload(summaries)
    return json.dumps(payload)


def _parse_clusters(raw: str) -> List[dict]:
    parsed = json.loads(raw)
    return parsed.get("clusters", [])


def _cluster_timeout_seconds() -> int:
    return int(os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "25"))


async def _call_gpt_clusters(
    client: AsyncOpenAI,
    recommendations: List[dict],
) -> List[dict]:
    response = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _read_prompt()},
            {
                "role": "user",
                "content": _cluster_prompt_content(recommendations),
            },
        ],
    )
    return _parse_clusters(response.choices[0].message.content or "{}")


async def _call_grok_clusters(
    client: AsyncOpenAI,
    recommendations: List[dict],
) -> List[dict]:
    response = await client.chat.completions.create(
        model=os.getenv("XAI_MODEL", "grok-2-latest"),
        temperature=0,
        max_tokens=1500,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": _read_prompt()},
            {
                "role": "user",
                "content": _cluster_prompt_content(recommendations),
            },
        ],
    )
    return _parse_clusters(response.choices[0].message.content or "{}")


async def form_clusters(
    recommendations: List[dict],
    api_key: str | None,
    openai_key: str | None = None,
    xai_key: str | None = None,
) -> List[dict]:
    if not recommendations:
        return []
    if not api_key and not openai_key and not xai_key:
        raise ValueError("No live AI provider configured for cluster synthesis")

    timeout = _cluster_timeout_seconds()
    tasks: list[tuple[str, asyncio.Task[List[dict]]]] = []

    if api_key:
        tasks.append(
            (
                "anthropic",
                asyncio.create_task(
                    asyncio.wait_for(
                        _call_anthropic_clusters(api_key, recommendations),
                        timeout=timeout,
                    )
                ),
            )
        )
    if openai_key:
        tasks.append(
            (
                "openai",
                asyncio.create_task(
                    asyncio.wait_for(
                        _call_gpt_clusters(AsyncOpenAI(api_key=openai_key), recommendations),
                        timeout=timeout,
                    )
                ),
            )
        )
    if xai_key:
        tasks.append(
            (
                "grok",
                asyncio.create_task(
                    asyncio.wait_for(
                        _call_grok_clusters(
                            AsyncOpenAI(
                                api_key=xai_key,
                                base_url=os.getenv(
                                    "XAI_BASE_URL",
                                    "https://api.x.ai/v1",
                                ),
                            ),
                            recommendations,
                        ),
                        timeout=timeout,
                    )
                ),
            )
        )

    if not tasks:
        raise ValueError("No live AI provider succeeded for cluster synthesis")

    pending = {task for _, task in tasks}
    names = {task: name for name, task in tasks}
    errors: list[str] = []

    while pending:
        done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            provider_name = names[task]
            try:
                return task.result()
            except Exception as exc:
                errors.append(f"{provider_name}: {exc}")

    raise ValueError("No live AI provider succeeded for cluster synthesis: " + " | ".join(errors))


async def _call_anthropic_clusters(api_key: str, recommendations: List[dict]) -> List[dict]:
    client = AsyncAnthropic(api_key=api_key)
    system_prompt = _read_prompt()
    user_message = _cluster_prompt_content(recommendations)
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        temperature=0,
        max_tokens=1500,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    raw = response.content[0].text
    return _parse_clusters(raw)
