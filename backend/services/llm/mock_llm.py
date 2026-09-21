"""
Mock LLM provider for development and testing.

Uses template-based responses keyed by conversation intent keywords.
No API keys required.

STATUS: MOCK_IMPLEMENTATION
"""

import asyncio
import json
import re

from backend.services.llm.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider for development.

    STATUS: MOCK_IMPLEMENTATION
    Uses template-based responses. No API required.
    """

    provider_name = "mock"

    AGENT_RESPONSES: dict[str, str] = {
        "greeting": (
            "Thank you for calling. This is CallGuard AI. I am screening this call "
            "on behalf of the user. Could you please tell me who you are and the "
            "purpose of your call?"
        ),
        "clarify_intent": (
            "I see. Could you tell me more about the purpose of this call?"
        ),
        "recruitment_followup": (
            "Thank you for the information. Could you share the company name and "
            "the position you are calling about?"
        ),
        "end_call": (
            "Thank you for your call. I have recorded the details and will pass "
            "them on. Goodbye."
        ),
        "transfer": (
            "Please hold while I connect you with the person you are trying to reach."
        ),
        "suspicious": (
            "I would like to verify some details before proceeding. Could you "
            "confirm the official company website?"
        ),
        "payment_request": (
            "I notice you mentioned a payment requirement. Legitimate employers "
            "do not charge candidates. Could you clarify this request?"
        ),
        "otp_request": (
            "We will never share OTP details with a third party. I am ending this "
            "call now as it appears to be fraudulent."
        ),
        "default": (
            "Thank you for the information. Could you please clarify the purpose "
            "of your call in more detail?"
        ),
    }

    # Intent keyword mapping for template selection
    _INTENT_KEYWORDS: list[tuple[str, str]] = [
        (r"otp|one.time.password|verify.*otp", "otp_request"),
        (r"pay|rupees|fee|deposit|amount|money", "payment_request"),
        (r"suspicious|verify|confirm.*website|official", "suspicious"),
        (r"recruitment|job|position|application|hiring|candidate", "recruitment_followup"),
        (r"transfer|connect|put.*through", "transfer"),
        (r"bye|goodbye|thank you|that.s all", "end_call"),
        (r"hello|hi|good morning|good afternoon|calling", "greeting"),
        (r"purpose|reason|why|what.*about", "clarify_intent"),
    ]

    async def generate(
        self,
        prompt: str,
        system: str = "",
        max_tokens: int = 500,
    ) -> str:
        """Return a template response matched to prompt keywords.

        Args:
            prompt: The caller text or conversation context.
            system: Ignored in mock mode.
            max_tokens: Ignored in mock mode.

        Returns:
            A mock agent response string.
        """
        await asyncio.sleep(0.05)  # simulate LLM latency
        intent = self._detect_intent(prompt)
        response = self.AGENT_RESPONSES.get(intent, self.AGENT_RESPONSES["default"])
        self.logger.debug(
            "[MOCK LLM] Generated response",
            intent=intent,
            prompt_preview=prompt[:80],
        )
        return response

    async def generate_structured(self, prompt: str, schema: dict) -> dict:
        """Return a mock structured response derived from the schema.

        Fills required fields with placeholder values appropriate to their type.

        Args:
            prompt: The conversation context.
            schema: JSON Schema dict.

        Returns:
            A dict conforming to the schema with mock values.
        """
        await asyncio.sleep(0.05)
        result = self._fill_schema(schema)
        self.logger.debug(
            "[MOCK LLM] Generated structured response",
            schema_keys=list(schema.get("properties", {}).keys()),
        )
        return result

    async def health_check(self) -> bool:
        """Always healthy in mock mode."""
        return True

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_intent(self, text: str) -> str:
        """Return the best-matching intent key for *text*."""
        lower = text.lower()
        for pattern, intent in self._INTENT_KEYWORDS:
            if re.search(pattern, lower):
                return intent
        return "default"

    def _fill_schema(self, schema: dict, depth: int = 0) -> dict | list | str | int | bool | None:
        """Recursively fill a JSON Schema with mock values."""
        if depth > 5:
            return None
        schema_type = schema.get("type", "object")
        if schema_type == "object":
            result: dict = {}
            for prop, prop_schema in schema.get("properties", {}).items():
                result[prop] = self._fill_schema(prop_schema, depth + 1)
            return result
        elif schema_type == "array":
            items_schema = schema.get("items", {"type": "string"})
            return [self._fill_schema(items_schema, depth + 1)]
        elif schema_type == "string":
            enum = schema.get("enum")
            if enum:
                return enum[0]
            return schema.get("example", "mock_value")
        elif schema_type == "number" or schema_type == "integer":
            return schema.get("example", 0)
        elif schema_type == "boolean":
            return False
        return None
