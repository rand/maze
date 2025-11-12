"""
Type system module for Maze.

Provides type inference, inhabitation search, and hole-driven code generation
with TypeScript support.
"""

from typing import Any, Dict, Optional

from maze.core.types import GenerationResult, Type, TypeContext
from maze.orchestrator.providers import GenerationRequest, GenerationResponse, ProviderAdapter
from maze.type_system.grammar_converter import TypeToGrammarConverter
from maze.type_system.holes import Hole, HoleFillingEngine, HoleFillResult
from maze.type_system.inference import InferenceResult, TypeInferenceEngine
from maze.type_system.inhabitation import InhabitationPath, InhabitationSolver
from maze.type_system.languages.typescript import TypeScriptTypeSystem


class TypeSystemOrchestrator:
    """
    Orchestrator for type-directed code generation.

    Integrates all type system components to provide a unified interface
    for type-safe code generation.

    Example:
        >>> orchestrator = TypeSystemOrchestrator(language="typescript")
        >>> context = TypeContext(variables={"x": Type("number")})
        >>> # Generate code with type constraints
        >>> result = orchestrator.generate_with_type_constraints(
        ...     prompt="Generate a function that doubles a number",
        ...     context=context,
        ...     expected_type=Type("function", (Type("number"), Type("number")))
        ... )
    """

    def __init__(self, language: str = "typescript"):
        """
        Initialize type system orchestrator.

        Args:
            language: Target language (typescript, python, rust)
        """
        self.language = language

        # Initialize components
        self.inference = TypeInferenceEngine()
        self.inhabitation = InhabitationSolver(max_depth=5, cache_size=1000)
        self.converter = TypeToGrammarConverter(language=language)

        # Language-specific type system
        if language == "typescript":
            self.type_system = TypeScriptTypeSystem()
        else:
            # Default to TypeScript for now
            self.type_system = TypeScriptTypeSystem()

    def generate_with_type_constraints(
        self,
        prompt: str,
        context: TypeContext,
        expected_type: Type | None = None,
        provider: ProviderAdapter | None = None,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> GenerationResult:
        """
        Generate code with type constraints.

        Args:
            prompt: Generation prompt
            context: Type context
            expected_type: Expected type for generated code
            provider: Provider adapter for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            GenerationResult with generated code and metadata

        Example:
            >>> orchestrator = TypeSystemOrchestrator()
            >>> context = TypeContext()
            >>> result = orchestrator.generate_with_type_constraints(
            ...     prompt="Generate number 42",
            ...     context=context,
            ...     expected_type=Type("number")
            ... )
        """
        # Generate grammar from expected type
        grammar = None
        if expected_type:
            grammar = self.converter.convert(expected_type, context)

        # If no provider, return mock result
        if not provider:
            return GenerationResult(
                code="",
                success=False,
                language=self.language,
                provider="none",
                model="none",
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                generation_time_ms=0.0,
                grammar_used=grammar,
            )

        # Generate with provider
        import time

        start_time = time.perf_counter()

        request = GenerationRequest(
            prompt=prompt, grammar=grammar, max_tokens=max_tokens, temperature=temperature
        )

        try:
            response = provider.generate(request)
            generation_time_ms = (time.perf_counter() - start_time) * 1000

            return GenerationResult(
                code=response.text,
                success=True,
                language=self.language,
                provider=provider.__class__.__name__,
                model=getattr(provider, "model", "unknown"),
                prompt_tokens=response.metadata.get("prompt_tokens", 0),
                completion_tokens=response.tokens_generated,
                total_tokens=response.metadata.get("total_tokens", response.tokens_generated),
                generation_time_ms=generation_time_ms,
                grammar_used=grammar,
            )
        except Exception:
            generation_time_ms = (time.perf_counter() - start_time) * 1000

            return GenerationResult(
                code="",
                success=False,
                language=self.language,
                provider=provider.__class__.__name__,
                model=getattr(provider, "model", "unknown"),
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                generation_time_ms=generation_time_ms,
                grammar_used=grammar,
            )

    def fill_typed_holes(
        self, code: str, context: TypeContext, provider: ProviderAdapter | None = None
    ) -> tuple[str, list[HoleFillResult]]:
        """
        Fill typed holes in code.

        Args:
            code: Code with typed holes
            context: Type context
            provider: Provider adapter for generation

        Returns:
            Tuple of (filled code, list of fill results)

        Example:
            >>> orchestrator = TypeSystemOrchestrator()
            >>> code = "const x: number = /*__HOLE_value__*/"
            >>> context = TypeContext()
            >>> filled, results = orchestrator.fill_typed_holes(code, context)
        """
        hole_engine = HoleFillingEngine(self.inference, self.converter, provider)

        return hole_engine.fill_all_holes(code, context, self.language)

    def infer_type(self, expr: Any, context: TypeContext) -> InferenceResult:
        """
        Infer type of expression.

        Args:
            expr: Expression to infer type for
            context: Type context

        Returns:
            Inference result with type and constraints
        """
        return self.inference.infer_expression(expr, context)

    def find_inhabitation_path(
        self, source: Type, target: Type, context: TypeContext
    ) -> InhabitationPath | None:
        """
        Find transformation path from source to target type.

        Args:
            source: Source type
            target: Target type
            context: Type context

        Returns:
            Best inhabitation path, or None if impossible
        """
        return self.inhabitation.find_best_path(source, target, context)

    def parse_type(self, type_annotation: str) -> Type:
        """
        Parse type annotation to Type.

        Args:
            type_annotation: Type annotation string

        Returns:
            Parsed Type

        Example:
            >>> orchestrator = TypeSystemOrchestrator()
            >>> type_obj = orchestrator.parse_type("Array<string>")
            >>> print(type_obj.name)
            Array
        """
        return self.type_system.parse_type(type_annotation)

    def is_assignable(self, source: Type, target: Type) -> bool:
        """
        Check if source type is assignable to target.

        Args:
            source: Source type
            target: Target type

        Returns:
            True if assignable

        Example:
            >>> orchestrator = TypeSystemOrchestrator()
            >>> orchestrator.is_assignable(Type("string"), Type("string"))
            True
        """
        return self.type_system.is_assignable(source, target)

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get performance statistics from caches.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "inference_cache_size": len(self.inference.inference_cache),
            "inhabitation_stats": self.inhabitation.get_cache_stats(),
        }

    def clear_caches(self) -> None:
        """Clear all internal caches."""
        self.inference.inference_cache.clear()
        self.inhabitation.clear_cache()


# Re-export commonly used classes
__all__ = [
    # Main orchestrator
    "TypeSystemOrchestrator",
    # Core components
    "TypeInferenceEngine",
    "InhabitationSolver",
    "TypeScriptTypeSystem",
    "TypeToGrammarConverter",
    "HoleFillingEngine",
    # Data structures
    "InferenceResult",
    "InhabitationPath",
    "Hole",
    "HoleFillResult",
]
