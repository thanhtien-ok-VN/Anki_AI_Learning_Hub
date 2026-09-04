"""Validate game payloads against new schema structure."""

VALID_OPTION_TYPES = {
    "correct", "antonym", "synonym", "near_synonym", "different_word_class",
    "wrong_tense", "wrong_verb_form", "collocation_error", "wrong_context",
    "semantic_close", "grammar_error", "related_word",
    "phrasal_verb", "distractor", "semantic_error",
    "wrong_character", "tone_confusion", "tone_mutation"
}
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
        
        # Normalize invalid option types silently to ensure system robustness
        for o in options:
            o_type = o.get("type")
            if o_type not in VALID_OPTION_TYPES:
                o["type"] = "semantic_close"

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
        # distractors are optional now, default to empty list if missing
        if "distractors" not in b:
            b["distractors"] = []
    return {}


def _validate_story(r: dict) -> dict:
    questions = r.get("questions", [])
    if not isinstance(questions, list):
        return {"error": "Invalid questions list format."}

    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            continue
        raw_opts = q.get("options", [])
        if not isinstance(raw_opts, list):
            q["options"] = []
            continue

        # Normalize options array in-place
        norm_opts = []
        for o in raw_opts:
            if isinstance(o, dict):
                txt = str(o.get("text") or o.get("word") or o.get("option") or "").strip()
                norm_opts.append({"text": txt, "is_correct": bool(o.get("is_correct"))})
            else:
                norm_opts.append({"text": str(o).strip(), "is_correct": False})
        q["options"] = norm_opts

        # Check exactly 1 correct option if options exist
        if norm_opts:
            correct_count = sum(1 for o in norm_opts if o["is_correct"])
            if correct_count != 1:
                return {"error": f"Question {i+1}: expected 1 correct option, found {correct_count}."}

        # Auto-normalize question type seamlessly
        q_type = str(q.get("type", "detail")).lower().strip()
        if any(k in q_type for k in ("inference", "purpose", "main_idea", "summary")):
            q["type"] = "inference"
        elif any(k in q_type for k in ("vocab", "reference", "context")):
            q["type"] = "vocabulary"
        else:
            q["type"] = "detail"

    return {}
