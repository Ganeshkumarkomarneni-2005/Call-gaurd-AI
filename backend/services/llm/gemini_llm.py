"""
Google Gemini LLM provider.

STATUS: STUB - Requires EXTERNAL CREDENTIAL (GEMINI_API_KEY)

Required environment variables:
    GEMINI_API_KEY  - Your Google AI Studio / Vertex AI API key
    GEMINI_MODEL    - Model name (default: gemini-1.5-flash)

Documentation: https://ai.google.dev/gemini-api/docs

Gemini advantages for CallGuard AI:
    - 1M token context window for long conversations
    - Native multilingual support including Hindi
    - Structured output via response schema
    - Free tier available for development

Install dependencies:
    pip install google-generativeai
"""

import os

from backend.services.llm.base import BaseLLMProvider


class GeminiLLMProvider(BaseLLMProvider):
    """
    Google Gemini LLM provider.

    STATUS: STUB - Requires EXTERNAL CREDENTIAL (GEMINI_API_KEY)
    """

    provider_name = "gemini"
    DEFAULT_MODEL = "gemini-1.5-flash"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        super().__init__()
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL", self.DEFAULT_MODEL)
        # TODO: Configure google.generativeai
        # import google.generativeai as genai
        # genai.configure(api_key=self.api_key)
        # self._model = genai.GenerativeModel(self.model)
        self.logger.warning(
            "GeminiLLMProvider is a stub. Real generation is not yet wired up."
        )

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 500,
    ) -> str:
        """Generate a completion via Gemini GenerativeModel.

        TODO: Implement using google.generativeai.GenerativeModel.generate_content_async.

        Args:
            prompt: User message.
            system: System instruction.
            max_tokens: Maximum tokens to generate.

        Returns:
            Generated text string.
        """
        raise NotImplementedError(
            "GeminiLLMProvider.generate requires GEMINI_API_KEY."
        )

    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Generate structured JSON using Gemini response_mime_type='application/json'.

        TODO: Implement using generation_config={"response_mime_type": "application/json"}.

        Args:
            prompt: User message.
            schema: JSON Schema dict describing expected output.

        Returns:
            Parsed dict matching the schema.
        """
        raise NotImplementedError(
            "GeminiLLMProvider.generate_structured requires GEMINI_API_KEY."
        )

    async def health_check(self) -> bool:
        """TODO: Make a minimal generate call to verify credentials."""
        self.logger.warning("GeminiLLMProvider health_check not implemented")
        return False
