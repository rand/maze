# Plan: Grammar Constraint Enforcement Fix

**Date**: 2025-11-12  
**Objective**: Make grammar-constrained generation work as designed  
**Current Status**: Constraints are sent but NOT enforced

---

## Problem Statement

**What's Broken**:
- Grammar constraints (Lark format) are sent to Modal endpoint
- vLLM receives `guided_grammar` parameter
- But LLM output is NOT constrained (generates invalid syntax like markdown fences)
- Core value proposition is non-functional

**What Should Work**:
- LLM should only generate tokens allowed by grammar
- Invalid syntax should be impossible
- 95%+ compilation success rate with constraints
- Measurable improvement over unconstrained generation

---

## Phase 1: Diagnostic Investigation

### Goal
Understand exactly WHERE the constraint enforcement breaks down.

### 1.1 Verify Request Path (15 min)

**Test**: Does grammar reach vLLM?

```bash
# Add debug logging to Modal deployment
# Check: Does FastAPI endpoint receive grammar?
# Check: Does vLLM generate() call include guided_grammar?
# Check: What does vLLM log say about grammar?
```

**Action Items**:
- [ ] Add print statements to `modal_app.py::_generate_internal()`
- [ ] Log request payload before vLLM call
- [ ] Log vLLM SamplingParams
- [ ] Redeploy with logging enabled
- [ ] Trigger generation and capture logs

**Success Criteria**:
- Logs show grammar is present in request
- Logs show `guided_grammar` parameter set on SamplingParams
- Identify point where grammar is lost/ignored

**Commands**:
```bash
# Add logging
edit deployment/modal/modal_app.py  # Add print(f"Grammar received: {grammar[:100]}...")

# Redeploy
modal deploy deployment/modal/modal_app.py

# Test with logging
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
uv run pytest tests/validation/test_constraint_enforcement.py::TestPythonConstraintEnforcement::test_constrained_produces_valid_syntax -xvs

# Check Modal logs
modal app logs maze-inference
```

---

### 1.2 Verify vLLM Configuration (10 min)

**Test**: Is vLLM configured correctly for llguidance?

**Action Items**:
- [ ] Check `guided_decoding_backend` is set to "llguidance" on LLM init
- [ ] Verify llguidance version compatibility (should be 0.7.11-0.7.99)
- [ ] Check vLLM 0.11.0 docs for correct guided_grammar API
- [ ] Compare with working llguidance examples

**Research**:
```bash
# Check vLLM docs
curl -s https://docs.vllm.ai/en/latest/serving/guided_decoding.html

# Check llguidance examples
librarian "How to use llguidance with vLLM 0.11.0 for Lark grammar constraints?"
```

**Success Criteria**:
- Confirm Modal deployment uses correct vLLM API
- Identify any API changes between versions
- Find working reference implementation

---

### 1.3 Test Grammar Format (20 min)

**Test**: Is the Lark grammar valid for llguidance?

**Action Items**:
- [ ] Test minimal Lark grammar with vLLM locally
- [ ] Verify grammar parses with Lark parser
- [ ] Check if llguidance requires preprocessing
- [ ] Test simple grammar vs complex grammar

**Test Script**:
```python
# tests/debug/test_grammar_format.py
from lark import Lark

# Test 1: Does Lark parse our grammar?
grammar_str = PYTHON_FUNCTION.grammar
parser = Lark(grammar_str)  # Should not raise

# Test 2: Minimal grammar with llguidance
minimal_grammar = """
?start: simple
simple: "return" NUMBER
NUMBER: /[0-9]+/
"""

# Test 3: Send to Modal with minimal grammar
# If minimal works but complex doesn't -> grammar complexity issue
```

**Success Criteria**:
- Grammar is valid Lark
- Identify if issue is grammar-specific or systemic
- Determine if preprocessing needed

---

### 1.4 Compare Constrained vs Unconstrained (15 min)

**Test**: Measure actual constraint effect

**Action Items**:
- [ ] Generate 10 samples WITH grammar
- [ ] Generate 10 samples WITHOUT grammar
- [ ] Syntax check all outputs
- [ ] Compare validity rates

**Test**:
```python
# tests/debug/test_constraint_comparison.py
for i in range(10):
    # With constraint
    resp_constrained = adapter.generate(GenerationRequest(
        prompt="def test():", 
        grammar=PYTHON_FUNCTION.grammar
    ))
    
    # Without constraint
    resp_unconstrained = adapter.generate(GenerationRequest(
        prompt="def test():",
        grammar=None
    ))
    
    # Compare
    print(f"Sample {i}:")
    print(f"  Constrained valid: {is_valid_python(resp_constrained.text)}")
    print(f"  Unconstrained valid: {is_valid_python(resp_unconstrained.text)}")
```

**Success Criteria**:
- Quantify if ANY constraint effect exists
- If rates are identical -> constraint completely ignored
- If rates differ slightly -> partial constraint application

---

## Phase 2: Root Cause Identification

### Goal
Pinpoint the exact cause of constraint failure.

### 2.1 Hypothesis Testing

Based on Phase 1 findings, test hypotheses:

**Hypothesis A**: Grammar format incompatibility
- **Test**: Try different grammar formats (JSON Schema, simpler Lark)
- **Fix**: Convert or preprocess grammar

**Hypothesis B**: vLLM API misuse
- **Test**: Review vLLM 0.11.0 guided decoding API
- **Fix**: Correct parameter names/structure

**Hypothesis C**: llguidance not enabled
- **Test**: Check vLLM was built with llguidance support
- **Fix**: Rebuild vLLM or use different backend

**Hypothesis D**: Backend mismatch
- **Test**: Check if vLLM defaulting to different backend (outlines, xgrammar)
- **Fix**: Explicitly force llguidance backend

**Hypothesis E**: Model incompatibility
- **Test**: Try different model (7B instead of 32B)
- **Fix**: Use compatible model or adjust approach

### 2.2 Minimal Reproduction (30 min)

**Goal**: Create smallest possible reproduction of issue

```python
# deployment/modal/minimal_test.py
import modal

app = modal.App("test-llguidance")

@app.function(gpu="a100-40gb", image=modal.Image.debian_slim().pip_install("vllm==0.11.0", "llguidance>=0.7.11,<0.8.0"))
def test_guided():
    from vllm import LLM, SamplingParams
    
    llm = LLM(
        model="Qwen/Qwen2.5-Coder-7B-Instruct",
        guided_decoding_backend="llguidance",
    )
    
    # Minimal grammar
    grammar = """
?start: func
func: "return" NUMBER
NUMBER: /[0-9]+/
"""
    
    params = SamplingParams(
        max_tokens=32,
        temperature=0.0,
        guided_grammar=grammar,
    )
    
    outputs = llm.generate(["def test():"], params)
    result = outputs[0].outputs[0].text
    
    print(f"Result: {result}")
    print(f"Valid: {'return' in result and 'def' not in result}")  # Should only have 'return N'
    
    return result

@app.local_entrypoint()
def main():
    result = test_guided.remote()
    print(f"Generated: {result}")
```

**Run**:
```bash
modal run deployment/modal/minimal_test.py
```

**Success Criteria**:
- Minimal case exposes same issue
- Or: Minimal case works -> complex grammar is problem
- Clear yes/no on constraint enforcement

---

## Phase 3: Fix Implementation

### Goal
Implement solution based on root cause.

### 3.1 Solution Paths

**Path A: Fix Grammar Format**

If issue is Lark grammar incompatibility:

```python
# src/maze/synthesis/grammar_preprocessor.py
def preprocess_for_llguidance(lark_grammar: str) -> str:
    """Convert Maze Lark grammar to llguidance-compatible format."""
    # Apply transformations identified in Phase 2
    # Examples:
    # - Escape special characters
    # - Simplify complex rules
    # - Add llguidance directives
    return processed_grammar
```

**Path B: Fix vLLM Integration**

If issue is API usage:

```python
# deployment/modal/modal_app.py
def _generate_internal(...):
    # Correct API based on vLLM 0.11.0 docs
    sampling_params = SamplingParams(
        temperature=temperature,
        max_tokens=max_tokens,
        # Fix: Use correct parameter name/structure
        guided_decoding={"backend": "llguidance", "grammar": grammar},  # Example
    )
```

**Path C: Use Alternative Backend**

If llguidance fundamentally broken:

```python
# Option 1: Switch to outlines
sampling_params.guided_decoding_backend = "outlines"
# Convert Lark -> Outlines format

# Option 2: Switch to xgrammar  
sampling_params.guided_decoding_backend = "xgrammar"
# Convert Lark -> XGrammar format

# Option 3: Use guidance library separately
from guidance import models
llm = models.vLLM(...)
result = llm + grammar_constraint + gen(max_tokens=128)
```

**Path D: Client-Side Constraint Enforcement**

If server-side fails, implement client-side:

```python
# src/maze/orchestrator/constraint_enforcer.py
class ClientSideConstraintEnforcer:
    """Enforce constraints during streaming generation."""
    
    def constrain_generation(self, prompt, grammar, llm):
        """Generate with client-side constraint checking."""
        # Use llguidance Python library directly
        # Or: Implement token masking
        # Or: Use guidance library
        pass
```

### 3.2 Implementation Steps

Once solution path chosen:

1. **Implement fix** (1-2 hours)
   - Code changes to identified component
   - Add logging/debugging
   - Write unit tests for fix

2. **Test locally** (30 min)
   - Run with 7B model locally
   - Verify constraint enforcement
   - Check syntax validity

3. **Deploy to Modal** (15 min)
   - Update modal_app.py
   - Redeploy
   - Test with 32B model

4. **Validate with test suite** (30 min)
   - Run constraint_enforcement tests
   - All should pass
   - Measure improvement

---

## Phase 4: Comprehensive Validation

### Goal
Prove constraints work as designed.

### 4.1 Syntax Validity Tests (30 min)

```bash
# Run full constraint enforcement suite
uv run pytest tests/validation/test_constraint_enforcement.py -v

# Expected results:
# ✅ test_constrained_produces_valid_syntax - 100% valid
# ✅ test_grammar_prevents_invalid_structures - No loops/conditionals in simple grammar
# ✅ test_constraint_enforcement_rate - Constrained ≥90%, better than unconstrained
# ✅ test_typescript_syntax_validity - tsc compiles without errors
# ✅ test_constraint_improves_validity_measurably - Measurable improvement
```

### 4.2 Multi-Language Validation (1 hour)

```bash
# Test all 5 languages
uv run pytest tests/validation/test_constraint_enforcement.py::TestMultiLanguageCorrectness -v

# Python: ast.parse succeeds
# TypeScript: tsc succeeds
# Rust: rustc succeeds
# Go: go build succeeds
# Zig: zig build succeeds (if compiler available)
```

### 4.3 Effectiveness Measurement (30 min)

**Metrics to collect**:
- Syntax validity rate: WITH vs WITHOUT constraints
- Compilation success rate: WITH vs WITHOUT
- Token-level constraint violations: Count per generation
- Grammar complexity vs validity: Correlation

**Target metrics** (from CLAUDE.md):
- Syntax validity: ≥95% with constraints
- Improvement over unconstrained: ≥20 percentage points
- Compilation success: ≥90%
- Constraint overhead: <100μs per token

**Test**:
```bash
uv run python benchmarks/constraint_effectiveness.py --samples 100

# Output:
# Constrained validity: 97/100 (97%)
# Unconstrained validity: 73/100 (73%)
# Improvement: +24 percentage points
# Average constraint overhead: 45μs per token
# ✅ All targets met
```

### 4.4 Real-World Scenario Tests (1 hour)

```bash
# Run comprehensive suite (the GOOD tests)
uv run pytest tests/validation/test_suite_comprehensive.py -v

# But NOW these tests should verify:
# - Generated code compiles (not just exists)
# - Syntax is valid (actually parse it)
# - Types are correct (run type checker)
```

---

## Phase 5: Documentation & Hardening

### Goal
Document findings, update claims, prevent regression.

### 5.1 Update Documentation (30 min)

**Files to update**:

```markdown
# README.md
- Add ACTUAL constraint enforcement metrics
- Remove unsupported claims
- Add "Verified working with vLLM 0.11.0 + llguidance X.Y.Z"

# deployment/modal/DEPLOYMENT_STATUS.md
- Update with constraint enforcement validation
- Add metrics from Phase 4
- Document any limitations discovered

# CLAUDE.md
- Update performance targets with actual measurements
- Document constraint enforcement approach
- Add lessons learned

# LESSONS_LEARNED.md
- Document root cause of initial failure
- Explain fix implemented
- Provide debugging guidance for future issues
```

### 5.2 Add Regression Tests (1 hour)

**Prevent this from breaking again**:

```python
# tests/regression/test_constraint_enforcement_regression.py
class TestConstraintEnforcementRegression:
    """Ensure constraints continue working after changes."""
    
    @pytest.mark.regression
    def test_python_constrained_never_produces_markdown_fences(self):
        """Regression test: Grammar should prevent markdown fences."""
        # This was the original failure - ensure it never happens again
        for i in range(10):
            result = generate_with_constraint(PYTHON_FUNCTION.grammar, "def test():")
            assert "```" not in result, "Grammar constraint broken: markdown fence in output"
    
    @pytest.mark.regression
    def test_constraint_enforcement_rate_never_drops_below_90(self):
        """Regression test: Maintain ≥90% validity."""
        validity_rate = measure_constraint_validity(samples=50)
        assert validity_rate >= 0.90, f"Constraint effectiveness dropped to {validity_rate:.0%}"
```

**Add to CI/CD**:
```yaml
# .github/workflows/test.yml
- name: Regression Tests
  run: uv run pytest tests/regression/ -v -m regression
  
- name: Constraint Validation
  run: uv run pytest tests/validation/test_constraint_enforcement.py -v
```

### 5.3 Performance Benchmarks (30 min)

**Establish baselines**:

```bash
# Create benchmark suite
uv run python benchmarks/constraint_overhead.py

# Measure:
# - Mask computation time (p50, p95, p99)
# - Grammar compilation time
# - End-to-end latency WITH vs WITHOUT constraints
# - Tokens per second WITH vs WITHOUT

# Save results
# benchmarks/results/baseline_2025-11-12.json
```

### 5.4 Monitoring & Alerts (1 hour)

**Add production monitoring**:

```python
# src/maze/monitoring/constraint_metrics.py
class ConstraintMetrics:
    """Track constraint enforcement in production."""
    
    def record_constraint_application(self, result: GenerationResponse):
        """Record whether constraints were applied and effective."""
        metrics = {
            "timestamp": time.time(),
            "grammar_applied": result.metadata.get("grammar_applied"),
            "syntax_valid": self._check_syntax(result.text),
            "constraint_overhead_us": result.metadata.get("constraint_overhead"),
        }
        
        # Alert if constraints not working
        if metrics["grammar_applied"] and not metrics["syntax_valid"]:
            logger.alert("Constraint enforcement failure detected")
```

---

## Phase 6: Communication & Learnings

### 6.1 Create Status Report (30 min)

```markdown
# deployment/modal/CONSTRAINT_ENFORCEMENT_RESOLUTION.md

## Issue
Grammar constraints were sent but not enforced (Nov 12, 2025)

## Root Cause
[Identified cause from Phase 2]

## Solution
[Implemented fix from Phase 3]

## Validation
- Syntax validity: [X]% with constraints vs [Y]% without
- Improvement: +[Z] percentage points
- All constraint enforcement tests passing

## Lessons Learned
1. Always validate core value proposition with real tests
2. Smoke tests (assert code != None) are insufficient
3. [Other learnings]

## Recommendations
1. Run constraint_enforcement tests in CI
2. Monitor constraint effectiveness in production
3. Benchmark before claiming performance targets
```

### 6.2 Update Test Strategy (15 min)

**Document testing approach**:

```markdown
# tests/TESTING_STRATEGY.md

## Test Pyramid for Maze

### Level 1: Unit Tests (fast, many)
- Grammar parsing
- Type system operations
- Individual components

### Level 2: Integration Tests (medium, moderate)
- Provider adapters
- Pipeline orchestration
- Constraint synthesis

### Level 3: Constraint Enforcement Tests (slow, critical)
- **MUST validate actual constraint enforcement**
- **MUST check syntax validity with parsers/compilers**
- **MUST measure improvement vs unconstrained**

### Level 4: End-to-End Tests (slowest, few)
- Full workflows
- Real-world scenarios
- But WITH syntax validation

## Anti-Patterns
❌ assert result.code is not None  # Meaningless
❌ assert len(result.code) > 10   # Doesn't validate correctness
✅ ast.parse(result.code)          # Actually validates syntax
✅ measure_validity_rate()         # Quantifies effectiveness
```

---

## Success Criteria

### Phase Completion Criteria

**Phase 1 (Diagnostic)**: ✅ when root cause identified
**Phase 2 (Root Cause)**: ✅ when hypothesis confirmed with evidence  
**Phase 3 (Fix)**: ✅ when constraints provably enforced in minimal test
**Phase 4 (Validation)**: ✅ when all constraint_enforcement tests pass
**Phase 5 (Documentation)**: ✅ when claims match reality
**Phase 6 (Communication)**: ✅ when learnings captured

### Overall Success Criteria

1. ✅ Grammar constraints demonstrably enforced
   - Test: `test_constrained_produces_valid_syntax` passes
   - Generated code is 100% syntactically valid
   
2. ✅ Measurable improvement over unconstrained
   - Constrained validity: ≥90%
   - Improvement: ≥20 percentage points over unconstrained
   
3. ✅ Multi-language support validated
   - Python: ast.parse succeeds
   - TypeScript: tsc compiles
   - Rust: rustc compiles
   - Go: go build succeeds
   
4. ✅ Performance targets met
   - Constraint overhead: <100μs per token
   - End-to-end latency: <5s per generation
   
5. ✅ Documentation accurate
   - No unvalidated claims
   - Metrics from real measurements
   - Limitations clearly stated
   
6. ✅ Regression prevention
   - Tests in CI
   - Monitoring in production
   - Clear debugging procedures

---

## Timeline Estimate

- **Phase 1 (Diagnostic)**: 1 hour
- **Phase 2 (Root Cause)**: 1 hour  
- **Phase 3 (Fix)**: 2-4 hours (depends on complexity)
- **Phase 4 (Validation)**: 2 hours
- **Phase 5 (Documentation)**: 2 hours
- **Phase 6 (Communication)**: 1 hour

**Total**: 9-11 hours of focused work

**Parallelization opportunities**:
- Phase 1.1-1.4 can run concurrently
- Phase 4.1-4.4 can run concurrently
- Phase 5.1-5.4 can run concurrently

**Critical path**: Phase 1 → Phase 2 → Phase 3 → Phase 4

---

## Risk Mitigation

### Risk: llguidance fundamentally incompatible

**Mitigation**: Have alternative backends ready (outlines, xgrammar, guidance)

### Risk: Fix takes >4 hours

**Mitigation**: Implement client-side constraint enforcement as fallback

### Risk: Constraints work but too slow

**Mitigation**: Optimize or make configurable (strict vs fast mode)

### Risk: Works for simple grammars, breaks on complex

**Mitigation**: Simplify grammars or implement grammar simplification pass

---

## Next Immediate Steps

1. **Right now**: Start Phase 1.1 (add logging to Modal deployment)
2. **In 15 min**: Redeploy and check logs
3. **In 30 min**: Complete diagnostic phase
4. **In 1 hour**: Know root cause
5. **In 3 hours**: Have working fix
6. **In 6 hours**: Full validation complete

---

## Notes

- This is a **principled engineering approach**: diagnose, understand, fix, validate, document
- Each phase has clear objectives and success criteria
- Built-in validation prevents false positives
- Documentation ensures knowledge transfer
- Focus on **actual measurable outcomes**, not assumptions

