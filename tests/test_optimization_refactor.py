import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

sys.modules.setdefault("aqt", MagicMock())
sys.modules.setdefault("aqt.qt", MagicMock())
sys.modules.setdefault("aqt.gui_hooks", MagicMock())
sys.modules.setdefault("aqt.utils", MagicMock())

from aqt import mw
from core.deck_source import list_source_models, sample_vocab_pairs
from core.engine import AIEngine
from gamemodes.base import GameModeBase


class TestOptimizationRefactor(unittest.TestCase):
    @patch("core.engine.SessionTimer")
    def setUp(self, mock_timer):
        self.engine = AIEngine()

    def test_handle_check_answer_dispatches_hint_level_to_all_modes(self):
        """Verify polymorphic check_answer accepts hint_level without reflection."""
        modes = [
            "fill_blank",
            "cloze",
            "translation",
            "unscramble",
            "matching",
            "story",
            "sentence_transform",
            "taboo",
        ]
        for mode_name in modes:
            mock_gm = MagicMock()
            mock_gm.check_answer.return_value = {"correct": True, "score": 10.0}
            with patch.object(self.engine, "get_gamemode", return_value=mock_gm):
                res = self.engine._handle_check_answer(
                    {
                        "gamemode": mode_name,
                        "user_input": "ans",
                        "correct": "ans",
                        "hint_level": 2,
                    }
                )
                self.assertTrue(res.get("correct"))
                mock_gm.check_answer.assert_called_once_with("ans", "ans", hint_level=2)

    def test_handle_save_prefs_atomic_write(self):
        """Verify prefs are written atomically and file content is valid JSON."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_prefs = {"volume": 0.8, "ui_lang": "vi", "dark_mode": True}
            with patch("core.engine.ADDON_PATH", tmp_dir):
                res = self.engine._handle_save_prefs(test_prefs)
                self.assertTrue(res.get("success"))

                target_file = os.path.join(tmp_dir, "user_files", "prefs.json")
                self.assertTrue(os.path.exists(target_file))

                # Ensure no stray .tmp files left behind
                files = os.listdir(os.path.join(tmp_dir, "user_files"))
                self.assertEqual(files, ["prefs.json"])

                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertEqual(data, test_prefs)

    def test_list_source_models_fast_path_sqlite(self):
        """Verify list_source_models uses SQLite query instead of N get_note calls."""
        mock_col = MagicMock()
        mock_col.decks.get.return_value = {"name": "TestDeck"}
        mock_col.decks.decks = {"1": {"name": "TestDeck"}}
        mock_col.db.list.return_value = [101, 102]
        mock_col.models.get.side_effect = lambda mid: {"id": mid, "name": f"Model_{mid}"}

        with patch("core.deck_source.mw") as mock_mw:
            mock_mw.col = mock_col
            mock_mw.taskman = None  # main thread execution

            res = list_source_models(deck_id=1)
            self.assertTrue(res["success"])
            models = res["data"]["models"]
            self.assertEqual(len(models), 2)
            self.assertEqual(models[0]["name"], "Model_101")
            self.assertEqual(models[1]["name"], "Model_102")

            # col.db.list should have been called once, get_note NEVER called
            mock_col.db.list.assert_called_once()
            mock_col.get_note.assert_not_called()

    def test_sample_vocab_pairs_bounded_hydration_on_10k_fixture(self):
        """Verify sample_vocab_pairs scales with limit, not total deck size (10k notes)."""
        mock_col = MagicMock()
        mock_col.decks.get.return_value = {"name": "BigDeck"}
        mock_col.decks.decks = {"1": {"name": "BigDeck"}}
        mock_col.models.get.return_value = {
            "flds": [{"name": "Front"}, {"name": "Back"}]
        }

        # 10,000 note IDs
        total_notes = 10000
        all_nids = list(range(1, total_notes + 1))
        mock_col.db.list.return_value = all_nids

        # Weak words search mock
        def mock_find_notes(query):
            if "obscure" in query:
                return [42, 99]
            if "did:" in query:
                return all_nids
            return []

        mock_col.find_notes.side_effect = mock_find_notes

        def make_note(nid):
            note = MagicMock()
            if nid == 42:
                note.__getitem__.side_effect = lambda f: "obscure" if f == "Front" else "meaning of obscure"
            elif nid == 99:
                note.__getitem__.side_effect = lambda f: "obscure_two" if f == "Front" else "meaning two"
            else:
                note.__getitem__.side_effect = lambda f: f"word_{nid}" if f == "Front" else f"def_{nid}"
            return note

        mock_col.get_note.side_effect = make_note

        with patch("core.deck_source.mw") as mock_mw:
            mock_mw.col = mock_col
            mock_mw.taskman = None

            res = sample_vocab_pairs(
                deck_id=1,
                model_id=1,
                term_field="Front",
                definition_field="Back",
                limit=50,
                weak_words=["obscure"],
            )

            self.assertTrue(res["success"])
            pairs = res["data"]["pairs"]
            self.assertEqual(len(pairs), 50)

            # Crucial assertion: get_note must NOT be called 10,000 times!
            # It should be called at most ~60-70 times (bounded by limit + weak search)
            call_count = mock_col.get_note.call_count
            self.assertLess(call_count, 100)
            self.assertGreater(call_count, 0)

            # Check that weak word is included
            weak_pairs = [p for p in pairs if p.get("is_weak")]
            self.assertTrue(len(weak_pairs) >= 1)
            self.assertEqual(weak_pairs[0]["term"], "obscure")

    def test_save_to_anki_targeted_duplicate_check(self):
        """Verify save_to_anki checks duplicates per item rather than scanning entire deck."""
        class DummyMode(GameModeBase):
            name = "dummy"
            def _format_anki_note(self, data):
                return (data.get("front", ""), data.get("back", ""))
            def render_ui_data(self, raw_result):
                return raw_result
            def check_answer(self, user_input, correct, hint_level=0):
                return {"correct": True}

        dummy_mode = DummyMode()
        mock_col = MagicMock()
        mock_deck = {"id": 1, "name": "VocabDeck"}
        mock_col.decks.by_name.return_value = mock_deck
        mock_model = {"id": 10, "name": "Basic", "flds": [{"name": "Front"}, {"name": "Back"}]}
        mock_col.models.by_name.return_value = mock_model

        # Only item 1 already exists, item 2 is new
        mock_col.find_notes.side_effect = lambda q: [123] if "existing_word" in q else []
        existing_note = MagicMock()
        existing_note.__getitem__.side_effect = lambda f: "existing_word" if f == "Front" else "def 1"
        mock_col.get_note.return_value = existing_note

        mock_note = MagicMock()
        mock_note.fields = ["", ""]
        mock_note_cls = MagicMock(return_value=mock_note)
        sys.modules["anki.notes"] = MagicMock(Note=mock_note_cls)

        with patch("aqt.mw") as mock_mw:
            mock_mw.col = mock_col
            mock_mw.taskman = None

            items = [
                {"front": "existing_word", "back": "def 1"},
                {"front": "new_word", "back": "def 2"},
            ]
            saved_count = dummy_mode.save_to_anki(items, deck_name="VocabDeck")

            self.assertEqual(saved_count, 1)
            mock_col.add_note.assert_called_once()
            # find_notes should be called targetedly per candidate item (2 calls)
            self.assertEqual(mock_col.find_notes.call_count, 2)


if __name__ == "__main__":
    unittest.main()
