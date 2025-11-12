"""Tests for provider configuration and error handling.

Test coverage target: 85%
"""

import os
from unittest.mock import Mock, patch

from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.orchestrator.providers import GenerationResponse


class TestProviderConfiguration:
    """Tests for provider configuration."""

    def test_api_key_from_environment(self):
        """Test API key loaded from environment."""
        config = Config()
        config.generation.provider = "openai"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test123"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=1
                )
                mock_create.return_value = mock_provider

                pipeline._generate_with_constraints("test", "", None)

                # Verify API key passed
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs.get("api_key") == "sk-test123"

    def test_missing_api_key_returns_message(self):
        """Test helpful message when API key missing."""
        config = Config()
        config.generation.provider = "openai"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {}, clear=True):
            code = pipeline._generate_with_constraints("test", "", None)

            assert "API key not found" in code
            assert "OPENAI_API_KEY" in code

    def test_retry_on_transient_error(self):
        """Test retry logic on transient errors."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.retry_attempts = 3
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()

                # Fail twice, succeed third time
                mock_provider.generate.side_effect = [
                    Exception("Timeout"),
                    Exception("Rate limit"),
                    GenerationResponse(text="success", finish_reason="stop", tokens_generated=1),
                ]
                mock_create.return_value = mock_provider

                with patch("time.sleep"):  # Mock sleep to speed up test
                    code = pipeline._generate_with_constraints("test", "", None)

                assert code == "success"
                assert mock_provider.generate.call_count == 3

    def test_no_retry_on_auth_error(self):
        """Test no retry on authentication errors."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.retry_attempts = 3
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-invalid"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.side_effect = Exception("Invalid API key")
                mock_create.return_value = mock_provider

                code = pipeline._generate_with_constraints("test", "", None)

                # Should only try once on auth error
                assert mock_provider.generate.call_count == 1
                assert "failed" in code.lower()

    def test_all_retries_exhausted(self):
        """Test behavior when all retries fail."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.retry_attempts = 2
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.side_effect = Exception("Server error")
                mock_create.return_value = mock_provider

                with patch("time.sleep"):
                    code = pipeline._generate_with_constraints("test", "", None)

                assert "failed after 2 attempts" in code
                assert mock_provider.generate.call_count == 2

    def test_metrics_recorded_on_success(self):
        """Test metrics recorded on successful generation."""
        config = Config()
        config.generation.provider = "openai"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=10
                )
                mock_create.return_value = mock_provider

                pipeline._generate_with_constraints("test", "", None)

                # Check metrics recorded
                stats = pipeline.metrics.get_latency_stats("provider_call")
                assert stats is not None
                assert stats["count"] == 1
                assert pipeline.metrics.counters["successful_generations"] == 1

    def test_error_metrics_recorded_on_failure(self):
        """Test error metrics recorded on failure."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.retry_attempts = 1
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.side_effect = Exception("Error")
                mock_create.return_value = mock_provider

                pipeline._generate_with_constraints("test", "", None)

                # Check error recorded
                assert pipeline.metrics.errors["generation_failure"] == 1
