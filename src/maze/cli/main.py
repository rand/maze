"""Main CLI entry point for Maze."""

import argparse
import sys

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


class CLI:
    """Maze command-line interface."""

    def __init__(self, config: Config | None = None):
        """Initialize CLI.

        Args:
            config: Maze configuration (loads default if None)
        """
        self.config = config
        self.commands = {
            "init": InitCommand,
            "config": ConfigCommand,
            "index": IndexCommand,
            "generate": GenerateCommand,
            "validate": ValidateCommand,
            "stats": StatsCommand,
            "debug": DebugCommand,
        }

    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all commands.

        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            prog="maze",
            description="Maze - Adaptive Constrained Code Generation",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest="command",
            title="commands",
            description="Available commands",
            required=True,
        )

        # Add init command
        init_parser = subparsers.add_parser("init", help="Initialize a new Maze project")
        InitCommand().setup_parser(init_parser)

        # Add config command
        config_parser = subparsers.add_parser("config", help="Manage configuration")
        ConfigCommand().setup_parser(config_parser)

        # Add index command
        index_parser = subparsers.add_parser("index", help="Index project for code context")
        IndexCommand().setup_parser(index_parser)

        # Add generate command
        generate_parser = subparsers.add_parser("generate", help="Generate code from prompt")
        GenerateCommand().setup_parser(generate_parser)

        # Add validate command
        validate_parser = subparsers.add_parser("validate", help="Validate code file")
        ValidateCommand().setup_parser(validate_parser)

        # Add stats command
        stats_parser = subparsers.add_parser("stats", help="Show project statistics")
        StatsCommand().setup_parser(stats_parser)

        # Add debug command
        debug_parser = subparsers.add_parser("debug", help="Debug tools and diagnostics")
        DebugCommand().setup_parser(debug_parser)

        return parser

    def run(self, args: list[str] | None = None) -> int:
        """Run CLI with given arguments.

        Args:
            args: Command-line arguments (uses sys.argv if None)

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        # Get command class
        command_class = self.commands.get(parsed_args.command)
        if command_class is None:
            print(f"Error: Unknown command '{parsed_args.command}'", file=sys.stderr)
            return 1

        # Execute command
        try:
            command = command_class(self.config)
            return command.execute(parsed_args)
        except KeyboardInterrupt:
            print("\nInterrupted", file=sys.stderr)
            return 130
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            if "--verbose" in sys.argv or "-v" in sys.argv:
                import traceback

                traceback.print_exc()
            return 1


def main() -> int:
    """Main entry point for maze CLI.

    Returns:
        Exit code
    """
    cli = CLI()
    return cli.run()


if __name__ == "__main__":
    sys.exit(main())
