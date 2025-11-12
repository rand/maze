"""
Tests for project adaptation manager.
"""

from pathlib import Path

import pytest

from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    Feedback,
    GenerationResult,
    ValidationResult,
)
from maze.learning.pattern_mining import (
    PatternMiningEngine,
    PatternSet,
    SemanticPattern,
    SyntacticPattern,
)
from maze.learning.project_adaptation import (
    AdaptationStats,
    ConventionSet,
    ProjectAdaptationManager,
    ProjectProfile,
)


class TestProjectAdaptationManager:
    """Test ProjectAdaptationManager class."""

    @pytest.fixture
    def pattern_miner(self):
        """Create pattern mining engine."""
        return PatternMiningEngine(language="python", min_frequency=1)

    @pytest.fixture
    def learner(self):
        """Create constraint learning system."""
        return ConstraintLearningSystem(learning_rate=0.1)

    @pytest.fixture
    def manager(self, pattern_miner, learner):
        """Create project adaptation manager."""
        return ProjectAdaptationManager(
            pattern_miner=pattern_miner, learner=learner, convergence_threshold=0.9
        )

    @pytest.fixture
    def sample_project(self, tmp_path):
        """Create sample project directory."""
        project = tmp_path / "sample_project"
        project.mkdir()

        # Create some Python files
        (project / "main.py").write_text(
            """
def process_data(input_data):
    return input_data * 2

class DataProcessor:
    def transform(self, data):
        return data
"""
        )

        (project / "utils.py").write_text(
            """
def calculate_sum(a, b):
    return a + b

def format_output(value):
    return str(value)
"""
        )

        return project

    def test_init(self, manager, pattern_miner, learner):
        """Test initialization."""
        assert manager.pattern_miner == pattern_miner
        assert manager.learner == learner
        assert manager.convergence_threshold == 0.9
        assert len(manager.profiles) == 0

    def test_initialize_project(self, manager, sample_project):
        """Test project initialization."""
        profile = manager.initialize_project(sample_project, language="python")

        assert isinstance(profile, ProjectProfile)
        assert profile.project_name == "sample_project"
        assert profile.project_path == sample_project
        assert profile.language == "python"
        assert isinstance(profile.conventions, ConventionSet)
        assert isinstance(profile.patterns, PatternSet)
        assert profile.generation_count == 0

    def test_detect_language_python(self, manager, tmp_path):
        """Test language detection for Python."""
        project = tmp_path / "py_project"
        project.mkdir()
        (project / "file1.py").write_text("# Python")
        (project / "file2.py").write_text("# Python")

        language = manager._detect_language(project)
        assert language == "python"

    def test_detect_language_typescript(self, manager, tmp_path):
        """Test language detection for TypeScript."""
        project = tmp_path / "ts_project"
        project.mkdir()
        (project / "file1.ts").write_text("// TypeScript")
        (project / "file2.tsx").write_text("// TypeScript")

        language = manager._detect_language(project)
        assert language == "typescript"

    def test_detect_language_default(self, manager, tmp_path):
        """Test default language detection."""
        project = tmp_path / "unknown_project"
        project.mkdir()
        (project / "README.md").write_text("# Readme")

        language = manager._detect_language(project)
        assert language == "python"  # Default

    def test_extract_naming_conventions_snake_case(self, manager):
        """Test extraction of snake_case naming convention."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern("function", "def foo(): ...", 1, ["def process_data(): pass"], {}),
                SyntacticPattern(
                    "function", "def bar(): ...", 1, ["def calculate_sum(): pass"], {}
                ),
                SyntacticPattern(
                    "function", "def baz(): ...", 1, ["def format_output(): pass"], {}
                ),
            ],
            type_patterns=[],
            semantic=[],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=3,
        )

        conventions = manager._extract_naming_conventions(patterns)

        assert "function" in conventions
        assert conventions["function"] == "snake_case"

    def test_extract_naming_conventions_camel_case(self, manager):
        """Test extraction of camelCase naming convention."""
        patterns = PatternSet(
            language="typescript",
            syntactic=[
                SyntacticPattern(
                    "function", "function foo() {}", 1, ["function processData() {}"], {}
                ),
                SyntacticPattern(
                    "function", "function bar() {}", 1, ["function calculateSum() {}"], {}
                ),
                SyntacticPattern(
                    "function", "function baz() {}", 1, ["function formatOutput() {}"], {}
                ),
            ],
            type_patterns=[],
            semantic=[],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=3,
        )

        conventions = manager._extract_naming_conventions(patterns)

        assert "function" in conventions
        assert conventions["function"] == "camelCase"

    def test_extract_naming_conventions_pascal_case(self, manager):
        """Test extraction of PascalCase naming convention."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern("class", "class Foo: ...", 1, ["class DataProcessor: pass"], {}),
                SyntacticPattern("class", "class Bar: ...", 1, ["class OutputFormatter: pass"], {}),
            ],
            type_patterns=[],
            semantic=[],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=2,
        )

        conventions = manager._extract_naming_conventions(patterns)

        assert "class" in conventions
        assert conventions["class"] == "PascalCase"

    def test_is_camel_case(self, manager):
        """Test camelCase detection."""
        assert manager._is_camel_case("processData") is True
        assert manager._is_camel_case("calculateSum") is True
        assert manager._is_camel_case("ProcessData") is False  # PascalCase
        assert manager._is_camel_case("process_data") is False  # snake_case
        assert manager._is_camel_case("processdata") is False  # No capitals

    def test_is_snake_case(self, manager):
        """Test snake_case detection."""
        assert manager._is_snake_case("process_data") is True
        assert manager._is_snake_case("calculate_sum") is True
        assert manager._is_snake_case("processData") is False  # camelCase
        assert manager._is_snake_case("ProcessData") is False  # PascalCase
        assert manager._is_snake_case("processdata") is False  # No underscores

    def test_is_pascal_case(self, manager):
        """Test PascalCase detection."""
        assert manager._is_pascal_case("DataProcessor") is True
        assert manager._is_pascal_case("OutputFormatter") is True
        assert manager._is_pascal_case("dataProcessor") is False  # camelCase
        assert manager._is_pascal_case("data_processor") is False  # snake_case
        assert manager._is_pascal_case("Dataprocessor") is False  # No capital in middle

    def test_extract_function_name(self, manager):
        """Test function name extraction."""
        code = "def process_data(x):\n    return x"
        name = manager._extract_function_name(code)
        assert name == "process_data"

    def test_extract_function_name_invalid(self, manager):
        """Test function name extraction with invalid code."""
        code = "not a function"
        name = manager._extract_function_name(code)
        assert name is None

    def test_extract_class_name(self, manager):
        """Test class name extraction."""
        code = "class DataProcessor:\n    pass"
        name = manager._extract_class_name(code)
        assert name == "DataProcessor"

    def test_extract_class_name_invalid(self, manager):
        """Test class name extraction with invalid code."""
        code = "not a class"
        name = manager._extract_class_name(code)
        assert name is None

    def test_detect_naming_style_mixed(self, manager):
        """Test detection of mixed naming style."""
        names = ["process_data", "calculateSum", "OutputFormatter"]
        style = manager._detect_naming_style(names)
        assert style == "mixed"

    def test_detect_naming_style_empty(self, manager):
        """Test detection with empty names."""
        names = []
        style = manager._detect_naming_style(names)
        assert style == "unknown"

    def test_extract_structure_patterns(self, manager):
        """Test structure pattern extraction."""
        patterns = PatternSet(
            language="python",
            syntactic=[],
            type_patterns=[],
            semantic=[],
            source=Path("/project/tests/test_file.py"),
            extraction_time_ms=100.0,
            total_patterns=0,
        )

        structure = manager._extract_structure_patterns(patterns)

        assert structure["has_tests"] is True
        assert structure["test_directory"] == "tests"

    def test_extract_testing_patterns_pytest(self, manager):
        """Test pytest testing pattern extraction."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern(
                    "function",
                    "def test_foo(): ...",
                    1,
                    ["def test_process_data(fixture):\n    assert True"],
                    {},
                ),
            ],
            type_patterns=[],
            semantic=[],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=1,
        )

        testing = manager._extract_testing_patterns(patterns)

        assert testing["test_prefix"] == "test_"
        assert testing["framework"] == "pytest"
        assert testing["uses_fixtures"] is True

    def test_extract_error_handling_patterns(self, manager):
        """Test error handling pattern extraction."""
        patterns = PatternSet(
            language="python",
            syntactic=[],
            type_patterns=[],
            semantic=[
                SemanticPattern(
                    "error_handling", "try-except", ["try:\n    op()\nexcept:\n    pass"], 3
                ),
                SemanticPattern(
                    "error_handling", "try-finally", ["try:\n    op()\nfinally:\n    cleanup()"], 2
                ),
            ],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=2,
        )

        error_patterns = manager._extract_error_handling_patterns(patterns)

        assert len(error_patterns) == 2
        assert "try-except" in error_patterns
        assert "try-finally" in error_patterns

    def test_extract_style_preferences(self, manager):
        """Test style preference extraction."""
        patterns = PatternSet(
            language="python",
            syntactic=[
                SyntacticPattern(
                    "function", "def foo(): ...", 1, ["def process_data():\n    return 'data'"], {}
                ),
            ],
            type_patterns=[],
            semantic=[],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=1,
        )

        style = manager._extract_style_preferences(patterns)

        assert "indentation" in style
        assert "quotes" in style

    def test_extract_api_patterns(self, manager):
        """Test API pattern extraction."""
        patterns = PatternSet(
            language="python",
            syntactic=[],
            type_patterns=[],
            semantic=[
                SemanticPattern(
                    "api_call",
                    "requests.get",
                    [
                        "import requests\nrequests.get(url)",
                        "import requests\nrequests.post(url)",
                        "import requests\nrequests.put(url)",
                    ],
                    3,
                ),
            ],
            source=Path("."),
            extraction_time_ms=100.0,
            total_patterns=1,
        )

        apis = manager._extract_api_patterns(patterns)

        assert "requests" in apis
        assert len(apis["requests"]) == 3

    def test_extract_api_name(self, manager):
        """Test API name extraction."""
        code = "import requests\nrequests.get(url)"
        api_name = manager._extract_api_name(code)
        assert api_name == "requests"

    def test_extract_api_name_module_call(self, manager):
        """Test API name extraction from module call."""
        code = "json.dumps(data)"
        api_name = manager._extract_api_name(code)
        assert api_name == "json"

    def test_create_adapted_constraints(self, manager):
        """Test constraint creation from conventions."""
        conventions = ConventionSet(
            naming={"function": "snake_case"},
            structure={"has_tests": True},
            testing={"framework": "pytest"},
            error_handling=["try-except"],
            style={"indentation": "4_spaces"},
            apis={"requests": ["example"]},
        )

        constraints = manager.create_adapted_constraints(conventions)

        assert constraints["naming"] == conventions.naming
        assert constraints["structure"] == conventions.structure
        assert constraints["testing"] == conventions.testing
        assert constraints["error_handling"] == conventions.error_handling
        assert constraints["style"] == conventions.style
        assert constraints["apis"] == conventions.apis

    def test_update_from_feedback_success(self, manager, sample_project):
        """Test profile update from successful feedback."""
        profile = manager.initialize_project(sample_project, language="python")

        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(
                code="def foo(): pass", language="python", generation_time_ms=50.0
            ),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive",
        )

        initial_count = profile.generation_count
        manager.update_from_feedback("sample_project", feedback)

        updated_profile = manager.profiles["sample_project"]
        assert updated_profile.generation_count == initial_count + 1

    def test_update_from_feedback_failure(self, manager, sample_project):
        """Test profile update from failed feedback."""
        profile = manager.initialize_project(sample_project, language="python")

        feedback = Feedback(
            success=False,
            generation_result=GenerationResult(
                code="def foo(", language="python", generation_time_ms=50.0
            ),
            validation_result=ValidationResult(
                success=False, diagnostics=[{"severity": "error", "message": "SyntaxError"}]
            ),
            repair_result=None,
            score=-1.0,
            feedback_type="negative",
        )

        manager.update_from_feedback("sample_project", feedback)

        updated_profile = manager.profiles["sample_project"]
        assert updated_profile.generation_count == 1

    def test_update_from_feedback_unknown_project(self, manager):
        """Test feedback update for unknown project."""
        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(
                code="def foo(): pass", language="python", generation_time_ms=50.0
            ),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive",
        )

        # Should not raise error
        manager.update_from_feedback("unknown_project", feedback)

    def test_get_adaptation_stats(self, manager, sample_project):
        """Test adaptation statistics retrieval."""
        manager.initialize_project(sample_project, language="python")

        stats = manager.get_adaptation_stats("sample_project")

        assert isinstance(stats, AdaptationStats)
        assert stats.total_examples >= 0
        assert stats.patterns_learned >= 0
        assert stats.conventions_extracted >= 0
        assert 0.0 <= stats.convergence_score <= 1.0

    def test_get_adaptation_stats_unknown_project(self, manager):
        """Test stats for unknown project."""
        stats = manager.get_adaptation_stats("unknown_project")

        assert stats.total_examples == 0
        assert stats.patterns_learned == 0
        assert stats.conventions_extracted == 0
        assert stats.convergence_score == 0.0

    def test_count_conventions(self, manager):
        """Test convention counting."""
        conventions = ConventionSet(
            naming={"function": "snake_case", "class": "PascalCase"},
            structure={"has_tests": True},
            testing={"framework": "pytest"},
            error_handling=["try-except", "try-finally"],
            style={"indentation": "4_spaces"},
            apis={"requests": ["example"]},
        )

        count = manager._count_conventions(conventions)
        # 2 naming + 1 structure + 1 testing + 2 error_handling + 1 style + 1 apis = 8
        assert count == 8

    def test_compute_convergence_no_profile(self, manager):
        """Test convergence for non-existent profile."""
        convergence = manager.compute_convergence("unknown_project")
        assert convergence == 0.0

    def test_compute_convergence_with_profile(self, manager, sample_project):
        """Test convergence computation with profile."""
        manager.initialize_project(sample_project, language="python")

        convergence = manager.compute_convergence("sample_project")

        assert 0.0 <= convergence <= 1.0

    def test_compute_convergence_increases_with_generations(self, manager, sample_project):
        """Test that convergence increases with more generations."""
        profile = manager.initialize_project(sample_project, language="python")

        initial_convergence = manager.compute_convergence("sample_project")

        # Simulate multiple successful generations
        feedback = Feedback(
            success=True,
            generation_result=GenerationResult(
                code="def foo(): pass", language="python", generation_time_ms=50.0
            ),
            validation_result=ValidationResult(success=True),
            repair_result=None,
            score=1.0,
            feedback_type="positive",
        )

        for _ in range(10):
            manager.update_from_feedback("sample_project", feedback)

        updated_convergence = manager.compute_convergence("sample_project")

        assert updated_convergence >= initial_convergence

    def test_extract_conventions(self, manager, sample_project):
        """Test convention extraction from profile."""
        profile = manager.initialize_project(sample_project, language="python")

        conventions = manager.extract_conventions(profile)

        assert isinstance(conventions, ConventionSet)
        assert isinstance(conventions.naming, dict)
        assert isinstance(conventions.structure, dict)
        assert isinstance(conventions.testing, dict)
        assert isinstance(conventions.error_handling, list)
        assert isinstance(conventions.style, dict)
        assert isinstance(conventions.apis, dict)

    def test_multiple_profiles(self, manager, tmp_path):
        """Test managing multiple project profiles."""
        # Create two projects
        project1 = tmp_path / "project1"
        project1.mkdir()
        (project1 / "main.py").write_text("def foo(): pass")

        project2 = tmp_path / "project2"
        project2.mkdir()
        (project2 / "main.py").write_text("def bar(): pass")

        # Initialize both
        profile1 = manager.initialize_project(project1, language="python")
        profile2 = manager.initialize_project(project2, language="python")

        assert len(manager.profiles) == 2
        assert "project1" in manager.profiles
        assert "project2" in manager.profiles
        assert manager.profiles["project1"] == profile1
        assert manager.profiles["project2"] == profile2

    def test_profile_persistence(self, manager, sample_project):
        """Test that profiles persist in manager."""
        profile1 = manager.initialize_project(sample_project, language="python")
        profile2 = manager.profiles["sample_project"]

        assert profile1 is profile2

    def test_convergence_threshold(self, manager):
        """Test convergence threshold configuration."""
        assert manager.convergence_threshold == 0.9

    def test_performance_initialize_project(self, manager, sample_project):
        """Test that project initialization meets performance target."""
        import time

        start = time.time()
        manager.initialize_project(sample_project, language="python")
        elapsed = time.time() - start

        # Should complete in < 30s
        assert elapsed < 30
