"""
Unit tests for provider adapters.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from maze.orchestrator.providers import (
    GenerationRequest,
    GenerationResponse,
    ProviderAdapter,
    OpenAIProviderAdapter,
    VLLMProviderAdapter,
    SGLangProviderAdapter,
    LlamaCppProviderAdapter,
    create_provider_adapter,
)


class TestDataclasses:
    """Test GenerationRequest and GenerationResponse dataclasses."""

    def test_generation_request_defaults(self):
        """Test GenerationRequest with default values."""
        request = GenerationRequest(prompt="test prompt")

        assert request.prompt == "test prompt"
        assert request.grammar is None
        assert request.schema is None
        assert request.max_tokens == 2048
        assert request.temperature == 0.7
        assert request.top_p == 1.0
        assert request.stop_sequences == []
        assert request.metadata == {}

    def test_generation_request_custom_values(self):
        """Test GenerationRequest with custom values."""
        request = GenerationRequest(
            prompt="custom prompt",
            grammar="test grammar",
            schema={"type": "object"},
            max_tokens=1000,
            temperature=0.5,
            top_p=0.9,
            stop_sequences=["</code>"],
            metadata={"key": "value"}
        )

        assert request.prompt == "custom prompt"
        assert request.grammar == "test grammar"
        assert request.schema == {"type": "object"}
        assert request.max_tokens == 1000
        assert request.temperature == 0.5
        assert request.top_p == 0.9
        assert request.stop_sequences == ["</code>"]
        assert request.metadata == {"key": "value"}

    def test_generation_response(self):
        """Test GenerationResponse dataclass."""
        response = GenerationResponse(
            text="generated text",
            finish_reason="stop",
            tokens_generated=50,
            metadata={"model": "gpt-4"}
        )

        assert response.text == "generated text"
        assert response.finish_reason == "stop"
        assert response.tokens_generated == 50
        assert response.metadata == {"model": "gpt-4"}


class TestOpenAIProviderAdapter:
    """Test OpenAI provider adapter."""

    def test_initialization(self):
        """Test OpenAI adapter initialization."""
        adapter = OpenAIProviderAdapter(model="gpt-4", api_key="test-key")

        assert adapter.model == "gpt-4"
        assert adapter.api_key == "test-key"

    def test_default_model(self):
        """Test default model selection."""
        adapter = OpenAIProviderAdapter()

        assert adapter.model == "gpt-4"

    def test_supports_grammar(self):
        """Test grammar support check."""
        adapter = OpenAIProviderAdapter()

        assert not adapter.supports_grammar()

    def test_supports_json_schema(self):
        """Test JSON Schema support check."""
        adapter = OpenAIProviderAdapter()

        assert adapter.supports_json_schema()

    def test_generate_with_grammar_raises_error(self):
        """Test that using grammar raises ValueError."""
        adapter = OpenAIProviderAdapter()
        request = GenerationRequest(
            prompt="test",
            grammar="test grammar"
        )

        with pytest.raises(ValueError, match="does not support grammar"):
            adapter.generate(request)

    def test_generate_basic(self):
        """Test basic generation without constraints."""
        # Mock OpenAI client
        mock_choice = Mock()
        mock_choice.message.content = "generated code"
        mock_choice.finish_reason = "stop"

        mock_usage = Mock()
        mock_usage.completion_tokens = 25
        mock_usage.model_dump.return_value = {"completion_tokens": 25}

        mock_response = Mock()
        mock_response.choices = [mock_choice]
        mock_response.model = "gpt-4"
        mock_response.usage = mock_usage

        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        # Mock OpenAI class
        mock_openai_class = Mock(return_value=mock_client)

        # Patch the import
        with patch.dict('sys.modules', {'openai': Mock(OpenAI=mock_openai_class)}):
            adapter = OpenAIProviderAdapter(api_key="test-key")
            request = GenerationRequest(prompt="Write a function")

            response = adapter.generate(request)

            assert response.text == "generated code"
            assert response.finish_reason == "stop"
            assert response.tokens_generated == 25
            assert response.metadata["model"] == "gpt-4"

    def test_generate_without_openai_package(self):
        """Test error when openai package not installed."""
        with patch.dict('sys.modules', {'openai': None}):
            adapter = OpenAIProviderAdapter()
            request = GenerationRequest(prompt="test")

            with pytest.raises(ImportError, match="openai package not installed"):
                adapter.generate(request)


class TestVLLMProviderAdapter:
    """Test vLLM provider adapter."""

    def test_initialization(self):
        """Test vLLM adapter initialization."""
        adapter = VLLMProviderAdapter(model="llama-3", api_base="http://localhost:9000")

        assert adapter.model == "llama-3"
        assert adapter.api_base == "http://localhost:9000"

    def test_supports_grammar(self):
        """Test grammar support check."""
        adapter = VLLMProviderAdapter(model="test")

        assert adapter.supports_grammar()

    def test_supports_json_schema(self):
        """Test JSON Schema support check."""
        adapter = VLLMProviderAdapter(model="test")

        assert adapter.supports_json_schema()

    def test_generate_with_grammar(self):
        """Test generation with grammar constraint."""
        # Mock requests module
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"text": "generated code", "finish_reason": "stop"}],
            "usage": {"completion_tokens": 30}
        }

        mock_requests = Mock()
        mock_requests.post.return_value = mock_response

        with patch.dict('sys.modules', {'requests': mock_requests}):
            adapter = VLLMProviderAdapter(model="llama-3")
            request = GenerationRequest(
                prompt="test",
                grammar="test grammar"
            )

            response = adapter.generate(request)

            assert response.text == "generated code"
            assert response.finish_reason == "stop"
            assert response.tokens_generated == 30


class TestSGLangProviderAdapter:
    """Test SGLang provider adapter."""

    def test_initialization(self):
        """Test SGLang adapter initialization."""
        adapter = SGLangProviderAdapter(model="test-model", api_base="http://localhost:40000")

        assert adapter.model == "test-model"
        assert adapter.api_base == "http://localhost:40000"

    def test_supports_grammar(self):
        """Test grammar support check."""
        adapter = SGLangProviderAdapter(model="test")

        assert adapter.supports_grammar()

    def test_supports_json_schema(self):
        """Test JSON Schema support check."""
        adapter = SGLangProviderAdapter(model="test")

        assert adapter.supports_json_schema()

    def test_generate_with_grammar(self):
        """Test generation with grammar constraint."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "text": "generated text",
            "meta_info": {
                "finish_reason": "stop",
                "completion_tokens": 20
            }
        }

        mock_requests = Mock()
        mock_requests.post.return_value = mock_response

        with patch.dict('sys.modules', {'requests': mock_requests}):
            adapter = SGLangProviderAdapter(model="test")
            request = GenerationRequest(
                prompt="test",
                grammar="test regex"
            )

            response = adapter.generate(request)

            assert response.text == "generated text"
            assert response.finish_reason == "stop"
            assert response.tokens_generated == 20


class TestLlamaCppProviderAdapter:
    """Test llama.cpp provider adapter."""

    def test_initialization(self):
        """Test llama.cpp adapter initialization."""
        adapter = LlamaCppProviderAdapter(api_base="http://localhost:9999")

        assert adapter.model == "model"
        assert adapter.api_base == "http://localhost:9999"

    def test_supports_grammar(self):
        """Test grammar support check."""
        adapter = LlamaCppProviderAdapter()

        assert adapter.supports_grammar()

    def test_supports_json_schema(self):
        """Test JSON Schema support check."""
        adapter = LlamaCppProviderAdapter()

        assert adapter.supports_json_schema()

    def test_generate_with_grammar(self):
        """Test generation with GBNF grammar."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "content": "generated output",
            "stop_reason": "eos",
            "tokens_predicted": 15,
            "timings": {},
            "truncated": False
        }

        mock_requests = Mock()
        mock_requests.post.return_value = mock_response

        with patch.dict('sys.modules', {'requests': mock_requests}):
            adapter = LlamaCppProviderAdapter()
            request = GenerationRequest(
                prompt="test",
                grammar="gbnf grammar"
            )

            response = adapter.generate(request)

            assert response.text == "generated output"
            assert response.finish_reason == "eos"
            assert response.tokens_generated == 15


class TestProviderFactory:
    """Test create_provider_adapter factory function."""

    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter."""
        adapter = create_provider_adapter("openai", model="gpt-3.5-turbo", api_key="test")

        assert isinstance(adapter, OpenAIProviderAdapter)
        assert adapter.model == "gpt-3.5-turbo"
        assert adapter.api_key == "test"

    def test_create_vllm_adapter(self):
        """Test creating vLLM adapter."""
        adapter = create_provider_adapter("vllm", model="llama-3", api_base="http://localhost:8000")

        assert isinstance(adapter, VLLMProviderAdapter)
        assert adapter.model == "llama-3"
        assert adapter.api_base == "http://localhost:8000"

    def test_create_sglang_adapter(self):
        """Test creating SGLang adapter."""
        adapter = create_provider_adapter("sglang", model="test")

        assert isinstance(adapter, SGLangProviderAdapter)
        assert adapter.model == "test"

    def test_create_llamacpp_adapter(self):
        """Test creating llama.cpp adapter."""
        adapter = create_provider_adapter("llamacpp")

        assert isinstance(adapter, LlamaCppProviderAdapter)
        assert adapter.model == "model"

    def test_create_with_default_models(self):
        """Test default model selection for each provider."""
        openai = create_provider_adapter("openai")
        assert openai.model == "gpt-4"

        vllm = create_provider_adapter("vllm")
        assert vllm.model == "model"

        sglang = create_provider_adapter("sglang")
        assert sglang.model == "model"

        llamacpp = create_provider_adapter("llamacpp")
        assert llamacpp.model == "model"

    def test_unknown_provider_raises_error(self):
        """Test that unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown provider: unknown"):
            create_provider_adapter("unknown")

    def test_error_message_lists_available_providers(self):
        """Test that error message lists available providers."""
        with pytest.raises(ValueError, match="openai.*vllm.*sglang.*llamacpp"):
            create_provider_adapter("invalid")
