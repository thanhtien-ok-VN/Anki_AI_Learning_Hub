"""LLM Provider Factory.

Enforces the Dependency Inversion Principle (DIP) by abstracting provider creation
and configuration away from the core generation service and game modes.
"""
import threading
from typing import Any, Dict, Optional, Type
from llm.base import BaseLLMProvider
from llm.gemini import GeminiProvider
from core.logger import log


class LLMProviderFactory:
    """Registry and factory for LLM Providers."""
    _registry: Dict[str, Type[BaseLLMProvider]] = {}

    @classmethod
    def register(cls, name: str, provider_cls: Type[BaseLLMProvider]) -> None:
        """Register a new LLM provider implementation."""
        cls._registry[name.lower()] = provider_cls
        log.info(f"Registered LLM provider: {name}")

    @classmethod
    def create(
        cls,
        name: str = "gemini",
        settings: Optional[Dict[str, Any]] = None,
        cancel_event: Optional[threading.Event] = None,
        **kwargs
    ) -> BaseLLMProvider:
        """Instantiate a provider by name with given settings and cancel token."""
        name = (name or "gemini").lower()
        provider_cls = cls._registry.get(name)
        if not provider_cls:
            log.warn(f"Unknown provider '{name}', falling back to 'gemini'")
            provider_cls = cls._registry.get("gemini", GeminiProvider)

        if hasattr(provider_cls, "from_settings"):
            return provider_cls.from_settings(settings=settings, cancel_event=cancel_event, **kwargs)

        # Generic provider construction
        return provider_cls(**kwargs)

    @classmethod
    def list_providers(cls) -> list[str]:
        """Return a list of registered provider names."""
        return list(cls._registry.keys())


# Pre-register default Gemini provider
LLMProviderFactory.register("gemini", GeminiProvider)
