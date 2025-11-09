"""
Learning module for adaptive constraint-based code generation.

Provides pattern mining, constraint learning, and project adaptation.
"""

from maze.learning.pattern_mining import (
    PatternMiningEngine,
    SyntacticPattern,
    TypePattern,
    SemanticPattern,
    PatternSet
)

__all__ = [
    "PatternMiningEngine",
    "SyntacticPattern",
    "TypePattern",
    "SemanticPattern",
    "PatternSet",
]
