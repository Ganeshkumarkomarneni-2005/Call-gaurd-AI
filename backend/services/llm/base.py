"""
Abstract base class for Large Language Model (LLM) providers.

All LLM implementations must satisfy this interface so that the conversation
engine and analysis pipeline can remain provider-independent.
"""

from abc import ABC, abstractmethod
import structlog


class BaseLLMProvider(ABC):
    """Abstract LLM provider interface."""

    provider_name: str = "base"

    def __init__(self) -> None:
        self.logger = structlog.get_logger(provider=self.provider_name)

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 500,
    ) -> str:
        """Generate a free-form text completion.

        Args:
            prompt: The user / human turn to respond to.
            system: Optional system instruction that frames the model role.
            max_tokens: Maximum number of tokens to generate.

        Returns:
            Generated text string.
        """

    @abstractmethod
    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Generate a structured JSON response conforming to *schema*.

        Args:
            prompt: The user / human turn to respond to.
            schema: JSON Schema dict describing the expected output.

        Returns:
            Parsed dict matching the schema.

        Raises:
            ValueError: If the response cannot be parsed or does not match.
        """

    async def health_check(self) -> bool:
        """Verify that the LLM provider is reachable and operational."""
        return True
