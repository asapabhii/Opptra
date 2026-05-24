from __future__ import annotations

import json
from typing import List

from models.recommendation import AiRecommendation


class RetryWithCorrectionError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class FallbackError(Exception):
    pass


def gate1_parse(raw_output: str, retry_count: int) -> dict:
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError as exc:
        cleaned_output = _extract_json_payload(raw_output)
        if cleaned_output is not None:
            try:
                return json.loads(cleaned_output)
            except json.JSONDecodeError:
                pass
        if retry_count < 2:
            raise RetryWithCorrectionError(
                "Your previous response was not valid JSON. Return ONLY valid "
                "JSON. No other text, no markdown backticks, no explanation."
            ) from exc
        raise FallbackError("JSON parse failed after retries") from exc


def _extract_json_payload(raw_output: str) -> str | None:
    text = raw_output.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3 and lines[-1].startswith("```"):
            return "\n".join(lines[1:-1]).strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start:end + 1]
    return None


def gate2_schema(parsed: dict) -> AiRecommendation:
    return AiRecommendation.model_validate(parsed)


def gate3_business_rules(payload: dict, rec: AiRecommendation) -> List[str]:
    violations: List[str] = []
    computed_floor = payload["computed_margin_floor"]
    if rec.recommended_price < computed_floor - 1.0:
        violations.append(
            "MARGIN_FLOOR_VIOLATION: "
            f"recommended={rec.recommended_price}, floor={computed_floor}"
        )
    if payload.get("map_enforced") and payload.get("map_price"):
        if rec.recommended_price < payload["map_price"] - 1.0:
            violations.append(
                    "MAP_VIOLATION: "
                    f"recommended={rec.recommended_price}, "
                    f"map={payload['map_price']}"
            )
    if rec.recommended_price <= 0:
        violations.append("ZERO_OR_NEGATIVE_PRICE")
    if abs(rec.margin_floor - computed_floor) / computed_floor > 0.02:
        violations.append(
            "MARGIN_FLOOR_MISMATCH: "
            f"ai_stated={rec.margin_floor}, computed={computed_floor}"
        )
    if rec.recommended_price > payload["current_price"] * 1.5:
        violations.append("ILLOGICAL_PRICE_HIKE")
    return violations


def apply_business_rule_violations(
    rec: AiRecommendation,
    violations: List[str],
) -> AiRecommendation:
    if not violations:
        return rec
    flags = set(rec.flags)
    flags.add("business_rule_violation_detected")
    rec.action_type = "escalate_to_human"
    rec.confidence = "low"
    rec.flags = list(flags)
    return rec
