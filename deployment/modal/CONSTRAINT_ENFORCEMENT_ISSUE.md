# Grammar Constraint Enforcement Issue

**Date**: 2025-11-12  
**Status**: ⚠️ CRITICAL FINDING

---

## Issue

**Grammar constraints are NOT being enforced by vLLM + llguidance**

### Evidence

Test: `test_constrained_produces_valid_syntax`

**Expected**: Grammar-constrained generation produces valid Python syntax

**Actual**: Generated code contains markdown code fences (```), which:
1. Violates Python syntax
2. Should be impossible with Python grammar constraint  
3. Proves grammar is NOT being enforced

### Generated Output

```python
def calculate_sum(a: int, b: int) -> int:
    """
    Calculate the sum of two integers.
    
    Args:
    a (int): The first integer.
    b (int): The second integer.
    
    Returns:
    int: The sum of the two integers.
    """
    return a + b

# Example usage
result = calculate_sum(5, 3)
print(result)  # Output: 8
```                    # <-- INVALID: Markdown fence in Python code

In this example, the function `calculate_sum` takes two parameters, `a` and `b`...
```

**Syntax Error**: `invalid syntax (<unknown>, line 17)` at the ``` marker

---

## Root Cause Analysis

### Hypothesis 1: Grammar Not Being Sent
- ❓ Modal adapter strips grammar from request?
- ❓ FastAPI endpoint doesn't forward grammar?

### Hypothesis 2: llguidance Not Applied
- ❓ `guided_grammar` parameter not working?
- ❓ Backend not set to "llguidance"?
- ❓ vLLM silently ignoring grammar?

### Hypothesis 3: Grammar Format Issue
- ❓ Lark grammar not compatible with llguidance version?
- ❓ Grammar template has syntax errors?

---

## What This Means

### For Current Tests
The "comprehensive" tests that passed earlier (21/21) were **FALSE POSITIVES**:
- They only checked `result.code is not None`
- They didn't validate syntax
- They didn't verify constraints were enforced
- They measured availability, not correctness

### For Maze's Value Proposition
**The core claim is unvalidated**:
- ❌ "Grammar constraints prevent invalid syntax" - UNPROVEN
- ❌ "llguidance enforces Lark grammars" - NOT WORKING
- ❌ "95%+ compilation success" - UNMEASURED
- ✅ "Modal endpoint responds" - TRUE (but insufficient)

---

## Immediate Actions

1. **Verify grammar is sent to Modal**
   - Add logging to Modal adapter
   - Check FastAPI endpoint receives grammar
   - Confirm vLLM receives `guided_grammar` parameter

2. **Test llguidance directly**
   - Minimal reproduction: Send simple prompt + grammar
   - Verify llguidance masks tokens correctly
   - Check vLLM logs for grammar application

3. **Validate grammar format**
   - Test Lark grammar parses correctly
   - Verify llguidance version compatibility
   - Check for any required grammar preprocessing

4. **Fix or document limitation**
   - If fixable: Correct integration
   - If not: Document that constraints don't work yet
   - Update all claims/docs accordingly

---

## Test That Exposed This

```python
def test_constrained_produces_valid_syntax(self):
    """Verify constrained generation produces valid Python."""
    adapter = ModalProviderAdapter()
    grammar = PYTHON_FUNCTION.grammar  # Lark Python function grammar
    
    request = GenerationRequest(
        prompt="def calculate_sum(a: int, b: int) -> int:",
        grammar=grammar,  # <-- This should constrain output
    )
    
    response = adapter.generate(request)
    full_code = request.prompt + response.text
    
    # Parse as Python
    ast.parse(full_code)  # <-- FAILS: SyntaxError from markdown ```
```

**This is the RIGHT test** - it actually validates the value proposition.

---

## Next Steps

1. Enable debug logging in Modal deployment
2. Check if `grammar_applied` metadata is True
3. Inspect vLLM logs for grammar processing
4. Test with minimal grammar to isolate issue
5. Compare with known-working llguidance examples

---

**Status**: Investigation required before claiming constraint enforcement works.
