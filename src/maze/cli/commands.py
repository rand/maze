"""CLI command implementations."""

import argparse
import json
import sys
from pathlib import Path

from maze.cli.base import Command
from maze.config import Config


class InitCommand(Command):
    """Initialize a new Maze project."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup init command arguments."""
        parser.add_argument(
            "--language",
            "-l",
            default="typescript",
            choices=["typescript", "python", "rust", "go", "zig"],
            help="Project language (default: typescript)",
        )
        parser.add_argument("--name", "-n", help="Project name (default: directory name)")

    def execute(self, args: argparse.Namespace) -> int:
        """Initialize project."""
        project_path = Path.cwd()
        maze_dir = project_path / ".maze"

        if maze_dir.exists():
            print(f"Error: Maze project already initialized at {project_path}")
            return 1

        # Create .maze directory
        maze_dir.mkdir(parents=True)
        print(f"✓ Created {maze_dir}")

        # Create config
        config = Config()
        config.project.name = args.name or project_path.name
        config.project.language = args.language
        config.project.path = project_path

        config_path = maze_dir / "config.toml"
        config.save(config_path)
        print(f"✓ Created {config_path}")

        # Create cache directory
        cache_dir = maze_dir / "cache"
        cache_dir.mkdir()
        print(f"✓ Created {cache_dir}")

        print(f"\n✓ Initialized Maze project: {config.project.name}")
        print(f"  Language: {config.project.language}")
        print(f"  Path: {project_path}")

        return 0


class ConfigCommand(Command):
    """Manage configuration."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup config command arguments."""
        subparsers = parser.add_subparsers(dest="config_action", required=True)

        # config get
        get_parser = subparsers.add_parser("get", help="Get configuration value")
        get_parser.add_argument("key", nargs="?", help="Config key (e.g., project.name)")

        # config set
        set_parser = subparsers.add_parser("set", help="Set configuration value")
        set_parser.add_argument("key", help="Config key")
        set_parser.add_argument("value", help="Config value")

        # config list
        subparsers.add_parser("list", help="List all configuration")

    def execute(self, args: argparse.Namespace) -> int:
        """Execute config command."""
        if args.config_action == "list":
            return self._list_config()
        elif args.config_action == "get":
            return self._get_config(args.key)
        elif args.config_action == "set":
            return self._set_config(args.key, args.value)
        return 1

    def _list_config(self) -> int:
        """List all configuration."""
        config_dict = self.config.to_dict()
        print(json.dumps(config_dict, indent=2))
        return 0

    def _get_config(self, key: str | None) -> int:
        """Get configuration value."""
        if key is None:
            return self._list_config()

        parts = key.split(".")
        value = self.config.to_dict()

        try:
            for part in parts:
                value = value[part]
            print(value)
            return 0
        except (KeyError, TypeError):
            print(f"Error: Configuration key '{key}' not found", file=sys.stderr)
            return 1

    def _set_config(self, key: str, value: str) -> int:
        """Set configuration value."""
        # Find config file
        config_path = Path.cwd() / ".maze" / "config.toml"
        if not config_path.exists():
            print("Error: Not in a Maze project (no .maze/config.toml)", file=sys.stderr)
            return 1

        # Parse value (handle numbers and booleans)
        parsed_value = value
        if value.lower() == "true":
            parsed_value = True
        elif value.lower() == "false":
            parsed_value = False
        elif value.isdigit():
            parsed_value = int(value)
        elif value.replace(".", "", 1).isdigit():
            parsed_value = float(value)

        # Update config
        parts = key.split(".")
        config_dict = self.config.to_dict()

        # Navigate to parent
        current = config_dict
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Set value
        current[parts[-1]] = parsed_value

        # Save
        updated_config = Config.from_dict(config_dict)
        updated_config.save(config_path)

        print(f"✓ Set {key} = {parsed_value}")
        return 0


class IndexCommand(Command):
    """Index project for code context."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup index command arguments."""
        parser.add_argument("path", nargs="?", type=Path, default=Path.cwd(), help="Path to index")
        parser.add_argument(
            "--output", "-o", type=Path, help="Output file for index results (JSON)"
        )
        parser.add_argument(
            "--watch", action="store_true", help="Watch for changes (not implemented)"
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute index command."""
        print(f"Indexing {args.path}...")

        pipeline = self.get_pipeline()

        try:
            result = pipeline.index_project(args.path)

            print(f"✓ Indexed {len(result.files_processed)} files")
            print(f"  Symbols: {len(result.symbols)}")
            print(f"  Tests: {len(result.tests)}")
            print(f"  Duration: {result.duration_ms:.0f}ms")

            if result.errors:
                print(f"\n⚠ Warnings: {len(result.errors)}")
                for error in result.errors[:5]:
                    print(f"  - {error}")

            # Save to file if requested
            if args.output:
                output_data = {
                    "files": result.files_processed,
                    "symbols": [s.to_dict() for s in result.symbols],
                    "tests": [
                        {"name": t.name, "kind": t.kind, "file": t.file_path} for t in result.tests
                    ],
                    "duration_ms": result.duration_ms,
                }
                args.output.write_text(json.dumps(output_data, indent=2))
                print(f"\n✓ Saved index to {args.output}")

            return 0

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


class GenerateCommand(Command):
    """Generate code from prompt."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup generate command arguments."""
        parser.add_argument("prompt", help="Generation prompt")
        parser.add_argument("--language", "-l", help="Target language (default: from config)")
        parser.add_argument("--provider", "-p", help="LLM provider (default: from config)")
        parser.add_argument("--output", "-o", type=Path, help="Output file")
        parser.add_argument(
            "--constraints",
            "-c",
            nargs="+",
            choices=["syntactic", "type", "semantic", "contextual"],
            help="Constraint types to apply",
        )

    def execute(self, args: argparse.Namespace) -> int:
        """Execute generate command."""
        print(f"Generating code for: {args.prompt}")

        # Override config if specified
        if args.language:
            self.config.project.language = args.language
        if args.provider:
            self.config.generation.provider = args.provider

        pipeline = self.get_pipeline()

        try:
            result = pipeline.run(args.prompt)

            if result.success:
                print(f"\n✓ Generation successful ({result.total_duration_ms:.0f}ms)")

                if args.output:
                    args.output.write_text(result.code)
                    print(f"✓ Saved to {args.output}")
                else:
                    print("\n" + "=" * 60)
                    print(result.code)
                    print("=" * 60)

                return 0
            else:
                print("\n✗ Generation failed", file=sys.stderr)
                for error in result.errors:
                    print(f"  - {error}", file=sys.stderr)
                return 1

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


class ValidateCommand(Command):
    """Validate code file."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup validate command arguments."""
        parser.add_argument("file", type=Path, help="File to validate")
        parser.add_argument("--run-tests", action="store_true", help="Run tests")
        parser.add_argument("--type-check", action="store_true", help="Run type checking")
        parser.add_argument("--fix", action="store_true", help="Attempt to fix errors")

    def execute(self, args: argparse.Namespace) -> int:
        """Execute validate command."""
        if not args.file.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            return 1

        print(f"Validating {args.file}...")

        code = args.file.read_text()
        pipeline = self.get_pipeline()

        try:
            result = pipeline.validate(code)

            if result.success:
                print("✓ Validation passed")
                print(f"  Duration: {result.validation_time_ms:.0f}ms")
                print(f"  Stages passed: {', '.join(result.stages_passed)}")
                return 0
            else:
                print("✗ Validation failed")
                print(f"  Stages failed: {', '.join(result.stages_failed)}")
                print(f"\nErrors ({len(result.diagnostics)}):")
                for diag in result.diagnostics[:10]:
                    print(f"  Line {diag.line}: {diag.message}")

                if args.fix:
                    print("\nAttempting to fix...")
                    repair_result = pipeline.repair(code, result.diagnostics, "fix errors", None)
                    if repair_result.success:
                        args.file.write_text(repair_result.repaired_code)
                        print(f"✓ Fixed and saved to {args.file}")
                        return 0
                    else:
                        print("✗ Could not fix all errors")
                        return 1

                return 1

        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1


class StatsCommand(Command):
    """Show project statistics."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup stats command arguments."""
        parser.add_argument(
            "--show-performance", action="store_true", help="Show performance metrics"
        )
        parser.add_argument("--show-cache", action="store_true", help="Show cache statistics")
        parser.add_argument("--show-patterns", action="store_true", help="Show learned patterns")

    def execute(self, args: argparse.Namespace) -> int:
        """Execute stats command."""
        pipeline = self.get_pipeline()

        # Get metrics summary
        summary = pipeline.metrics.summary()

        print("Maze Statistics")
        print("=" * 60)

        # Show latency stats
        if args.show_performance or not any([args.show_cache, args.show_patterns]):
            print("\nPerformance:")
            for op, stats in summary["latencies"].items():
                if stats:
                    print(f"  {op}:")
                    print(f"    Mean: {stats['mean']:.2f}ms")
                    print(f"    P95: {stats['p95']:.2f}ms")
                    print(f"    P99: {stats['p99']:.2f}ms")

        # Show cache stats
        if args.show_cache or not any([args.show_performance, args.show_patterns]):
            print("\nCache Hit Rates:")
            for cache, rate in summary["cache_hit_rates"].items():
                print(f"  {cache}: {rate:.1%}")

        # Show error stats
        if summary["errors"]:
            print("\nErrors:")
            for error_type, count in summary["errors"].items():
                print(f"  {error_type}: {count}")

        return 0


class DebugCommand(Command):
    """Debug tools and diagnostics."""

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup debug command arguments."""
        parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
        parser.add_argument("--profile", action="store_true", help="Enable profiling")

    def execute(self, args: argparse.Namespace) -> int:
        """Execute debug command."""
        print("Maze Debug Information")
        print("=" * 60)

        print("\nConfig:")
        print(f"  Project: {self.config.project.name}")
        print(f"  Language: {self.config.project.language}")
        print(f"  Provider: {self.config.generation.provider}")

        print("\nPaths:")
        print(f"  Project: {self.config.project.path}")
        print(f"  Cache: {self.config.indexer.cache_path}")

        if args.verbose:
            print("\nFull Configuration:")
            config_dict = self.config.to_dict()
            print(json.dumps(config_dict, indent=2))

        if args.profile:
            print("\nProfiling: Enabled")
            self.config.performance.enable_profiling = True

        return 0
