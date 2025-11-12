"""End-to-end integration tests for Path A (Provider Integration).

Tests complete workflow with grammar loading and provider integration.

Test coverage: 10 E2E tests
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.orchestrator.providers import GenerationResponse


class TestPathAIntegration:
    """E2E tests for Path A provider integration."""

    def test_e2e_grammar_to_provider_flow(self):
        """Test complete flow: grammar loading → provider call."""
        config = Config()
        config.project.language = "typescript"
        config.constraints.syntactic_enabled = True

        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="function add(a: number, b: number): number { return a + b; }",
                    finish_reason="stop",
                    tokens_generated=20,
                )
                mock_create.return_value = mock_provider

                # Generate with grammar
                result = pipeline.generate("Create add function")

                # Verify grammar was synthesized and passed
                request = mock_provider.generate.call_args[0][0]
                assert request.grammar is not None
                assert len(request.grammar) > 0

    def test_e2e_full_pipeline_with_grammar(self):
        """Test full pipeline: index → grammar → generate → validate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "test.ts").write_text("const x = 1;")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)

            with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
                with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                    mock_provider = Mock()
                    mock_provider.generate.return_value = GenerationResponse(
                        text="const result = 42;",
                        finish_reason="stop",
                        tokens_generated=5,
                    )
                    mock_create.return_value = mock_provider

                    # Full flow
                    result = pipeline.run("Create a constant")

                    # Should have indexed
                    assert pipeline._indexed_context is not None

                    # Should have generated
                    assert result.code == "const result = 42;"

                    # Should have validation metrics
                    assert result.validation is not None

    def test_e2e_grammar_caching_across_generations(self):
        """Test grammar cached across multiple generations."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=1
                )
                mock_create.return_value = mock_provider

                # First generation
                pipeline.generate("Create function 1")

                # Second generation
                pipeline.generate("Create function 2")

                # Check cache hit rate
                hit_rate = pipeline.metrics.get_cache_hit_rate("grammar")
                assert hit_rate == 0.5  # 1 hit, 1 miss

    def test_e2e_repair_receives_grammar(self):
        """Test repair receives grammar for refinement."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="invalid code",
                    finish_reason="stop",
                    tokens_generated=2,
                )
                mock_create.return_value = mock_provider

                # Generate (will have validation errors)
                result = pipeline.generate("test")

                # Grammar should be stored
                assert pipeline._last_grammar != ""

    def test_e2e_metrics_collection(self):
        """Test metrics collected throughout workflow."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=5
                )
                mock_create.return_value = mock_provider

                pipeline.generate("test")

                summary = pipeline.metrics.summary()

                # Should have recorded provider call
                assert "provider_call" in summary["latencies"]

                # Should have successful generation counter
                assert summary["counters"]["successful_generations"] >= 1

                # Should have cache metrics
                assert "grammar" in summary["cache_hit_rates"]

    def test_e2e_provider_switching(self):
        """Test switching providers between pipelines."""
        # OpenAI pipeline
        config1 = Config()
        config1.generation.provider = "openai"
        pipeline1 = Pipeline(config1)

        # vLLM pipeline
        config2 = Config()
        config2.generation.provider = "vllm"
        pipeline2 = Pipeline(config2)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=1
                )
                mock_create.return_value = mock_provider

                # Use different providers
                pipeline1.generate("test")

                # Second call should use different provider
                pipeline2.generate("test")

                assert mock_create.call_count == 2
                calls = [call[1] for call in mock_create.call_args_list]
                assert calls[0]["provider"] == "openai"
                assert calls[1]["provider"] == "vllm"

    def test_e2e_error_recovery(self):
        """Test error recovery with retry."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.retry_attempts = 2
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()

                # Fail first, succeed second
                mock_provider.generate.side_effect = [
                    Exception("Timeout"),
                    GenerationResponse(text="recovered", finish_reason="stop", tokens_generated=1),
                ]
                mock_create.return_value = mock_provider

                with patch("time.sleep"):
                    result = pipeline.generate("test")

                assert result.code == "recovered"
                assert mock_provider.generate.call_count == 2

    def test_e2e_graceful_degradation_no_api_key(self):
        """Test graceful degradation without API key."""
        config = Config()
        config.generation.provider = "openai"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {}, clear=True):
            result = pipeline.generate("test")

            # Should not crash
            assert result is not None
            assert "API key not found" in result.code

    def test_e2e_grammar_and_provider_metrics(self):
        """Test both grammar and provider metrics collected."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
            with patch("maze.core.pipeline.create_provider_adapter") as mock_create:
                mock_provider = Mock()
                mock_provider.generate.return_value = GenerationResponse(
                    text="code", finish_reason="stop", tokens_generated=1
                )
                mock_create.return_value = mock_provider

                # Multiple generations
                pipeline.generate("Create function 1")
                pipeline.generate("Create function 2")
                pipeline.generate("Create function 3")

                summary = pipeline.metrics.summary()

                # Grammar cache should show hits
                assert summary["cache_hit_rates"]["grammar"] > 0

                # Provider calls recorded
                assert summary["latencies"]["provider_call"]["count"] == 3

                # Successful generations counted
                assert summary["counters"]["successful_generations"] == 3

    def test_e2e_full_cli_workflow(self):
        """Test CLI workflow with provider integration."""
        from maze.cli.main import CLI

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            import os as os_module

            original_cwd = os_module.getcwd()
            os_module.chdir(project_path)

            try:
                cli = CLI()

                # Init project
                cli.run(["init", "--language", "typescript"])

                # Create test file
                (project_path / "test.ts").write_text("const x = 1;")

                # Index
                cli.run(["index", "."])

                # Generate (would work with API key)
                # For test, just verify command parses and runs
                with patch.dict(os.environ, {}, clear=True):
                    result = cli.run(["generate", "Create function"])
                    # Will return code about missing API key, but shouldn't crash
                    assert result in [0, 1]

            finally:
                os_module.chdir(original_cwd)
