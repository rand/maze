"""
Unit tests for provider adapters.
"""

import pytest
from maze.orchestrator.providers import (
    ProviderAdapter,
    GenerationRequest,
    GenerationResponse,
    OpenAIProviderAdapter,
    VLLMProviderAdapter,
    SGLangProviderAdapter,
    LlamaCppProviderAdapter,
    create_provider_adapter,
)


class TestGenerationRequest:
    """Test generation request data structure."""

    def test_basic_request(self):
        """Test creating basic generation request."""
        request = GenerationRequest(prompt="Write a function")

        assert request.prompt == "Write a function"
        assert request.grammar is None
        assert request.schema is None
        assert request.max_tokens == 2048
        assert request.temperature == 0.7

    def test_request_with_grammar(self):
        """Test request with grammar constraint."""
        grammar = "?start: expr\nexpr: NUMBER"
        request = GenerationRequest(
            prompt="Generate number",
            grammar=grammar
        )

        assert request.grammar == grammar

    def test_request_with_schema(self):
        """Test request with JSON Schema constraint."""
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}
        request = GenerationRequest(
            prompt="Generate JSON",
            schema=schema
        )

        assert request.schema == schema

    def test_request_with_custom_params(self):
        """Test request with custom generation parameters."""
        request = GenerationRequest(
            prompt="Test",
            max_tokens=1024,
            temperature=0.5,
            top_p=0.9,
            stop_sequences=["END", "STOP"]
        )

        assert request.max_tokens == 1024
        assert request.temperature == 0.5
        assert request.top_p == 0.9
        assert request.stop_sequences == ["END", "STOP"]


class TestGenerationResponse:
    """Test generation response data structure."""

    def test_basic_response(self):
        """Test creating basic generation response."""
        response = GenerationResponse(
            text="function test() {}",
            finish_reason="stop",
            tokens_generated=10
        )

        assert response.text == "function test() {}"
        assert response.finish_reason == "stop"
        assert response.tokens_generated == 10
        assert response.metadata == {}

    def test_response_with_metadata(self):
        """Test response with metadata."""
        response = GenerationResponse(
            text="code",
            finish_reason="length",
            tokens_generated=100,
            metadata={"model": "gpt-4", "usage": {"total_tokens": 150}}
        )

        assert response.metadata["model"] == "gpt-4"
        assert response.metadata["usage"]["total_tokens"] == 150


class TestOpenAIProviderAdapter:
    """Test OpenAI provider adapter."""

    def test_adapter_creation(self):
        """Test creating OpenAI adapter."""
        adapter = OpenAIProviderAdapter(model="gpt-4", api_key="test-key")

        assert adapter.model == "gpt-4"
        assert adapter.api_key == "test-key"

    def test_supports_json_schema(self):
        """Test JSON Schema support check."""
        adapter = OpenAIProviderAdapter()
        assert adapter.supports_json_schema() is True

    def test_does_not_support_grammar(self):
        """Test grammar support check."""
        adapter = OpenAIProviderAdapter()
        assert adapter.supports_grammar() is False

    def test_generate_with_grammar_raises(self):
        """Test error on grammar constraint."""
        adapter = OpenAIProviderAdapter()
        request = GenerationRequest(
            prompt="Test",
            grammar="?start: expr"
        )

        with pytest.raises(ValueError, match="does not support grammar"):
            adapter.generate(request)


class TestVLLMProviderAdapter:
    """Test vLLM provider adapter."""

    def test_adapter_creation(self):
        """Test creating vLLM adapter."""
        adapter = VLLMProviderAdapter(
            model="meta-llama/Llama-2-7b",
            api_base="http://localhost:8000"
        )

        assert adapter.model == "meta-llama/Llama-2-7b"
        assert adapter.api_base == "http://localhost:8000"

    def test_supports_both_constraints(self):
        """Test constraint support."""
        adapter = VLLMProviderAdapter(model="test")

        assert adapter.supports_grammar() is True
        assert adapter.supports_json_schema() is True

    def test_default_api_base(self):
        """Test default API base URL."""
        adapter = VLLMProviderAdapter(model="test")
        assert adapter.api_base == "http://localhost:8000"


class TestSGLangProviderAdapter:
    """Test SGLang provider adapter."""

    def test_adapter_creation(self):
        """Test creating SGLang adapter."""
        adapter = SGLangProviderAdapter(
            model="meta-llama/Llama-2-7b",
            api_base="http://localhost:30000"
        )

        assert adapter.model == "meta-llama/Llama-2-7b"
        assert adapter.api_base == "http://localhost:30000"

    def test_supports_both_constraints(self):
        """Test constraint support."""
        adapter = SGLangProviderAdapter(model="test")

        assert adapter.supports_grammar() is True
        assert adapter.supports_json_schema() is True

    def test_default_api_base(self):
        """Test default API base URL."""
        adapter = SGLangProviderAdapter(model="test")
        assert adapter.api_base == "http://localhost:30000"


class TestLlamaCppProviderAdapter:
    """Test llama.cpp provider adapter."""

    def test_adapter_creation(self):
        """Test creating llama.cpp adapter."""
        adapter = LlamaCppProviderAdapter(
            model="model",
            api_base="http://localhost:8080"
        )

        assert adapter.model == "model"
        assert adapter.api_base == "http://localhost:8080"

    def test_supports_grammar(self):
        """Test GBNF grammar support."""
        adapter = LlamaCppProviderAdapter()
        assert adapter.supports_grammar() is True

    def test_supports_json_schema(self):
        """Test JSON Schema support (via GBNF)."""
        adapter = LlamaCppProviderAdapter()
        # Returns True but implementation incomplete
        assert adapter.supports_json_schema() is True

    def test_default_api_base(self):
        """Test default API base URL."""
        adapter = LlamaCppProviderAdapter()
        assert adapter.api_base == "http://localhost:8080"


class TestProviderFactory:
    """Test provider adapter factory."""

    def test_create_openai_adapter(self):
        """Test creating OpenAI adapter via factory."""
        adapter = create_provider_adapter("openai", model="gpt-4", api_key="test")

        assert isinstance(adapter, OpenAIProviderAdapter)
        assert adapter.model == "gpt-4"
        assert adapter.api_key == "test"

    def test_create_vllm_adapter(self):
        """Test creating vLLM adapter via factory."""
        adapter = create_provider_adapter("vllm", model="test-model")

        assert isinstance(adapter, VLLMProviderAdapter)
        assert adapter.model == "test-model"

    def test_create_sglang_adapter(self):
        """Test creating SGLang adapter via factory."""
        adapter = create_provider_adapter("sglang", model="test-model")

        assert isinstance(adapter, SGLangProviderAdapter)
        assert adapter.model == "test-model"

    def test_create_llamacpp_adapter(self):
        """Test creating llama.cpp adapter via factory."""
        adapter = create_provider_adapter("llamacpp")

        assert isinstance(adapter, LlamaCppProviderAdapter)
        assert adapter.model == "model"

    def test_default_models(self):
        """Test default models for each provider."""
        adapters = [
            ("openai", "gpt-4"),
            ("vllm", "model"),
            ("sglang", "model"),
            ("llamacpp", "model"),
        ]

        for provider, expected_model in adapters:
            adapter = create_provider_adapter(provider)
            assert adapter.model == expected_model

    def test_unknown_provider(self):
        """Test error on unknown provider."""
        with pytest.raises(ValueError, match="Unknown provider"):
            create_provider_adapter("unknown")

    def test_custom_kwargs(self):
        """Test passing custom kwargs to adapter."""
        adapter = create_provider_adapter(
            "vllm",
            model="custom",
            api_base="http://custom:9000"
        )

        assert adapter.api_base == "http://custom:9000"


class TestProviderCapabilities:
    """Test provider capability detection."""

    def test_all_adapters_implement_interface(self):
        """Test all adapters implement ProviderAdapter interface."""
        adapters = [
            OpenAIProviderAdapter(model="test"),
            VLLMProviderAdapter(model="test"),
            SGLangProviderAdapter(model="test"),
            LlamaCppProviderAdapter(model="test"),
        ]

        for adapter in adapters:
            assert isinstance(adapter, ProviderAdapter)
            assert hasattr(adapter, "generate")
            assert hasattr(adapter, "supports_grammar")
            assert hasattr(adapter, "supports_json_schema")

    def test_capability_matrix(self):
        """Test capability matrix for all providers."""
        capabilities = [
            ("openai", False, True),   # grammar, json_schema
            ("vllm", True, True),
            ("sglang", True, True),
            ("llamacpp", True, True),
        ]

        for provider, grammar, json_schema in capabilities:
            adapter = create_provider_adapter(provider)
            assert adapter.supports_grammar() == grammar, f"{provider} grammar support mismatch"
            assert adapter.supports_json_schema() == json_schema, f"{provider} JSON Schema support mismatch"
