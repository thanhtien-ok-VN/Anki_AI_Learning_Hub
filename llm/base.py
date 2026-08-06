"""Base interface for LLM Providers enforcing DIP (Dependency Inversion Principle)."""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional


class BaseLLMProvider(ABC):
    @abstractmethod
    def generate_structured(
        self,
        prompt: str,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.7,
        max_retries: int = 3,
        base_delay: float = 4.0,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from LLM."""
        pass

    @abstractmethod
    def generate_text_result(
        self,
        prompt: str,
        temperature: float = 0.7,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """Generate raw text response from LLM."""
        pass
