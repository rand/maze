"""
Project adaptation manager for adaptive code generation.

Adapts Maze to project-specific conventions and patterns.
"""

import ast
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from maze.learning.pattern_mining import PatternMiningEngine, PatternSet, SyntacticPattern
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    Feedback,
)


@dataclass
class ConventionSet:
    """Project-specific conventions."""
    naming: dict[str, str] = field(default_factory=dict)  # "function" -> "camelCase", etc.
    structure: dict[str, Any] = field(default_factory=dict)  # File organization patterns
    testing: dict[str, Any] = field(default_factory=dict)  # Test patterns
    error_handling: list[str] = field(default_factory=list)  # Error handling patterns
    style: dict[str, Any] = field(default_factory=dict)  # Code style preferences
    apis: dict[str, list[str]] = field(default_factory=dict)  # Common API usage patterns


@dataclass
class ProjectProfile:
    """Profile of project conventions."""
    project_name: str
    project_path: Path
    language: str
    conventions: ConventionSet
    patterns: PatternSet
    created_at: float
    updated_at: float
    generation_count: int = 0


@dataclass
class AdaptationStats:
    """Statistics about adaptation progress."""
    total_examples: int
    patterns_learned: int
    conventions_extracted: int
    convergence_score: float  # 0-1, higher = more adapted
    last_updated: float


class ProjectAdaptationManager:
    """
    Adapt to project-specific conventions.

    Learns from existing codebase to match project style:
    - Naming conventions (camelCase vs snake_case)
    - File structure patterns
    - Testing conventions
    - Error handling patterns
    - Code style preferences
    - Common API usage patterns
    """

    def __init__(
        self,
        pattern_miner: PatternMiningEngine,
        learner: ConstraintLearningSystem,
        convergence_threshold: float = 0.9
    ):
        """
        Initialize project adaptation manager.

        Args:
            pattern_miner: Pattern mining engine
            learner: Constraint learning system
            convergence_threshold: Convergence target (0-1)
        """
        self.pattern_miner = pattern_miner
        self.learner = learner
        self.convergence_threshold = convergence_threshold
        self.profiles: dict[str, ProjectProfile] = {}

    def initialize_project(
        self,
        project_path: Path,
        language: Optional[str] = None
    ) -> ProjectProfile:
        """
        Initialize project profile.

        Args:
            project_path: Path to project root
            language: Override language detection

        Returns:
            Project profile

        Performance: <30s for typical project
        """
        start_time = time.time()

        # Detect language if not provided
        if language is None:
            language = self._detect_language(project_path)

        # Mine patterns from project
        patterns = self.pattern_miner.mine_patterns(project_path, language)

        # Extract conventions
        conventions = self.extract_conventions_from_patterns(patterns)

        # Create profile
        project_name = project_path.name
        profile = ProjectProfile(
            project_name=project_name,
            project_path=project_path,
            language=language,
            conventions=conventions,
            patterns=patterns,
            created_at=time.time(),
            updated_at=time.time(),
            generation_count=0
        )

        self.profiles[project_name] = profile

        elapsed = time.time() - start_time
        assert elapsed < 30, f"initialize_project took {elapsed:.1f}s (target: <30s)"

        return profile

    def _detect_language(self, project_path: Path) -> str:
        """Detect primary language of project."""
        # Count file extensions
        extension_counts: dict[str, int] = {}

        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                extension_counts[ext] = extension_counts.get(ext, 0) + 1

        # Map extensions to languages
        language_map = {
            ".py": "python",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".js": "javascript",
            ".jsx": "javascript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
        }

        # Find most common language
        language_counts: dict[str, int] = {}
        for ext, count in extension_counts.items():
            if ext in language_map:
                lang = language_map[ext]
                language_counts[lang] = language_counts.get(lang, 0) + count

        if language_counts:
            return max(language_counts.items(), key=lambda x: x[1])[0]

        return "python"  # Default

    def extract_conventions(
        self,
        project: ProjectProfile
    ) -> ConventionSet:
        """
        Extract project conventions from patterns.

        Args:
            project: Project profile

        Returns:
            Convention set
        """
        return self.extract_conventions_from_patterns(project.patterns)

    def extract_conventions_from_patterns(
        self,
        patterns: PatternSet
    ) -> ConventionSet:
        """
        Extract conventions from pattern set.

        Args:
            patterns: Pattern set

        Returns:
            Convention set
        """
        conventions = ConventionSet()

        # Extract naming conventions
        conventions.naming = self._extract_naming_conventions(patterns)

        # Extract structure patterns
        conventions.structure = self._extract_structure_patterns(patterns)

        # Extract testing patterns
        conventions.testing = self._extract_testing_patterns(patterns)

        # Extract error handling patterns
        conventions.error_handling = self._extract_error_handling_patterns(patterns)

        # Extract style preferences
        conventions.style = self._extract_style_preferences(patterns)

        # Extract API usage patterns
        conventions.apis = self._extract_api_patterns(patterns)

        return conventions

    def _extract_naming_conventions(self, patterns: PatternSet) -> dict[str, str]:
        """Extract naming style from patterns."""
        function_names: list[str] = []
        class_names: list[str] = []

        for pattern in patterns.syntactic:
            if pattern.pattern_type == "function":
                # Extract function names from examples
                for example in pattern.examples:
                    func_name = self._extract_function_name(example)
                    if func_name:
                        function_names.append(func_name)
            elif pattern.pattern_type == "class":
                for example in pattern.examples:
                    class_name = self._extract_class_name(example)
                    if class_name:
                        class_names.append(class_name)

        conventions = {}

        # Detect naming style
        if function_names:
            style = self._detect_naming_style(function_names)
            conventions["function"] = style

        if class_names:
            style = self._detect_naming_style(class_names)
            conventions["class"] = style

        return conventions

    def _extract_function_name(self, code: str) -> Optional[str]:
        """Extract function name from code."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return node.name
        except SyntaxError:
            pass

        # Try regex fallback for various languages
        # Python: def foo(
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)

        # JavaScript/TypeScript: function foo(
        match = re.search(r'function\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)

        # Arrow functions: const foo = (
        match = re.search(r'const\s+(\w+)\s*=\s*\(', code)
        if match:
            return match.group(1)

        return None

    def _extract_class_name(self, code: str) -> Optional[str]:
        """Extract class name from code."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    return node.name
        except SyntaxError:
            # Try regex fallback
            match = re.search(r'class\s+(\w+)', code)
            if match:
                return match.group(1)
        return None

    def _detect_naming_style(self, names: list[str]) -> str:
        """Detect predominant naming style."""
        if not names:
            return "unknown"

        camel_case = sum(1 for n in names if self._is_camel_case(n))
        snake_case = sum(1 for n in names if self._is_snake_case(n))
        pascal_case = sum(1 for n in names if self._is_pascal_case(n))

        total = len(names)
        if camel_case / total > 0.6:
            return "camelCase"
        elif snake_case / total > 0.6:
            return "snake_case"
        elif pascal_case / total > 0.6:
            return "PascalCase"
        else:
            return "mixed"

    def _is_camel_case(self, name: str) -> bool:
        """Check if name is camelCase."""
        if not name or name[0].isupper():
            return False
        return bool(re.match(r'^[a-z][a-zA-Z0-9]*$', name)) and any(c.isupper() for c in name)

    def _is_snake_case(self, name: str) -> bool:
        """Check if name is snake_case."""
        return bool(re.match(r'^[a-z][a-z0-9_]*$', name)) and '_' in name

    def _is_pascal_case(self, name: str) -> bool:
        """Check if name is PascalCase."""
        if not name or not name[0].isupper():
            return False
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', name)) and any(c.isupper() for c in name[1:])

    def _extract_structure_patterns(self, patterns: PatternSet) -> dict[str, Any]:
        """Extract file structure patterns."""
        structure = {
            "has_tests": False,
            "test_directory": None,
            "has_src": False,
            "module_structure": "flat"
        }

        # Check for common directory patterns in source path
        source_str = str(patterns.source)
        if "test" in source_str.lower():
            structure["has_tests"] = True
            if "/tests/" in source_str:
                structure["test_directory"] = "tests"
            elif "/test/" in source_str:
                structure["test_directory"] = "test"

        if "/src/" in source_str:
            structure["has_src"] = True

        return structure

    def _extract_testing_patterns(self, patterns: PatternSet) -> dict[str, Any]:
        """Extract testing patterns."""
        testing = {
            "framework": "unknown",
            "test_prefix": "test_",
            "uses_fixtures": False,
            "uses_mocks": False
        }

        # Look for test patterns in syntactic patterns
        for pattern in patterns.syntactic:
            if pattern.pattern_type == "function":
                for example in pattern.examples:
                    if "test" in example.lower():
                        if example.strip().startswith("def test"):
                            testing["test_prefix"] = "test_"
                        elif "Test" in example:
                            testing["test_prefix"] = "Test"

                        if "pytest" in example or "@pytest" in example:
                            testing["framework"] = "pytest"
                        elif "unittest" in example:
                            testing["framework"] = "unittest"
                        elif "fixture" in example.lower() and testing["framework"] == "unknown":
                            # Fixtures strongly suggest pytest
                            testing["framework"] = "pytest"

                        if "fixture" in example:
                            testing["uses_fixtures"] = True
                        if "mock" in example.lower():
                            testing["uses_mocks"] = True

        return testing

    def _extract_error_handling_patterns(self, patterns: PatternSet) -> list[str]:
        """Extract error handling patterns."""
        error_patterns = []

        for pattern in patterns.semantic:
            if pattern.intent == "error_handling":
                error_patterns.append(pattern.structure)

        # Deduplicate
        return list(set(error_patterns))

    def _extract_style_preferences(self, patterns: PatternSet) -> dict[str, Any]:
        """Extract code style preferences."""
        style = {
            "indentation": "unknown",
            "quotes": "unknown",
            "line_length": None
        }

        # Analyze examples for style patterns
        for pattern in patterns.syntactic[:10]:  # Sample first 10
            if pattern.examples:
                example = pattern.examples[0]

                # Detect indentation
                lines = example.split('\n')
                for line in lines:
                    if line and line[0] == ' ':
                        leading = len(line) - len(line.lstrip(' '))
                        if leading > 0:
                            style["indentation"] = f"{leading}_spaces"
                            break
                    elif line and line[0] == '\t':
                        style["indentation"] = "tabs"
                        break

                # Detect quotes
                if '"' in example and "'" not in example:
                    style["quotes"] = "double"
                elif "'" in example and '"' not in example:
                    style["quotes"] = "single"

        return style

    def _extract_api_patterns(self, patterns: PatternSet) -> dict[str, list[str]]:
        """Extract common API usage patterns."""
        api_usage: dict[str, list[str]] = {}

        for pattern in patterns.semantic:
            if pattern.intent in ["api_call", "library_usage"]:
                # Extract API calls
                for impl in pattern.implementations:
                    api_name = self._extract_api_name(impl)
                    if api_name:
                        if api_name not in api_usage:
                            api_usage[api_name] = []
                        api_usage[api_name].append(impl)

        # Keep only frequently used APIs
        return {
            api: usages
            for api, usages in api_usage.items()
            if len(usages) >= 3
        }

    def _extract_api_name(self, code: str) -> Optional[str]:
        """Extract API/library name from code."""
        # Look for import statements
        import_match = re.search(r'import\s+(\w+)', code)
        if import_match:
            return import_match.group(1)

        # Look for module.function patterns
        module_match = re.search(r'(\w+)\.\w+\(', code)
        if module_match:
            return module_match.group(1)

        return None

    def create_adapted_constraints(
        self,
        conventions: ConventionSet
    ) -> dict[str, Any]:
        """
        Create constraints from conventions.

        Args:
            conventions: Project conventions

        Returns:
            Constraint set adapted to project
        """
        constraints = {
            "naming": conventions.naming,
            "structure": conventions.structure,
            "testing": conventions.testing,
            "error_handling": conventions.error_handling,
            "style": conventions.style,
            "apis": conventions.apis
        }

        return constraints

    def update_from_feedback(
        self,
        project_name: str,
        feedback: Feedback
    ) -> None:
        """
        Update project profile from feedback.

        Args:
            project_name: Project identifier
            feedback: Generation feedback
        """
        if project_name not in self.profiles:
            return

        profile = self.profiles[project_name]
        profile.generation_count += 1
        profile.updated_at = time.time()

        # Update learner constraints based on feedback
        if feedback.success:
            self.learner.learn_from_success(
                feedback.generation_result,
                feedback.validation_result
            )
        else:
            diagnostics = [
                {"severity": d.get("severity", "error"), "message": d.get("message", "")}
                for d in feedback.validation_result.diagnostics
            ]
            self.learner.learn_from_failure(
                feedback.generation_result,
                diagnostics
            )

    def get_adaptation_stats(
        self,
        project_name: str
    ) -> AdaptationStats:
        """
        Get adaptation statistics.

        Args:
            project_name: Project identifier

        Returns:
            Adaptation statistics
        """
        if project_name not in self.profiles:
            return AdaptationStats(
                total_examples=0,
                patterns_learned=0,
                conventions_extracted=0,
                convergence_score=0.0,
                last_updated=time.time()
            )

        profile = self.profiles[project_name]

        return AdaptationStats(
            total_examples=profile.patterns.total_patterns,
            patterns_learned=len(self.learner.constraints),
            conventions_extracted=self._count_conventions(profile.conventions),
            convergence_score=self.compute_convergence(project_name),
            last_updated=profile.updated_at
        )

    def _count_conventions(self, conventions: ConventionSet) -> int:
        """Count number of extracted conventions."""
        count = 0
        count += len(conventions.naming)
        count += len(conventions.structure)
        count += len(conventions.testing)
        count += len(conventions.error_handling)
        count += len(conventions.style)
        count += len(conventions.apis)
        return count

    def compute_convergence(
        self,
        project_name: str
    ) -> float:
        """
        Compute adaptation convergence score.

        Args:
            project_name: Project identifier

        Returns:
            Convergence score (0-1)
        """
        if project_name not in self.profiles:
            return 0.0

        profile = self.profiles[project_name]

        # Convergence based on:
        # 1. Number of patterns learned
        # 2. Number of generations
        # 3. Constraint stability

        pattern_score = min(1.0, profile.patterns.total_patterns / 100.0)
        generation_score = min(1.0, profile.generation_count / 50.0)

        # Constraint stability (high weight = stable)
        if self.learner.constraints:
            avg_weight = sum(self.learner.constraints.values()) / len(self.learner.constraints)
            stability_score = avg_weight
        else:
            stability_score = 0.0

        # Weighted combination
        convergence = (
            pattern_score * 0.4 +
            generation_score * 0.3 +
            stability_score * 0.3
        )

        return convergence


__all__ = [
    "ProjectAdaptationManager",
    "ProjectProfile",
    "ConventionSet",
    "AdaptationStats",
]
