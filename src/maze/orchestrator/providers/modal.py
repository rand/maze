"""Modal provider adapter for Maze.

Connects to Modal-deployed vLLM + llguidance inference server.

Configuration:
    export MODAL_ENDPOINT_URL=https://<user>--maze-inference-fastapi-app.modal.run
    
    maze config set generation.provider modal
    maze config set generation.model qwen2.5-coder-32b
"""

from __future__ import annotations

import os
from typing import Optional

from maze.orchestrator.providers import (
    GenerationRequest,
    GenerationResponse,
    ProviderAdapter,
)


class ModalProviderAdapter(ProviderAdapter):
    """Adapter for Modal-deployed Maze inference server.
    
    Connects to vLLM + llguidance running on Modal.com.
    """

    def __init__(
        self,
        model: str = "qwen2.5-coder-32b",
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        """Initialize Modal provider adapter.

        Args:
            model: Model identifier (for reference)
            api_key: Optional API key for authentication
            api_base: Modal endpoint URL (or set MODAL_ENDPOINT_URL env var)
        """
        super().__init__(model, api_key)
        
        # Try to get endpoint from multiple sources
        self.api_base = (
            api_base
            or os.getenv("MODAL_ENDPOINT_URL")
            # Default to deployed endpoint
            or "https://rand--maze-inference-fastapi-app.modal.run"
        )
        
        if "not-configured" in self.api_base:
            raise ValueError(
                "Modal endpoint not configured. Set MODAL_ENDPOINT_URL environment variable."
            )

    def supports_grammar(self) -> bool:
        """Modal server supports grammar constraints via llguidance."""
        return True

    def supports_json_schema(self) -> bool:
        """Modal server supports JSON Schema (can convert to grammar)."""
        return True

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate code using Modal endpoint.

        Args:
            request: Generation request with prompt and optional grammar

        Returns:
            Generated code response

        Raises:
            ImportError: If requests not installed
            ValueError: If endpoint returns error
        """
        try:
            import requests
        except ImportError:
            raise ImportError("requests package required. Install with: uv add requests")

        # Build request payload
        payload = {
            "prompt": request.prompt,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }
        
        # Add grammar if provided
        if request.grammar:
            payload["grammar"] = request.grammar
        
        # Add language hint if available
        if "language" in request.metadata:
            payload["language"] = request.metadata["language"]

        # Add API key if configured
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        # Make request to Modal endpoint
        try:
            response = requests.post(
                f"{self.api_base}/generate",
                json=payload,
                headers=headers,
                timeout=120,  # 2 minutes max
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parse response
            return GenerationResponse(
                text=data["code"],
                finish_reason=data.get("metadata", {}).get("finish_reason", "stop"),
                tokens_generated=data.get("metadata", {}).get("tokens_generated", 0),
                metadata=data.get("metadata", {}),
            )
            
        except requests.exceptions.Timeout:
            raise ValueError("Modal endpoint timeout (>120s)")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Modal endpoint error: {e}")
        except (KeyError, ValueError) as e:
            raise ValueError(f"Invalid response from Modal endpoint: {e}")
