"""Game Mode Manifest & Control Descriptors.

Defines the contract for self-describing game modes in Anki AI Learning Hub.
"""
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class GameControlField:
    """Descriptor for custom control inputs in the Game Configuration Panel."""
    id: str
    type: str  # "select" | "number" | "text"
    label_key: str
    default_label: str
    default_value: Any
    options: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GameModeManifest:
    """Self-describing manifest for a game mode plugin."""
    id: str
    icon: str
    title_key: str
    default_title: str
    desc_key: str
    default_desc: str
    min_items: int = 1
    max_items: int = 10
    default_items: int = 5
    requires_anki_cards: bool = False
    custom_controls: List[GameControlField] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        res = asdict(self)
        res["custom_controls"] = [c.to_dict() if hasattr(c, "to_dict") else c for c in self.custom_controls]
        return res
