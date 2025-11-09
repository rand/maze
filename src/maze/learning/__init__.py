"""
Learning module for adaptive constraint-based code generation.

Provides pattern mining, constraint learning, and project adaptation.
"""

# Core pattern mining (no circular dependencies)
from maze.learning.pattern_mining import (
    PatternMiningEngine,
    SyntacticPattern,
    TypePattern,
    SemanticPattern,
    PatternSet
)

# Constraint learning (no circular dependencies)
from maze.learning.constraint_learning import (
    ConstraintLearningSystem,
    ConstraintRefinement,
    Feedback,
    GenerationResult,
    ValidationResult,
    RepairResult,
    LearningEvent,
)

# Project adaptation (no circular dependencies)
from maze.learning.project_adaptation import (
    ProjectAdaptationManager,
    ProjectProfile,
    ConventionSet,
    AdaptationStats,
)

# Hybrid weighting (no circular dependencies)
from maze.learning.hybrid_weighting import (
    HybridConstraintWeighter,
    WeightedConstraintSet,
    TokenWeights,
    ConstraintSet,
    GenerationState,
)

# Feedback orchestrator uses lazy import to avoid circular dependency
# (imports mnemosyne which imports pattern_mining)
# Import directly: from maze.learning.feedback_orchestrator import FeedbackLoopOrchestrator

__all__ = [
    # Pattern mining
    "PatternMiningEngine",
    "SyntacticPattern",
    "TypePattern",
    "SemanticPattern",
    "PatternSet",
    # Constraint learning
    "ConstraintLearningSystem",
    "ConstraintRefinement",
    "Feedback",
    "GenerationResult",
    "ValidationResult",
    "RepairResult",
    "LearningEvent",
    # Project adaptation
    "ProjectAdaptationManager",
    "ProjectProfile",
    "ConventionSet",
    "AdaptationStats",
    # Hybrid weighting
    "HybridConstraintWeighter",
    "WeightedConstraintSet",
    "TokenWeights",
    "ConstraintSet",
    "GenerationState",
    # Feedback orchestration (use direct import to avoid circular dependency)
    # "FeedbackLoopOrchestrator",
    # "FeedbackResult",
    # "FeedbackStats",
]
