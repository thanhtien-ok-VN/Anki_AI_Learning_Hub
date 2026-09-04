import os
import json
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Mock dependencies
import sys
sys.modules['core.logger'] = MagicMock()

from core.settings import SettingsManager, DEFAULT_SETTINGS

class TestSettingsManager(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.settings_path = os.path.join(self.temp_dir, "settings.json")

    def tearDown(self):
        if os.path.exists(self.settings_path):
            os.remove(self.settings_path)
        for f in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, f))
        os.rmdir(self.temp_dir)

    def test_defaults(self):
        sm = SettingsManager(self.settings_path)
        keys = sm.get_api_keys()
        self.assertEqual(len(keys), 10)
        self.assertEqual(keys, [""] * 10)
        self.assertNotIn("api_key", sm._settings)
        self.assertNotIn("api_key_count", sm._settings)
        self.assertEqual(sm.get("model"), "auto")

    def test_legacy_migration(self):
        legacy_data = {
            "api_key": "legacy-key",
            "api_key_count": 3,
            "api_key1": "",
            "model": "gpt-4"
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)
        
        sm = SettingsManager(self.settings_path)
        self.assertEqual(sm.get("api_key1"), "legacy-key")
        self.assertNotIn("api_key", sm._settings)
        self.assertNotIn("api_key_count", sm._settings)

    def test_legacy_migration_not_overwrite(self):
        legacy_data = {
            "api_key": "legacy-key",
            "api_key1": "new-key"
        }
        with open(self.settings_path, "w", encoding="utf-8") as f:
            json.dump(legacy_data, f)
        
        sm = SettingsManager(self.settings_path)
        self.assertEqual(sm.get("api_key1"), "new-key")
        self.assertNotIn("api_key", sm._settings)

    def test_set_many_validation(self):
        sm = SettingsManager(self.settings_path)
        
        res = sm.set_many({"temperature": 1.5})
        self.assertFalse(res["ok"])
        self.assertEqual(res["error_code"], "E_VALIDATION")
        
        res = sm.set_many({"unknown_field": "test", "api_key2": " test-key "})
        self.assertTrue(res["ok"])
        self.assertIn("unknown_field", res["ignored_keys"])
        self.assertIn("api_key2", res["changed_keys"])
        self.assertEqual(sm.get("api_key2"), "test-key")
        
    def test_atomic_save(self):
        sm = SettingsManager(self.settings_path)
        sm.set("api_key3", "some-key")
        
        self.assertTrue(os.path.exists(self.settings_path))
        with open(self.settings_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["api_key3"], "some-key")

    def test_corrupt_json(self):
        with open(self.settings_path, "w", encoding="utf-8") as f:
            f.write("{corrupt json")
            
        sm = SettingsManager(self.settings_path)
        self.assertEqual(sm.get("model"), "auto")
        
        files = os.listdir(self.temp_dir)
        self.assertTrue(any(f.startswith("settings.corrupt.") for f in files))
        
    def test_api_keys_methods(self):
        sm = SettingsManager(self.settings_path)
        sm.set_many({
            "api_key1": "short",
            "api_key2": "abcdefgh", # len=8
            "api_key3": "long-api-key-here-12345" # len>12
        })
        
        keys = sm.get_api_keys()
        self.assertEqual(len(keys), 10)
        self.assertEqual(keys[0], "short")
        
        active = sm.get_active_keys()
        self.assertEqual(len(active), 3)
        self.assertTrue(sm.has_any_key())
        
        masked = sm.get_masked_api_keys()
        self.assertEqual(len(masked), 10)
        self.assertEqual(masked[0], "****")
        self.assertEqual(masked[1], "ab****gh")
        self.assertEqual(masked[2], "long...2345")
        self.assertEqual(masked[3], "")

if __name__ == '__main__':
    unittest.main()
