"""Tests for CLI main entry point.

Test coverage target: 80%
"""

import sys
from unittest.mock import Mock, patch

import pytest

from maze.cli.main import CLI, main


class TestCLI:
    """Tests for CLI class."""

    def test_cli_initialization(self):
        """Test CLI initializes correctly."""
        cli = CLI()
        
        assert cli.config is None
        assert len(cli.commands) == 7
        assert "init" in cli.commands
        assert "generate" in cli.commands

    def test_create_parser(self):
        """Test parser creation."""
        cli = CLI()
        parser = cli.create_parser()
        
        assert parser is not None
        assert parser.prog == "maze"

    def test_run_init_command(self):
        """Test running init command."""
        cli = CLI()
        
        with patch("maze.cli.commands.InitCommand.execute") as mock_execute:
            mock_execute.return_value = 0
            
            result = cli.run(["init", "--language", "python"])
            
            assert result == 0
            mock_execute.assert_called_once()

    def test_run_config_list(self):
        """Test running config list command."""
        cli = CLI()
        
        with patch("maze.cli.commands.ConfigCommand.execute") as mock_execute:
            mock_execute.return_value = 0
            
            result = cli.run(["config", "list"])
            
            assert result == 0

    def test_run_unknown_command(self):
        """Test running unknown command."""
        cli = CLI()
        
        with pytest.raises(SystemExit):
            cli.run(["unknown-command"])

    def test_run_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        cli = CLI()
        
        with patch("maze.cli.commands.InitCommand.execute") as mock_execute:
            mock_execute.side_effect = KeyboardInterrupt()
            
            result = cli.run(["init"])
            
            assert result == 130

    def test_run_exception_handling(self):
        """Test exception handling."""
        cli = CLI()
        
        with patch("maze.cli.commands.InitCommand.execute") as mock_execute:
            mock_execute.side_effect = Exception("Test error")
            
            result = cli.run(["init"])
            
            assert result == 1


class TestMainEntry:
    """Tests for main entry point."""

    def test_main_function(self):
        """Test main function."""
        with patch("maze.cli.main.CLI.run") as mock_run:
            mock_run.return_value = 0
            
            result = main()
            
            assert result == 0

    def test_main_with_args(self):
        """Test main with specific args."""
        with patch.object(sys, "argv", ["maze", "debug"]):
            with patch("maze.cli.commands.DebugCommand.execute") as mock_execute:
                mock_execute.return_value = 0
                
                result = main()
                
                assert result == 0


class TestCLICommands:
    """Integration tests for CLI command parsing."""

    def test_parse_init_command(self):
        """Test parsing init command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["init", "--language", "rust"])
        
        assert args.command == "init"
        assert args.language == "rust"

    def test_parse_config_get_command(self):
        """Test parsing config get command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["config", "get", "project.name"])
        
        assert args.command == "config"
        assert args.config_action == "get"
        assert args.key == "project.name"

    def test_parse_config_set_command(self):
        """Test parsing config set command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["config", "set", "generation.temperature", "0.8"])
        
        assert args.command == "config"
        assert args.config_action == "set"
        assert args.key == "generation.temperature"
        assert args.value == "0.8"

    def test_parse_index_command(self):
        """Test parsing index command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["index", "/path/to/project"])
        
        assert args.command == "index"
        assert str(args.path) == "/path/to/project"

    def test_parse_generate_command(self):
        """Test parsing generate command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args([
            "generate",
            "Create a function",
            "--language",
            "python",
            "--provider",
            "openai",
        ])
        
        assert args.command == "generate"
        assert args.prompt == "Create a function"
        assert args.language == "python"
        assert args.provider == "openai"

    def test_parse_validate_command(self):
        """Test parsing validate command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["validate", "test.ts", "--run-tests", "--fix"])
        
        assert args.command == "validate"
        assert str(args.file) == "test.ts"
        assert args.run_tests is True
        assert args.fix is True

    def test_parse_stats_command(self):
        """Test parsing stats command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["stats", "--show-performance", "--show-cache"])
        
        assert args.command == "stats"
        assert args.show_performance is True
        assert args.show_cache is True

    def test_parse_debug_command(self):
        """Test parsing debug command."""
        cli = CLI()
        parser = cli.create_parser()
        
        args = parser.parse_args(["debug", "--verbose", "--profile"])
        
        assert args.command == "debug"
        assert args.verbose is True
        assert args.profile is True


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_missing_required_argument(self):
        """Test missing required argument."""
        cli = CLI()
        parser = cli.create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["config", "set", "key"])  # Missing value

    def test_invalid_choice(self):
        """Test invalid choice for argument."""
        cli = CLI()
        parser = cli.create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(["init", "--language", "invalid"])

    def test_no_command_specified(self):
        """Test no command specified."""
        cli = CLI()
        parser = cli.create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args([])
