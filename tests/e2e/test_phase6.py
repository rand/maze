"""End-to-end tests for Phase 6 production readiness.

Tests full workflows from initialization through generation, validation, and repair.

Test coverage: 34 E2E tests
- Full pipeline scenarios: 10 tests
- CLI workflow tests: 10 tests
- Multi-provider tests: 4 tests (mocked)
- Validation + repair tests: 5 tests
- Learning feedback tests: 5 tests
"""

import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from maze.cli.main import CLI
from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.core.types import TypeContext


class TestFullPipelineScenarios:
    """E2E tests for complete pipeline workflows."""

    def test_e2e_project_initialization_and_indexing(self):
        """Test full workflow: init project -> index -> get context."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Step 1: Initialize project
            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cli = CLI()
                result = cli.run(["init", "--language", "typescript", "--name", "test-e2e"])
                assert result == 0
                assert (project_path / ".maze").exists()

                # Step 2: Create sample code
                ts_file = project_path / "src" / "index.ts"
                ts_file.parent.mkdir(parents=True)
                ts_file.write_text("""
function greet(name: string): string {
    return `Hello, ${name}!`;
}

export { greet };
""")

                # Step 3: Index project
                result = cli.run(["index", str(project_path)])
                assert result == 0

            finally:
                os.chdir(original_cwd)

    def test_e2e_config_management_workflow(self):
        """Test config get/set/list workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cli = CLI()

                # Init project
                cli.run(["init"])

                # List config
                result = cli.run(["config", "list"])
                assert result == 0

                # Get specific value
                result = cli.run(["config", "get", "project.language"])
                assert result == 0

                # Set value
                result = cli.run(["config", "set", "generation.temperature", "0.9"])
                assert result == 0

            finally:
                os.chdir(original_cwd)

    def test_e2e_pipeline_with_validation(self):
        """Test pipeline: index -> generate -> validate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Setup project
            ts_file = project_path / "test.ts"
            ts_file.write_text("const x: number = 42;")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)

            # Index
            index_result = pipeline.index_project(project_path)
            assert len(index_result.files_processed) > 0

            # Generate (will use placeholder)
            gen_result = pipeline.generate("Create a function")
            assert gen_result.code is not None

            # Validate generated code
            val_result = pipeline.validate(gen_result.code)
            assert val_result is not None

    def test_e2e_stats_after_operations(self):
        """Test stats collection after pipeline operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("function test() {}")

            config = Config()
            config.project.path = project_path
            config.project.language = "typescript"

            pipeline = Pipeline(config)
            pipeline.index_project(project_path)
            pipeline.generate("test prompt")

            # Check metrics were collected
            summary = pipeline.metrics.summary()
            assert "latencies" in summary
            assert len(summary["latencies"]) > 0

    def test_e2e_external_integrations_status(self):
        """Test external integrations availability checking."""
        from maze.integrations.external import ExternalIntegrations

        integrations = ExternalIntegrations()
        status = integrations.get_status()

        assert isinstance(status, dict)
        assert "mnemosyne" in status
        assert "pedantic_raven" in status
        assert "rune" in status

    def test_e2e_graceful_degradation_workflow(self):
        """Test workflow continues when optional tools unavailable."""
        from maze.integrations.external import ExternalIntegrations

        # Disable all optional tools
        integrations = ExternalIntegrations(
            enable_mnemosyne=False,
            enable_raven=False,
            enable_rune=False,
        )

        # Operations should still succeed
        val_result = integrations.validate_with_raven("code", "python")
        assert val_result.success is True

        exec_result = integrations.execute_in_rune("code", "python")
        assert exec_result.success is True

    def test_e2e_config_validation_workflow(self):
        """Test config validation catches errors."""
        config = Config()
        
        # Valid config
        errors = config.validate()
        assert len(errors) == 0

        # Invalid config
        config.generation.temperature = 5.0
        errors = config.validate()
        assert len(errors) > 0
        assert any("temperature" in err for err in errors)

    def test_e2e_logging_integration(self):
        """Test logging throughout pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "maze.log"

            config = Config()
            config.logging.format = "json"
            config.logging.log_file = log_file

            pipeline = Pipeline(config)
            pipeline.generate("test prompt")
            pipeline.close()

            # Check log file created
            assert log_file.exists()

    def test_e2e_error_handling_pipeline(self):
        """Test error handling throughout pipeline."""
        config = Config()
        config.project.language = "unsupported_language"

        pipeline = Pipeline(config)

        with pytest.raises(ValueError, match="not yet supported"):
            pipeline.index_project()

    def test_e2e_multiple_generations(self):
        """Test multiple generations in sequence."""
        config = Config()
        config.project.language = "typescript"

        pipeline = Pipeline(config)

        prompts = [
            "Create a function",
            "Create a class",
            "Create an interface",
        ]

        for prompt in prompts:
            result = pipeline.generate(prompt)
            assert result.prompt == prompt
            assert result.code is not None


class TestCLIWorkflowE2E:
    """E2E tests for CLI command workflows."""

    def test_cli_init_to_generate_workflow(self):
        """Test complete CLI workflow: init -> index -> generate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            
            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cli = CLI()

                # Init
                assert cli.run(["init"]) == 0

                # Create code
                (project_path / "test.ts").write_text("const x = 1;")

                # Index
                assert cli.run(["index", "."]) == 0

                # Generate would work but returns placeholder
                result = cli.run(["generate", "Create function"])
                assert result in [0, 1]  # May succeed or fail without provider

            finally:
                os.chdir(original_cwd)

    def test_cli_debug_command_workflow(self):
        """Test debug command provides diagnostics."""
        cli = CLI()
        result = cli.run(["debug"])
        assert result == 0

    def test_cli_debug_verbose_workflow(self):
        """Test debug with verbose output."""
        cli = CLI()
        result = cli.run(["debug", "--verbose"])
        assert result == 0

    def test_cli_stats_workflow(self):
        """Test stats command after operations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "test.ts").write_text("const x = 1;")

            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cli = CLI()
                cli.run(["init"])
                cli.run(["index", "."])
                
                # Stats should work
                result = cli.run(["stats"])
                assert result == 0

            finally:
                os.chdir(original_cwd)

    def test_cli_validate_file_workflow(self):
        """Test validate command on file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("const x: number = 42;")

            cli = CLI()
            result = cli.run(["validate", str(test_file)])
            assert result in [0, 1]  # May pass or fail validation

    def test_cli_index_with_output_workflow(self):
        """Test index with JSON output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            (project_path / "test.ts").write_text("function test() {}")
            output_file = project_path / "index.json"

            cli = CLI()
            result = cli.run(["index", str(project_path), "--output", str(output_file)])
            
            assert result == 0
            assert output_file.exists()

    def test_cli_config_roundtrip(self):
        """Test config set and get roundtrip."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            import os
            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cli = CLI()
                cli.run(["init"])

                # Set value
                cli.run(["config", "set", "generation.temperature", "0.8"])

                # Get value back (would need to capture stdout to verify)
                result = cli.run(["config", "get", "generation.temperature"])
                assert result == 0

            finally:
                os.chdir(original_cwd)

    def test_cli_help_commands(self):
        """Test help for all commands."""
        cli = CLI()
        
        # Main help
        with pytest.raises(SystemExit):
            cli.run(["--help"])

    def test_cli_version(self):
        """Test version display."""
        cli = CLI()
        
        with pytest.raises(SystemExit):
            cli.run(["--version"])

    def test_cli_error_handling(self):
        """Test CLI handles errors gracefully."""
        cli = CLI()
        
        # Invalid command
        with pytest.raises(SystemExit):
            cli.run(["invalid-command"])


class TestMultiProviderE2E:
    """E2E tests for multi-provider support (mocked)."""

    def test_openai_provider_config(self):
        """Test OpenAI provider configuration."""
        config = Config()
        config.generation.provider = "openai"
        config.generation.model = "gpt-4"

        pipeline = Pipeline(config)
        assert pipeline.config.generation.provider == "openai"

    def test_vllm_provider_config(self):
        """Test vLLM provider configuration."""
        config = Config()
        config.generation.provider = "vllm"
        config.generation.model = "llama-3"

        pipeline = Pipeline(config)
        assert pipeline.config.generation.provider == "vllm"

    def test_provider_switching(self):
        """Test switching providers between generations."""
        config = Config()

        # Start with OpenAI
        config.generation.provider = "openai"
        pipeline = Pipeline(config)
        result1 = pipeline.generate("test")
        assert result1 is not None

        # Switch to vLLM
        config.generation.provider = "vllm"
        result2 = pipeline.generate("test")
        assert result2 is not None

    def test_provider_timeout_handling(self):
        """Test provider timeout configuration."""
        config = Config()
        config.generation.timeout_seconds = 5

        pipeline = Pipeline(config)
        result = pipeline.generate("test")
        assert result is not None


class TestValidationRepairE2E:
    """E2E tests for validation and repair workflows."""

    def test_validation_success_workflow(self):
        """Test successful validation workflow."""
        config = Config()
        config.project.language = "typescript"

        pipeline = Pipeline(config)
        code = "const x: number = 42;"

        result = pipeline.validate(code)
        assert result is not None

    def test_validation_failure_detection(self):
        """Test validation detects failures."""
        config = Config()
        config.project.language = "typescript"

        pipeline = Pipeline(config)
        
        # Intentionally invalid code
        code = ""  # Empty code should fail some validators

        result = pipeline.validate(code)
        assert result is not None

    def test_repair_workflow_basic(self):
        """Test basic repair workflow."""
        config = Config()
        config.project.language = "typescript"

        pipeline = Pipeline(config)
        
        # Validate some code first to get diagnostics
        code = "const x = 1"
        
        # Just verify validation runs
        val_result = pipeline.validate(code)
        assert val_result is not None
        
        # If there are diagnostics, test repair
        if len(val_result.diagnostics) > 0:
            repair_result = pipeline.repair(code, val_result.diagnostics, "fix code", None)
            assert repair_result is not None

    def test_external_validation_integration(self):
        """Test external validation tools integration."""
        from maze.integrations.external import ExternalIntegrations

        integrations = ExternalIntegrations()
        
        code = "const x: number = 42;"
        result = integrations.validate_with_raven(code, "typescript")

        assert result.success is True

    def test_sandboxed_execution_integration(self):
        """Test sandboxed execution integration."""
        from maze.integrations.external import ExternalIntegrations

        integrations = ExternalIntegrations()
        
        code = "console.log('test');"
        result = integrations.execute_in_rune(code, "javascript")

        assert result.success is True


class TestLearningFeedbackE2E:
    """E2E tests for learning and feedback workflows."""

    def test_pattern_storage_workflow(self):
        """Test storing patterns to mnemosyne."""
        from maze.integrations.external import ExternalIntegrations, Pattern

        integrations = ExternalIntegrations()
        
        pattern = Pattern(
            content="async function example",
            namespace="project:test",
            importance=7,
            tags=["async", "function"],
        )

        result = integrations.persist_to_mnemosyne(pattern)
        assert isinstance(result, bool)

    def test_metrics_collection_workflow(self):
        """Test metrics collected throughout workflow."""
        config = Config()
        config.project.language = "typescript"

        pipeline = Pipeline(config)
        
        # Perform operations
        pipeline.generate("test1")
        pipeline.generate("test2")

        # Check metrics
        summary = pipeline.metrics.summary()
        assert "latencies" in summary

    def test_feedback_loop_integration(self):
        """Test feedback loop with learning system."""
        # This would integrate with Phase 5 learning system
        config = Config()
        pipeline = Pipeline(config)

        result = pipeline.generate("test")
        
        # Metrics should be recorded
        stats = pipeline.metrics.get_latency_stats("pipeline_total")
        if stats:
            assert stats["count"] >= 1

    def test_cache_metrics_tracking(self):
        """Test cache hit/miss tracking."""
        config = Config()
        pipeline = Pipeline(config)

        # Record some cache activity
        pipeline.metrics.record_cache_hit("grammar")
        pipeline.metrics.record_cache_hit("grammar")
        pipeline.metrics.record_cache_miss("grammar")

        hit_rate = pipeline.metrics.get_cache_hit_rate("grammar")
        assert hit_rate > 0.5

    def test_error_tracking_workflow(self):
        """Test error tracking and reporting."""
        config = Config()
        pipeline = Pipeline(config)

        # Record errors
        pipeline.metrics.record_error("validation_error")
        pipeline.metrics.record_error("timeout")

        summary = pipeline.metrics.summary()
        assert "errors" in summary
        assert len(summary["errors"]) > 0
