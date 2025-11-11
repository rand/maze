"""Tests for Maze pipeline orchestration.

Test coverage target: 85%
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from maze.config import Config
from maze.core.pipeline import (
    IndexingMetrics,
    Pipeline,
    PipelineConfig,
    PipelineResult,
)
from maze.core.types import TypeContext
from maze.indexer.base import IndexingResult


class TestPipelineConfig:
    """Tests for PipelineConfig."""

    def test_default_config(self):
        """Test default pipeline configuration."""
        config = PipelineConfig(
            project_path=Path("/tmp/project"), language="typescript"
        )

        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.enable_syntactic is True
        assert config.enable_type is True
        assert config.max_repair_attempts == 3

    def test_custom_config(self):
        """Test custom pipeline configuration."""
        config = PipelineConfig(
            project_path=Path("/tmp/project"),
            language="python",
            provider="vllm",
            model="llama-3",
            enable_repair=False,
        )

        assert config.language == "python"
        assert config.provider == "vllm"
        assert config.enable_repair is False


class TestPipeline:
    """Tests for Pipeline class."""

    def test_pipeline_initialization(self):
        """Test pipeline initializes with config."""
        config = Config()
        pipeline = Pipeline(config)

        assert pipeline.config == config
        assert pipeline.logger is not None
        assert pipeline.metrics is not None
        assert pipeline.grammar_builder is not None
        assert pipeline.validator is not None

    def test_index_project_typescript(self):
        """Test indexing TypeScript project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create sample TypeScript file
            ts_file = project_path / "test.ts"
            ts_file.write_text("function hello(): string { return 'world'; }")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)
            result = pipeline.index_project()

            assert isinstance(result, IndexingResult)
            assert len(result.files_processed) > 0
            assert pipeline._indexed_context is not None

    def test_index_project_unsupported_language(self):
        """Test indexing with unsupported language raises error."""
        config = Config()
        config.project.language = "rust"  # Not yet supported

        pipeline = Pipeline(config)

        with pytest.raises(ValueError, match="not yet supported"):
            pipeline.index_project()

    def test_validate_code(self):
        """Test code validation."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        code = "const x: number = 42;"
        result = pipeline.validate(code)

        # Result should have validation structure
        assert hasattr(result, "success")
        assert hasattr(result, "diagnostics")

    def test_generate_without_indexing(self):
        """Test generation auto-indexes if needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("const x = 1;")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)
            result = pipeline.run("Create a function")

            # Should have auto-indexed
            assert pipeline._indexed_context is not None
            assert isinstance(result, PipelineResult)

    def test_generate_with_context(self):
        """Test generation with provided context."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        type_ctx = TypeContext()
        result = pipeline.generate("Create a function", type_ctx)

        assert isinstance(result, PipelineResult)
        assert result.language == "typescript"
        assert result.prompt == "Create a function"

    def test_pipeline_result_structure(self):
        """Test pipeline result has expected structure."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        result = pipeline.generate("test prompt")

        assert isinstance(result, PipelineResult)
        assert result.prompt == "test prompt"
        assert result.language == "typescript"
        assert isinstance(result.code, str)
        assert isinstance(result.success, bool)
        assert isinstance(result.total_duration_ms, float)

    def test_metrics_recording(self):
        """Test pipeline records metrics."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        pipeline.generate("test")

        # Should have recorded metrics
        summary = pipeline.metrics.summary()
        assert "latencies" in summary

    def test_pipeline_close(self):
        """Test pipeline cleanup."""
        config = Config()
        pipeline = Pipeline(config)

        # Should not raise
        pipeline.close()

    @pytest.mark.skip(reason="Requires provider integration")
    def test_full_pipeline_with_repair(self):
        """Test full pipeline with validation and repair."""
        # This test requires actual provider integration
        pass

    @pytest.mark.skip(reason="Requires provider integration")
    def test_constraint_synthesis(self):
        """Test constraint synthesis from context."""
        # This test requires grammar builder integration
        pass


class TestPipelineIntegration:
    """Integration tests for pipeline components."""

    def test_pipeline_with_validation(self):
        """Test pipeline validates generated code."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        # Generate and validate
        result = pipeline.generate("Create a function")

        # Should have validation metrics
        assert result.validation is not None

    def test_pipeline_error_handling(self):
        """Test pipeline handles errors gracefully."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        # Force an error by mocking validator to raise
        pipeline.validator.validate = Mock(side_effect=Exception("Test error"))

        result = pipeline.generate("test")

        # Should capture error
        assert len(result.errors) > 0
        assert result.success is False

    def test_pipeline_timeout(self):
        """Test pipeline respects timeout."""
        config = Config()
        config.project.language = "typescript"
        config.generation.timeout_seconds = 1
        pipeline = Pipeline(config)

        # Normal operation should complete within timeout
        result = pipeline.generate("test", TypeContext())
        assert result is not None

    def test_indexing_metrics(self):
        """Test indexing records proper metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("const x = 1;")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)
            result = pipeline.index_project()

            # Check metrics were recorded
            stats = pipeline.metrics.get_latency_stats("indexing")
            assert stats is not None
            assert stats["count"] >= 1


class TestPipelinePerformance:
    """Performance tests for pipeline."""

    def test_pipeline_setup_performance(self):
        """Test pipeline initialization is fast."""
        import time

        config = Config()

        start = time.perf_counter()
        pipeline = Pipeline(config)
        duration_ms = (time.perf_counter() - start) * 1000

        # Should be <100ms as per target
        assert duration_ms < 100

    def test_small_file_indexing_performance(self):
        """Test indexing small files is fast."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create small TypeScript file
            ts_file = project_path / "test.ts"
            ts_file.write_text("function add(a: number, b: number): number { return a + b; }")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)

            start = time.perf_counter()
            pipeline.index_project()
            duration_ms = (time.perf_counter() - start) * 1000

            # Small file should index quickly (<1s)
            assert duration_ms < 1000
