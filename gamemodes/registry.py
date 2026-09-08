"""Dynamic Game Mode Registry.

Provides central registration, manifest discovery, and limits resolution
for all game modes in the Anki AI Learning Hub.
"""
from typing import Any, Dict, List, Optional, Tuple, Type


class GameModeRegistry:
    """Thread-safe registry for GameMode plugins."""

    def __init__(self):
        self._modes: Dict[str, Any] = {}

    def register(self, mode_id: str, mode_cls: Any) -> None:
        """Register a GameMode class under a unique identifier."""
        self._modes[mode_id] = mode_cls

    def get(self, mode_id: str) -> Optional[Any]:
        """Retrieve a registered GameMode class by ID."""
        return self._modes.get(mode_id)

    def list_mode_ids(self) -> List[str]:
        """Return a list of all registered mode identifiers."""
        return list(self._modes.keys())

    def list_manifests(self) -> List[Dict[str, Any]]:
        """Return serialized manifests for all registered game modes."""
        manifests = []
        for mode_id, cls in self._modes.items():
            manifest = getattr(cls, "manifest", None)
            if manifest:
                manifests.append(manifest.to_dict() if hasattr(manifest, "to_dict") else manifest)
            else:
                # Fallback manifest for unmigrated or dynamic classes
                manifests.append({
                    "id": mode_id,
                    "icon": getattr(cls, "icon", "🎮"),
                    "title_key": f"{mode_id}.title",
                    "default_title": getattr(cls, "display_name", mode_id.replace("_", " ").title()),
                    "desc_key": f"{mode_id}.desc",
                    "default_desc": "",
                    "min_items": 1,
                    "max_items": 10,
                    "default_items": 5,
                    "requires_anki_cards": False,
                    "custom_controls": [],
                })
        return manifests

    def get_limits(self, mode_id: str) -> Tuple[int, int]:
        """Return (min_items, max_items) for a given mode from its manifest."""
        cls = self.get(mode_id)
        if cls:
            manifest = getattr(cls, "manifest", None)
            if manifest:
                return (manifest.min_items, manifest.max_items)
        # Default fallback limits
        if mode_id == "matching":
            return (5, 50)
        elif mode_id == "story":
            return (3, 10)
        return (1, 10)

    def get_all_limits(self) -> Dict[str, Tuple[int, int]]:
        """Return a dictionary of mode_id -> (min_items, max_items)."""
        return {mode_id: self.get_limits(mode_id) for mode_id in self._modes}


# Global singleton instance
registry = GameModeRegistry()
