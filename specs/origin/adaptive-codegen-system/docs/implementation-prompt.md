# Implementation Prompt for Adaptive Constraint-Based Code Generation System

## System Context

You are tasked with implementing ACCS (Adaptive Constraint-Based Code Generation System), a sophisticated framework that enhances LLM code generation through intelligent constraint management. The system must integrate with llguidance for high-performance constrained decoding while adding multiple layers of type-aware, semantic, and contextual constraints.

## Core Requirements

### 1. Architecture Overview
Build a modular system with these key components:
- **Constraint Analysis Engine**: Extracts constraints from specifications
- **llguidance Integration Layer**: Provides fast token masking
- **Type System Module**: Implements type-directed synthesis
- **Adaptive Learning Component**: Learns from successful generations
- **Generation Orchestrator**: Coordinates the entire pipeline

### 2. Technical Specifications

#### Performance Requirements
- Token mask computation: <100μs (using llguidance)
- Type checking overhead: <1ms per token
- Memory footprint: <1GB for typical projects
- Startup time: <500ms
- Support for vocabularies up to 256k tokens

#### Correctness Guarantees
- 100% syntactic validity (via CFG constraints)
- Type safety with gradual typing support
- Semantic constraint satisfaction when specified
- Preservation of model's natural distribution (minimally invasive)

## Implementation Guidelines

### Phase 1: Core Constraint Engine

```python
# Start with this base architecture
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod
import llguidance

@dataclass
class ConstraintSet:
    """Hierarchical constraint representation"""
    syntactic: 'SyntacticConstraints'
    type_based: 'TypeConstraints'
    semantic: 'SemanticConstraints'
    contextual: 'ContextualConstraints'
    
    def compute_mask(self, state: 'GenerationState', vocab: List[str]) -> 'TokenMask':
        """Compute token mask combining all constraint levels"""
        # Start with syntactic constraints (fastest)
        mask = self.syntactic.get_mask(state, vocab)
        
        # Apply type constraints (moderate cost)
        if state.requires_type_checking:
            mask &= self.type_based.get_mask(state, vocab)
        
        # Apply semantic constraints (expensive, use sparingly)
        if state.at_critical_point:
            mask &= self.semantic.get_mask(state, vocab)
            
        # Apply soft contextual constraints
        weights = self.contextual.get_weights(state, vocab)
        mask = self._apply_soft_constraints(mask, weights)
        
        return mask
```

### Phase 2: llguidance Integration

Implement efficient parsing using llguidance's architecture:

```python
class LLGuidanceAdapter:
    """Adapter for llguidance high-performance parsing"""
    
    def __init__(self, grammar: str, tokenizer: Any):
        # Build the parser with llguidance
        self.parser = llguidance.LLGuidance(
            grammar,
            tokenizer,
            model_type="transformers"  # or "llama.cpp", "openai"
        )
        
        # Build token trie for efficient traversal
        self.token_trie = self._build_trie(tokenizer.get_vocab())
        
        # Initialize caches
        self.mask_cache = LRUCache(capacity=10000)
        self.state_cache = StateCache()
        
    def compute_mask(self, text: str, vocab_size: int) -> List[bool]:
        """Compute valid token mask for current position"""
        # Check cache
        cache_key = hash(text)
        if cache_key in self.mask_cache:
            return self.mask_cache[cache_key]
        
        # Get parser state
        state = self.parser.parse_partial(text)
        
        # Compute mask via trie traversal
        mask = [False] * vocab_size
        for token_id, token_bytes in enumerate(self.token_trie):
            if self._can_continue(state, token_bytes):
                mask[token_id] = True
                
        # Cache result
        self.mask_cache[cache_key] = mask
        return mask
```

### Phase 3: Type System Implementation

Implement type-directed synthesis with inhabitation checking:

```python
class TypeDirectedSynthesizer:
    """Type-aware code synthesis engine"""
    
    def __init__(self, type_system: 'TypeSystem'):
        self.type_checker = TypeChecker(type_system)
        self.inhabitation_solver = InhabitationSolver()
        self.reachability_graph = TypeReachabilityGraph()
        
    def synthesize_completion(
        self,
        partial_code: str,
        target_type: 'Type',
        context: 'TypeContext'
    ) -> List['Completion']:
        """Generate type-correct completions"""
        
        # Parse partial code
        ast = parse_partial(partial_code)
        
        # Identify holes
        holes = self.find_holes(ast)
        
        for hole in holes:
            # Get expected type
            expected = self.type_checker.get_expected_type(hole, context)
            
            # Find inhabitation paths
            paths = self.inhabitation_solver.find_paths(
                current_type=hole.inferred_type,
                target_type=expected,
                context=context,
                max_depth=5
            )
            
            # Generate completions
            completions = []
            for path in paths[:10]:  # Limit to top 10
                code = self.path_to_code(path, context)
                completions.append(Completion(code, path.cost))
                
        return sorted(completions, key=lambda c: c.cost)
    
    def path_to_code(self, path: 'TypePath', context: 'TypeContext') -> str:
        """Convert type inhabitation path to concrete code"""
        code_fragments = []
        
        for step in path.steps:
            if isinstance(step, FunctionApplication):
                code_fragments.append(f"{step.function}(")
            elif isinstance(step, MemberAccess):
                code_fragments.append(f".{step.member}")
            elif isinstance(step, TypeCast):
                code_fragments.append(f" as {step.target_type}")
                
        return "".join(code_fragments)
```

### Phase 4: Adaptive Learning Module

Implement pattern learning and constraint adaptation:

```python
class AdaptiveLearner:
    """Learns project-specific patterns and constraints"""
    
    def __init__(self):
        self.pattern_extractor = PatternExtractor()
        self.constraint_miner = ConstraintMiner()
        self.feedback_processor = FeedbackProcessor()
        
        # Neural components for pattern recognition
        self.pattern_embedder = load_model("pattern_embedder")
        self.constraint_predictor = load_model("constraint_predictor")
        
    def learn_from_codebase(self, project_path: str) -> 'LearnedConstraints':
        """Extract constraints from existing codebase"""
        
        # Parse all code files
        asts = []
        for file_path in find_code_files(project_path):
            ast = parse_file(file_path)
            asts.append(ast)
            
        # Extract patterns
        patterns = self.pattern_extractor.extract(asts)
        
        # Mine constraints
        constraints = []
        for pattern in patterns:
            # Get pattern embedding
            embedding = self.pattern_embedder.encode(pattern)
            
            # Predict likely constraints
            constraint_probs = self.constraint_predictor.predict(embedding)
            
            # Add high-confidence constraints
            for constraint, prob in constraint_probs.items():
                if prob > 0.8:
                    constraints.append(constraint)
                    
        return LearnedConstraints(constraints, patterns)
    
    def update_from_feedback(
        self,
        generation: 'Generation',
        feedback: 'UserFeedback'
    ):
        """Update constraints based on user feedback"""
        
        if feedback.is_positive:
            # Reinforce successful patterns
            self.reinforce_patterns(generation.patterns_used)
            
        else:
            # Analyze failure and adjust
            failure_analysis = self.analyze_failure(
                generation,
                feedback.error_type
            )
            
            # Update constraint weights
            self.adjust_constraint_weights(failure_analysis)
```

### Phase 5: Generation Orchestrator

Implement the main generation pipeline:

```python
class GenerationOrchestrator:
    """Coordinates the entire generation pipeline"""
    
    def __init__(self, config: 'Config'):
        self.llm = load_llm(config.model_name)
        self.constraint_engine = ConstraintEngine(config)
        self.guidance_adapter = LLGuidanceAdapter(
            config.base_grammar,
            self.llm.tokenizer
        )
        self.type_synthesizer = TypeDirectedSynthesizer(config.type_system)
        self.learner = AdaptiveLearner()
        
        # Performance optimizations
        self.speculative_decoder = SpeculativeDecoder()
        self.parallel_validator = ParallelValidator()
        
    async def generate(
        self,
        specification: 'Specification',
        context: Optional['ProjectContext'] = None
    ) -> 'GeneratedCode':
        """Main generation entry point"""
        
        # Build constraint hierarchy
        constraints = await self.build_constraints(specification, context)
        
        # Initialize generation state
        state = GenerationState(
            prompt=specification.to_prompt(),
            constraints=constraints,
            context=context
        )
        
        # Generation loop with speculation
        while not state.is_complete:
            # Speculative generation of multiple tokens
            candidates = await self.speculative_decoder.generate_batch(
                state,
                n_tokens=4
            )
            
            # Parallel validation
            valid_prefix = await self.parallel_validator.validate_longest(
                candidates,
                constraints
            )
            
            # Commit valid tokens
            state.commit_tokens(valid_prefix)
            
            # Check for holes and refine
            if hole := state.detect_hole():
                completion = self.type_synthesizer.synthesize_completion(
                    state.partial_code,
                    hole.expected_type,
                    state.type_context
                )
                state.fill_hole(hole, completion)
                
        # Final validation and cleanup
        result = self.finalize_generation(state)
        
        # Update adaptive learning
        if context:
            self.learner.record_generation(result, context)
            
        return result
    
    async def build_constraints(
        self,
        spec: 'Specification',
        context: Optional['ProjectContext']
    ) -> 'ConstraintSet':
        """Build complete constraint hierarchy"""
        
        # Base syntactic constraints
        syntactic = SyntacticConstraints(
            grammar=spec.language.grammar,
            style_rules=spec.style_guide
        )
        
        # Type constraints
        type_based = TypeConstraints(
            type_system=spec.language.type_system,
            signatures=spec.type_signatures,
            inference_rules=spec.type_inference
        )
        
        # Semantic constraints
        semantic = SemanticConstraints(
            invariants=spec.invariants,
            examples=spec.io_examples,
            properties=spec.properties
        )
        
        # Contextual constraints (learned)
        contextual = ContextualConstraints()
        if context:
            learned = await self.learner.get_constraints(context.project_id)
            contextual.add_learned(learned)
            
        return ConstraintSet(syntactic, type_based, semantic, contextual)
```

## Critical Implementation Details

### 1. Token Alignment
Always handle subword tokenization carefully:
```python
def align_constraints_with_tokenizer(constraint, tokenizer):
    """Ensure constraints respect token boundaries"""
    # Never split in the middle of a token
    # Account for BPE, SentencePiece, etc.
    aligned = []
    for boundary in constraint.boundaries:
        token_boundary = tokenizer.find_token_boundary(boundary)
        aligned.append(token_boundary)
    return aligned
```

### 2. Prefix Property Maintenance
Ensure every parser state can reach an accepting state:
```python
def maintain_prefix_property(automaton):
    """Ensure automaton maintains prefix property"""
    # Remove dead states
    reachable = find_reachable_states(automaton.initial)
    productive = find_productive_states(automaton.accepting)
    valid_states = reachable & productive
    
    # Rebuild with only valid states
    return automaton.restrict_to(valid_states)
```

### 3. Type Search Optimization
Implement efficient type inhabitation search:
```python
def optimized_type_search(source_type, target_type, depth_limit=5):
    """Search with memoization and pruning"""
    memo = {}
    
    def search(current, target, depth, visited):
        # Memoization key
        key = (current, target, depth)
        if key in memo:
            return memo[key]
            
        # Base cases
        if current == target:
            return []
        if depth >= depth_limit:
            return None
        if current in visited:  # Cycle detection
            return None
            
        # Try each possible operation
        visited_new = visited | {current}
        for op in get_applicable_ops(current):
            result_type = op.apply(current)
            
            # Pruning heuristic
            if complexity(result_type) > complexity(target) + 2:
                continue
                
            path = search(result_type, target, depth + 1, visited_new)
            if path is not None:
                result = [op] + path
                memo[key] = result
                return result
                
        memo[key] = None
        return None
    
    return search(source_type, target_type, 0, set())
```

### 4. Incremental Parsing
Implement efficient incremental parsing:
```python
class IncrementalParser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.parse_stack = []
        self.state_cache = {}
        
    def parse_incremental(self, new_tokens):
        """Parse new tokens incrementally"""
        # Reuse previous parse state
        if self.parse_stack:
            state = self.parse_stack[-1]
        else:
            state = self.grammar.initial_state()
            
        # Process new tokens
        for token in new_tokens:
            # Check cache
            cache_key = (state, token)
            if cache_key in self.state_cache:
                state = self.state_cache[cache_key]
            else:
                state = self.grammar.transition(state, token)
                self.state_cache[cache_key] = state
                
            self.parse_stack.append(state)
            
        return state
```

### 5. Parallel Constraint Evaluation
Leverage parallelism for performance:
```python
async def evaluate_constraints_parallel(state, constraints):
    """Evaluate multiple constraints in parallel"""
    tasks = []
    
    # Group by estimated cost
    fast_constraints = [c for c in constraints if c.is_fast]
    slow_constraints = [c for c in constraints if not c.is_fast]
    
    # Evaluate fast constraints first
    fast_results = await asyncio.gather(*[
        c.evaluate_async(state) for c in fast_constraints
    ])
    
    # Early exit if fast constraints fail
    if not all(fast_results):
        return False
        
    # Evaluate slow constraints in parallel
    if slow_constraints:
        slow_results = await asyncio.gather(*[
            c.evaluate_async(state) for c in slow_constraints
        ])
        return all(slow_results)
        
    return True
```

## Testing Strategy

### Unit Tests
Test each component in isolation:
```python
def test_type_inhabitation():
    """Test type search algorithm"""
    solver = InhabitationSolver()
    
    # Test basic inhabitation
    path = solver.find_path(
        source=IntType(),
        target=StringType()
    )
    assert path == [ToString()]
    
    # Test with constraints
    path = solver.find_path(
        source=ListType(IntType()),
        target=ListType(StringType()),
        constraints=[PreserveLength()]
    )
    assert path == [Map(ToString())]
```

### Integration Tests
Test component interactions:
```python
def test_constraint_integration():
    """Test constraint engine integration"""
    engine = ConstraintEngine()
    
    # Build multi-level constraints
    constraints = engine.build_constraints(
        spec=TypedSpecification(
            syntax="typescript",
            types={"input": "number[]", "output": "string[]"},
            examples=[([1,2,3], ["1","2","3"])]
        )
    )
    
    # Test mask computation
    state = GenerationState("function transform(arr: number[]): string[] { return ")
    mask = constraints.compute_mask(state, vocab)
    
    # Should allow array operations
    assert mask[vocab.index("arr.map")]
    # Should not allow incompatible operations
    assert not mask[vocab.index("arr.sum")]
```

### Performance Benchmarks
Monitor system performance:
```python
def benchmark_mask_computation():
    """Benchmark token mask computation speed"""
    engine = create_engine()
    state = create_typical_state()
    vocab = create_vocab(size=100000)
    
    start = time.perf_counter()
    for _ in range(1000):
        mask = engine.compute_mask(state, vocab)
    elapsed = time.perf_counter() - start
    
    avg_time = elapsed / 1000
    assert avg_time < 0.0001  # <100μs target
```

## Deployment Considerations

### 1. Model Agnostic Design
Ensure compatibility with different LLMs:
```python
class ModelAdapter(ABC):
    @abstractmethod
    def get_tokenizer(self):
        pass
    
    @abstractmethod
    def get_vocab(self):
        pass
    
    @abstractmethod
    def forward(self, input_ids):
        pass

class GPTAdapter(ModelAdapter):
    # Implementation for GPT models
    pass

class LlamaAdapter(ModelAdapter):
    # Implementation for Llama models
    pass
```

### 2. Resource Management
Implement careful resource management:
```python
class ResourceManager:
    def __init__(self, memory_limit_gb=1.0):
        self.memory_limit = memory_limit_gb * 1024 * 1024 * 1024
        self.current_usage = 0
        self.cache_manager = CacheManager()
        
    def allocate(self, size_bytes):
        if self.current_usage + size_bytes > self.memory_limit:
            # Evict from caches
            freed = self.cache_manager.evict_lru(size_bytes)
            self.current_usage -= freed
            
        self.current_usage += size_bytes
```

### 3. Error Recovery
Implement robust error handling:
```python
class ConstraintRelaxation:
    """Gradually relax constraints on failure"""
    
    def __init__(self):
        self.relaxation_levels = [
            "strict",      # All constraints enforced
            "moderate",    # Relax style constraints
            "lenient",     # Relax semantic constraints
            "minimal"      # Only syntax and types
        ]
        self.current_level = 0
        
    def relax(self) -> bool:
        """Relax constraints by one level"""
        if self.current_level < len(self.relaxation_levels) - 1:
            self.current_level += 1
            return True
        return False
```

## Success Metrics

Monitor these metrics in production:

1. **Performance Metrics**
   - Token generation rate (tokens/second)
   - Mask computation time (p50, p95, p99)
   - Memory usage (peak and average)
   - Cache hit rates

2. **Quality Metrics**
   - Compilation success rate
   - Type error rate
   - Test pass rate
   - User acceptance rate

3. **Adaptation Metrics**
   - Constraint learning convergence
   - Pattern recognition accuracy
   - Feedback incorporation rate

## Additional Resources

- llguidance documentation: https://github.com/guidance-ai/llguidance
- Type inhabitation algorithms: See Gvero et al. papers
- Constraint solving references: Z3 tutorials
- Performance optimization guides: Systems papers on parallel parsing

## Final Notes

Remember that the key to success is balancing:
- **Correctness vs Performance**: Cache aggressively but validate carefully
- **Strictness vs Flexibility**: Use soft constraints where appropriate
- **Generality vs Specialization**: Adapt to projects without overfitting
- **Complexity vs Usability**: Keep interfaces simple despite internal complexity

The system should feel magical to users while being rigorously engineered internally. Focus on developer experience while maintaining formal guarantees.
