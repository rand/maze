"""Tests for grammar template loading in pipeline.

Test coverage target: 90%
"""


from maze.config import Config
from maze.core.pipeline import Pipeline


class TestGrammarLoading:
    """Tests for grammar template loading."""

    def test_load_typescript_function_grammar(self):
        """Test loading TypeScript function grammar."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        grammar = pipeline._synthesize_constraints("Create a function", None)

        assert len(grammar) > 0
        assert "function" in grammar.lower()

    def test_load_typescript_interface_grammar(self):
        """Test loading TypeScript interface grammar."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        grammar = pipeline._synthesize_constraints("Create an interface User", None)

        assert len(grammar) > 0
        assert "interface" in grammar.lower()

    def test_grammar_caching(self):
        """Test grammar is cached after first load."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        # First load
        grammar1 = pipeline._synthesize_constraints("Create a function", None)
        assert pipeline.metrics.get_cache_hit_rate("grammar") == 0.0

        # Second load (should hit cache)
        grammar2 = pipeline._synthesize_constraints("Create another function", None)
        assert grammar1 == grammar2
        assert pipeline.metrics.get_cache_hit_rate("grammar") == 0.5

    def test_grammar_cache_metrics(self):
        """Test grammar cache metrics tracking."""
        config = Config()
        config.project.language = "typescript"
        pipeline = Pipeline(config)

        # First load - cache miss
        pipeline._synthesize_constraints("Create a function", None)

        # Second load - cache hit
        pipeline._synthesize_constraints("Create a function", None)

        summary = pipeline.metrics.summary()
        assert "cache_hit_rates" in summary
        assert summary["cache_hit_rates"]["grammar"] == 0.5

    def test_syntactic_disabled_returns_empty(self):
        """Test empty grammar when syntactic constraints disabled."""
        config = Config()
        config.project.language = "typescript"
        config.constraints.syntactic_enabled = False

        pipeline = Pipeline(config)
        grammar = pipeline._synthesize_constraints("Create a function", None)

        assert grammar == ""

    def test_unsupported_language_returns_empty(self):
        """Test empty grammar for unsupported languages."""
        config = Config()
        config.project.language = "unsupported"

        pipeline = Pipeline(config)
        grammar = pipeline._synthesize_constraints("Create a function", None)

        assert grammar == ""
