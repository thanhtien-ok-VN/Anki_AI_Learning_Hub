"""Validate Gemini game payloads before the web UI receives them."""
from __future__ import annotations

CHOICE_GAMES = {"fill_blank": "questions", "cloze": "blanks", "story": "comprehension_questions"}


def validate_game_result(gamemode: str, result: dict, requested_count: int) -> dict:
    if not isinstance(result, dict):
        return {"error": "AI returned an invalid response."}
    key = CHOICE_GAMES.get(gamemode)
    if not key:
        return {}
    items = result.get(key)
    if not isinstance(items, list) or not items:
        return {"error": f"AI response is missing {key}."}
    if len(items) > requested_count:
        result[key] = items[:requested_count]
        items = result[key]
    for item in items:
        options = item.get("options")
        correct = item.get("correct_index")
        if not isinstance(options, list) or len(options) != 4:
            return {"error": "AI must provide exactly four answer options for every question."}
        normalised = [str(option).strip() for option in options]
        if not all(normalised) or len({option.casefold() for option in normalised}) != 4:
            return {"error": "AI generated duplicate or empty answer options."}
        if not isinstance(correct, int) or correct < 0 or correct >= 4:
            return {"error": "AI generated an invalid correct answer index."}
        item["options"] = normalised
    return {}
