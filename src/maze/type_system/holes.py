"""
Hole filling engine for hole-driven code generation.

Implements typed hole identification, type inference, grammar generation,
and constrained hole filling with retry logic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Literal

from maze.core.types import Type, TypeContext
from maze.type_system.inference import TypeInferenceEngine
from maze.type_system.grammar_converter import TypeToGrammarConverter
from maze.orchestrator.providers import ProviderAdapter, GenerationRequest


@dataclass
class Hole:
    """
    Typed hole in code.

    Represents a location in code that needs to be filled with
    type-constrained generation.

    Examples:
        >>> hole = Hole(
        ...     name="formatName",
        ...     location=(10, 5),
        ...     expected_type=Type("string"),
        ...     context=TypeContext(),
        ...     kind="expression"
        ... )
    """
    name: str
    location: Tuple[int, int]  # (line, column)
    expected_type: Optional[Type]
    context: TypeContext
    kind: Literal["expression", "statement", "type"]
    original_code: str = ""  # Code surrounding the hole

@dataclass
class HoleFillResult:
    """
    Result of filling a hole.

    Contains the filled code, inferred type, grammar used,
    and success status.
    """
    hole: Hole
    filled_code: str
    inferred_type: Type
    grammar_used: str
    success: bool
    attempts: int
    error_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hole_name": self.hole.name,
            "filled_code": self.filled_code,
            "inferred_type": str(self.inferred_type),
            "success": self.success,
            "attempts": self.attempts,
            "error_message": self.error_message
        }


class HoleFillingEngine:
    """
    Engine for hole-driven code generation.

    Identifies typed holes in code, infers expected types,
    generates type-constrained grammars, and fills holes using
    constrained generation.

    Performance target: <10ms per hole
    """

    # Hole patterns for different languages
    HOLE_PATTERNS = {
        "typescript": r"/\*__HOLE_(\w+)__\*/",
        "python": r"#\s*__HOLE_(\w+)__",
        "rust": r"/\*\s*__HOLE_(\w+)__\s*\*/"
    }

    def __init__(
        self,
        inference_engine: TypeInferenceEngine,
        grammar_converter: TypeToGrammarConverter,
        provider: Optional[ProviderAdapter] = None
    ):
        """
        Initialize hole filling engine.

        Args:
            inference_engine: Type inference engine
            grammar_converter: Type-to-grammar converter
            provider: Provider adapter for generation (optional)
        """
        self.inference = inference_engine
        self.converter = grammar_converter
        self.provider = provider

    def identify_holes(self, code: str, language: str = "typescript") -> List[Hole]:
        """
        Identify typed holes in code.

        Args:
            code: Source code containing holes
            language: Programming language

        Returns:
            List of identified holes

        Example:
            >>> engine = HoleFillingEngine(
            ...     TypeInferenceEngine(),
            ...     TypeToGrammarConverter()
            ... )
            >>> code = "const x: string = /*__HOLE_value__*/"
            >>> holes = engine.identify_holes(code)
            >>> print(len(holes))
            1
        """
        pattern = self.HOLE_PATTERNS.get(language, self.HOLE_PATTERNS["typescript"])
        holes = []

        for match in re.finditer(pattern, code):
            hole_name = match.group(1)
            start_pos = match.start()

            # Calculate line and column
            line = code[:start_pos].count('\n') + 1
            column = start_pos - code[:start_pos].rfind('\n')

            # Create hole with empty context for now
            # Full implementation would parse surrounding code for context
            hole = Hole(
                name=hole_name,
                location=(line, column),
                expected_type=None,  # Will be inferred
                context=TypeContext(language=language),
                kind="expression",  # Simplified
                original_code=code
            )

            holes.append(hole)

        return holes

    def infer_hole_type(
        self,
        hole: Hole,
        context: TypeContext
    ) -> Type:
        """
        Infer expected type for hole.

        Args:
            hole: Hole to infer type for
            context: Type context

        Returns:
            Inferred type

        Example:
            >>> engine = HoleFillingEngine(
            ...     TypeInferenceEngine(),
            ...     TypeToGrammarConverter()
            ... )
            >>> hole = Hole("x", (1, 1), None, TypeContext(), "expression")
            >>> inferred = engine.infer_hole_type(hole, TypeContext())
            >>> print(inferred.name)
            unknown
        """
        # If type is already specified, use it
        if hole.expected_type:
            return hole.expected_type

        # Try to infer from context
        # In full implementation, would parse surrounding code
        # and use type inference engine

        # For now, try to look up variable type from context
        if hole.name in context.variables:
            return context.variables[hole.name]

        # Default to unknown
        return Type("unknown")

    def generate_grammar_for_hole(
        self,
        hole: Hole,
        hole_type: Type
    ) -> str:
        """
        Generate grammar constrained by hole type.

        Args:
            hole: Hole to generate grammar for
            hole_type: Expected type for hole

        Returns:
            Lark grammar string

        Example:
            >>> engine = HoleFillingEngine(
            ...     TypeInferenceEngine(),
            ...     TypeToGrammarConverter()
            ... )
            >>> hole = Hole("x", (1, 1), Type("number"), TypeContext(), "expression")
            >>> grammar = engine.generate_grammar_for_hole(hole, Type("number"))
            >>> print("number_value" in grammar)
            True
        """
        return self.converter.convert(hole_type, hole.context)

    def fill_hole(
        self,
        hole: Hole,
        max_attempts: int = 3
    ) -> HoleFillResult:
        """
        Fill hole with type-constrained generation.

        Args:
            hole: Hole to fill
            max_attempts: Maximum fill attempts

        Returns:
            Hole fill result

        Example:
            >>> from unittest.mock import Mock
            >>> engine = HoleFillingEngine(
            ...     TypeInferenceEngine(),
            ...     TypeToGrammarConverter(),
            ...     None  # No provider for this example
            ... )
            >>> hole = Hole("x", (1, 1), Type("number"), TypeContext(), "expression")
            >>> # Without provider, this will fail gracefully
            >>> result = engine.fill_hole(hole, max_attempts=1)
            >>> print(result.success)
            False
        """
        # Infer hole type
        hole_type = self.infer_hole_type(hole, hole.context)

        # Generate grammar
        grammar = self.generate_grammar_for_hole(hole, hole_type)

        # Check if provider is available
        if not self.provider:
            return HoleFillResult(
                hole=hole,
                filled_code="",
                inferred_type=hole_type,
                grammar_used=grammar,
                success=False,
                attempts=0,
                error_message="No provider configured"
            )

        # Attempt to fill hole
        for attempt in range(1, max_attempts + 1):
            try:
                # Generate with constraints
                request = GenerationRequest(
                    prompt=f"Fill the hole {hole.name} with a value of type {hole_type}",
                    grammar=grammar,
                    max_tokens=100,
                    temperature=0.7
                )

                response = self.provider.generate(request)

                # Validate generated code
                # In full implementation, would parse and type-check
                if response.text.strip():
                    return HoleFillResult(
                        hole=hole,
                        filled_code=response.text.strip(),
                        inferred_type=hole_type,
                        grammar_used=grammar,
                        success=True,
                        attempts=attempt
                    )

            except Exception as e:
                if attempt == max_attempts:
                    return HoleFillResult(
                        hole=hole,
                        filled_code="",
                        inferred_type=hole_type,
                        grammar_used=grammar,
                        success=False,
                        attempts=attempt,
                        error_message=str(e)
                    )

        # All attempts failed
        return HoleFillResult(
            hole=hole,
            filled_code="",
            inferred_type=hole_type,
            grammar_used=grammar,
            success=False,
            attempts=max_attempts,
            error_message="Max attempts exceeded"
        )

    def fill_all_holes(
        self,
        code: str,
        context: TypeContext,
        language: str = "typescript"
    ) -> Tuple[str, List[HoleFillResult]]:
        """
        Fill all holes in code.

        Args:
            code: Source code with holes
            context: Type context
            language: Programming language

        Returns:
            Tuple of (filled code, list of fill results)

        Example:
            >>> engine = HoleFillingEngine(
            ...     TypeInferenceEngine(),
            ...     TypeToGrammarConverter()
            ... )
            >>> code = "const x: number = /*__HOLE_value__*/"
            >>> context = TypeContext()
            >>> filled, results = engine.fill_all_holes(code, context)
            >>> print(len(results))
            1
        """
        # Identify all holes
        holes = self.identify_holes(code, language)

        if not holes:
            return code, []

        # Fill each hole
        results = []
        filled_code = code

        for hole in holes:
            # Update hole context
            hole.context = context

            # Fill hole
            result = self.fill_hole(hole)
            results.append(result)

            # Replace hole in code if successful
            if result.success:
                pattern = self.HOLE_PATTERNS.get(language, self.HOLE_PATTERNS["typescript"])
                hole_pattern = pattern.replace(r"(\w+)", re.escape(hole.name))
                filled_code = re.sub(hole_pattern, result.filled_code, filled_code, count=1)

        return filled_code, results


# Re-export for cleaner imports
__all__ = [
    "Hole",
    "HoleFillResult",
    "HoleFillingEngine",
]
