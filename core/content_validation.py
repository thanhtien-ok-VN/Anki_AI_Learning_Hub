"""Validate game payloads against new schema structure."""

VALID_OPTION_TYPES = {"correct", "antonym", "grammar_error", "semantic_close"}
VALID_QUESTION_TYPES = {"detail", "inference", "vocabulary"}


def validate_game_result(gamemode: str, result: dict, requested_count: int = 0) -> dict:
    """Return {"error": "msg"} on failure, {} on success. Mutates result in-place for cleanup."""
    if not isinstance(result, dict):
        return {"error": "AI returned an invalid response."}

    if gamemode == "fill_blank":
        return _validate_fill_blank(result)
    elif gamemode == "cloze":
        return _validate_cloze(result)
    elif gamemode == "story":
        return _validate_story(result)
    return {}


def _validate_fill_blank(r: dict) -> dict:
    questions = r.get("questions", [r])
    for i, q in enumerate(questions):
        options = q.get("options", [])
        if len(options) != 4:
            return {"error": f"Question {i+1}: expected 4 options, got {len(options)}."}
        correct_count = sum(1 for o in options if o.get("is_correct"))
        if correct_count != 1:
            return {"error": f"Question {i+1}: expected 1 correct option, found {correct_count}."}
        types = {o.get("type") for o in options}
        invalid = types - VALID_OPTION_TYPES
        if invalid:
            return {"error": f"Question {i+1}: invalid option types: {invalid}"}
        words = [o.get("word", "").strip().lower() for o in options]
        if len(set(words)) != 4 or not all(words):
            return {"error": f"Question {i+1}: duplicate or empty option words."}
    return {}


def _validate_cloze(r: dict) -> dict:
    blanks = r.get("blanks", [])
    if not blanks:
        return {"error": "No blanks found in cloze result."}
    for i, b in enumerate(blanks):
        if not b.get("answer"):
            return {"error": f"Blank {i+1} missing answer."}
        distractors = b.get("distractors", [])
        if len(distractors) != 3:
            return {"error": f"Blank {i+1}: expected 3 distractors, got {len(distractors)}."}
    return {}


def _validate_story(r: dict) -> dict:
    questions = r.get("questions", [])
    for i, q in enumerate(questions):
        options = q.get("options", [])
        correct_count = sum(1 for o in options if o.get("is_correct"))
        if correct_count != 1:
            return {"error": f"Question {i+1}: expected 1 correct option, found {correct_count}."}
        if q.get("type") not in VALID_QUESTION_TYPES:
            return {"error": f"Question {i+1}: invalid type '{q.get('type')}'."}
    return {}
