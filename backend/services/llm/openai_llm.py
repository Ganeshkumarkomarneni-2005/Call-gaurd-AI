"""
OpenAI LLM provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (OPENAI_API_KEY)

Required environment variables:
    OPENAI_API_KEY   - Your OpenAI API key
    OPENAI_MODEL     - Model name (default: gpt-4o-mini)

Documentation: https://platform.openai.com/docs/api-reference

Install dependencies:
    pip install openai
"""

import json
import os

from backend.services.llm.base import BaseLLMProvider


class OpenAILLMProvider(BaseLLMProvider):
    """
    OpenAI LLM provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (OPENAI_API_KEY)
    """

    provider_name = "openai"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model or os.environ.get("OPENAI_MODEL", self.DEFAULT_MODEL)
        # TODO: Initialise openai.AsyncOpenAI client
        # import openai
        # self._client = openai.AsyncOpenAI(api_key=self.api_key)
        self.logger.warning(
            "OpenAILLMProvider is a stub. Real generation is not yet wired up."
        )

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 500,
    ) -> str:
        """Generate a completion via OpenAI Chat Completions API.

        TODO: Implement using openai.AsyncOpenAI.chat.completions.create.

        Args:
            prompt: User message.
            system: System prompt.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text string.
        """
        raise NotImplementedError(
            "OpenAILLMProvider.generate requires OPENAI_API_KEY."
        )

    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Generate structured JSON via OpenAI function-calling / JSON mode.

        TODO: Implement using response_format={"type": "json_object"} and
              a system prompt that instructs JSON-only output.

        Args:
            prompt: User message.
            schema: JSON Schema dict describing expected output.

        Returns:
            Parsed dict matching the schema.
        """
        raise NotImplementedError(
            "OpenAILLMProvider.generate_structured requires OPENAI_API_KEY."
        )

    async def health_check(self) -> bool:
        """TODO: Make a minimal /models list call to verify credentials."""
        self.logger.warning("OpenAILLMProvider health_check not implemented")
        return False
