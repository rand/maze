"""End-to-end pipeline orchestrating Maze components.

Coordinates indexing, constraint synthesis, generation, validation, repair,
and adaptive learning into a cohesive workflow.

Performance targets:
- Pipeline setup: <100ms
- Full generation workflow: <10s per prompt
- Indexing: <30s for 100K LOC
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from maze.config import Config
from maze.core.types import TypeContext
from maze.indexer.base import BaseIndexer, IndexingResult
from maze.indexer.languages.typescript import TypeScriptIndexer
from maze.logging import (
    GenerationResult as LogGenerationResult,
    MetricsCollector,
    StructuredLogger,
)
from maze.repair.orchestrator import RepairContext, RepairOrchestrator
from maze.synthesis.grammar_builder import GrammarBuilder
from maze.validation.pipeline import ValidationContext, ValidationPipeline


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution."""

    project_path: Path
    language: str
    provider: str = "openai"
    model: str = "gpt-4"
    enable_syntactic: bool = True
    enable_type: bool = True
    enable_semantic: bool = False
    enable_contextual: bool = True
    enable_repair: bool = True
    max_repair_attempts: int = 3
    timeout_seconds: int = 30


@dataclass
class IndexingMetrics:
    """Metrics from indexing phase."""

    duration_ms: float
    files_indexed: int
    symbols_extracted: int
    errors: List[str] = field(default_factory=list)


@dataclass
class GenerationMetrics:
    """Metrics from generation phase."""

    duration_ms: float
    tokens_generated: int
    provider: str
    model: str
    constraints_applied: List[str] = field(default_factory=list)


@dataclass
class ValidationMetrics:
    """Metrics from validation phase."""

    duration_ms: float
    syntax_valid: bool
    type_valid: bool
    tests_passed: int
    tests_failed: int
    errors_found: int


@dataclass
class RepairMetrics:
    """Metrics from repair phase."""

    duration_ms: float
    attempts: int
    success: bool
    errors_fixed: int


@dataclass
class PipelineResult:
    """Complete result from pipeline execution."""

    success: bool
    code: str
    prompt: str
    language: str
    indexing: Optional[IndexingMetrics] = None
    generation: Optional[GenerationMetrics] = None
    validation: Optional[ValidationMetrics] = None
    repair: Optional[RepairMetrics] = None
    total_duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)


class Pipeline:
    """End-to-end code generation pipeline.

    Orchestrates:
    1. Project indexing (extract context)
    2. Constraint synthesis (build grammars)
    3. Code generation (with constraints)
    4. Multi-level validation
    5. Repair (if validation fails)
    6. Adaptive learning (store patterns)
    """

    def __init__(self, config: Config):
        """Initialize pipeline with configuration.

        Args:
            config: Maze configuration
        """
        self.config = config
        self.logger = StructuredLogger(config.logging)
        self.metrics = MetricsCollector()

        # Initialize components
        self.indexer: Optional[BaseIndexer] = None
        self.grammar_builder = GrammarBuilder()
        self.validator = ValidationPipeline()
        self.repair_orchestrator: Optional[RepairOrchestrator] = None

        # Cached context from indexing
        self._indexed_context: Optional[IndexingResult] = None
        self._type_context: Optional[TypeContext] = None

    def index_project(self, project_path: Optional[Path] = None) -> IndexingResult:
        """Index project to extract context.

        Args:
            project_path: Path to project (uses config if None)

        Returns:
            IndexingResult with symbols, types, patterns

        Raises:
            ValueError: If language not supported
        """
        start = time.perf_counter()

        path = project_path or self.config.project.path
        language = self.config.project.language

        # Select indexer based on language
        if language == "typescript" or language == "javascript":
            self.indexer = TypeScriptIndexer(project_path=path)
        else:
            raise ValueError(f"Language '{language}' not yet supported for indexing")

        # Perform indexing
        result = self.indexer.index_directory(path)

        duration_ms = (time.perf_counter() - start) * 1000

        # Cache for later use
        self._indexed_context = result

        # Build type context from symbols
        self._type_context = TypeContext()
        for symbol in result.symbols:
            if symbol.kind == "variable":
                # Store variable type information (simplified)
                self._type_context.variables[symbol.name] = symbol.type_str
            elif symbol.kind == "function":
                # Store function signature (simplified)
                self._type_context.functions[symbol.name] = ([], symbol.type_str)

        # Log metrics
        self.metrics.record_latency("indexing", duration_ms)
        self.logger.log_info(
            "indexing_complete",
            duration_ms=duration_ms,
            files=len(result.files_processed),
            symbols=len(result.symbols),
        )

        return result

    def generate(
        self, prompt: str, context: Optional[TypeContext] = None
    ) -> PipelineResult:
        """Generate code with full pipeline.

        Args:
            prompt: Generation prompt
            context: Type context (uses indexed if None)

        Returns:
            PipelineResult with generated code and metrics
        """
        pipeline_start = time.perf_counter()

        language = self.config.project.language
        type_ctx = context or self._type_context

        result = PipelineResult(
            success=False,
            code="",
            prompt=prompt,
            language=language,
        )

        try:
            # Step 1: Constraint synthesis (build grammar)
            grammar = self._synthesize_constraints(prompt, type_ctx)

            # Step 2: Code generation (placeholder - needs provider integration)
            gen_start = time.perf_counter()
            code = self._generate_with_constraints(prompt, grammar, type_ctx)
            gen_duration_ms = (time.perf_counter() - gen_start) * 1000

            result.generation = GenerationMetrics(
                duration_ms=gen_duration_ms,
                tokens_generated=len(code.split()),  # Rough estimate
                provider=self.config.generation.provider,
                model=self.config.generation.model,
                constraints_applied=["syntactic"] if grammar else [],
            )

            # Step 3: Validation
            val_result = self.validate(code, type_ctx)
            result.validation = ValidationMetrics(
                duration_ms=val_result.validation_time_ms,
                syntax_valid=val_result.success,
                type_valid=val_result.success,
                tests_passed=0,
                tests_failed=0,
                errors_found=len(val_result.diagnostics),
            )

            # Step 4: Repair if validation failed
            if not val_result.success and self.config.constraints.adaptive_weighting:
                repair_result = self.repair(code, val_result.diagnostics, prompt, type_ctx)
                result.repair = RepairMetrics(
                    duration_ms=repair_result.repair_time_ms,
                    attempts=repair_result.attempts,
                    success=repair_result.success,
                    errors_fixed=len(repair_result.diagnostics_resolved),
                )

                if repair_result.success and repair_result.repaired_code:
                    code = repair_result.repaired_code
                    result.success = True
            else:
                result.success = val_result.success

            result.code = code

        except Exception as e:
            result.errors.append(str(e))
            self.logger.log_error("generation_failed", error=str(e), prompt=prompt[:100])

        finally:
            result.total_duration_ms = (time.perf_counter() - pipeline_start) * 1000
            self.metrics.record_latency("pipeline_total", result.total_duration_ms)

        return result

    def validate(
        self, code: str, context: Optional[TypeContext] = None
    ) -> Any:  # Returns ValidationResult
        """Validate generated code.

        Args:
            code: Code to validate
            context: Type context for validation

        Returns:
            ValidationResult from validation pipeline
        """
        start = time.perf_counter()

        language = self.config.project.language
        val_context = ValidationContext(
            type_context=context,
            timeout_ms=self.config.validation.timeout_seconds * 1000,
        )

        result = self.validator.validate(code, language, val_context)

        duration_ms = (time.perf_counter() - start) * 1000
        self.metrics.record_latency("validation", duration_ms)

        return result

    def repair(
        self,
        code: str,
        errors: List[Any],  # List[Diagnostic]
        prompt: str,
        context: Optional[TypeContext] = None,
    ) -> Any:  # Returns RepairResult
        """Repair code based on validation errors.

        Args:
            code: Code to repair
            errors: Validation diagnostics
            prompt: Original prompt
            context: Type context

        Returns:
            RepairResult from repair orchestrator
        """
        if self.repair_orchestrator is None:
            # Lazy initialization
            from maze.repair.orchestrator import RepairOrchestrator

            self.repair_orchestrator = RepairOrchestrator(validator=self.validator)

        repair_ctx = RepairContext(
            type_context=context,
            original_prompt=prompt,
            max_attempts=self.config.constraints.adaptive_weighting and 3 or 1,
        )

        # RepairOrchestrator.repair signature: (code, prompt, grammar, language, context)
        # For now, use empty grammar (full implementation requires grammar from generation)
        result = self.repair_orchestrator.repair(
            code=code,
            prompt=prompt,
            grammar="",  # TODO: Pass actual grammar from generation step
            language=self.config.project.language,
            context=repair_ctx
        )

        return result

    def _synthesize_constraints(
        self, prompt: str, context: Optional[TypeContext]
    ) -> str:
        """Synthesize constraints (grammar) for generation.

        Args:
            prompt: Generation prompt
            context: Type context

        Returns:
            Grammar string for llguidance
        """
        if not self.config.constraints.syntactic_enabled:
            return ""

        # For now, return empty grammar (full implementation requires grammar templates)
        # TODO: Load language-specific templates
        # TODO: Add type constraints if enabled
        # TODO: Add contextual patterns if available

        return ""

    def _generate_with_constraints(
        self, prompt: str, grammar: str, context: Optional[TypeContext]
    ) -> str:
        """Generate code with constraints.

        This is a placeholder - actual implementation requires provider integration.

        Args:
            prompt: Generation prompt
            grammar: Grammar constraints
            context: Type context

        Returns:
            Generated code
        """
        # TODO: Integrate with provider adapters (OpenAI, vLLM, etc.)
        # For now, return placeholder
        return f"// Generated code for: {prompt}\n// TODO: Implement provider integration"

    def run(self, prompt: str, config: Optional[PipelineConfig] = None) -> PipelineResult:
        """Run complete generation pipeline.

        High-level API that handles indexing, generation, validation, and repair.

        Args:
            prompt: Generation prompt
            config: Pipeline configuration (uses default if None)

        Returns:
            PipelineResult with generated code and metrics
        """
        # Index project if not already done
        if self._indexed_context is None:
            self.index_project()

        # Generate with validation and repair
        result = self.generate(prompt)

        # Log final result
        log_result = LogGenerationResult(
            prompt=prompt,
            code=result.code,
            duration_ms=result.total_duration_ms,
            provider=self.config.generation.provider,
            model=self.config.generation.model,
            success=result.success,
            error="; ".join(result.errors) if result.errors else None,
        )
        self.logger.log_generation(prompt, log_result)

        return result

    def close(self) -> None:
        """Clean up resources."""
        self.logger.close()
