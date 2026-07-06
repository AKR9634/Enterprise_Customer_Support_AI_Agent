"""Unit tests for the LLM provider layer."""

from unittest.mock import MagicMock, patch

import pytest
from openai import (
    APITimeoutError as OpenAITimeoutError,
    AuthenticationError as OpenAIAuthError,
    RateLimitError as OpenAIRateLimitError,
)

from app.llm.provider import (
    LLMClient,
    LLMClientAuthError,
    LLMClientError,
    LLMClientRateLimitError,
    LLMClientTimeoutError,
)


class _FakeMessage:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeClassificationOutput:
    def __init__(self, label: str) -> None:
        self.label = label


# ──────────────────────────────────────────────────────────────────────────────
# Constructor / request shape
# ──────────────────────────────────────────────────────────────────────────────


class TestConstructor:
    """Verify that ChatOpenAI receives the expected configuration."""

    def test_passes_config_correctly(self) -> None:
        with (
            patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI,
            patch("app.llm.provider.config.LLM_MODEL", "test-model"),
            patch("app.llm.provider.config.LLM_TEMPERATURE", 0.5),
            patch("app.llm.provider.config.LLM_MAX_TOKENS", 512),
            patch("app.llm.provider.config.OPEN_ROUTER_API_KEY", "sk-test"),
            patch("app.llm.provider.config.OPEN_ROUTER_BASE_URL", "https://test.example.com/v1"),
        ):
            LLMClient()

        MockChatOpenAI.assert_called_once_with(
            model="test-model",
            api_key="sk-test",
            base_url="https://test.example.com/v1",
            temperature=0.5,
            max_tokens=512,
        )


# ──────────────────────────────────────────────────────────────────────────────
# classify()
# ──────────────────────────────────────────────────────────────────────────────


class TestClassify:
    """Tests for LLMClient.classify()."""

    def test_returns_label_from_permitted_set(self) -> None:
        fake_output = _FakeClassificationOutput("billing")
        structured_mock = MagicMock()
        structured_mock.invoke.return_value = fake_output

        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.with_structured_output.return_value = structured_mock

            client = LLMClient(model="test")
            label = client.classify("Categorize: I want a refund", ["billing", "general", "order"])

        assert label == "billing"
        mock_instance.with_structured_output.assert_called_once()

    def test_raises_on_out_of_set_response(self) -> None:
        fake_output = _FakeClassificationOutput("spam")
        structured_mock = MagicMock()
        structured_mock.invoke.return_value = fake_output

        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.with_structured_output.return_value = structured_mock

            client = LLMClient(model="test")
            with pytest.raises(LLMClientError, match="not in the permitted set"):
                client.classify("Categorize this", ["billing", "general", "order"])

    def test_rate_limit_during_classify(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.request = MagicMock()

        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            structured_mock = MagicMock()
            structured_mock.invoke.side_effect = OpenAIRateLimitError(
                "rate limit", response=mock_response, body=None
            )
            mock_instance.with_structured_output.return_value = structured_mock

            client = LLMClient(model="test")
            with pytest.raises(LLMClientRateLimitError):
                client.classify("test", ["a", "b"])


# ──────────────────────────────────────────────────────────────────────────────
# generate()
# ──────────────────────────────────────────────────────────────────────────────


class TestGenerate:
    """Tests for LLMClient.generate()."""

    def test_returns_message_content(self) -> None:
        fake = _FakeMessage("Hello, world!")

        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.return_value = fake

            client = LLMClient(model="test")
            result = client.generate("Say hello")

        assert result == "Hello, world!"

    def test_includes_system_prompt(self) -> None:
        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.return_value = _FakeMessage("ok")

            client = LLMClient(model="test")
            client.generate("Hello", system_prompt="You are a bot")

            args, _ = mock_instance.invoke.call_args
            messages = args[0]
            assert len(messages) == 2
            assert messages[0].content == "You are a bot"
            assert messages[1].content == "Hello"


# ──────────────────────────────────────────────────────────────────────────────
# Error typing
# ──────────────────────────────────────────────────────────────────────────────


class TestErrorTyping:
    """Every API failure mode raises the correct typed exception."""

    def _build_response_mock(self, status_code: int) -> MagicMock:
        m = MagicMock()
        m.status_code = status_code
        m.request = MagicMock()
        return m

    def test_rate_limit(self) -> None:
        resp = self._build_response_mock(429)
        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.side_effect = OpenAIRateLimitError(
                "rate limit", response=resp, body=None
            )

            client = LLMClient(model="test")
            with pytest.raises(LLMClientRateLimitError):
                client.generate("test")

    def test_auth_error(self) -> None:
        resp = self._build_response_mock(401)
        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.side_effect = OpenAIAuthError(
                "invalid key", response=resp, body=None
            )

            client = LLMClient(model="test")
            with pytest.raises(LLMClientAuthError):
                client.generate("test")

    def test_timeout(self) -> None:
        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.side_effect = OpenAITimeoutError("timed out")

            client = LLMClient(model="test")
            with pytest.raises(LLMClientTimeoutError):
                client.generate("test")

    def test_generic_error(self) -> None:
        with patch("app.llm.provider.ChatOpenAI") as MockChatOpenAI:
            mock_instance = MockChatOpenAI.return_value
            mock_instance.invoke.side_effect = ValueError("something unexpected")

            client = LLMClient(model="test")
            with pytest.raises(LLMClientError):
                client.generate("test")
