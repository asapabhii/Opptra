from __future__ import annotations


def get_candidates(all_signals: dict[str, dict]) -> list[str]:
    candidates: list[str] = []
    for sku_id, signals in all_signals.items():
        if signals["state_6"] != "winning_cleanly" or signals["doc_current"] > 60:
            candidates.append(sku_id)
    return candidates
