import json
import sys
import unittest
from unittest.mock import MagicMock

# Mock aqt and GUI dependencies so tests run standalone
sys.modules['aqt'] = MagicMock()
sys.modules['aqt.qt'] = MagicMock()
sys.modules['aqt.gui_hooks'] = MagicMock()
sys.modules['aqt.utils'] = MagicMock()

from gamemodes import registry, list_manifests, get_gamemode, get_mode_limits, REGISTRY
from gamemodes.manifest import GameModeManifest, GameControlField
from core.engine import AIEngine, GAME_LIMITS


class TestManifestRegistry(unittest.TestCase):
    def test_all_8_modes_registered(self):
        mode_ids = registry.list_mode_ids()
        expected = [
            "fill_blank", "cloze", "translation", "unscramble",
            "matching", "story", "sentence_transform", "taboo"
        ]
        for m in expected:
            self.assertIn(m, mode_ids, f"Mode {m} missing from registry")
            cls = get_gamemode(m)
            self.assertIsNotNone(cls, f"get_gamemode('{m}') returned None")
            self.assertIsNotNone(getattr(cls, "manifest", None), f"Mode {m} has no manifest")

    def test_manifest_structure(self):
        manifests = list_manifests()
        self.assertEqual(len(manifests), 8)
        manifest_by_id = {m["id"]: m for m in manifests}

        # Check cloze custom controls
        cloze_m = manifest_by_id["cloze"]
        self.assertEqual(cloze_m["min_items"], 1)
        self.assertEqual(cloze_m["max_items"], 1)
        self.assertTrue(len(cloze_m["custom_controls"]) >= 1)
        num_blanks = cloze_m["custom_controls"][0]
        self.assertEqual(num_blanks["id"], "num_blanks")
        self.assertEqual(num_blanks["type"], "select")

        # Check sentence_transform custom controls
        st_m = manifest_by_id["sentence_transform"]
        self.assertEqual(st_m["min_items"], 1)
        self.assertEqual(st_m["max_items"], 1)
        self.assertTrue(len(st_m["custom_controls"]) >= 1)
        focus_ctrl = st_m["custom_controls"][0]
        self.assertEqual(focus_ctrl["id"], "focus")
        self.assertEqual(focus_ctrl["type"], "select")

        # Check matching
        match_m = manifest_by_id["matching"]
        self.assertEqual(match_m["min_items"], 5)
        self.assertEqual(match_m["max_items"], 50)
        self.assertTrue(match_m["requires_anki_cards"])

    def test_game_limits_alignment(self):
        limits = registry.get_all_limits()
        for mode_id, (min_val, max_val) in limits.items():
            self.assertIn(mode_id, GAME_LIMITS)
            self.assertEqual(GAME_LIMITS[mode_id], (min_val, max_val))

    def test_get_gamemodes_ipc_action(self):
        engine = AIEngine()
        raw_req = json.dumps({"action": "get_gamemodes", "data": {}})
        resp = engine.handle_js_message(raw_req)

        self.assertTrue(resp.get("success"), f"IPC call failed: {resp}")
        data = resp.get("data", {})
        self.assertIn("gamemodes", data)
        self.assertEqual(len(data["gamemodes"]), 8)


if __name__ == "__main__":
    unittest.main()
