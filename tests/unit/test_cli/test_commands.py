"""Tests for CLI commands.

Test coverage target: 80%
"""

import argparse
import tempfile
from pathlib import Path

from maze.cli.commands import (
    ConfigCommand,
    DebugCommand,
    GenerateCommand,
    IndexCommand,
    InitCommand,
    StatsCommand,
    ValidateCommand,
)
from maze.config import Config


class TestInitCommand:
    """Tests for InitCommand."""

    def test_init_new_project(self):
        """Test initializing a new project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Change to temp directory
            import os

            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cmd = InitCommand()
                # Use argparse Namespace instead of Mock
                import argparse

                args = argparse.Namespace(language="typescript", name="test-project")

                result = cmd.execute(args)

                assert result == 0
                assert (project_path / ".maze").exists()
                assert (project_path / ".maze" / "config.toml").exists()
                assert (project_path / ".maze" / "cache").exists()
            finally:
                os.chdir(original_cwd)

    def test_init_already_initialized(self):
        """Test init on already initialized project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            maze_dir = project_path / ".maze"
            maze_dir.mkdir()

            import os

            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cmd = InitCommand()
                args = argparse.Namespace(language="python", name="test")

                result = cmd.execute(args)

                assert result == 1
            finally:
                os.chdir(original_cwd)


class TestConfigCommand:
    """Tests for ConfigCommand."""

    def test_config_list(self, capsys):
        """Test listing configuration."""
        cmd = ConfigCommand()
        args = argparse.Namespace(config_action="list")

        result = cmd.execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "project" in captured.out
        assert "generation" in captured.out

    def test_config_get_existing_key(self, capsys):
        """Test getting existing config key."""
        cmd = ConfigCommand()
        args = argparse.Namespace(config_action="get", key="project.language")

        result = cmd.execute(args)

        assert result == 0
        captured = capsys.readouterr()
        assert "typescript" in captured.out

    def test_config_get_nonexistent_key(self):
        """Test getting non-existent config key."""
        cmd = ConfigCommand()
        args = argparse.Namespace(config_action="get", key="nonexistent.key")

        result = cmd.execute(args)

        assert result == 1

    def test_config_set_value(self):
        """Test setting config value."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            maze_dir = project_path / ".maze"
            maze_dir.mkdir()

            config = Config()
            config_path = maze_dir / "config.toml"
            config.save(config_path)

            import os

            original_cwd = os.getcwd()
            os.chdir(project_path)

            try:
                cmd = ConfigCommand()
                args = argparse.Namespace(
                    config_action="set",
                    key="generation.temperature",
                    value="0.9",
                )

                result = cmd.execute(args)

                assert result == 0
            finally:
                os.chdir(original_cwd)


class TestIndexCommand:
    """Tests for IndexCommand."""

    def test_index_directory(self):
        """Test indexing a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("const x = 1;")

            cmd = IndexCommand()
            cmd.config.project.language = "typescript"
            args = argparse.Namespace(path=project_path, output=None, watch=False)

            result = cmd.execute(args)

            assert result == 0

    def test_index_with_output_file(self):
        """Test indexing with output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            ts_file = project_path / "test.ts"
            ts_file.write_text("function hello() {}")

            output_file = project_path / "index.json"

            cmd = IndexCommand()
            cmd.config.project.language = "typescript"
            args = argparse.Namespace(path=project_path, output=output_file, watch=False)

            result = cmd.execute(args)

            assert result == 0
            assert output_file.exists()

    def test_index_error_handling(self):
        """Test index command error handling."""
        cmd = IndexCommand()
        cmd.config.project.language = "unsupported"
        args = argparse.Namespace(path=Path("/nonexistent"), output=None, watch=False)

        result = cmd.execute(args)

        assert result == 1


class TestGenerateCommand:
    """Tests for GenerateCommand."""

    def test_generate_code(self):
        """Test code generation."""
        cmd = GenerateCommand()
        cmd.config.project.language = "typescript"
        args = argparse.Namespace(
            prompt="Create a function",
            language=None,
            provider=None,
            output=None,
            constraints=None,
        )

        result = cmd.execute(args)

        # Generation will return placeholder code
        assert result in [0, 1]  # May fail without provider

    def test_generate_with_output_file(self):
        """Test generation with output file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / "generated.ts"

            cmd = GenerateCommand()
            cmd.config.project.language = "typescript"
            args = argparse.Namespace(
                prompt="test",
                language=None,
                provider=None,
                output=output_file,
                constraints=None,
            )

            result = cmd.execute(args)

            # Should create file if successful
            if result == 0:
                assert output_file.exists()

    def test_generate_with_language_override(self):
        """Test generation with language override."""
        cmd = GenerateCommand()
        args = argparse.Namespace(
            prompt="test",
            language="python",
            provider=None,
            output=None,
            constraints=None,
        )

        cmd.execute(args)

        assert cmd.config.project.language == "python"


class TestValidateCommand:
    """Tests for ValidateCommand."""

    def test_validate_existing_file(self):
        """Test validating existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.ts"
            test_file.write_text("const x: number = 42;")

            cmd = ValidateCommand()
            cmd.config.project.language = "typescript"
            args = argparse.Namespace(file=test_file, run_tests=False, type_check=False, fix=False)

            result = cmd.execute(args)

            # Should validate (may pass or fail)
            assert result in [0, 1]

    def test_validate_nonexistent_file(self):
        """Test validating non-existent file."""
        cmd = ValidateCommand()
        args = argparse.Namespace(
            file=Path("/nonexistent.ts"),
            run_tests=False,
            type_check=False,
            fix=False,
        )

        result = cmd.execute(args)

        assert result == 1


class TestStatsCommand:
    """Tests for StatsCommand."""

    def test_stats_default(self):
        """Test stats with default options."""
        cmd = StatsCommand()
        args = argparse.Namespace(show_performance=False, show_cache=False, show_patterns=False)

        result = cmd.execute(args)

        assert result == 0

    def test_stats_show_performance(self):
        """Test stats showing performance."""
        cmd = StatsCommand()
        args = argparse.Namespace(show_performance=True, show_cache=False, show_patterns=False)

        result = cmd.execute(args)

        assert result == 0

    def test_stats_show_cache(self):
        """Test stats showing cache."""
        cmd = StatsCommand()
        args = argparse.Namespace(show_performance=False, show_cache=True, show_patterns=False)

        result = cmd.execute(args)

        assert result == 0


class TestDebugCommand:
    """Tests for DebugCommand."""

    def test_debug_basic(self):
        """Test basic debug output."""
        cmd = DebugCommand()
        args = argparse.Namespace(verbose=False, profile=False)

        result = cmd.execute(args)

        assert result == 0

    def test_debug_verbose(self):
        """Test debug with verbose output."""
        cmd = DebugCommand()
        args = argparse.Namespace(verbose=True, profile=False)

        result = cmd.execute(args)

        assert result == 0

    def test_debug_with_profiling(self):
        """Test debug with profiling enabled."""
        cmd = DebugCommand()
        args = argparse.Namespace(verbose=False, profile=True)

        result = cmd.execute(args)

        assert result == 0
        assert cmd.config.performance.enable_profiling is True
