# Root Cause Found & Solution Implemented

**Date**: 2025-11-12  
**Status**: ✅ CONSTRAINTS NOW WORKING

---

## Root Cause Summary

**Three issues identified and fixed**:

1. **API Issue**: Using deprecated API instead of `StructuredOutputsParams`
2. **Grammar Syntax Issue**: Using `?start:` which llguidance doesn't support  
3. **Grammar Design Issue**: Grammar defines full function, but we're completing partial functions

---

## Issue #1: Wrong API

### Problem
Used deprecated `guided_grammar` parameter:
```python
sampling_params.guided_grammar = grammar  # DEPRECATED
```

### Solution
Use `StructuredOutputsParams` (vLLM 0.11.0 correct API):
```python
sampling_params = SamplingParams(
    structured_outputs=StructuredOutputsParams(grammar=grammar)
)
```

### Evidence
✅ Minimal test with simple grammar WORKED after API fix

---

## Issue #2: Inline Rule Syntax

### Problem
Used `?start:` in grammar (Lark inline rule syntax):
```lark
?start: function_def  # ❌ llguidance doesn't support ?start
```

Error: `Failed to convert the grammar from GBNF to Lark: Expected name at line 2, '\n' ^ '?start: function_def'`

### Solution
Remove `?` prefix from start rule:
```lark
start: function_def  # ✅ Standard start rule
```

### Applied To
- `src/maze/synthesis/grammars/python.py` (3 occurrences)
- `src/maze/synthesis/grammars/rust.py` (3 occurrences)
- `src/maze/synthesis/grammars/typescript.py` (4 occurrences)

---

## Issue #3: Grammar Design Mismatch

### Problem
Grammar expects FULL function definition:
```lark
start: function_def
function_def: "def" IDENT "(" params ")" ":" suite
```

But prompts are PARTIAL (function signature already given):
```python
prompt = "def calculate_sum(a: int, b: int) -> int:"  # Already has "def", name, params
```

Result: Model repeats the signature:
```python
def calculate_sum(...):def calculate_sum(...):  # DUPLICATE
```

### Solution Options

**Option A: Completion Grammars** (Recommended)
Create grammars that expect only the BODY/continuation:

```python
# grammar for completing function body ONLY
PYTHON_FUNCTION_BODY = """
start: suite
suite: NEWLINE INDENT statement+ DEDENT
statement: simple_stmt | compound_stmt
...
"""

# Usage:
prompt = "def calculate_sum(a: int, b: int) -> int:"  # Function signature
grammar = PYTHON_FUNCTION_BODY  # Only constrains the body
# Result: "def calculate_sum(a: int, b: int) -> int:\n    return a + b"
```

**Option B: Full Generation Prompts**
Change prompts to NOT include function signature:

```python
# Before
prompt = "def calculate_sum(a: int, b: int) -> int:"  # ❌ Too specific

# After  
prompt = "Create a function that calculates the sum of two integers"  # ✅ Let grammar define structure
grammar = PYTHON_FUNCTION  # Full function grammar
```

**Option C: Prompt Templates**
Extract signature from prompt, use body grammar:

```python
def generate_with_grammar(prompt, language):
    if prompt.startswith("def ") and prompt.endswith(":"):
        # Completing function - use body grammar
        grammar = get_body_grammar(language)
    else:
        # Generating from scratch - use full grammar
        grammar = get_full_grammar(language)
```

---

## Current Status

### What Works ✅
- StructuredOutputsParams API working
- vLLM V1 guidance backend functional
- Grammar constraints ARE being enforced
- Simple grammars work perfectly
- No more markdown fences in output
- No more unconstrained text

### What's Partially Working ⚠️
- Complex full function grammars work BUT clash with partial prompts
- Grammar syntax fixed (`?start:` removed)
- Need to design completion-focused grammars

### What Needs Fixing 🔧
1. Create function BODY grammars (not full function grammars)
2. Or adapt prompts to work with full grammars
3. Test with real code generation scenarios

---

## Immediate Next Steps

1. **Create completion grammars** for each language (1 hour)
   ```python
   PYTHON_FUNCTION_BODY
   TYPESCRIPT_FUNCTION_BODY  
   RUST_FUNCTION_BODY
   GO_FUNCTION_BODY
   ```

2. **Update pipeline to select grammar based on prompt** (30 min)
   - If prompt has signature → use body grammar
   - If prompt is description → use full grammar

3. **Run constraint enforcement tests** (30 min)
   - Should now pass with proper grammars
   - Validate 95%+ syntax validity

4. **Measure improvement vs unconstrained** (30 min)
   - Run test_constraint_improves_validity_measurably
   - Document actual improvement metrics

---

## Key Technical Findings

### vLLM V1 API (0.11.0)

**Correct usage**:
```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

# Initialize (V1 is default, don't need runner="v1")
llm = LLM(
    model="...",
    structured_outputs_config={"backend": "guidance"},  # Optional: set default backend
)

# Generate with grammar
params = SamplingParams(
    max_tokens=128,
    structured_outputs=StructuredOutputsParams(grammar=lark_grammar_string),
)

outputs = llm.generate([prompt], params)
```

### llguidance Lark Support

**Supported** (from llguidance docs):
- Lark format with minor variations
- Must use `start:` not `?start:`
- Supports regex, terminals, rules
- Supports JSON schema embedding

**Example that works**:
```lark
start: simple
simple: "return " NUMBER  
NUMBER: /[0-9]+/
```

---

## Validation Results

### Minimal Test (7B model)
- ✅ Without grammar: Generated full function with explanation
- ✅ With grammar: Generated ONLY `return 100000...` (matched grammar)
- ✅ No markdown fences
- ✅ Constraint demonstrably enforced

### Complex Grammar Test (32B model)
- ⚠️ Grammar processed (no "conversion failed" error anymore)
- ⚠️ Signature repeated (grammar/prompt mismatch)
- ⚠️ Need completion-focused grammars

---

## Performance Impact

**Observed** (from minimal test):
- Without grammar: 0.44s, 72 tokens/sec
- With grammar: 2.92s, 11 tokens/sec

**Analysis**:
- ~6.6x slower with grammar constraints
- This is EXPECTED - constraints require token masking
- Still within acceptable range (<5s for short generations)
- Will improve with caching and optimizations

---

## Recommendations

### For Production Deployment

1. **Use vLLM V1 (default in 0.11.0)** ✅ 
2. **Set `structured_outputs_config={"backend": "guidance"}`** ✅
3. **Pass `StructuredOutputsParams(grammar=...)` in SamplingParams** ✅
4. **Remove `?` from start rules** ✅
5. **Create completion grammars for partial prompts** 🔧 TODO

### For Maze Architecture

1. **Dual Grammar Strategy**:
   - Full grammars: For generation from scratch
   - Body/completion grammars: For completing partial code

2. **Smart Grammar Selection**:
   - Analyze prompt to determine context
   - Select appropriate grammar automatically

3. **Grammar Library Organization**:
   ```
   grammars/
     python/
       full_function.lark
       function_body.lark
       class_full.lark
       class_body.lark
     typescript/
       ...
   ```

---

## Timeline

- **Phase 1-2 (Diagnostic)**: ✅ COMPLETE (4 hours)
- **Phase 3 (Root Cause)**: ✅ COMPLETE (found all 3 issues)
- **Phase 4 (API Fix)**: ✅ COMPLETE
- **Phase 5 (Grammar Syntax Fix)**: ✅ COMPLETE
- **Phase 6 (Grammar Design)**:  🔧 IN PROGRESS
  - Estimated: 2-3 hours
  - Create completion grammars
  - Test with real scenarios
  - Validate constraints work

---

**Next**: Create completion-focused grammars and validate they work for Maze's actual use cases.
