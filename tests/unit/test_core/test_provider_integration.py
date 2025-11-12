"""Tests for provider integration in pipeline.

Test coverage target: 85%
"""

from unittest.mock import Mock, patch

from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.orchestrator.providers import GenerationRequest, GenerationResponse


class TestProviderIntegration:
    """Tests for provider adapter integration."""

    def test_provider_created_on_first_generation(self):
        """Test provider created lazily on first generation."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        assert pipeline.provider is None

        # Mock the provider creation
        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="const x = 1;",
                finish_reason="stop",
                tokens_generated=5,
            )
            mock_create.return_value = mock_provider

            code = pipeline._generate_with_constraints("test", "", None)

            assert pipeline.provider is not None
            mock_create.assert_called_once()

    def test_provider_reused_across_generations(self):
        """Test provider instance reused."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="code", finish_reason="stop", tokens_generated=1
            )
            mock_create.return_value = mock_provider

            # First generation
            pipeline._generate_with_constraints("test1", "", None)

            # Second generation
            pipeline._generate_with_constraints("test2", "", None)

            # Provider created only once
            assert mock_create.call_count == 1

    def test_grammar_passed_to_provider(self):
        """Test grammar passed in generation request."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="code", finish_reason="stop", tokens_generated=1
            )
            mock_create.return_value = mock_provider

            grammar = "start: 'test'"
            pipeline._generate_with_constraints("test", grammar, None)

            # Check generate was called with grammar
            call_args = mock_provider.generate.call_args
            request = call_args[0][0]
            assert isinstance(request, GenerationRequest)
            assert request.grammar == grammar

    def test_config_params_passed_to_provider(self):
        """Test config parameters passed to provider."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 1024
        config.generation.temperature = 0.9

        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="code", finish_reason="stop", tokens_generated=1
            )
            mock_create.return_value = mock_provider

            pipeline._generate_with_constraints("test", "", None)

            request = mock_provider.generate.call_args[0][0]
            assert request.max_tokens == 1024
            assert request.temperature == 0.9

    def test_provider_unavailable_fallback(self):
        """Test fallback when provider unavailable."""
        config = Config()
        config.generation.provider = "nonexistent"
        pipeline = Pipeline(config)

        code = pipeline._generate_with_constraints("test", "", None)

        assert "not available" in code
        assert pipeline.provider is None

    def test_generation_error_handling(self):
        """Test error handling during generation."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.side_effect = Exception("API Error")
            mock_create.return_value = mock_provider

            code = pipeline._generate_with_constraints("test", "", None)

            assert "Generation failed" in code
            assert "API Error" in code

    def test_generated_code_returned(self):
        """Test generated code returned from provider."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        expected_code = "function test() { return 42; }"

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text=expected_code,
                finish_reason="stop",
                tokens_generated=10,
            )
            mock_create.return_value = mock_provider

            code = pipeline._generate_with_constraints("test", "", None)

            assert code == expected_code

    def test_empty_grammar_handled(self):
        """Test empty grammar passed as None to provider."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="code", finish_reason="stop", tokens_generated=1
            )
            mock_create.return_value = mock_provider

            pipeline._generate_with_constraints("test", "", None)

            request = mock_provider.generate.call_args[0][0]
            assert request.grammar is None

    def test_provider_selection_from_config(self):
        """Test provider selected based on config."""
        config = Config()
        config.generation.provider = "vllm"
        config.generation.model = "llama-3"

        pipeline = Pipeline(config)

        with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
            mock_provider = Mock()
            mock_provider.generate.return_value = GenerationResponse(
                text="code", finish_reason="stop", tokens_generated=1
            )
            mock_create.return_value = mock_provider

            pipeline._generate_with_constraints("test", "", None)

            mock_create.assert_called_with(provider="vllm", model="llama-3", api_key=None)
