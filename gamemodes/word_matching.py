import random
import uuid
from typing import Any, Optional
from .base import GameModeBase


class WordMatchingMode(GameModeBase):
    name = "matching"
    display_name = "Word Matching"
    icon = "🔗"
    is_offline = True

    BUILTIN_PAIRS = [
        ("ubiquitous", "present, appearing, or found everywhere"),
        ("pragmatic", "dealing with things in a practical way"),
        ("ambiguous", "open to more than one interpretation"),
        ("eloquent", "fluent or persuasive in speaking or writing"),
        ("resilient", "able to recover quickly from difficulties"),
        ("ephemeral", "lasting for a very short time"),
        ("consensus", "a general agreement among a group"),
        ("deteriorate", "to become progressively worse"),
        ("scrutiny", "critical observation or examination"),
        ("advocate", "to publicly recommend or support"),
        ("inevitable", "certain to happen; unavoidable"),
        ("mitigate", "to make less severe or serious"),
        ("paradigm", "a typical example or pattern of something"),
        ("verbose", "using more words than needed"),
        ("concise", "giving a lot of information briefly"),
        ("hypothesis", "a proposed explanation made as a starting point"),
        ("comprehensive", "including all elements or aspects"),
        ("perceive", "to become aware of through the senses"),
        ("plausible", "seeming reasonable or probable"),
        ("articulate", "having the ability to speak fluently and clearly"),
    ]

    def __init__(self, api_client=None, prompt_mgr=None):
        super().__init__(api_client, prompt_mgr)

    def generate(self, **kwargs) -> dict:
        count = kwargs.get("count", 8)
        source = kwargs.get("source", "builtin")
        selected_pairs = kwargs.get("vocab_pairs") or []

        if selected_pairs:
            pairs = [
                (pair.get("term", ""), pair.get("definition", ""))
                for pair in selected_pairs
                if pair.get("term") and pair.get("definition")
            ]
        elif source == "deck":
            pairs = self._extract_from_deck(kwargs.get("deck_name", ""), count)
        else:
            pairs = self.BUILTIN_PAIRS[:]

        if len(pairs) < count:
            needed = count - len(pairs)
            remaining_builtin = [p for p in self.BUILTIN_PAIRS if p not in pairs]
            pairs.extend(random.sample(remaining_builtin, min(needed, len(remaining_builtin))))

        if len(pairs) < 5:
            return {
                "error": True,
                "error_code": "E_NOT_ENOUGH_VOCAB",
                "message": "Không đủ từ vựng để nối. Cần ít nhất 5 cặp từ."
            }

        selected = random.sample(pairs, min(count, len(pairs)))
        game_id = str(uuid.uuid4())

        return {
            "game_id": game_id,
            "pairs": [
                {
                    "id": f"pair_{i+1}",
                    "term": term,
                    "definition": definition
                }
                for i, (term, definition) in enumerate(selected)
            ],
            "config": {
                "total_pairs": len(selected),
                "time_limit_sec": 60
            },
            "metadata": {
                "topic": kwargs.get("topic", ""),
                "level": kwargs.get("level", "")
            }
        }

    def _extract_from_deck(self, deck_name: str, count: int) -> list:
        from core.deck_source import _run_on_main, _collection, _plain
        from core.logger import log

        def _inner():
            col = _collection()
            if not col:
                return []
            pairs = []
            try:
                query = f'deck:"{deck_name}"' if deck_name else ""
                note_ids = col.find_notes(query)
                for nid in note_ids[: count * 4]:
                    note = col.get_note(nid)
                    fields = list(note.keys())
                    if len(fields) >= 2:
                        term = _plain(note[fields[0]])
                        definition = _plain(note[fields[1]])
                        if term and definition:
                            pairs.append((term, definition))
                    if len(pairs) >= count:
                        break
            except Exception as e:
                log.exception(f"Error extracting notes for matching game from deck '{deck_name}': {e}")
            return pairs

        extracted = _run_on_main(_inner) or []
        if len(extracted) < count:
            needed = count - len(extracted)
            remaining_builtin = [p for p in self.BUILTIN_PAIRS if p not in extracted]
            extracted.extend(random.sample(remaining_builtin, min(needed, len(remaining_builtin))))
        return extracted[:count]

    def render_ui_data(self, raw_result: dict) -> dict:
        return raw_result

    def check_answer(self, user_input: Any, correct: Any) -> dict:
        selected_pair = user_input.get("pair_id", "") if isinstance(user_input, dict) else ""
        target_pair = correct.get("pair_id", "") if isinstance(correct, dict) else ""
        is_match = selected_pair == target_pair and selected_pair != ""
        return {
            "correct": is_match,
            "user_pair": selected_pair,
            "expected_pair": target_pair,
            "points": 1 if is_match else 0,
        }

    def _format_anki_note(self, data: dict) -> tuple:
        front = data.get("term", data.get("word", data.get("content", "")))
        back = data.get("definition", data.get("meaning", data.get("translation", "")))
        return (front, back)
