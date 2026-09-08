"""Central path resolution and configuration for Anki AI Learning Hub.

Defines canonical filesystem paths for add-on resources, user files, logs, and templates.
Supports dependency injection via PathConfig for hermetic unit testing.
"""
from dataclasses import dataclass
import os
from typing import Optional

# Root directory of the add-on package
ADDON_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@dataclass(frozen=True)
class PathConfig:
    """Configurable path resolver supporting custom directory roots."""
    addon_root: str = ADDON_ROOT

    @property
    def user_files_dir(self) -> str:
        return os.path.join(self.addon_root, "user_files")

    @property
    def prefs_path(self) -> str:
        return os.path.join(self.user_files_dir, "prefs.json")

    @property
    def settings_path(self) -> str:
        return os.path.join(self.user_files_dir, "settings.json")

    @property
    def log_path(self) -> str:
        return os.path.join(self.user_files_dir, "ai_hub.log")

    @property
    def flow_log_path(self) -> str:
        return os.path.join(self.user_files_dir, "ai_hub_flow.jsonl")

    @property
    def prompts_dir(self) -> str:
        return os.path.join(self.addon_root, "prompts")

    @property
    def lang_dir(self) -> str:
        return os.path.join(self.addon_root, "lang")

    @property
    def web_dir(self) -> str:
        return os.path.join(self.addon_root, "web")


# Default global instance
PATHS = PathConfig()

# Canonical constant exports for backward compatibility
ADDON_PATH = PATHS.addon_root
USER_FILES_DIR = PATHS.user_files_dir
PREFS_PATH = PATHS.prefs_path
SETTINGS_PATH = PATHS.settings_path
LOG_PATH = PATHS.log_path
FLOW_LOG_PATH = PATHS.flow_log_path
PROMPTS_DIR = PATHS.prompts_dir
LANG_DIR = PATHS.lang_dir
WEB_DIR = PATHS.web_dir
