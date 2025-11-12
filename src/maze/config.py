"""Configuration system for Maze.

Manages project and global configuration with TOML files.
Configuration hierarchy: CLI args > Project config > Global config

Performance targets:
- Config loading: <50ms
- Config merging: <10ms
- Config validation: <10ms
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore


@dataclass
class ProjectConfig:
    """Project-level configuration."""

    name: str = "maze-project"
    path: Path = field(default_factory=Path.cwd)
    language: str = "typescript"
    source_paths: list[str] = field(default_factory=lambda: ["src/"])
    test_patterns: list[str] = field(default_factory=lambda: ["**/*test.ts", "**/*.test.ts"])


@dataclass
class IndexerConfig:
    """Indexer configuration."""

    enabled: bool = True
    cache_enabled: bool = True
    cache_path: Path = field(default_factory=lambda: Path(".maze/cache"))
    incremental: bool = True
    max_file_size_kb: int = 1024  # 1MB
    excluded_dirs: list[str] = field(
        default_factory=lambda: ["node_modules", ".git", "dist", "build"]
    )


@dataclass
class GenerationConfig:
    """Code generation configuration."""

    provider: str = "modal"  # Default to Modal (only provider with grammar support)
    model: str = "qwen2.5-coder-32b"
    temperature: float = 0.7
    max_tokens: int = 2048
    timeout_seconds: int = 30
    retry_attempts: int = 3


@dataclass
class ConstraintConfig:
    """Constraint system configuration."""

    syntactic_enabled: bool = True
    type_enabled: bool = True
    semantic_enabled: bool = False
    contextual_enabled: bool = True
    type_search_depth: int = 5
    adaptive_weighting: bool = True


@dataclass
class ValidationConfig:
    """Validation configuration."""

    syntax_check: bool = True
    type_check: bool = True
    run_tests: bool = False
    lint: bool = True
    timeout_seconds: int = 60


@dataclass
class PerformanceConfig:
    """Performance tuning configuration."""

    cache_size: int = 100_000
    parallel_indexing: bool = True
    max_workers: int = field(default_factory=lambda: os.cpu_count() or 4)
    enable_profiling: bool = False
    memory_limit_mb: int = 2048


@dataclass
class LoggingConfig:
    """Logging configuration."""

    level: str = "INFO"
    format: str = "json"
    output: str = "stdout"
    log_file: Path | None = None
    metrics_enabled: bool = True


@dataclass
class Config:
    """Complete Maze configuration.

    Supports hierarchical loading:
    1. Global config: ~/.config/maze/config.toml
    2. Project config: .maze/config.toml
    3. CLI args (via merge)
    """

    project: ProjectConfig = field(default_factory=ProjectConfig)
    indexer: IndexerConfig = field(default_factory=IndexerConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)
    constraints: ConstraintConfig = field(default_factory=ConstraintConfig)
    validation: ValidationConfig = field(default_factory=ValidationConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, project_path: Path | None = None) -> Config:
        """Load configuration from global and project configs.

        Args:
            project_path: Path to project directory (looks for .maze/config.toml)

        Returns:
            Merged configuration (global < project)
        """
        config = cls()

        # Load global config
        global_config_path = Path.home() / ".config" / "maze" / "config.toml"
        if global_config_path.exists():
            config = config.merge(cls._load_from_file(global_config_path))

        # Load project config
        if project_path is not None:
            project_config_path = project_path / ".maze" / "config.toml"
            if project_config_path.exists():
                config = config.merge(cls._load_from_file(project_config_path))

        return config

    @classmethod
    def _load_from_file(cls, path: Path) -> Config:
        """Load configuration from TOML file."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create Config from dictionary."""
        return cls(
            project=cls._dict_to_dataclass(ProjectConfig, data.get("project", {})),
            indexer=cls._dict_to_dataclass(IndexerConfig, data.get("indexer", {})),
            generation=cls._dict_to_dataclass(GenerationConfig, data.get("generation", {})),
            constraints=cls._dict_to_dataclass(ConstraintConfig, data.get("constraints", {})),
            validation=cls._dict_to_dataclass(ValidationConfig, data.get("validation", {})),
            performance=cls._dict_to_dataclass(PerformanceConfig, data.get("performance", {})),
            logging=cls._dict_to_dataclass(LoggingConfig, data.get("logging", {})),
        )

    @staticmethod
    def _dict_to_dataclass(cls_type: type, data: dict[str, Any]) -> Any:
        """Convert dict to dataclass, handling Path conversion."""
        kwargs = {}
        for key, value in data.items():
            # Convert string paths to Path objects
            if key.endswith("_path") or key.endswith("_paths"):
                if isinstance(value, str):
                    value = Path(value)
                elif isinstance(value, list):
                    value = [Path(v) if isinstance(v, str) else v for v in value]
            kwargs[key] = value

        return cls_type(**kwargs)

    def save(self, path: Path) -> None:
        """Save configuration to TOML file.

        Args:
            path: Path to save config file
        """
        import tomli_w

        path.parent.mkdir(parents=True, exist_ok=True)

        data = self.to_dict()

        with open(path, "wb") as f:
            tomli_w.dump(data, f)

    def to_dict(self) -> dict[str, Any]:
        """Convert Config to dictionary for serialization."""
        return {
            "project": self._dataclass_to_dict(self.project),
            "indexer": self._dataclass_to_dict(self.indexer),
            "generation": self._dataclass_to_dict(self.generation),
            "constraints": self._dataclass_to_dict(self.constraints),
            "validation": self._dataclass_to_dict(self.validation),
            "performance": self._dataclass_to_dict(self.performance),
            "logging": self._dataclass_to_dict(self.logging),
        }

    @staticmethod
    def _dataclass_to_dict(obj: Any) -> dict[str, Any]:
        """Convert dataclass to dict, handling Path serialization."""
        result = {}
        for key, value in obj.__dict__.items():
            # Skip None values (TOML doesn't serialize None)
            if value is None:
                continue
            if isinstance(value, Path):
                result[key] = str(value)
            elif isinstance(value, list):
                result[key] = [str(v) if isinstance(v, Path) else v for v in value]
            else:
                result[key] = value
        return result

    def merge(self, other: Config) -> Config:
        """Merge another config into this one.

        Args:
            other: Config to merge (takes priority)

        Returns:
            New merged Config instance
        """
        return Config(
            project=self._merge_dataclass(self.project, other.project),
            indexer=self._merge_dataclass(self.indexer, other.indexer),
            generation=self._merge_dataclass(self.generation, other.generation),
            constraints=self._merge_dataclass(self.constraints, other.constraints),
            validation=self._merge_dataclass(self.validation, other.validation),
            performance=self._merge_dataclass(self.performance, other.performance),
            logging=self._merge_dataclass(self.logging, other.logging),
        )

    @staticmethod
    def _merge_dataclass(base: Any, override: Any) -> Any:
        """Merge two dataclass instances, preferring override values."""
        base_dict = base.__dict__.copy()
        override_dict = override.__dict__

        # Update base with non-default override values
        base_defaults = {k: v for k, v in base.__class__.__dict__.items() if not k.startswith("_")}

        for key, value in override_dict.items():
            # Only override if value is not default
            if key in base_defaults:
                default_val = base_defaults.get(key)
                if value != default_val:
                    base_dict[key] = value
            else:
                base_dict[key] = value

        return base.__class__(**base_dict)

    def validate(self) -> list[str]:
        """Validate configuration.

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Project validation
        if not self.project.name:
            errors.append("project.name cannot be empty")

        if not self.project.language:
            errors.append("project.language cannot be empty")

        # Generation validation
        if self.generation.temperature < 0 or self.generation.temperature > 2:
            errors.append("generation.temperature must be between 0 and 2")

        if self.generation.max_tokens < 1:
            errors.append("generation.max_tokens must be positive")

        if self.generation.timeout_seconds < 1:
            errors.append("generation.timeout_seconds must be positive")

        # Constraint validation
        if self.constraints.type_search_depth < 1:
            errors.append("constraints.type_search_depth must be positive")

        # Performance validation
        if self.performance.cache_size < 1:
            errors.append("performance.cache_size must be positive")

        if self.performance.max_workers < 1:
            errors.append("performance.max_workers must be positive")

        if self.performance.memory_limit_mb < 256:
            errors.append("performance.memory_limit_mb must be at least 256 MB")

        # Logging validation
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_log_levels:
            errors.append(
                f"logging.level must be one of {valid_log_levels}, got {self.logging.level}"
            )

        valid_log_formats = ["json", "text"]
        if self.logging.format not in valid_log_formats:
            errors.append(
                f"logging.format must be one of {valid_log_formats}, got {self.logging.format}"
            )

        return errors
