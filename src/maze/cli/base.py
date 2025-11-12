"""Base command interface for Maze CLI."""

import argparse
from abc import ABC, abstractmethod

from maze.config import Config
from maze.core.pipeline import Pipeline


class Command(ABC):
    """Abstract base class for CLI commands."""

    def __init__(self, config: Config | None = None):
        """Initialize command.

        Args:
            config: Maze configuration (loads default if None)
        """
        self.config = config or Config.load()
        self.pipeline: Pipeline | None = None

    @abstractmethod
    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """Setup command-specific arguments.

        Args:
            parser: Argument parser to configure
        """
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> int:
        """Execute the command.

        Args:
            args: Parsed command-line arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass

    def get_pipeline(self) -> Pipeline:
        """Get or create pipeline instance.

        Returns:
            Pipeline instance
        """
        if self.pipeline is None:
            self.pipeline = Pipeline(self.config)
        return self.pipeline
