"""
Single LLMClient wrapper around ChatOpenAI (OpenRouter-compatible):
generate() and classify(). Centralizing this here means swapping
models or providers later is a one-file change.
"""

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, create_model
from openai import (
    APITimeoutError as OpenAITimeoutError,
    AuthenticationError as OpenAIAuthError,
    RateLimitError as OpenAIRateLimitError,
)

from app import config


class LLMClientError(Exception):
    """Base exception for all LLM provider errors."""


class LLMClientRateLimitError(LLMClientError):
    """Raised when the upstream API returns a rate-limit response."""


class LLMClientTimeoutError(LLMClientError):
    """Raised when the upstream API request times out."""


class LLMClientAuthError(LLMClientError):
    """Raised when the upstream API rejects the API key."""


def _build_classification_model(categories: list[str]) -> type[BaseModel]:
    """Build a Pydantic model with an enum constraint for the given categories."""
    return create_model(
        "_ClassificationOutput",
        label=(str, Field(
            ...,
            description=f"Must be exactly one of: {', '.join(categories)}",
            json_schema_extra={"enum": categories},
        )),
    )


class LLMClient:
    """Thin wrapper around ChatOpenAI pointed at OpenRouter."""

    def __init__(self, model: str | None = None) -> None:
        self._model = model or config.LLM_MODEL
        self._llm = ChatOpenAI(
            model=self._model,
            api_key=config.OPEN_ROUTER_API_KEY,
            base_url=config.OPEN_ROUTER_BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=config.LLM_MAX_TOKENS,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> str:
        """Send a prompt and optional system prompt, return the response text."""
        messages: list[Any] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        try:
            result = self._llm.invoke(messages)
        except OpenAIRateLimitError as e:
            raise LLMClientRateLimitError(str(e)) from e
        except OpenAIAuthError as e:
            raise LLMClientAuthError(str(e)) from e
        except OpenAITimeoutError as e:
            raise LLMClientTimeoutError(str(e)) from e
        except Exception as e:
            raise LLMClientError(str(e)) from e

        return result.content

    def classify(self, prompt: str, categories: list[str]) -> str:
        """Classify *prompt* into one of the given *categories* using structured output."""
        model_cls = _build_classification_model(categories)
        structured = self._llm.with_structured_output(model_cls)
        messages: list[Any] = [HumanMessage(content=prompt)]

        try:
            result = structured.invoke(messages)
        except OpenAIRateLimitError as e:
            raise LLMClientRateLimitError(str(e)) from e
        except OpenAIAuthError as e:
            raise LLMClientAuthError(str(e)) from e
        except OpenAITimeoutError as e:
            raise LLMClientTimeoutError(str(e)) from e
        except Exception as e:
            raise LLMClientError(str(e)) from e

        if result.label not in categories:
            raise LLMClientError(
                f"Classification returned '{result.label}', "
                f"which is not in the permitted set: {categories}"
            )

        return result.label
