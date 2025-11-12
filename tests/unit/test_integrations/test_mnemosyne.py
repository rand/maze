"""
Tests for mnemosyne integration.
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from maze.integrations.mnemosyne import (
    EvolutionStats,
    GenerationContext,
    LearningTask,
    MnemosyneIntegration,
    OrchestrationResult,
    ScoredPattern,
)
from maze.learning.pattern_mining import SemanticPattern, SyntacticPattern, TypePattern


class TestMnemosyneIntegration:
    """Test MnemosyneIntegration class."""

    @pytest.fixture
    def local_cache_path(self, tmp_path):
        """Provide temporary cache path."""
        return tmp_path / "pattern_cache.jsonl"

    @pytest.fixture
    def integration_local_cache(self, local_cache_path):
        """Integration with local cache (no mnemosyne)."""
        with patch.object(MnemosyneIntegration, "_ensure_mnemosyne_available", return_value=False):
            return MnemosyneIntegration(
                enable_orchestration=False, local_cache_path=local_cache_path
            )

    @pytest.fixture
    def integration_with_mnemosyne(self, local_cache_path):
        """Integration with mocked mnemosyne."""
        with patch.object(MnemosyneIntegration, "_ensure_mnemosyne_available", return_value=True):
            return MnemosyneIntegration(
                enable_orchestration=False, local_cache_path=local_cache_path
            )

    def test_init_local_cache(self, integration_local_cache, local_cache_path):
        """Test initialization with local cache."""
        assert integration_local_cache.use_local_cache is True
        assert integration_local_cache.local_cache_path == local_cache_path
        assert integration_local_cache.stats["patterns_stored"] == 0

    def test_init_with_mnemosyne(self, integration_with_mnemosyne):
        """Test initialization with mnemosyne available."""
        assert integration_with_mnemosyne.use_local_cache is False

    def test_store_pattern_syntactic_local(self, integration_local_cache):
        """Test storing syntactic pattern in local cache."""
        pattern = SyntacticPattern(
            pattern_type="function",
            template="def foo(arg1, arg2): ...",
            frequency=5,
            examples=["def add(x, y): return x + y"],
            context={"args_count": 2},
        )

        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=8, tags=["math", "function"]
        )

        assert integration_local_cache.stats["patterns_stored"] == 1
        assert integration_local_cache.stats["local_cache_fallbacks"] == 1
        assert len(integration_local_cache.pattern_cache) == 1

        # Verify pattern stored correctly
        stored = list(integration_local_cache.pattern_cache.values())[0]
        assert stored.pattern_type == "syntactic"
        assert stored.namespace == "project:test"
        assert stored.importance == 8
        assert "math" in stored.tags

    def test_store_pattern_type_local(self, integration_local_cache):
        """Test storing type pattern in local cache."""
        pattern = TypePattern(
            signature="int",
            common_usages=["x: int", "count: int"],
            frequency=10,
            generic_variants=["T"],
        )

        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=7
        )

        assert integration_local_cache.stats["patterns_stored"] == 1
        stored = list(integration_local_cache.pattern_cache.values())[0]
        assert stored.pattern_type == "type"

    def test_store_pattern_semantic_local(self, integration_local_cache):
        """Test storing semantic pattern in local cache."""
        pattern = SemanticPattern(
            intent="error_handling",
            structure="try-except",
            implementations=["try:\n    op()\nexcept Exception:\n    handle()"],
            frequency=3,
        )

        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=9
        )

        assert integration_local_cache.stats["patterns_stored"] == 1
        stored = list(integration_local_cache.pattern_cache.values())[0]
        assert stored.pattern_type == "semantic"

    @patch("subprocess.run")
    def test_store_pattern_with_mnemosyne(self, mock_run, integration_with_mnemosyne):
        """Test storing pattern with mnemosyne CLI."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        pattern = SyntacticPattern(
            pattern_type="function", template="def foo(): ...", frequency=1, examples=[], context={}
        )

        integration_with_mnemosyne.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "mnemosyne" in call_args
        assert "remember" in call_args

    @patch("subprocess.run")
    def test_store_pattern_mnemosyne_fallback(self, mock_run, integration_with_mnemosyne):
        """Test fallback to local cache when mnemosyne fails."""
        mock_run.side_effect = subprocess.TimeoutExpired("mnemosyne", 1)

        pattern = SyntacticPattern(
            pattern_type="function", template="def foo(): ...", frequency=1, examples=[], context={}
        )

        integration_with_mnemosyne.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        # Should fallback to local cache
        assert integration_with_mnemosyne.use_local_cache is True
        assert integration_with_mnemosyne.stats["local_cache_fallbacks"] == 1

    def test_recall_patterns_local_cache(self, integration_local_cache):
        """Test recalling patterns from local cache."""
        # Store some patterns
        patterns = [
            SyntacticPattern("function", "def add(): ...", 1, [], {}),
            SyntacticPattern("class", "class Foo: ...", 1, [], {}),
            TypePattern("str", ["name: str"], 5, []),
        ]

        for i, pattern in enumerate(patterns):
            integration_local_cache.store_pattern(
                pattern=pattern, namespace="project:test", importance=5 + i
            )

        # Recall with context
        context = GenerationContext(
            language="python", task_description="add function implementation"
        )

        recalled = integration_local_cache.recall_patterns(
            context=context, namespace="project:test", limit=10
        )

        assert len(recalled) > 0
        assert all(isinstance(p, ScoredPattern) for p in recalled)
        assert all(p.score > 0 for p in recalled)

    def test_recall_patterns_relevance_scoring(self, integration_local_cache):
        """Test relevance scoring in pattern recall."""
        # Store pattern matching language
        pattern1 = SyntacticPattern("function", "def python_func(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern1, namespace="project:test", importance=5, tags=["python"]
        )

        # Store pattern not matching
        pattern2 = TypePattern("int", [], 1, [])
        integration_local_cache.store_pattern(
            pattern=pattern2, namespace="project:test", importance=5
        )

        context = GenerationContext(language="python", task_description="function implementation")

        recalled = integration_local_cache.recall_patterns(context=context, limit=10)

        # Python function pattern should score higher
        assert len(recalled) >= 1
        assert recalled[0].score > 0

    @patch("subprocess.run")
    def test_recall_patterns_with_mnemosyne(self, mock_run, integration_with_mnemosyne):
        """Test recalling patterns from mnemosyne."""
        # Mock mnemosyne response
        mock_memories = [
            {
                "id": "mem-1",
                "content": 'Pattern: syntactic | {"type": "syntactic", "pattern_type": "function", "template": "def foo(): ...", "frequency": 1, "examples": [], "context": {}}',
                "namespace": "project:test",
                "importance": 7,
                "tags": ["function"],
                "timestamp": 1234567890,
                "relevance": 0.8,
            }
        ]
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps(mock_memories))

        context = GenerationContext(language="python", task_description="function")

        recalled = integration_with_mnemosyne.recall_patterns(context=context, limit=10)

        assert len(recalled) == 1
        assert recalled[0].pattern.pattern_type == "syntactic"
        assert recalled[0].score > 0

    def test_recall_patterns_namespace_filter(self, integration_local_cache):
        """Test namespace filtering in recall."""
        # Store patterns in different namespaces
        pattern1 = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern1, namespace="project:app1", importance=5
        )

        pattern2 = SyntacticPattern("function", "def bar(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern2, namespace="project:app2", importance=5
        )

        context = GenerationContext(language="python", task_description="function")

        # Recall only from app1
        recalled = integration_local_cache.recall_patterns(
            context=context, namespace="project:app1", limit=10
        )

        assert all(p.pattern.namespace == "project:app1" for p in recalled)

    def test_update_pattern_score_success(self, integration_local_cache):
        """Test updating pattern score on success."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]
        stored = integration_local_cache.pattern_cache[pattern_id]

        # Update with success
        integration_local_cache.update_pattern_score(pattern_id, success=True)

        assert stored.recall_count == 1
        assert stored.success_count == 1
        assert stored.failure_count == 0

    def test_update_pattern_score_failure(self, integration_local_cache):
        """Test updating pattern score on failure."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]
        stored = integration_local_cache.pattern_cache[pattern_id]

        # Update with failure
        integration_local_cache.update_pattern_score(pattern_id, success=False)

        assert stored.recall_count == 1
        assert stored.success_count == 0
        assert stored.failure_count == 1

    def test_update_pattern_importance_adjustment(self, integration_local_cache):
        """Test importance adjustment based on success rate."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]
        stored = integration_local_cache.pattern_cache[pattern_id]

        # Record multiple successes
        for _ in range(5):
            integration_local_cache.update_pattern_score(pattern_id, success=True)

        # Importance should increase with high success rate
        assert stored.importance > 5

    def test_evolve_memories_local_cache(self, integration_local_cache):
        """Test memory evolution with local cache."""
        # Store some patterns
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        stats = integration_local_cache.evolve_memories()

        assert isinstance(stats, EvolutionStats)
        assert stats.total_patterns >= 0
        assert stats.execution_time_ms >= 0

    def test_evolve_memories_archival(self, integration_local_cache):
        """Test pattern archival based on low success rate."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]
        stored = integration_local_cache.pattern_cache[pattern_id]

        # Set old timestamp and low success rate
        import time

        stored.timestamp = time.time() - (31 * 86400)  # 31 days ago
        stored.recall_count = 10
        stored.success_count = 1  # 10% success rate

        stats = integration_local_cache.evolve_memories()

        # Pattern should be archived
        assert pattern_id not in integration_local_cache.pattern_cache

    @patch("subprocess.run")
    def test_evolve_memories_with_mnemosyne(self, mock_run, integration_with_mnemosyne):
        """Test memory evolution with mnemosyne."""
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        stats = integration_with_mnemosyne.evolve_memories()

        assert mock_run.called
        assert "evolve" in mock_run.call_args[0][0]

    def test_orchestrate_learning_disabled(self, integration_local_cache):
        """Test orchestration when disabled."""
        context = GenerationContext(language="python", task_description="test")
        task = LearningTask(task_type="pattern_discovery", context=context)

        result = integration_local_cache.orchestrate_learning(task)

        assert isinstance(result, OrchestrationResult)
        assert result.task == task
        assert len(result.new_patterns) == 0
        assert len(result.agent_trace) == 0

    def test_orchestrate_learning_enabled(self, local_cache_path):
        """Test orchestration when enabled."""
        with patch.object(MnemosyneIntegration, "_ensure_mnemosyne_available", return_value=False):
            integration = MnemosyneIntegration(
                enable_orchestration=True, local_cache_path=local_cache_path
            )

        context = GenerationContext(language="python", task_description="test")
        task = LearningTask(task_type="pattern_discovery", context=context)

        result = integration.orchestrate_learning(task)

        assert isinstance(result, OrchestrationResult)
        assert len(result.agent_trace) > 0

    def test_get_stats(self, integration_local_cache):
        """Test statistics retrieval."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        stats = integration_local_cache.get_stats()

        assert isinstance(stats, dict)
        assert stats["patterns_stored"] == 1
        assert stats["local_cache_fallbacks"] >= 1

    def test_pattern_persistence(self, integration_local_cache, local_cache_path):
        """Test pattern persistence to disk."""
        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        # Verify file written
        assert local_cache_path.exists()
        assert local_cache_path.stat().st_size > 0

        # Create new integration and verify pattern loaded
        with patch.object(MnemosyneIntegration, "_ensure_mnemosyne_available", return_value=False):
            new_integration = MnemosyneIntegration(
                enable_orchestration=False, local_cache_path=local_cache_path
            )

        assert len(new_integration.pattern_cache) == 1

    def test_performance_store_pattern(self, integration_local_cache):
        """Test store_pattern performance (<50ms)."""
        import time

        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})

        start = time.time()
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 50

    def test_performance_recall_patterns(self, integration_local_cache):
        """Test recall_patterns performance (<100ms)."""
        import time

        # Store some patterns
        for i in range(10):
            pattern = SyntacticPattern("function", f"def func{i}(): ...", 1, [], {})
            integration_local_cache.store_pattern(
                pattern=pattern, namespace="project:test", importance=5
            )

        context = GenerationContext(language="python", task_description="function")

        start = time.time()
        integration_local_cache.recall_patterns(context=context, limit=10)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 100

    def test_performance_update_pattern_score(self, integration_local_cache):
        """Test update_pattern_score performance (<20ms)."""
        import time

        pattern = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=5
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]

        start = time.time()
        integration_local_cache.update_pattern_score(pattern_id, success=True)
        elapsed_ms = (time.time() - start) * 1000

        assert elapsed_ms < 20

    def test_error_handling_corrupted_cache(self, tmp_path):
        """Test error handling for corrupted cache file."""
        cache_path = tmp_path / "corrupted.jsonl"
        cache_path.write_text("invalid json\n{not json either\n")

        with patch.object(MnemosyneIntegration, "_ensure_mnemosyne_available", return_value=False):
            integration = MnemosyneIntegration(
                enable_orchestration=False, local_cache_path=cache_path
            )

        # Should start with empty cache
        assert len(integration.pattern_cache) == 0

    def test_pattern_id_generation(self, integration_local_cache):
        """Test consistent pattern ID generation."""
        pattern1 = SyntacticPattern("function", "def foo(): ...", 1, [], {})
        pattern2 = SyntacticPattern("function", "def foo(): ...", 1, [], {})

        integration_local_cache.store_pattern(
            pattern=pattern1, namespace="project:test", importance=5
        )

        id1 = list(integration_local_cache.pattern_cache.keys())[0]

        integration_local_cache.store_pattern(
            pattern=pattern2, namespace="project:test", importance=5
        )

        # Same pattern should generate same ID
        assert len(integration_local_cache.pattern_cache) == 1

    def test_recall_limit_respected(self, integration_local_cache):
        """Test that recall limit is respected."""
        # Store many patterns
        for i in range(20):
            pattern = SyntacticPattern("function", f"def func{i}(): ...", 1, [], {})
            integration_local_cache.store_pattern(
                pattern=pattern, namespace="project:test", importance=5
            )

        context = GenerationContext(language="python", task_description="function")

        recalled = integration_local_cache.recall_patterns(context=context, limit=5)

        assert len(recalled) <= 5

    def test_score_calculation_components(self, integration_local_cache):
        """Test score calculation components."""
        # Pattern with high importance and success rate
        pattern = SyntacticPattern("function", "def python_func(): ...", 1, [], {})
        integration_local_cache.store_pattern(
            pattern=pattern, namespace="project:test", importance=9, tags=["python"]
        )

        pattern_id = list(integration_local_cache.pattern_cache.keys())[0]
        stored = integration_local_cache.pattern_cache[pattern_id]

        # Simulate high success rate
        for _ in range(5):
            integration_local_cache.update_pattern_score(pattern_id, success=True)

        context = GenerationContext(
            language="python", task_description="python function implementation"
        )

        recalled = integration_local_cache.recall_patterns(context=context, limit=10)

        # Should have high score due to language match + success rate + importance
        assert len(recalled) > 0
        assert recalled[0].score > 5  # Combined score
