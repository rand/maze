"""Tests for Maze configuration system.

Test coverage target: 90%
"""

import tempfile
from pathlib import Path

from maze.config import (
    Config,
    ConstraintConfig,
    GenerationConfig,
    IndexerConfig,
    LoggingConfig,
    PerformanceConfig,
    ProjectConfig,
    ValidationConfig,
)


class TestProjectConfig:
    """Tests for ProjectConfig."""

    def test_default_values(self):
        """Test default project configuration."""
        config = ProjectConfig()
        assert config.name == "maze-project"
        assert config.language == "typescript"
        assert "src/" in config.source_paths

    def test_custom_values(self):
        """Test custom project configuration."""
        config = ProjectConfig(name="my-project", language="python", source_paths=["lib/", "app/"])
        assert config.name == "my-project"
        assert config.language == "python"
        assert config.source_paths == ["lib/", "app/"]


class TestIndexerConfig:
    """Tests for IndexerConfig."""

    def test_default_values(self):
        """Test default indexer configuration."""
        config = IndexerConfig()
        assert config.enabled is True
        assert config.cache_enabled is True
        assert config.incremental is True
        assert "node_modules" in config.excluded_dirs

    def test_custom_values(self):
        """Test custom indexer configuration."""
        config = IndexerConfig(enabled=False, cache_enabled=False, max_file_size_kb=2048)
        assert config.enabled is False
        assert config.cache_enabled is False
        assert config.max_file_size_kb == 2048


class TestGenerationConfig:
    """Tests for GenerationConfig."""

    def test_default_values(self):
        """Test default generation configuration."""
        config = GenerationConfig()
        assert config.provider == "modal"  # Default changed to modal
        assert config.model == "qwen2.5-coder-32b"  # Default model for modal
        assert config.temperature == 0.7
        assert config.max_tokens == 2048

    def test_custom_values(self):
        """Test custom generation configuration."""
        config = GenerationConfig(provider="vllm", model="llama-3", temperature=1.0)
        assert config.provider == "vllm"
        assert config.model == "llama-3"
        assert config.temperature == 1.0


class TestConstraintConfig:
    """Tests for ConstraintConfig."""

    def test_default_values(self):
        """Test default constraint configuration."""
        config = ConstraintConfig()
        assert config.syntactic_enabled is True
        assert config.type_enabled is True
        assert config.semantic_enabled is False
        assert config.contextual_enabled is True
        assert config.type_search_depth == 5

    def test_all_constraints_enabled(self):
        """Test enabling all constraints."""
        config = ConstraintConfig(
            syntactic_enabled=True,
            type_enabled=True,
            semantic_enabled=True,
            contextual_enabled=True,
        )
        assert config.syntactic_enabled is True
        assert config.type_enabled is True
        assert config.semantic_enabled is True
        assert config.contextual_enabled is True


class TestValidationConfig:
    """Tests for ValidationConfig."""

    def test_default_values(self):
        """Test default validation configuration."""
        config = ValidationConfig()
        assert config.syntax_check is True
        assert config.type_check is True
        assert config.run_tests is False
        assert config.lint is True

    def test_custom_values(self):
        """Test custom validation configuration."""
        config = ValidationConfig(run_tests=True, timeout_seconds=120)
        assert config.run_tests is True
        assert config.timeout_seconds == 120


class TestPerformanceConfig:
    """Tests for PerformanceConfig."""

    def test_default_values(self):
        """Test default performance configuration."""
        config = PerformanceConfig()
        assert config.cache_size == 100_000
        assert config.parallel_indexing is True
        assert config.max_workers >= 1
        assert config.enable_profiling is False

    def test_custom_values(self):
        """Test custom performance configuration."""
        config = PerformanceConfig(cache_size=50_000, max_workers=8, enable_profiling=True)
        assert config.cache_size == 50_000
        assert config.max_workers == 8
        assert config.enable_profiling is True


class TestLoggingConfig:
    """Tests for LoggingConfig."""

    def test_default_values(self):
        """Test default logging configuration."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "json"
        assert config.output == "stdout"
        assert config.metrics_enabled is True

    def test_custom_values(self):
        """Test custom logging configuration."""
        config = LoggingConfig(level="DEBUG", format="text", log_file=Path("/tmp/maze.log"))
        assert config.level == "DEBUG"
        assert config.format == "text"
        assert config.log_file == Path("/tmp/maze.log")


class TestConfig:
    """Tests for main Config class."""

    def test_default_config(self):
        """Test default configuration."""
        config = Config()
        assert config.project.name == "maze-project"
        assert config.generation.provider == "modal"  # Default changed to modal
        assert config.constraints.syntactic_enabled is True

    def test_from_dict(self):
        """Test creating Config from dictionary."""
        data = {
            "project": {"name": "test-project", "language": "python"},
            "generation": {"provider": "vllm", "temperature": 0.5},
            "constraints": {"type_search_depth": 10},
        }
        config = Config.from_dict(data)
        assert config.project.name == "test-project"
        assert config.project.language == "python"
        assert config.generation.provider == "vllm"
        assert config.generation.temperature == 0.5
        assert config.constraints.type_search_depth == 10

    def test_to_dict(self):
        """Test converting Config to dictionary."""
        config = Config()
        config.project.name = "my-project"
        config.generation.temperature = 0.9

        data = config.to_dict()
        assert data["project"]["name"] == "my-project"
        assert data["generation"]["temperature"] == 0.9

    def test_path_serialization(self):
        """Test Path objects are serialized to strings."""
        config = Config()
        config.indexer.cache_path = Path("/tmp/cache")

        data = config.to_dict()
        assert data["indexer"]["cache_path"] == "/tmp/cache"

    def test_merge_configs(self):
        """Test merging two configurations."""
        base = Config()
        base.project.name = "base-project"
        base.generation.temperature = 0.5

        override = Config()
        override.project.name = "override-project"
        override.constraints.type_search_depth = 10

        merged = base.merge(override)
        assert merged.project.name == "override-project"
        assert merged.generation.temperature == 0.5
        assert merged.constraints.type_search_depth == 10

    def test_save_and_load(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.toml"

            # Create and save config
            config = Config()
            config.project.name = "test-project"
            config.generation.temperature = 0.8
            config.save(config_path)

            assert config_path.exists()

            # Load config
            loaded = Config._load_from_file(config_path)
            assert loaded.project.name == "test-project"
            assert loaded.generation.temperature == 0.8

    def test_load_global_config(self):
        """Test loading global configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Monkey-patch Path.home()
            original_home = Path.home
            Path.home = lambda: Path(tmpdir)

            try:
                global_config_dir = Path(tmpdir) / ".config" / "maze"
                global_config_dir.mkdir(parents=True)
                global_config_path = global_config_dir / "config.toml"

                # Create global config
                config = Config()
                config.project.name = "global-project"
                config.save(global_config_path)

                # Load should find global config
                loaded = Config.load()
                assert loaded.project.name == "global-project"
            finally:
                Path.home = original_home

    def test_load_project_config(self):
        """Test loading project configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)
            maze_dir = project_path / ".maze"
            maze_dir.mkdir()
            config_path = maze_dir / "config.toml"

            # Create project config
            config = Config()
            config.project.name = "project-config"
            config.save(config_path)

            # Load project config
            loaded = Config.load(project_path)
            assert loaded.project.name == "project-config"

    def test_load_hierarchy(self):
        """Test configuration hierarchy (global < project)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Monkey-patch Path.home()
            original_home = Path.home
            Path.home = lambda: Path(tmpdir)

            try:
                # Create global config
                global_config_dir = Path(tmpdir) / ".config" / "maze"
                global_config_dir.mkdir(parents=True)
                global_config_path = global_config_dir / "config.toml"

                global_config = Config()
                global_config.project.name = "global"
                global_config.generation.temperature = 0.5
                global_config.save(global_config_path)

                # Create project config
                project_path = Path(tmpdir) / "project"
                project_path.mkdir()
                maze_dir = project_path / ".maze"
                maze_dir.mkdir()
                project_config_path = maze_dir / "config.toml"

                project_config = Config()
                project_config.project.name = "project"
                project_config.save(project_config_path)

                # Load with hierarchy
                loaded = Config.load(project_path)
                assert loaded.project.name == "project"  # Project overrides
                assert loaded.generation.temperature == 0.5  # Global value
            finally:
                Path.home = original_home


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_valid_config(self):
        """Test valid configuration has no errors."""
        config = Config()
        errors = config.validate()
        assert len(errors) == 0

    def test_invalid_temperature(self):
        """Test invalid temperature range."""
        config = Config()
        config.generation.temperature = 3.0
        errors = config.validate()
        assert any("temperature" in err for err in errors)

    def test_invalid_max_tokens(self):
        """Test invalid max tokens."""
        config = Config()
        config.generation.max_tokens = 0
        errors = config.validate()
        assert any("max_tokens" in err for err in errors)

    def test_invalid_timeout(self):
        """Test invalid timeout."""
        config = Config()
        config.generation.timeout_seconds = 0
        errors = config.validate()
        assert any("timeout_seconds" in err for err in errors)

    def test_invalid_type_search_depth(self):
        """Test invalid type search depth."""
        config = Config()
        config.constraints.type_search_depth = 0
        errors = config.validate()
        assert any("type_search_depth" in err for err in errors)

    def test_invalid_cache_size(self):
        """Test invalid cache size."""
        config = Config()
        config.performance.cache_size = 0
        errors = config.validate()
        assert any("cache_size" in err for err in errors)

    def test_invalid_max_workers(self):
        """Test invalid max workers."""
        config = Config()
        config.performance.max_workers = 0
        errors = config.validate()
        assert any("max_workers" in err for err in errors)

    def test_invalid_memory_limit(self):
        """Test invalid memory limit."""
        config = Config()
        config.performance.memory_limit_mb = 100
        errors = config.validate()
        assert any("memory_limit_mb" in err for err in errors)

    def test_invalid_log_level(self):
        """Test invalid log level."""
        config = Config()
        config.logging.level = "INVALID"
        errors = config.validate()
        assert any("level" in err for err in errors)

    def test_invalid_log_format(self):
        """Test invalid log format."""
        config = Config()
        config.logging.format = "xml"
        errors = config.validate()
        assert any("format" in err for err in errors)

    def test_empty_project_name(self):
        """Test empty project name."""
        config = Config()
        config.project.name = ""
        errors = config.validate()
        assert any("name" in err for err in errors)

    def test_empty_language(self):
        """Test empty language."""
        config = Config()
        config.project.language = ""
        errors = config.validate()
        assert any("language" in err for err in errors)
