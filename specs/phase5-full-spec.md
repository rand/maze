# Phase 5: Adaptive Learning - Full Specification

> **Purpose**: Complete technical specification for the adaptive learning system with pattern mining, constraint learning, project adaptation, feedback loop orchestration, and mnemosyne integration.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Component Specifications](#2-component-specifications)
3. [Data Structures](#3-data-structures)
4. [Interfaces and Protocols](#4-interfaces-and-protocols)
5. [Dependency Graph](#5-dependency-graph)
6. [Test Plan](#6-test-plan)
7. [Performance Requirements](#7-performance-requirements)
8. [Edge Cases and Error Handling](#8-edge-cases-and-error-handling)
9. [Traceability Matrix](#9-traceability-matrix)

---

## 1. Architecture Overview

### System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    Adaptive Learning System                       │
└──────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
     ┌──────────▼────────┐   │   ┌─────────▼──────────┐
     │  Pattern Mining   │   │   │  Constraint        │
     │     Engine        │   │   │  Learning System   │
     └───────────────────┘   │   └────────────────────┘
                              │
                ┌─────────────▼──────────────┐
                │  Feedback Loop             │
                │  Orchestrator              │
                └─────────────┬──────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
   ┌──────▼────────┐  ┌──────▼────────┐  ┌──────▼────────┐
   │ Project       │  │ Mnemosyne     │  │ Hybrid        │
   │ Adaptation    │  │ Integration   │  │ Constraint    │
   │ Manager       │  │               │  │ Weighter      │
   └───────────────┘  └───────────────┘  └───────────────┘
```

### Data Flow

```
Codebase
   │
   ▼
Pattern Mining ────┐
   │               │
   ▼               │
Patterns ──────────┤
   │               │
   ▼               ▼
Constraint    Feedback Loop ◄── Generation Results
Learning           │                    │
   │               │                    │
   ▼               ▼                    ▼
Learned ────► mnemosyne ◄───── Project Profile
Constraints        │
   │               │
   ▼               ▼
Hybrid Weighting ──┐
   │               │
   ▼               ▼
Weighted Constraints ──► Code Generation
```

---

## 2. Component Specifications

### 2.1 Pattern Mining Engine

#### Purpose
Extract reusable patterns from existing codebases for learning and adaptation.

#### Complete Interface

```python
from dataclasses import dataclass
from typing import Protocol, Optional
from pathlib import Path
import ast

@dataclass
class SyntacticPattern:
    """Pattern from syntax/structure analysis."""
    pattern_type: str  # "function", "class", "import", "error_handling"
    template: str  # Code template with placeholders
    frequency: int  # Occurrences in codebase
    examples: list[str]  # Concrete examples
    context: dict[str, Any]  # Additional metadata

@dataclass
class TypePattern:
    """Pattern from type usage analysis."""
    signature: str  # Type signature
    common_usages: list[str]  # How type is typically used
    frequency: int
    generic_variants: list[str]  # Generic instantiations

@dataclass
class SemanticPattern:
    """High-level semantic pattern."""
    intent: str  # "error_handling", "validation", "transformation"
    structure: str  # Abstract structure
    implementations: list[str]  # Concrete implementations
    frequency: int

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
        self.extractors: dict[str, PatternExtractor] = {}

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
        ...

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
        ...

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
        ...

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
        ...

    def rank_patterns(
        self,
        patterns: list[Pattern],
        ranking_criteria: Optional[dict] = None
    ) -> list[ScoredPattern]:
        """
        Rank patterns by relevance and frequency.

        Args:
            patterns: Patterns to rank
            ranking_criteria: Custom ranking weights

        Returns:
            Patterns with scores (sorted descending)
        """
        ...

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
        ...

    def get_mining_stats(self) -> dict[str, Any]:
        """
        Get mining performance statistics.

        Returns:
            Dictionary with stats
        """
        ...
```

#### Implementation Details

**Syntactic Pattern Extraction**:
```python
def _extract_function_patterns(self, ast_node: ast.AST) -> list[SyntacticPattern]:
    """Extract function definition patterns."""
    patterns = []
    for node in ast.walk(ast_node):
        if isinstance(node, ast.FunctionDef):
            # Extract pattern template
            template = self._generalize_function(node)
            patterns.append(SyntacticPattern(
                pattern_type="function",
                template=template,
                frequency=1,  # Updated during aggregation
                examples=[ast.unparse(node)],
                context={
                    "args_count": len(node.args.args),
                    "has_return": any(isinstance(n, ast.Return) for n in ast.walk(node)),
                    "decorators": [d.id for d in node.decorator_list if isinstance(d, ast.Name)]
                }
            ))
    return patterns
```

**Type Pattern Extraction**:
```python
def _extract_type_usage_patterns(self, types: TypeContext) -> list[TypePattern]:
    """Extract common type usage patterns."""
    type_usages: dict[str, list[str]] = {}

    for var_name, var_type in types.variables.items():
        type_str = str(var_type)
        if type_str not in type_usages:
            type_usages[type_str] = []
        type_usages[type_str].append(var_name)

    patterns = []
    for type_str, usages in type_usages.items():
        if len(usages) >= self.min_frequency:
            patterns.append(TypePattern(
                signature=type_str,
                common_usages=usages,
                frequency=len(usages),
                generic_variants=self._find_generic_variants(type_str)
            ))

    return patterns
```

**Performance Optimization**:
- Use parallel processing for large codebases
- Cache parsed ASTs
- Incremental updates for changed files only
- Lazy semantic analysis (only if enabled)

---

### 2.2 Constraint Learning System

#### Purpose
Learn soft constraints from patterns and generation feedback.

#### Complete Interface

```python
@dataclass
class ConstraintRefinement:
    """Constraint update from learning."""
    constraint_type: str  # "syntactic", "type", "semantic", "style"
    operation: str  # "add", "update", "remove", "reweight"
    constraint_data: dict[str, Any]
    weight: float  # 0-1, higher = stronger preference
    rationale: str  # Why this refinement was made
    source: str  # "pattern_mining", "feedback", "user"

@dataclass
class Feedback:
    """Feedback from generation outcome."""
    success: bool
    generation_result: GenerationResult
    validation_result: ValidationResult
    repair_result: Optional[RepairResult]
    score: float  # Overall quality score
    feedback_type: str  # "positive", "negative", "neutral"

class ConstraintLearningSystem:
    """Learn soft constraints from feedback and patterns."""

    def __init__(
        self,
        learning_rate: float = 0.1,
        min_score: float = 0.1,
        max_constraints: int = 10000,
        decay_rate: float = 0.01
    ):
        """
        Initialize constraint learning system.

        Args:
            learning_rate: Weight update rate
            min_score: Minimum score to keep constraint
            max_constraints: Maximum constraints to maintain
            decay_rate: Periodic score decay rate
        """
        self.learning_rate = learning_rate
        self.min_score = min_score
        self.max_constraints = max_constraints
        self.decay_rate = decay_rate
        self.constraints: dict[str, float] = {}  # constraint_id -> weight
        self.learning_history: list[LearningEvent] = []

    def learn_from_success(
        self,
        generation_result: GenerationResult,
        validation_result: ValidationResult
    ) -> ConstraintRefinement:
        """
        Learn from successful generation.

        Args:
            generation_result: Successful generation
            validation_result: Passing validation

        Returns:
            Constraint refinement to apply
        """
        ...

    def learn_from_failure(
        self,
        generation_result: GenerationResult,
        diagnostics: list[Diagnostic]
    ) -> ConstraintRefinement:
        """
        Learn from failed generation.

        Args:
            generation_result: Failed generation
            diagnostics: Validation diagnostics

        Returns:
            Constraint refinement to prevent failure
        """
        ...

    def learn_from_patterns(
        self,
        patterns: PatternSet
    ) -> list[ConstraintRefinement]:
        """
        Create constraints from mined patterns.

        Args:
            patterns: Mined patterns

        Returns:
            List of constraint refinements
        """
        ...

    def update_weights(
        self,
        pattern: Pattern,
        feedback: Feedback
    ) -> float:
        """
        Update pattern weight based on feedback.

        Args:
            pattern: Pattern to update
            feedback: Feedback to incorporate

        Returns:
            New weight value
        """
        ...

    def prune_constraints(
        self,
        min_score: Optional[float] = None
    ) -> int:
        """
        Remove low-scoring constraints.

        Args:
            min_score: Override minimum score

        Returns:
            Number of constraints removed
        """
        ...

    def decay_weights(self) -> None:
        """Apply periodic decay to all weights."""
        ...

    def get_learning_stats(self) -> dict[str, Any]:
        """
        Get learning statistics.

        Returns:
            Dictionary with stats
        """
        ...
```

#### Learning Algorithm

**Positive Feedback (Success)**:
```python
def _update_from_success(self, feedback: Feedback) -> None:
    """Update weights from successful generation."""
    score_delta = self._compute_score_delta(feedback)

    # Identify patterns used in successful generation
    patterns_used = self._extract_patterns_from_code(
        feedback.generation_result.code
    )

    # Boost weights for successful patterns
    for pattern in patterns_used:
        pattern_id = self._pattern_to_id(pattern)
        current_weight = self.constraints.get(pattern_id, 0.5)
        new_weight = min(1.0, current_weight + (self.learning_rate * score_delta))
        self.constraints[pattern_id] = new_weight

        self.learning_history.append(LearningEvent(
            timestamp=time.time(),
            event_type="weight_increase",
            pattern_id=pattern_id,
            old_weight=current_weight,
            new_weight=new_weight,
            reason=f"successful_generation_score_{score_delta}"
        ))
```

**Negative Feedback (Failure)**:
```python
def _update_from_failure(self, feedback: Feedback) -> None:
    """Update weights from failed generation."""
    # Identify patterns in failed generation
    patterns_used = self._extract_patterns_from_code(
        feedback.generation_result.code
    )

    # Analyze failure cause
    failure_type = self._classify_failure(feedback.validation_result.diagnostics)

    # Reduce weights for patterns leading to failures
    for pattern in patterns_used:
        pattern_id = self._pattern_to_id(pattern)
        if pattern_id in self.constraints:
            current_weight = self.constraints[pattern_id]
            penalty = self._compute_penalty(failure_type)
            new_weight = max(0.0, current_weight - (self.learning_rate * penalty))
            self.constraints[pattern_id] = new_weight

            self.learning_history.append(LearningEvent(
                timestamp=time.time(),
                event_type="weight_decrease",
                pattern_id=pattern_id,
                old_weight=current_weight,
                new_weight=new_weight,
                reason=f"failure_{failure_type}"
            ))
```

**Score Computation**:
```python
def _compute_score_delta(self, feedback: Feedback) -> float:
    """Compute score change from feedback."""
    score = 0.0

    if feedback.validation_result.success:
        score += 1.0

    if feedback.repair_result:
        # Fewer repair attempts = better
        score += max(0, 1.0 - (feedback.repair_result.attempts * 0.25))

    # Test results
    if hasattr(feedback.validation_result, 'test_results'):
        test_results = feedback.validation_result.test_results
        if test_results.total > 0:
            score += (test_results.passed / test_results.total)

    # Security (critical)
    security_violations = getattr(feedback.validation_result, 'security_violations', [])
    critical_violations = [v for v in security_violations if v.severity == "critical"]
    score -= len(critical_violations) * 2.0

    return max(-2.0, min(2.0, score))  # Clamp to [-2, 2]
```

---

### 2.3 Project Adaptation Manager

#### Purpose
Adapt Maze to project-specific conventions and patterns.

#### Complete Interface

```python
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
    generation_count: int

@dataclass
class ConventionSet:
    """Project-specific conventions."""
    naming: dict[str, str]  # "function" -> "camelCase", etc.
    structure: dict[str, Any]  # File organization patterns
    testing: dict[str, Any]  # Test patterns
    error_handling: list[str]  # Error handling patterns
    style: dict[str, Any]  # Code style preferences
    apis: dict[str, list[str]]  # Common API usage patterns

@dataclass
class AdaptationStats:
    """Statistics about adaptation progress."""
    total_examples: int
    patterns_learned: int
    conventions_extracted: int
    convergence_score: float  # 0-1, higher = more adapted
    last_updated: float

class ProjectAdaptationManager:
    """Adapt to project-specific conventions."""

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
            convergence_threshold: Convergence target
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
        ...

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
        ...

    def create_adapted_constraints(
        self,
        conventions: ConventionSet
    ) -> ConstraintSet:
        """
        Create constraints from conventions.

        Args:
            conventions: Project conventions

        Returns:
            Constraint set adapted to project
        """
        ...

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
        ...

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
        ...

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
        ...
```

#### Convention Extraction

**Naming Conventions**:
```python
def _extract_naming_conventions(self, patterns: PatternSet) -> dict[str, str]:
    """Extract naming style from patterns."""
    function_names = []
    class_names = []
    variable_names = []

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
        conventions["function"] = style  # "camelCase", "snake_case", etc.

    if class_names:
        style = self._detect_naming_style(class_names)
        conventions["class"] = style  # "PascalCase", etc.

    return conventions

def _detect_naming_style(self, names: list[str]) -> str:
    """Detect predominant naming style."""
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
```

**API Usage Patterns**:
```python
def _extract_api_patterns(self, patterns: PatternSet) -> dict[str, list[str]]:
    """Extract common API usage patterns."""
    api_usage = {}

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
```

---

### 2.4 Feedback Loop Orchestrator

#### Purpose
Coordinate learning from all generation results.

#### Complete Interface

```python
@dataclass
class FeedbackResult:
    """Result of feedback processing."""
    pattern: Pattern
    score: float
    refinements: list[ConstraintRefinement]
    updated_weights: dict[str, float]

@dataclass
class FeedbackStats:
    """Feedback loop statistics."""
    total_feedback_events: int
    positive_events: int
    negative_events: int
    average_score: float
    refinements_applied: int
    last_update: float

class FeedbackLoopOrchestrator:
    """Coordinate learning from generation results."""

    def __init__(
        self,
        learner: ConstraintLearningSystem,
        adapter: ProjectAdaptationManager,
        memory: MnemosyneIntegration,
        enable_auto_persist: bool = True
    ):
        """
        Initialize feedback loop orchestrator.

        Args:
            learner: Constraint learning system
            adapter: Project adaptation manager
            memory: Mnemosyne integration
            enable_auto_persist: Auto-save to mnemosyne
        """
        self.learner = learner
        self.adapter = adapter
        self.memory = memory
        self.enable_auto_persist = enable_auto_persist
        self.stats = FeedbackStats(
            total_feedback_events=0,
            positive_events=0,
            negative_events=0,
            average_score=0.0,
            refinements_applied=0,
            last_update=time.time()
        )

    def process_feedback(
        self,
        generation: GenerationResult,
        validation: ValidationResult,
        repair: Optional[RepairResult] = None,
        project_name: Optional[str] = None
    ) -> FeedbackResult:
        """
        Process feedback from generation outcome.

        Args:
            generation: Generation result
            validation: Validation result
            repair: Optional repair result
            project_name: Optional project identifier

        Returns:
            Feedback processing result

        Performance: <20ms
        """
        ...

    def update_learning_state(
        self,
        feedback: FeedbackResult,
        project_name: Optional[str] = None
    ) -> None:
        """
        Update learning state from feedback.

        Args:
            feedback: Feedback result
            project_name: Optional project identifier
        """
        ...

    def persist_to_memory(
        self,
        feedback: FeedbackResult,
        namespace: str
    ) -> None:
        """
        Persist feedback to mnemosyne.

        Args:
            feedback: Feedback result
            namespace: Memory namespace
        """
        ...

    def get_feedback_stats(self) -> FeedbackStats:
        """
        Get feedback loop statistics.

        Returns:
            Feedback statistics
        """
        ...
```

#### Feedback Processing Flow

```python
def process_feedback(
    self,
    generation: GenerationResult,
    validation: ValidationResult,
    repair: Optional[RepairResult] = None,
    project_name: Optional[str] = None
) -> FeedbackResult:
    """Process feedback from generation outcome."""
    start_time = time.perf_counter()

    # Build feedback object
    feedback = Feedback(
        success=validation.success,
        generation_result=generation,
        validation_result=validation,
        repair_result=repair,
        score=self._compute_overall_score(validation, repair),
        feedback_type=self._classify_feedback(validation, repair)
    )

    # Update statistics
    self.stats.total_feedback_events += 1
    if feedback.success:
        self.stats.positive_events += 1
    else:
        self.stats.negative_events += 1
    self.stats.average_score = (
        (self.stats.average_score * (self.stats.total_feedback_events - 1) + feedback.score)
        / self.stats.total_feedback_events
    )

    # Learn from feedback
    refinements = []
    if feedback.success:
        refinement = self.learner.learn_from_success(generation, validation)
        refinements.append(refinement)
    else:
        refinement = self.learner.learn_from_failure(
            generation,
            validation.diagnostics
        )
        refinements.append(refinement)

    # Update project adaptation if project specified
    if project_name:
        self.adapter.update_from_feedback(project_name, feedback)

    # Extract patterns and update weights
    patterns = self._extract_patterns_from_result(generation)
    updated_weights = {}
    for pattern in patterns:
        new_weight = self.learner.update_weights(pattern, feedback)
        pattern_id = self._pattern_to_id(pattern)
        updated_weights[pattern_id] = new_weight

    self.stats.refinements_applied += len(refinements)
    self.stats.last_update = time.time()

    result = FeedbackResult(
        pattern=patterns[0] if patterns else None,
        score=feedback.score,
        refinements=refinements,
        updated_weights=updated_weights
    )

    # Auto-persist to mnemosyne
    if self.enable_auto_persist and project_name:
        namespace = f"project:{project_name}:feedback"
        self.persist_to_memory(result, namespace)

    processing_time_ms = (time.perf_counter() - start_time) * 1000
    assert processing_time_ms < 20, f"Feedback processing took {processing_time_ms}ms (target: <20ms)"

    return result
```

---

### 2.5 Mnemosyne Integration

#### Purpose
Persistent cross-session learning and agentic orchestration.

#### Complete Interface

```python
@dataclass
class StoredPattern:
    """Pattern stored in mnemosyne."""
    pattern: Pattern
    namespace: str
    importance: int  # 1-10
    score: float
    created_at: float
    last_accessed: float
    access_count: int

@dataclass
class OrchestrationResult:
    """Result from orchestration."""
    task_id: str
    success: bool
    agents_used: list[str]
    duration_ms: float
    outputs: dict[str, Any]

class MnemosyneIntegration:
    """Integration with mnemosyne memory system."""

    def __init__(
        self,
        enable_orchestration: bool = True,
        cache_size: int = 1000
    ):
        """
        Initialize mnemosyne integration.

        Args:
            enable_orchestration: Enable agent orchestration
            cache_size: Local cache size
        """
        self.enable_orchestration = enable_orchestration
        self.cache_size = cache_size
        self.pattern_cache: dict[str, StoredPattern] = {}

    def store_pattern(
        self,
        pattern: Pattern,
        namespace: str,
        importance: int,
        tags: Optional[list[str]] = None
    ) -> None:
        """
        Store pattern in mnemosyne.

        Args:
            pattern: Pattern to store
            namespace: Memory namespace
            importance: Importance (1-10)
            tags: Optional tags for retrieval
        """
        ...

    def recall_patterns(
        self,
        context: GenerationContext,
        namespace: Optional[str] = None,
        limit: int = 10
    ) -> list[ScoredPattern]:
        """
        Recall relevant patterns from memory.

        Args:
            context: Generation context
            namespace: Optional namespace filter
            limit: Maximum patterns to return

        Returns:
            List of patterns with scores

        Performance: <100ms
        """
        ...

    def update_pattern_score(
        self,
        pattern_id: str,
        delta: float
    ) -> None:
        """
        Update pattern score.

        Args:
            pattern_id: Pattern identifier
            delta: Score change
        """
        ...

    def evolve_memories(self) -> EvolutionStats:
        """
        Run memory evolution (consolidation, decay, archival).

        Returns:
            Evolution statistics
        """
        ...

    def orchestrate_learning(
        self,
        task: LearningTask
    ) -> OrchestrationResult:
        """
        Orchestrate multi-agent learning workflow.

        Args:
            task: Learning task specification

        Returns:
            Orchestration result
        """
        ...

    def get_memory_stats(self) -> dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with stats
        """
        ...
```

#### Memory Storage Implementation

```python
def store_pattern(
    self,
    pattern: Pattern,
    namespace: str,
    importance: int,
    tags: Optional[list[str]] = None
) -> None:
    """Store pattern in mnemosyne."""
    # Serialize pattern
    pattern_json = self._serialize_pattern(pattern)

    # Build content for mnemosyne
    content = json.dumps({
        "pattern_type": pattern.__class__.__name__,
        "pattern_data": pattern_json,
        "score": getattr(pattern, 'score', 0.5),
        "metadata": {
            "created_at": time.time(),
            "access_count": 0
        }
    })

    # Compute importance (1-10 scale)
    importance_level = max(1, min(10, importance))

    # Store via mnemosyne CLI
    tag_str = ",".join(tags) if tags else "pattern"
    self._mnemosyne_remember(
        content=content,
        namespace=namespace,
        importance=importance_level,
        tags=tag_str
    )

    # Update local cache
    pattern_id = self._pattern_to_id(pattern)
    self.pattern_cache[pattern_id] = StoredPattern(
        pattern=pattern,
        namespace=namespace,
        importance=importance,
        score=getattr(pattern, 'score', 0.5),
        created_at=time.time(),
        last_accessed=time.time(),
        access_count=0
    )

def _mnemosyne_remember(
    self,
    content: str,
    namespace: str,
    importance: int,
    tags: str
) -> None:
    """Call mnemosyne remember command."""
    cmd = [
        "mnemosyne", "remember",
        "-c", content,
        "-n", namespace,
        "-i", str(importance),
        "-t", tags
    ]
    subprocess.run(cmd, check=True)
```

#### Pattern Recall Implementation

```python
def recall_patterns(
    self,
    context: GenerationContext,
    namespace: Optional[str] = None,
    limit: int = 10
) -> list[ScoredPattern]:
    """Recall relevant patterns from memory."""
    start_time = time.perf_counter()

    # Build query from context
    query = self._context_to_query(context)

    # Query mnemosyne
    recall_args = [
        "mnemosyne", "recall",
        "-q", query,
        "-l", str(limit),
        "-f", "json"
    ]
    if namespace:
        recall_args.extend(["-n", namespace])

    result = subprocess.run(
        recall_args,
        capture_output=True,
        text=True,
        check=True
    )

    # Parse results
    memories = json.loads(result.stdout)

    # Deserialize patterns
    scored_patterns = []
    for memory in memories:
        pattern_data = json.loads(memory["content"])
        pattern = self._deserialize_pattern(pattern_data)

        # Score based on relevance + importance
        relevance_score = memory.get("relevance_score", 0.5)
        importance = memory.get("importance", 5)
        combined_score = (relevance_score * 0.7) + (importance / 10 * 0.3)

        scored_patterns.append(ScoredPattern(
            pattern=pattern,
            score=combined_score
        ))

        # Update cache
        pattern_id = self._pattern_to_id(pattern)
        if pattern_id in self.pattern_cache:
            self.pattern_cache[pattern_id].last_accessed = time.time()
            self.pattern_cache[pattern_id].access_count += 1

    recall_time_ms = (time.perf_counter() - start_time) * 1000
    assert recall_time_ms < 100, f"Pattern recall took {recall_time_ms}ms (target: <100ms)"

    return sorted(scored_patterns, key=lambda sp: sp.score, reverse=True)
```

---

### 2.6 Hybrid Constraint Weighting

#### Purpose
Combine hard and soft constraints with temperature control.

#### Complete Interface

```python
@dataclass
class WeightedConstraintSet:
    """Constraint set with weights."""
    hard_constraints: ConstraintSet  # Binary (always enforced)
    soft_constraints: dict[str, float]  # Constraint ID -> weight
    temperature: float  # 0-1

@dataclass
class TokenWeights:
    """Per-token weights for generation."""
    token_ids: list[int]
    weights: list[float]  # 0-1
    hard_masked: list[bool]  # Hard constraint mask

class HybridConstraintWeighter:
    """Combine hard and soft constraints."""

    def __init__(
        self,
        default_temperature: float = 0.5
    ):
        """
        Initialize hybrid constraint weighter.

        Args:
            default_temperature: Default temperature
        """
        self.default_temperature = default_temperature

    def combine_constraints(
        self,
        hard: ConstraintSet,
        soft: ConstraintSet,
        temperature: Optional[float] = None
    ) -> WeightedConstraintSet:
        """
        Combine hard and soft constraints.

        Args:
            hard: Hard constraints (always enforced)
            soft: Soft constraints (preferences)
            temperature: Temperature (0-1)

        Returns:
            Weighted constraint set
        """
        ...

    def compute_token_weights(
        self,
        weighted_constraints: WeightedConstraintSet,
        current_state: GenerationState
    ) -> TokenWeights:
        """
        Compute per-token weights.

        Args:
            weighted_constraints: Weighted constraints
            current_state: Current generation state

        Returns:
            Token weights
        """
        ...

    def apply_temperature(
        self,
        weights: TokenWeights,
        temperature: float
    ) -> TokenWeights:
        """
        Apply temperature scaling to weights.

        Args:
            weights: Token weights
            temperature: Temperature (0-1)

        Returns:
            Scaled weights
        """
        ...
```

#### Weight Combination Algorithm

```python
def combine_constraints(
    self,
    hard: ConstraintSet,
    soft: ConstraintSet,
    temperature: Optional[float] = None
) -> WeightedConstraintSet:
    """Combine hard and soft constraints."""
    temp = temperature if temperature is not None else self.default_temperature

    # Extract soft constraint weights
    soft_weights = {}
    for constraint in soft.constraints:
        constraint_id = self._constraint_to_id(constraint)
        weight = getattr(constraint, 'weight', 0.5)
        soft_weights[constraint_id] = weight

    return WeightedConstraintSet(
        hard_constraints=hard,
        soft_constraints=soft_weights,
        temperature=temp
    )

def compute_token_weights(
    self,
    weighted_constraints: WeightedConstraintSet,
    current_state: GenerationState
) -> TokenWeights:
    """Compute per-token weights."""
    vocab_size = len(current_state.vocabulary)

    # Start with uniform weights
    token_weights = [1.0] * vocab_size
    hard_masked = [False] * vocab_size

    # Apply hard constraints (binary mask)
    for constraint in weighted_constraints.hard_constraints.constraints:
        allowed_tokens = self._get_allowed_tokens(constraint, current_state)
        for token_id in range(vocab_size):
            if token_id not in allowed_tokens:
                token_weights[token_id] = 0.0
                hard_masked[token_id] = True

    # Apply soft constraints (weight adjustments)
    for constraint_id, weight in weighted_constraints.soft_constraints.items():
        constraint = self._id_to_constraint(constraint_id)
        preferred_tokens = self._get_preferred_tokens(constraint, current_state)

        for token_id in preferred_tokens:
            if not hard_masked[token_id]:
                # Boost weight for preferred tokens
                token_weights[token_id] *= (1.0 + weight)

    # Normalize weights
    total_weight = sum(w for w, masked in zip(token_weights, hard_masked) if not masked)
    if total_weight > 0:
        token_weights = [
            w / total_weight if not masked else 0.0
            for w, masked in zip(token_weights, hard_masked)
        ]

    # Apply temperature
    token_weights_obj = TokenWeights(
        token_ids=list(range(vocab_size)),
        weights=token_weights,
        hard_masked=hard_masked
    )

    if weighted_constraints.temperature != 1.0:
        token_weights_obj = self.apply_temperature(
            token_weights_obj,
            weighted_constraints.temperature
        )

    return token_weights_obj

def apply_temperature(
    self,
    weights: TokenWeights,
    temperature: float
) -> TokenWeights:
    """Apply temperature scaling."""
    import math

    # Temperature scaling
    # temp = 0: very strict (sharpen distribution)
    # temp = 1: neutral (no change)
    # temp > 1: more creative (flatten distribution)

    if temperature == 0:
        # Select top tokens only
        max_weight = max(weights.weights)
        scaled_weights = [
            w if w == max_weight and not masked else 0.0
            for w, masked in zip(weights.weights, weights.hard_masked)
        ]
    else:
        # Softmax-style temperature scaling
        scaled_weights = []
        for w, masked in zip(weights.weights, weights.hard_masked):
            if masked:
                scaled_weights.append(0.0)
            else:
                # Scale by temperature (higher temp = flatter)
                scaled = math.exp(math.log(w + 1e-10) / temperature)
                scaled_weights.append(scaled)

        # Renormalize
        total = sum(scaled_weights)
        if total > 0:
            scaled_weights = [w / total for w in scaled_weights]

    return TokenWeights(
        token_ids=weights.token_ids,
        weights=scaled_weights,
        hard_masked=weights.hard_masked
    )
```

---

## 3. Data Structures

### Pattern Types

```python
from dataclasses import dataclass
from typing import Union

Pattern = Union[SyntacticPattern, TypePattern, SemanticPattern]

@dataclass
class ScoredPattern:
    """Pattern with relevance score."""
    pattern: Pattern
    score: float  # 0-1

@dataclass
class LearningEvent:
    """Event in learning history."""
    timestamp: float
    event_type: str  # "weight_increase", "weight_decrease", "pattern_added"
    pattern_id: str
    old_weight: float
    new_weight: float
    reason: str
```

### Generation Context

```python
@dataclass
class GenerationContext:
    """Context for pattern recall."""
    language: str
    prompt: str
    type_context: TypeContext
    project_name: Optional[str] = None
    recent_code: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
```

### Learning Task

```python
@dataclass
class LearningTask:
    """Task for mnemosyne orchestration."""
    task_type: str  # "pattern_mining", "adaptation", "evolution"
    project_path: Optional[Path] = None
    parameters: dict[str, Any] = field(default_factory=dict)
    priority: int = 1
```

### Evolution Stats

```python
@dataclass
class EvolutionStats:
    """Statistics from memory evolution."""
    patterns_consolidated: int
    patterns_decayed: int
    patterns_archived: int
    duration_ms: float
```

---

## 4. Interfaces and Protocols

### PatternExtractor Protocol

```python
class PatternExtractor(Protocol):
    """Protocol for language-specific pattern extractors."""

    def extract(self, code: str) -> list[Pattern]:
        """Extract patterns from code."""
        ...

    def supports_language(self, language: str) -> bool:
        """Check if language is supported."""
        ...
```

### ConstraintBuilder Protocol

```python
class ConstraintBuilder(Protocol):
    """Protocol for building constraints from patterns."""

    def build_from_pattern(self, pattern: Pattern) -> Constraint:
        """Build constraint from pattern."""
        ...

    def combine_constraints(self, constraints: list[Constraint]) -> ConstraintSet:
        """Combine multiple constraints."""
        ...
```

---

## 5. Dependency Graph

```
Phase 4 Components (Complete)
    │
    ├─► ValidationPipeline ──┐
    │                        │
    ├─► RepairOrchestrator ──┤
    │                        ├──► FeedbackLoopOrchestrator (5.4)
    └─► PedanticRaven ───────┘         │
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────┐
│                    Phase 5 Components                     │
└──────────────────────────────────────────────────────────┘

PatternMiningEngine (5.1) ─────┐
                               │
                               ├──► ConstraintLearningSystem (5.2)
                               │           │
                               │           │
ProjectAdaptationManager (5.3) ┤           │
                               │           │
                               └───────────┤
                                           │
                                           ▼
                              FeedbackLoopOrchestrator (5.4)
                                           │
                  ┌────────────────────────┼──────────────────────┐
                  │                        │                      │
                  ▼                        ▼                      ▼
       MnemosyneIntegration (5.5)  HybridWeighting (5.6)  Integration (5.7)
```

**Critical Path**:
1. PatternMiningEngine (5.1)
2. ConstraintLearningSystem (5.2)
3. FeedbackLoopOrchestrator (5.4)
4. Integration (5.7)

**Parallel Streams**:
- Stream A: 5.1 → 5.2 → 5.4
- Stream B: 5.3 → 5.4
- Stream C: 5.5 (independent)
- Stream D: 5.6 (depends on 5.2)

---

## 6. Test Plan

### Unit Test Breakdown (110 tests total)

#### 6.1 Pattern Mining Engine (maze-zih.5.1) - 20 tests

```python
class TestPatternMiningEngine:
    def test_mine_patterns_basic(self):
        """Test basic pattern mining."""
        ...

    def test_extract_syntactic_patterns_functions(self):
        """Test function pattern extraction."""
        ...

    def test_extract_syntactic_patterns_classes(self):
        """Test class pattern extraction."""
        ...

    def test_extract_type_patterns(self):
        """Test type pattern extraction."""
        ...

    def test_extract_semantic_patterns(self):
        """Test semantic pattern extraction."""
        ...

    def test_rank_patterns_by_frequency(self):
        """Test pattern ranking."""
        ...

    def test_rank_patterns_custom_criteria(self):
        """Test custom ranking criteria."""
        ...

    def test_incremental_mine(self):
        """Test incremental pattern mining."""
        ...

    def test_mining_performance_large_codebase(self):
        """Test performance on large codebase (100K LOC)."""
        ...

    def test_parallel_mining(self):
        """Test parallel mining optimization."""
        ...

    def test_min_frequency_filter(self):
        """Test minimum frequency filtering."""
        ...

    def test_max_patterns_limit(self):
        """Test maximum patterns limit."""
        ...

    def test_pattern_deduplication(self):
        """Test duplicate pattern removal."""
        ...

    def test_context_extraction(self):
        """Test pattern context metadata."""
        ...

    def test_error_handling_invalid_code(self):
        """Test error handling for invalid code."""
        ...

    def test_multi_language_support(self):
        """Test multiple language support."""
        ...

    def test_pattern_template_generalization(self):
        """Test pattern template generalization."""
        ...

    def test_cache_utilization(self):
        """Test AST cache utilization."""
        ...

    def test_mining_stats(self):
        """Test mining statistics."""
        ...

    def test_semantic_pattern_disabled(self):
        """Test with semantic extraction disabled."""
        ...
```

#### 6.2 Constraint Learning System (maze-zih.5.2) - 20 tests

```python
class TestConstraintLearningSystem:
    def test_learn_from_success_basic(self):
        """Test learning from successful generation."""
        ...

    def test_learn_from_failure_basic(self):
        """Test learning from failed generation."""
        ...

    def test_learn_from_patterns(self):
        """Test constraint creation from patterns."""
        ...

    def test_update_weights_positive_feedback(self):
        """Test weight increase from positive feedback."""
        ...

    def test_update_weights_negative_feedback(self):
        """Test weight decrease from negative feedback."""
        ...

    def test_weight_update_learning_rate(self):
        """Test learning rate effect on updates."""
        ...

    def test_prune_constraints(self):
        """Test low-score constraint pruning."""
        ...

    def test_decay_weights(self):
        """Test periodic weight decay."""
        ...

    def test_max_constraints_limit(self):
        """Test maximum constraints enforcement."""
        ...

    def test_score_clamping(self):
        """Test score clamping to valid range."""
        ...

    def test_learning_history_tracking(self):
        """Test learning event history."""
        ...

    def test_pattern_extraction_from_code(self):
        """Test pattern extraction from generated code."""
        ...

    def test_failure_classification(self):
        """Test failure type classification."""
        ...

    def test_penalty_computation(self):
        """Test failure penalty computation."""
        ...

    def test_multi_source_learning(self):
        """Test learning from multiple sources."""
        ...

    def test_constraint_refinement_types(self):
        """Test different refinement types."""
        ...

    def test_learning_stats(self):
        """Test learning statistics."""
        ...

    def test_weight_persistence(self):
        """Test weight persistence across restarts."""
        ...

    def test_convergence_detection(self):
        """Test learning convergence detection."""
        ...

    def test_performance_learning_update(self):
        """Test update performance (<10ms)."""
        ...
```

#### 6.3 Project Adaptation Manager (maze-zih.5.3) - 15 tests

```python
class TestProjectAdaptationManager:
    def test_initialize_project_basic(self):
        """Test basic project initialization."""
        ...

    def test_extract_naming_conventions(self):
        """Test naming convention extraction."""
        ...

    def test_extract_structure_conventions(self):
        """Test structure convention extraction."""
        ...

    def test_extract_testing_conventions(self):
        """Test testing pattern extraction."""
        ...

    def test_extract_api_patterns(self):
        """Test API usage pattern extraction."""
        ...

    def test_create_adapted_constraints(self):
        """Test constraint creation from conventions."""
        ...

    def test_update_from_feedback(self):
        """Test profile update from feedback."""
        ...

    def test_adaptation_stats(self):
        """Test adaptation statistics."""
        ...

    def test_compute_convergence(self):
        """Test convergence computation."""
        ...

    def test_multi_project_isolation(self):
        """Test project isolation."""
        ...

    def test_language_detection(self):
        """Test automatic language detection."""
        ...

    def test_performance_initialization(self):
        """Test initialization performance (<30s)."""
        ...

    def test_convention_conflict_resolution(self):
        """Test handling conflicting conventions."""
        ...

    def test_incremental_adaptation(self):
        """Test incremental adaptation updates."""
        ...

    def test_fallback_to_defaults(self):
        """Test fallback when no conventions found."""
        ...
```

#### 6.4 Feedback Loop Orchestrator (maze-zih.5.4) - 15 tests

```python
class TestFeedbackLoopOrchestrator:
    def test_process_feedback_success(self):
        """Test feedback processing for success."""
        ...

    def test_process_feedback_failure(self):
        """Test feedback processing for failure."""
        ...

    def test_process_feedback_with_repair(self):
        """Test feedback with repair result."""
        ...

    def test_score_computation(self):
        """Test overall score computation."""
        ...

    def test_feedback_classification(self):
        """Test feedback type classification."""
        ...

    def test_statistics_tracking(self):
        """Test statistics updates."""
        ...

    def test_pattern_extraction(self):
        """Test pattern extraction from results."""
        ...

    def test_weight_updates(self):
        """Test weight update coordination."""
        ...

    def test_project_adaptation_integration(self):
        """Test project adaptation integration."""
        ...

    def test_auto_persist_enabled(self):
        """Test auto-persistence to mnemosyne."""
        ...

    def test_auto_persist_disabled(self):
        """Test with auto-persist disabled."""
        ...

    def test_performance_feedback_processing(self):
        """Test processing performance (<20ms)."""
        ...

    def test_refinement_application(self):
        """Test constraint refinement application."""
        ...

    def test_feedback_stats(self):
        """Test feedback statistics."""
        ...

    def test_concurrent_feedback(self):
        """Test concurrent feedback processing."""
        ...
```

#### 6.5 Mnemosyne Integration (maze-zih.5.5) - 15 tests

```python
class TestMnemosyneIntegration:
    def test_store_pattern_basic(self):
        """Test basic pattern storage."""
        ...

    def test_recall_patterns_basic(self):
        """Test basic pattern recall."""
        ...

    def test_recall_patterns_namespace_filter(self):
        """Test namespace-filtered recall."""
        ...

    def test_update_pattern_score(self):
        """Test pattern score updates."""
        ...

    def test_pattern_serialization(self):
        """Test pattern serialization."""
        ...

    def test_pattern_deserialization(self):
        """Test pattern deserialization."""
        ...

    def test_cache_utilization(self):
        """Test local cache utilization."""
        ...

    def test_cache_eviction(self):
        """Test LRU cache eviction."""
        ...

    def test_evolve_memories(self):
        """Test memory evolution."""
        ...

    def test_orchestrate_learning_task(self):
        """Test orchestration (if enabled)."""
        ...

    def test_memory_stats(self):
        """Test memory statistics."""
        ...

    def test_performance_recall(self):
        """Test recall performance (<100ms)."""
        ...

    def test_namespace_isolation(self):
        """Test namespace isolation."""
        ...

    def test_tag_based_retrieval(self):
        """Test tag-based pattern retrieval."""
        ...

    def test_error_handling_mnemosyne_unavailable(self):
        """Test graceful degradation."""
        ...
```

#### 6.6 Hybrid Constraint Weighting (maze-zih.5.6) - 10 tests

```python
class TestHybridConstraintWeighting:
    def test_combine_constraints_basic(self):
        """Test basic constraint combination."""
        ...

    def test_compute_token_weights_hard_only(self):
        """Test with hard constraints only."""
        ...

    def test_compute_token_weights_hard_and_soft(self):
        """Test with both hard and soft constraints."""
        ...

    def test_apply_temperature_zero(self):
        """Test temperature = 0 (strict)."""
        ...

    def test_apply_temperature_one(self):
        """Test temperature = 1 (neutral)."""
        ...

    def test_apply_temperature_high(self):
        """Test temperature > 1 (creative)."""
        ...

    def test_weight_normalization(self):
        """Test weight normalization."""
        ...

    def test_hard_mask_priority(self):
        """Test hard mask takes priority."""
        ...

    def test_soft_weight_boosting(self):
        """Test soft constraint boosting."""
        ...

    def test_temperature_modes(self):
        """Test different temperature modes."""
        ...
```

#### 6.7 Integration Tests (maze-zih.5.7) - 15 tests

```python
class TestIntegration:
    def test_end_to_end_learning_workflow(self):
        """Test complete learning workflow."""
        ...

    def test_cross_session_persistence(self):
        """Test pattern persistence across sessions."""
        ...

    def test_multi_project_learning(self):
        """Test learning from multiple projects."""
        ...

    def test_quality_improvement_after_100_examples(self):
        """Test >10% improvement after 100 examples."""
        ...

    def test_pattern_recall_accuracy(self):
        """Test >90% pattern recall accuracy."""
        ...

    def test_adaptation_convergence(self):
        """Test convergence within 100 examples."""
        ...

    def test_performance_end_to_end(self):
        """Test end-to-end performance."""
        ...

    def test_memory_usage(self):
        """Test memory usage limits."""
        ...

    def test_concurrent_learning(self):
        """Test concurrent learning from multiple sessions."""
        ...

    def test_feedback_loop_integration_with_phase4(self):
        """Test integration with Phase 4 components."""
        ...

    def test_pattern_mining_to_constraints(self):
        """Test pattern → constraint pipeline."""
        ...

    def test_adaptive_generation_improvement(self):
        """Test generation improvement with learning."""
        ...

    def test_cold_start_fallback(self):
        """Test cold start without patterns."""
        ...

    def test_error_recovery(self):
        """Test error recovery in learning loop."""
        ...

    def test_benchmarks_all_metrics(self):
        """Test all performance benchmarks."""
        ...
```

### Test Coverage Targets

- **Pattern Mining**: 90%
- **Constraint Learning**: 90%
- **Project Adaptation**: 85%
- **Feedback Loop**: 90%
- **Mnemosyne Integration**: 85%
- **Hybrid Weighting**: 85%
- **Integration**: 80%
- **Overall**: 85%

---

## 7. Performance Requirements

### Per-Component Targets

| Component | Operation | Target | Critical |
|-----------|-----------|--------|----------|
| PatternMiningEngine | mine_patterns (100K LOC) | <5s | Yes |
| PatternMiningEngine | extract_syntactic | <500ms | No |
| PatternMiningEngine | rank_patterns | <100ms | No |
| ConstraintLearningSystem | update_weights | <10ms | Yes |
| ConstraintLearningSystem | prune_constraints | <50ms | No |
| ProjectAdaptationManager | initialize_project | <30s | No |
| ProjectAdaptationManager | extract_conventions | <2s | No |
| FeedbackLoopOrchestrator | process_feedback | <20ms | Yes |
| MnemosyneIntegration | recall_patterns | <100ms | Yes |
| MnemosyneIntegration | store_pattern | <50ms | No |
| HybridConstraintWeighter | compute_token_weights | <10ms | Yes |
| HybridConstraintWeighter | apply_temperature | <5ms | No |

### System-Level Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Generation overhead | <10% | Compare with/without learning |
| Quality improvement | >10% | After 100 examples |
| Pattern recall accuracy | >90% | Precision + recall |
| Adaptation convergence | <100 examples | Convergence score >0.9 |
| Cross-session retention | >95% | Pattern availability |
| Memory usage | <500MB | Resident set size |

---

## 8. Edge Cases and Error Handling

### 8.1 Cold Start

**Problem**: No patterns available for new project.

**Solution**:
```python
def _handle_cold_start(self, project_name: str) -> PatternSet:
    """Handle cold start with fallback."""
    # Try global patterns
    global_patterns = self.memory.recall_patterns(
        context=GenerationContext(language=self.language, prompt=""),
        namespace="global:patterns",
        limit=50
    )

    if global_patterns:
        logger.info(f"Cold start for {project_name}: using {len(global_patterns)} global patterns")
        return self._convert_to_pattern_set(global_patterns)

    # Fallback to empty patterns
    logger.warning(f"Cold start for {project_name}: no patterns available")
    return PatternSet(
        syntactic=[],
        type_patterns=[],
        semantic=[],
        language=self.language,
        source=Path("."),
        extraction_time_ms=0.0,
        total_patterns=0
    )
```

### 8.2 Pattern Conflicts

**Problem**: Multiple patterns apply with conflicting suggestions.

**Solution**:
```python
def _resolve_pattern_conflicts(
    self,
    patterns: list[ScoredPattern]
) -> ScoredPattern:
    """Resolve conflicting patterns."""
    # Sort by score (descending)
    sorted_patterns = sorted(patterns, key=lambda p: p.score, reverse=True)

    # Check for conflicts
    conflicts = self._detect_conflicts(sorted_patterns)

    if not conflicts:
        return sorted_patterns[0]  # Return highest scored

    # Use recency as tie-breaker
    recent_patterns = [
        p for p in sorted_patterns
        if self._is_recent(p, threshold_days=30)
    ]

    if recent_patterns:
        return recent_patterns[0]

    # Fallback to highest score
    return sorted_patterns[0]
```

### 8.3 Over-fitting

**Problem**: Patterns too specific, reduce creativity.

**Solution**:
```python
def _prevent_overfitting(
    self,
    constraints: ConstraintSet,
    temperature: float
) -> ConstraintSet:
    """Prevent over-specific constraints."""
    # Check constraint specificity
    specificity = self._compute_specificity(constraints)

    if specificity > 0.8:  # Too specific
        # Increase temperature to allow deviation
        adjusted_temp = min(1.0, temperature + 0.2)
        logger.warning(f"High specificity ({specificity:.2f}): increasing temperature to {adjusted_temp:.2f}")

        # Prune most specific constraints
        pruned = self._prune_by_specificity(constraints, keep_ratio=0.7)
        return pruned

    return constraints
```

### 8.4 Memory Exhaustion

**Problem**: Too many patterns stored.

**Solution**:
```python
def _manage_memory_limits(self) -> None:
    """Manage memory usage."""
    current_patterns = len(self.constraints)

    if current_patterns > self.max_constraints:
        # Prune by score
        pruned = self.prune_constraints(min_score=self.min_score)
        logger.info(f"Pruned {pruned} low-scoring patterns")

        # If still over limit, increase min_score
        if len(self.constraints) > self.max_constraints:
            new_min_score = self._compute_adaptive_threshold(
                target_count=self.max_constraints
            )
            pruned = self.prune_constraints(min_score=new_min_score)
            logger.info(f"Increased min_score to {new_min_score:.2f}, pruned {pruned} more patterns")
```

### 8.5 Cross-Project Pollution

**Problem**: Wrong patterns recalled for project.

**Solution**:
```python
def recall_patterns(
    self,
    context: GenerationContext,
    namespace: Optional[str] = None,
    limit: int = 10
) -> list[ScoredPattern]:
    """Recall patterns with namespace isolation."""
    # Prefer project-specific namespace
    if context.project_name:
        project_namespace = f"project:{context.project_name}:patterns"
        project_patterns = self._recall_from_namespace(
            context,
            project_namespace,
            limit=limit
        )

        if len(project_patterns) >= limit // 2:
            # Sufficient project-specific patterns
            return project_patterns

        # Supplement with global patterns
        global_patterns = self._recall_from_namespace(
            context,
            "global:patterns",
            limit=limit - len(project_patterns)
        )

        return project_patterns + global_patterns

    # Fallback to global
    return self._recall_from_namespace(context, "global:patterns", limit=limit)
```

### 8.6 Stale Patterns

**Problem**: Outdated conventions from old code.

**Solution**:
```python
def _apply_time_decay(self, patterns: list[ScoredPattern]) -> list[ScoredPattern]:
    """Apply time-based decay to pattern scores."""
    current_time = time.time()

    decayed = []
    for pattern in patterns:
        # Get pattern age
        created_at = getattr(pattern.pattern, 'created_at', current_time)
        age_days = (current_time - created_at) / (24 * 3600)

        # Apply exponential decay
        # Half-life = 90 days
        decay_factor = 0.5 ** (age_days / 90)

        decayed_score = pattern.score * decay_factor

        decayed.append(ScoredPattern(
            pattern=pattern.pattern,
            score=decayed_score
        ))

    return decayed
```

### 8.7 Performance Degradation

**Problem**: Too many soft constraints slow generation.

**Solution**:
```python
def _adaptive_constraint_filtering(
    self,
    soft_constraints: dict[str, float],
    max_active: int = 100
) -> dict[str, float]:
    """Filter soft constraints adaptively."""
    if len(soft_constraints) <= max_active:
        return soft_constraints

    # Sort by weight
    sorted_constraints = sorted(
        soft_constraints.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Keep top N
    filtered = dict(sorted_constraints[:max_active])

    logger.info(
        f"Filtered soft constraints: {len(soft_constraints)} → {len(filtered)}"
    )

    return filtered
```

---

## 9. Traceability Matrix

| Requirement | Spec | Component | Tests | Implementation |
|-------------|------|-----------|-------|----------------|
| REQ-5.1: Pattern Mining | phase5-spec.md#1 | PatternMiningEngine | test_pattern_mining.py | pattern_mining.py |
| REQ-5.2: Syntactic Patterns | phase5-spec.md#1 | PatternMiningEngine | test_pattern_mining.py::test_extract_syntactic | pattern_mining.py::extract_syntactic_patterns |
| REQ-5.3: Type Patterns | phase5-spec.md#1 | PatternMiningEngine | test_pattern_mining.py::test_extract_type | pattern_mining.py::extract_type_patterns |
| REQ-5.4: Semantic Patterns | phase5-spec.md#1 | PatternMiningEngine | test_pattern_mining.py::test_extract_semantic | pattern_mining.py::extract_semantic_patterns |
| REQ-5.5: Pattern Ranking | phase5-spec.md#1 | PatternMiningEngine | test_pattern_mining.py::test_rank_patterns | pattern_mining.py::rank_patterns |
| REQ-5.6: Constraint Learning | phase5-spec.md#2 | ConstraintLearningSystem | test_constraint_learning.py | constraint_learning.py |
| REQ-5.7: Learn from Success | phase5-spec.md#2 | ConstraintLearningSystem | test_constraint_learning.py::test_learn_from_success | constraint_learning.py::learn_from_success |
| REQ-5.8: Learn from Failure | phase5-spec.md#2 | ConstraintLearningSystem | test_constraint_learning.py::test_learn_from_failure | constraint_learning.py::learn_from_failure |
| REQ-5.9: Weight Updates | phase5-spec.md#2 | ConstraintLearningSystem | test_constraint_learning.py::test_update_weights | constraint_learning.py::update_weights |
| REQ-5.10: Constraint Pruning | phase5-spec.md#2 | ConstraintLearningSystem | test_constraint_learning.py::test_prune_constraints | constraint_learning.py::prune_constraints |
| REQ-5.11: Project Adaptation | phase5-spec.md#3 | ProjectAdaptationManager | test_project_adaptation.py | project_adaptation.py |
| REQ-5.12: Convention Extraction | phase5-spec.md#3 | ProjectAdaptationManager | test_project_adaptation.py::test_extract_conventions | project_adaptation.py::extract_conventions |
| REQ-5.13: Adapted Constraints | phase5-spec.md#3 | ProjectAdaptationManager | test_project_adaptation.py::test_create_adapted_constraints | project_adaptation.py::create_adapted_constraints |
| REQ-5.14: Feedback Loop | phase5-spec.md#4 | FeedbackLoopOrchestrator | test_feedback_loop.py | feedback_loop.py |
| REQ-5.15: Feedback Processing | phase5-spec.md#4 | FeedbackLoopOrchestrator | test_feedback_loop.py::test_process_feedback | feedback_loop.py::process_feedback |
| REQ-5.16: mnemosyne Storage | phase5-spec.md#5 | MnemosyneIntegration | test_mnemosyne_integration.py | mnemosyne_integration.py |
| REQ-5.17: Pattern Recall | phase5-spec.md#5 | MnemosyneIntegration | test_mnemosyne_integration.py::test_recall_patterns | mnemosyne_integration.py::recall_patterns |
| REQ-5.18: Memory Evolution | phase5-spec.md#5 | MnemosyneIntegration | test_mnemosyne_integration.py::test_evolve_memories | mnemosyne_integration.py::evolve_memories |
| REQ-5.19: Hybrid Weighting | phase5-spec.md#6 | HybridConstraintWeighter | test_hybrid_weighting.py | hybrid_weighting.py |
| REQ-5.20: Token Weights | phase5-spec.md#6 | HybridConstraintWeighter | test_hybrid_weighting.py::test_compute_token_weights | hybrid_weighting.py::compute_token_weights |
| REQ-5.21: Temperature Control | phase5-spec.md#6 | HybridConstraintWeighter | test_hybrid_weighting.py::test_apply_temperature | hybrid_weighting.py::apply_temperature |
| REQ-5.22: Quality Improvement | phase5-spec.md | Integration | test_integration.py::test_quality_improvement | - |
| REQ-5.23: Pattern Accuracy | phase5-spec.md | Integration | test_integration.py::test_pattern_recall_accuracy | - |
| REQ-5.24: Convergence Speed | phase5-spec.md | Integration | test_integration.py::test_adaptation_convergence | - |

---

## Summary

This full specification provides:

1. **Complete component breakdown** with detailed interfaces
2. **Comprehensive data structures** for all pattern and learning types
3. **Dependency graph** showing critical path and parallelization
4. **Detailed test plan** with 110 tests across all components
5. **Performance requirements** with specific targets
6. **Edge case handling** with concrete solutions
7. **Traceability matrix** linking requirements to implementation

**Next Steps**: Create execution plan (phase5-plan.md) with task ordering, time estimates, and implementation sequence.
