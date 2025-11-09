"""
Pattern mining engine for extracting reusable patterns from codebases.

Extracts multi-level patterns (syntactic, type, semantic) from code to enable
adaptive learning and project-specific customization.
"""

import ast
import re
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed

from maze.core.types import TypeContext, Type


@dataclass
class SyntacticPattern:
    """Pattern from syntax/structure analysis."""

    pattern_type: str  # "function", "class", "import", "error_handling"
    template: str  # Code template with placeholders
    frequency: int  # Occurrences in codebase
    examples: list[str]  # Concrete examples
    context: dict[str, Any]  # Additional metadata

    def __hash__(self) -> int:
        """Hash based on pattern type and template."""
        return hash((self.pattern_type, self.template))


@dataclass
class TypePattern:
    """Pattern from type usage analysis."""

    signature: str  # Type signature
    common_usages: list[str]  # How type is typically used
    frequency: int
    generic_variants: list[str] = field(default_factory=list)  # Generic instantiations

    def __hash__(self) -> int:
        """Hash based on signature."""
        return hash(self.signature)


@dataclass
class SemanticPattern:
    """High-level semantic pattern."""

    intent: str  # "error_handling", "validation", "transformation"
    structure: str  # Abstract structure
    implementations: list[str]  # Concrete implementations
    frequency: int

    def __hash__(self) -> int:
        """Hash based on intent and structure."""
        return hash((self.intent, self.structure))


@dataclass
class PatternSet:
    """Collection of patterns with metadata."""

    syntactic: list[SyntacticPattern]
    type_patterns: list[TypePattern]
    semantic: list[SemanticPattern]
    language: str
    source: Path
    extraction_time_ms: float
    total_patterns: int


class PatternMiningEngine:
    """Extract reusable patterns from codebases."""

    def __init__(
        self,
        language: str = "typescript",
        min_frequency: int = 3,
        max_patterns: int = 1000,
        enable_semantic: bool = True
    ):
        """
        Initialize pattern mining engine.

        Args:
            language: Target language
            min_frequency: Minimum pattern occurrences
            max_patterns: Maximum patterns to extract
            enable_semantic: Enable semantic pattern extraction
        """
        self.language = language
        self.min_frequency = min_frequency
        self.max_patterns = max_patterns
        self.enable_semantic = enable_semantic

        # Cache for parsed ASTs
        self._ast_cache: dict[str, ast.AST] = {}

        # Statistics
        self.stats = {
            "files_processed": 0,
            "total_patterns": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }

    def mine_patterns(
        self,
        codebase: Path,
        language: Optional[str] = None
    ) -> PatternSet:
        """
        Mine patterns from entire codebase.

        Args:
            codebase: Path to codebase root
            language: Override language

        Returns:
            PatternSet with all extracted patterns

        Performance: <5s for 100K LOC
        """
        start_time = time.perf_counter()
        lang = language or self.language

        # Collect all source files
        files = self._collect_source_files(codebase, lang)

        # Extract patterns from all files
        all_syntactic: list[SyntacticPattern] = []
        all_type: list[TypePattern] = []
        all_semantic: list[SemanticPattern] = []

        # Use parallel processing for large codebases
        if len(files) > 10:
            all_syntactic, all_type, all_semantic = self._mine_parallel(files, lang)
        else:
            for file_path in files:
                try:
                    code = file_path.read_text(encoding='utf-8')

                    # Extract patterns
                    syntactic = self._extract_syntactic_from_file(code, lang)
                    type_patterns = self._extract_type_from_file(code, lang)

                    all_syntactic.extend(syntactic)
                    all_type.extend(type_patterns)

                    if self.enable_semantic:
                        semantic = self._extract_semantic_from_file(code, lang)
                        all_semantic.extend(semantic)

                    self.stats["files_processed"] += 1

                except Exception as e:
                    # Skip files with errors
                    continue

        # Aggregate and rank patterns
        syntactic_patterns = self._aggregate_syntactic_patterns(all_syntactic)
        type_patterns = self._aggregate_type_patterns(all_type)
        semantic_patterns = self._aggregate_semantic_patterns(all_semantic)

        # Filter by frequency
        syntactic_patterns = [
            p for p in syntactic_patterns
            if p.frequency >= self.min_frequency
        ]
        type_patterns = [
            p for p in type_patterns
            if p.frequency >= self.min_frequency
        ]
        semantic_patterns = [
            p for p in semantic_patterns
            if p.frequency >= self.min_frequency
        ]

        # Limit total patterns
        syntactic_patterns = syntactic_patterns[:self.max_patterns // 3]
        type_patterns = type_patterns[:self.max_patterns // 3]
        semantic_patterns = semantic_patterns[:self.max_patterns // 3]

        extraction_time_ms = (time.perf_counter() - start_time) * 1000
        total = len(syntactic_patterns) + len(type_patterns) + len(semantic_patterns)

        self.stats["total_patterns"] = total

        return PatternSet(
            syntactic=syntactic_patterns,
            type_patterns=type_patterns,
            semantic=semantic_patterns,
            language=lang,
            source=codebase,
            extraction_time_ms=extraction_time_ms,
            total_patterns=total
        )

    def extract_syntactic_patterns(
        self,
        ast_node: ast.AST,
        code: str
    ) -> list[SyntacticPattern]:
        """
        Extract syntactic patterns from AST.

        Args:
            ast_node: Parsed AST
            code: Source code

        Returns:
            List of syntactic patterns
        """
        patterns = []

        # Extract function patterns
        patterns.extend(self._extract_function_patterns(ast_node, code))

        # Extract class patterns
        patterns.extend(self._extract_class_patterns(ast_node, code))

        # Extract import patterns
        patterns.extend(self._extract_import_patterns(ast_node, code))

        # Extract error handling patterns
        patterns.extend(self._extract_error_handling_patterns(ast_node, code))

        return patterns

    def extract_type_patterns(
        self,
        types: TypeContext,
        code: str
    ) -> list[TypePattern]:
        """
        Extract type usage patterns.

        Args:
            types: Type context
            code: Source code

        Returns:
            List of type patterns
        """
        patterns = []

        # Group by type signature
        type_usages: dict[str, list[str]] = defaultdict(list)

        for var_name, var_type in types.variables.items():
            type_str = str(var_type)
            type_usages[type_str].append(var_name)

        # Create patterns
        for type_str, usages in type_usages.items():
            patterns.append(TypePattern(
                signature=type_str,
                common_usages=usages,
                frequency=len(usages),
                generic_variants=self._find_generic_variants(type_str)
            ))

        return patterns

    def extract_semantic_patterns(
        self,
        code: str,
        ast_node: Optional[ast.AST] = None
    ) -> list[SemanticPattern]:
        """
        Extract high-level semantic patterns.

        Args:
            code: Source code
            ast_node: Optional parsed AST

        Returns:
            List of semantic patterns
        """
        if ast_node is None and self.language == "python":
            try:
                ast_node = ast.parse(code)
            except:
                return []

        patterns = []

        if ast_node:
            # Error handling patterns
            patterns.extend(self._extract_error_handling_semantic(ast_node, code))

            # Validation patterns
            patterns.extend(self._extract_validation_patterns(ast_node, code))

            # Transformation patterns
            patterns.extend(self._extract_transformation_patterns(ast_node, code))

        return patterns

    def rank_patterns(
        self,
        patterns: list,
        ranking_criteria: Optional[dict] = None
    ) -> list:
        """
        Rank patterns by relevance and frequency.

        Args:
            patterns: Patterns to rank
            ranking_criteria: Custom ranking weights

        Returns:
            Patterns with scores (sorted descending)
        """
        criteria = ranking_criteria or {
            "frequency": 0.6,
            "examples": 0.2,
            "complexity": 0.2
        }

        scored_patterns = []

        for pattern in patterns:
            score = 0.0

            # Frequency score
            freq_score = min(1.0, pattern.frequency / 10.0)
            score += freq_score * criteria["frequency"]

            # Examples score (more examples = better)
            if hasattr(pattern, 'examples'):
                examples_score = min(1.0, len(pattern.examples) / 5.0)
                score += examples_score * criteria["examples"]

            # Complexity score (more complex = higher value)
            if hasattr(pattern, 'template'):
                complexity = len(pattern.template.split('\n'))
                complexity_score = min(1.0, complexity / 10.0)
                score += complexity_score * criteria["complexity"]

            scored_patterns.append((pattern, score))

        # Sort by score (descending)
        scored_patterns.sort(key=lambda x: x[1], reverse=True)

        return [p for p, _ in scored_patterns]

    def incremental_mine(
        self,
        file_path: Path,
        existing_patterns: PatternSet
    ) -> PatternSet:
        """
        Incrementally update patterns with new file.

        Args:
            file_path: New/modified file
            existing_patterns: Current pattern set

        Returns:
            Updated pattern set
        """
        start_time = time.perf_counter()

        # Extract patterns from new file
        code = file_path.read_text(encoding='utf-8')

        new_syntactic = self._extract_syntactic_from_file(code, self.language)
        new_type = self._extract_type_from_file(code, self.language)
        new_semantic = []

        if self.enable_semantic:
            new_semantic = self._extract_semantic_from_file(code, self.language)

        # Merge with existing patterns
        all_syntactic = existing_patterns.syntactic + new_syntactic
        all_type = existing_patterns.type_patterns + new_type
        all_semantic = existing_patterns.semantic + new_semantic

        # Re-aggregate
        syntactic_patterns = self._aggregate_syntactic_patterns(all_syntactic)
        type_patterns = self._aggregate_type_patterns(all_type)
        semantic_patterns = self._aggregate_semantic_patterns(all_semantic)

        extraction_time_ms = (time.perf_counter() - start_time) * 1000
        total = len(syntactic_patterns) + len(type_patterns) + len(semantic_patterns)

        return PatternSet(
            syntactic=syntactic_patterns,
            type_patterns=type_patterns,
            semantic=semantic_patterns,
            language=self.language,
            source=existing_patterns.source,
            extraction_time_ms=extraction_time_ms,
            total_patterns=total
        )

    def get_mining_stats(self) -> dict[str, Any]:
        """
        Get mining performance statistics.

        Returns:
            Dictionary with stats
        """
        return self.stats.copy()

    # Private helper methods

    def _collect_source_files(self, codebase: Path, language: str) -> list[Path]:
        """Collect source files for language."""
        extensions = {
            "python": [".py"],
            "typescript": [".ts", ".tsx"],
            "rust": [".rs"],
            "go": [".go"],
            "zig": [".zig"]
        }

        exts = extensions.get(language, [".py"])
        files = []

        for ext in exts:
            files.extend(codebase.rglob(f"*{ext}"))

        return files

    def _mine_parallel(
        self,
        files: list[Path],
        language: str
    ) -> tuple[list[SyntacticPattern], list[TypePattern], list[SemanticPattern]]:
        """Mine patterns in parallel."""
        all_syntactic = []
        all_type = []
        all_semantic = []

        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(self._extract_patterns_from_file, f, language): f
                for f in files
            }

            for future in as_completed(futures):
                try:
                    syntactic, type_patterns, semantic = future.result()
                    all_syntactic.extend(syntactic)
                    all_type.extend(type_patterns)
                    all_semantic.extend(semantic)
                except Exception:
                    continue

        return all_syntactic, all_type, all_semantic

    def _extract_patterns_from_file(
        self,
        file_path: Path,
        language: str
    ) -> tuple[list[SyntacticPattern], list[TypePattern], list[SemanticPattern]]:
        """Extract all patterns from a file."""
        code = file_path.read_text(encoding='utf-8')

        syntactic = self._extract_syntactic_from_file(code, language)
        type_patterns = self._extract_type_from_file(code, language)
        semantic = []

        if self.enable_semantic:
            semantic = self._extract_semantic_from_file(code, language)

        return syntactic, type_patterns, semantic

    def _extract_syntactic_from_file(
        self,
        code: str,
        language: str
    ) -> list[SyntacticPattern]:
        """Extract syntactic patterns from file."""
        if language != "python":
            return []  # TODO: Add support for other languages

        try:
            tree = self._parse_with_cache(code)
            return self.extract_syntactic_patterns(tree, code)
        except:
            return []

    def _extract_type_from_file(
        self,
        code: str,
        language: str
    ) -> list[TypePattern]:
        """Extract type patterns from file."""
        # Placeholder - would integrate with type system
        return []

    def _extract_semantic_from_file(
        self,
        code: str,
        language: str
    ) -> list[SemanticPattern]:
        """Extract semantic patterns from file."""
        if language != "python":
            return []

        try:
            tree = self._parse_with_cache(code)
            return self.extract_semantic_patterns(code, tree)
        except:
            return []

    def _parse_with_cache(self, code: str) -> ast.AST:
        """Parse code with caching."""
        code_hash = hashlib.md5(code.encode()).hexdigest()

        if code_hash in self._ast_cache:
            self.stats["cache_hits"] += 1
            return self._ast_cache[code_hash]

        self.stats["cache_misses"] += 1
        tree = ast.parse(code)
        self._ast_cache[code_hash] = tree

        return tree

    def _extract_function_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SyntacticPattern]:
        """Extract function definition patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                template = self._generalize_function(node)

                patterns.append(SyntacticPattern(
                    pattern_type="function",
                    template=template,
                    frequency=1,
                    examples=[ast.unparse(node)[:200]],  # Truncate long examples
                    context={
                        "args_count": len(node.args.args),
                        "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                        "decorators": [
                            d.id if isinstance(d, ast.Name) else "decorator"
                            for d in node.decorator_list
                        ],
                        "is_async": isinstance(node, ast.AsyncFunctionDef)
                    }
                ))

        return patterns

    def _extract_class_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SyntacticPattern]:
        """Extract class definition patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                template = f"class {node.name}({', '.join(self._get_base_names(node))})"

                patterns.append(SyntacticPattern(
                    pattern_type="class",
                    template=template,
                    frequency=1,
                    examples=[ast.unparse(node)[:200]],
                    context={
                        "methods": len([m for m in node.body if isinstance(m, ast.FunctionDef)]),
                        "has_init": any(m.name == "__init__" for m in node.body if isinstance(m, ast.FunctionDef)),
                        "decorators": [
                            d.id if isinstance(d, ast.Name) else "decorator"
                            for d in node.decorator_list
                        ]
                    }
                ))

        return patterns

    def _extract_import_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SyntacticPattern]:
        """Extract import patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    patterns.append(SyntacticPattern(
                        pattern_type="import",
                        template=f"import {alias.name}",
                        frequency=1,
                        examples=[f"import {alias.name}"],
                        context={"module": alias.name}
                    ))
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                patterns.append(SyntacticPattern(
                    pattern_type="import",
                    template=f"from {module} import ...",
                    frequency=1,
                    examples=[f"from {module} import {', '.join(names[:3])}"],
                    context={"module": module, "imports": names}
                ))

        return patterns

    def _extract_error_handling_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SyntacticPattern]:
        """Extract error handling patterns."""
        patterns = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                exception_types = []
                for handler in node.handlers:
                    if handler.type:
                        if isinstance(handler.type, ast.Name):
                            exception_types.append(handler.type.id)
                        elif isinstance(handler.type, ast.Tuple):
                            exception_types.extend([
                                e.id for e in handler.type.elts
                                if isinstance(e, ast.Name)
                            ])

                patterns.append(SyntacticPattern(
                    pattern_type="error_handling",
                    template="try: ... except ...",
                    frequency=1,
                    examples=[ast.unparse(node)[:200]],
                    context={
                        "exception_types": exception_types,
                        "has_finally": len(node.finalbody) > 0,
                        "has_else": len(node.orelse) > 0
                    }
                ))

        return patterns

    def _extract_error_handling_semantic(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SemanticPattern]:
        """Extract semantic error handling patterns."""
        patterns = []

        try_blocks = [node for node in ast.walk(tree) if isinstance(node, ast.Try)]

        if try_blocks:
            patterns.append(SemanticPattern(
                intent="error_handling",
                structure="try-except pattern",
                implementations=[ast.unparse(node)[:200] for node in try_blocks[:3]],
                frequency=len(try_blocks)
            ))

        return patterns

    def _extract_validation_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SemanticPattern]:
        """Extract validation patterns."""
        patterns = []

        # Look for assertion patterns
        assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]

        if assertions:
            patterns.append(SemanticPattern(
                intent="validation",
                structure="assertion pattern",
                implementations=[ast.unparse(node)[:200] for node in assertions[:3]],
                frequency=len(assertions)
            ))

        return patterns

    def _extract_transformation_patterns(
        self,
        tree: ast.AST,
        code: str
    ) -> list[SemanticPattern]:
        """Extract transformation patterns."""
        # Placeholder for transformation pattern extraction
        return []

    def _generalize_function(self, node: ast.FunctionDef) -> str:
        """Generalize function to template."""
        args_str = ", ".join(["arg" for _ in node.args.args])
        return f"def {node.name}({args_str}): ..."

    def _get_base_names(self, node: ast.ClassDef) -> list[str]:
        """Get base class names."""
        bases = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            else:
                bases.append("Base")
        return bases

    def _find_generic_variants(self, type_str: str) -> list[str]:
        """Find generic type variants."""
        # Placeholder for generic variant detection
        return []

    def _aggregate_syntactic_patterns(
        self,
        patterns: list[SyntacticPattern]
    ) -> list[SyntacticPattern]:
        """Aggregate syntactic patterns by template."""
        aggregated: dict[tuple, SyntacticPattern] = {}

        for pattern in patterns:
            key = (pattern.pattern_type, pattern.template)

            if key in aggregated:
                # Merge with existing
                existing = aggregated[key]
                existing.frequency += 1
                if pattern.examples and pattern.examples[0] not in existing.examples:
                    existing.examples.append(pattern.examples[0])
                    # Limit examples
                    existing.examples = existing.examples[:5]
            else:
                aggregated[key] = pattern

        # Sort by frequency
        result = sorted(aggregated.values(), key=lambda p: p.frequency, reverse=True)
        return result

    def _aggregate_type_patterns(
        self,
        patterns: list[TypePattern]
    ) -> list[TypePattern]:
        """Aggregate type patterns by signature."""
        aggregated: dict[str, TypePattern] = {}

        for pattern in patterns:
            if pattern.signature in aggregated:
                existing = aggregated[pattern.signature]
                existing.frequency += pattern.frequency
                existing.common_usages.extend(pattern.common_usages)
                existing.common_usages = list(set(existing.common_usages))[:10]
            else:
                aggregated[pattern.signature] = pattern

        result = sorted(aggregated.values(), key=lambda p: p.frequency, reverse=True)
        return result

    def _aggregate_semantic_patterns(
        self,
        patterns: list[SemanticPattern]
    ) -> list[SemanticPattern]:
        """Aggregate semantic patterns by intent."""
        aggregated: dict[tuple, SemanticPattern] = {}

        for pattern in patterns:
            key = (pattern.intent, pattern.structure)

            if key in aggregated:
                existing = aggregated[key]
                existing.frequency += pattern.frequency
                existing.implementations.extend(pattern.implementations)
                existing.implementations = list(set(existing.implementations))[:5]
            else:
                aggregated[key] = pattern

        result = sorted(aggregated.values(), key=lambda p: p.frequency, reverse=True)
        return result
