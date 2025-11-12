"""Tests for Modal provider adapter.

Test coverage target: 85%
"""

import os
from unittest.mock import Mock, patch

import pytest

from maze.orchestrator.providers import GenerationRequest
from maze.orchestrator.providers.modal import ModalProviderAdapter


class TestModalProvider:
    """Tests for ModalProviderAdapter."""

    def test_initialization_with_env_var(self):
        """Test adapter initialization from environment variable."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            assert "test.modal.run" in adapter.api_base

    def test_initialization_without_endpoint_fails(self):
        """Test adapter fails without endpoint configured."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="not configured"):
                ModalProviderAdapter()

    def test_supports_grammar(self):
        """Test Modal adapter supports grammar constraints."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            assert adapter.supports_grammar() is True

    def test_supports_json_schema(self):
        """Test Modal adapter supports JSON Schema."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            assert adapter.supports_json_schema() is True

    def test_generate_with_grammar(self):
        """Test generation with grammar constraints."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "success": True,
                    "code": "def add(a, b): return a + b",
                    "metadata": {
                        "tokens_generated": 10,
                        "finish_reason": "stop",
                    }
                }
                mock_post.return_value = mock_response
                
                request = GenerationRequest(
                    prompt="def add(a, b):",
                    grammar="?start: function",
                    max_tokens=128,
                )
                
                response = adapter.generate(request)
                
                assert response.text == "def add(a, b): return a + b"
                assert response.tokens_generated == 10
                
                # Verify grammar was sent
                call_args = mock_post.call_args[1]
                assert call_args["json"]["grammar"] == "?start: function"

    def test_generate_without_grammar(self):
        """Test generation without grammar constraints."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            
            with patch("requests.post") as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {
                    "success": True,
                    "code": "generated code",
                    "metadata": {"tokens_generated": 5}
                }
                mock_post.return_value = mock_response
                
                request = GenerationRequest(
                    prompt="test",
                    max_tokens=128,
                )
                
                response = adapter.generate(request)
                assert response.text == "generated code"

    def test_timeout_handling(self):
        """Test timeout handling."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            
            with patch("requests.post") as mock_post:
                import requests
                mock_post.side_effect = requests.exceptions.Timeout()
                
                request = GenerationRequest(prompt="test")
                
                with pytest.raises(ValueError, match="timeout"):
                    adapter.generate(request)

    def test_error_handling(self):
        """Test error response handling."""
        with patch.dict(os.environ, {"MODAL_ENDPOINT_URL": "https://test.modal.run"}):
            adapter = ModalProviderAdapter()
            
            with patch("requests.post") as mock_post:
                import requests
                mock_post.side_effect = requests.exceptions.RequestException("Connection failed")
                
                request = GenerationRequest(prompt="test")
                
                with pytest.raises(ValueError, match="endpoint error"):
                    adapter.generate(request)
