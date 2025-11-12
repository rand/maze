"""
Provider-specific orchestration for constrained code generation.

This module provides adapters for different LLM providers, coordinating
between grammar/schema synthesis and provider-specific APIs.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from maze.synthesis.grammar_builder import GrammarBuilder
from maze.synthesis.schema_builder import SchemaBuilder

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """Request for constrained code generation."""

    prompt: str
    grammar: str | None = None
    schema: dict[str, Any] | None = None
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 1.0
    stop_sequences: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResponse:
    """Response from constrained code generation."""

    text: str
    finish_reason: str
    tokens_generated: int
    metadata: dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(ABC):
    """
    Abstract base class for provider-specific adapters.

    Each adapter handles conversion between Maze's constraint
    representation and the provider's expected format.
    """

    def __init__(self, model: str, api_key: str | None = None):
        """
        Initialize provider adapter.

        Args:
            model: Model identifier
            api_key: API key for authentication
        """
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate code with constraints.

        Args:
            request: Generation request

        Returns:
            Generated code with metadata
        """
        pass

    @abstractmethod
    def supports_grammar(self) -> bool:
        """Check if provider supports grammar-based constraints."""
        pass

    @abstractmethod
    def supports_json_schema(self) -> bool:
        """Check if provider supports JSON Schema constraints."""
        pass


class OpenAIProviderAdapter(ProviderAdapter):
    """
    Adapter for OpenAI API with Structured Outputs.

    OpenAI's Structured Outputs only support JSON Schema, not arbitrary grammars.
    """

    def __init__(self, model: str = "gpt-4", api_key: str | None = None):
        """
        Initialize OpenAI adapter.

        Args:
            model: OpenAI model (e.g., "gpt-4", "gpt-3.5-turbo")
            api_key: OpenAI API key
        """
        super().__init__(model, api_key)

    def supports_grammar(self) -> bool:
        """OpenAI does not support arbitrary grammars."""
        return False

    def supports_json_schema(self) -> bool:
        """OpenAI supports JSON Schema via Structured Outputs."""
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate using OpenAI API with optional JSON Schema.

        Args:
            request: Generation request

        Returns:
            Generated response

        Raises:
            ValueError: If grammar constraint provided (not supported)
            ImportError: If openai package not installed
        """
        if request.grammar:
            raise ValueError(
                "OpenAI does not support grammar constraints. Use JSON Schema instead."
            )

        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("openai package not installed. Install with: uv add openai")

        client = OpenAI(api_key=self.api_key)

        # Build API call parameters
        params: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": request.prompt}],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }

        if request.stop_sequences:
            params["stop"] = request.stop_sequences

        # Add JSON Schema if provided
        if request.schema:
            params["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": "response", "strict": True, "schema": request.schema},
            }

        # Make API call
        response = client.chat.completions.create(**params)

        choice = response.choices[0]
        return GenerationResponse(
            text=choice.message.content or "",
            finish_reason=choice.finish_reason or "unknown",
            tokens_generated=response.usage.completion_tokens if response.usage else 0,
            metadata={
                "model": response.model,
                "usage": response.usage.model_dump() if response.usage else None,
            },
        )


class VLLMProviderAdapter(ProviderAdapter):
    """
    Adapter for vLLM with llguidance backend.

    vLLM supports both grammars and JSON Schema when configured with llguidance.
    """

    def __init__(self, model: str, api_base: str = "http://localhost:8000"):
        """
        Initialize vLLM adapter.

        Args:
            model: Model path or identifier
            api_base: vLLM server base URL
        """
        super().__init__(model, None)
        self.api_base = api_base

    def supports_grammar(self) -> bool:
        """vLLM supports grammars via llguidance."""
        return True

    def supports_json_schema(self) -> bool:
        """vLLM supports JSON Schema via llguidance."""
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate using vLLM API with grammar or JSON Schema.

        Args:
            request: Generation request

        Returns:
            Generated response

        Raises:
            ImportError: If requests package not installed
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package not installed. Install with: uv add requests")

        # Build request payload
        payload = {
            "model": self.model,
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }

        if request.stop_sequences:
            payload["stop"] = request.stop_sequences

        # Add grammar if provided
        if request.grammar:
            payload["guided_generation"] = {
                "type": "grammar",
                "grammar": request.grammar,
                "backend": "llguidance",
            }

        # Add JSON Schema if provided (takes precedence)
        if request.schema:
            payload["guided_generation"] = {
                "type": "json_schema",
                "schema": request.schema,
                "backend": "llguidance",
            }

        # Make API call
        response = requests.post(f"{self.api_base}/v1/completions", json=payload)
        response.raise_for_status()
        data = response.json()

        choice = data["choices"][0]
        return GenerationResponse(
            text=choice["text"],
            finish_reason=choice.get("finish_reason", "unknown"),
            tokens_generated=data.get("usage", {}).get("completion_tokens", 0),
            metadata={"usage": data.get("usage")},
        )


class SGLangProviderAdapter(ProviderAdapter):
    """
    Adapter for SGLang with constraint support.

    SGLang supports grammars and JSON Schema constraints.
    """

    def __init__(self, model: str, api_base: str = "http://localhost:30000"):
        """
        Initialize SGLang adapter.

        Args:
            model: Model path or identifier
            api_base: SGLang server base URL
        """
        super().__init__(model, None)
        self.api_base = api_base

    def supports_grammar(self) -> bool:
        """SGLang supports grammar constraints."""
        return True

    def supports_json_schema(self) -> bool:
        """SGLang supports JSON Schema constraints."""
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate using SGLang API with constraints.

        Args:
            request: Generation request

        Returns:
            Generated response

        Raises:
            ImportError: If requests package not installed
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package not installed. Install with: uv add requests")

        # Build request payload
        payload = {
            "text": request.prompt,
            "sampling_params": {
                "max_new_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
            },
        }

        if request.stop_sequences:
            payload["sampling_params"]["stop"] = request.stop_sequences

        # Add grammar constraint if provided
        if request.grammar:
            payload["sampling_params"]["regex"] = request.grammar

        # Add JSON Schema constraint if provided
        if request.schema:
            # SGLang supports JSON Schema natively
            payload["sampling_params"]["json_schema"] = request.schema

        # Make API call
        response = requests.post(f"{self.api_base}/generate", json=payload)
        response.raise_for_status()
        data = response.json()

        return GenerationResponse(
            text=data.get("text", ""),
            finish_reason=data.get("meta_info", {}).get("finish_reason", "unknown"),
            tokens_generated=data.get("meta_info", {}).get("completion_tokens", 0),
            metadata=data.get("meta_info", {}),
        )


class LlamaCppProviderAdapter(ProviderAdapter):
    """
    Adapter for llama.cpp server with grammar support.

    llama.cpp supports GBNF grammars natively.
    """

    def __init__(self, model: str = "model", api_base: str = "http://localhost:8080"):
        """
        Initialize llama.cpp adapter.

        Args:
            model: Model identifier (usually just "model")
            api_base: llama.cpp server base URL
        """
        super().__init__(model, None)
        self.api_base = api_base

    def supports_grammar(self) -> bool:
        """llama.cpp supports GBNF grammars."""
        return True

    def supports_json_schema(self) -> bool:
        """llama.cpp supports JSON Schema (converted to GBNF)."""
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """
        Generate using llama.cpp API with grammar.

        Args:
            request: Generation request

        Returns:
            Generated response

        Raises:
            ImportError: If requests package not installed
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package not installed. Install with: uv add requests")

        # Build request payload
        payload = {
            "prompt": request.prompt,
            "n_predict": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
        }

        if request.stop_sequences:
            payload["stop"] = request.stop_sequences

        # Add grammar if provided (llama.cpp uses GBNF format)
        if request.grammar:
            payload["grammar"] = request.grammar

        # For JSON Schema, convert to GBNF grammar
        if request.schema:
            gbnf_grammar = self._schema_to_gbnf(request.schema)
            payload["grammar"] = gbnf_grammar

        # Make API call
        response = requests.post(f"{self.api_base}/completion", json=payload)
        response.raise_for_status()
        data = response.json()

        return GenerationResponse(
            text=data.get("content", ""),
            finish_reason=data.get("stop_reason", "unknown"),
            tokens_generated=data.get("tokens_predicted", 0),
            metadata={"timings": data.get("timings"), "truncated": data.get("truncated", False)},
        )

    def _schema_to_gbnf(self, schema: dict[str, Any]) -> str:
        """Convert JSON Schema to GBNF grammar.

        Args:
            schema: JSON Schema dictionary

        Returns:
            GBNF grammar string
        """
        # Basic GBNF grammar for JSON Schema types
        if schema.get("type") == "object" and "properties" in schema:
            # Object with specific properties
            props = schema["properties"]

            rules = ['root ::= "{"']
            prop_list = []

            for i, (prop_name, prop_schema) in enumerate(props.items()):
                sep = ' ","' if i > 0 else ""
                prop_type = prop_schema.get("type", "string")

                if prop_type == "string":
                    prop_list.append(f'{sep} "\\"" {prop_name} "\\"" ":" "\\"" [^"]* "\\""')
                elif prop_type == "number":
                    prop_list.append(f'{sep} "\\"" {prop_name} "\\"" ":" [0-9]+ ("." [0-9]+)?')
                elif prop_type == "boolean":
                    prop_list.append(f'{sep} "\\"" {prop_name} "\\"" ":" ("true" | "false")')

            rules.append(" ".join(prop_list) + ' "}"')
            return "\n".join(rules)

        # Array type
        elif schema.get("type") == "array":
            return 'root ::= "[" json_value ("," json_value)* "]"'

        # Fallback: generic JSON
        return "root ::= json_value"


def create_provider_adapter(provider: str, model: str | None = None, **kwargs) -> ProviderAdapter:
    """
    Create a provider adapter.

    Args:
        provider: Provider name (openai, vllm, sglang, llamacpp)
        model: Model identifier (provider-specific)
        **kwargs: Additional provider-specific arguments

    Returns:
        Configured provider adapter

    Raises:
        ValueError: If unknown provider

    Example:
        >>> adapter = create_provider_adapter("openai", model="gpt-4", api_key="...")
        >>> request = GenerationRequest(prompt="Write a function", schema={...})
        >>> response = adapter.generate(request)
    """
    # Import Modal adapter lazily
    try:
        from maze.orchestrator.providers.modal import ModalProviderAdapter
    except ImportError:
        ModalProviderAdapter = None

    adapters = {
        "openai": OpenAIProviderAdapter,
        "vllm": VLLMProviderAdapter,
        "sglang": SGLangProviderAdapter,
        "llamacpp": LlamaCppProviderAdapter,
    }

    # Add Modal if available
    if ModalProviderAdapter:
        adapters["modal"] = ModalProviderAdapter

    if provider not in adapters:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(adapters.keys())}")

    adapter_class = adapters[provider]

    # Set default models if not provided
    if model is None:
        defaults = {
            "openai": "gpt-4",
            "vllm": "model",
            "sglang": "model",
            "llamacpp": "model",
        }
        model = defaults[provider]

    return adapter_class(model=model, **kwargs)


__all__ = [
    "ProviderAdapter",
    "GenerationRequest",
    "GenerationResponse",
    "OpenAIProviderAdapter",
    "VLLMProviderAdapter",
    "SGLangProviderAdapter",
    "LlamaCppProviderAdapter",
    "create_provider_adapter",
]
