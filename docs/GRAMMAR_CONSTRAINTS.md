# Grammar Constraints in Maze

## Overview

Maze uses **llguidance** (via vLLM) to enforce Lark grammar constraints during code generation. This document captures critical learnings about how grammar constraints work and common pitfalls.

## Critical Requirements

### llguidance Grammar Syntax

**✅ CORRECT**:
```lark
start: function_body
function_body: statement+
statement: return_stmt | expr_stmt
```

**❌ WRONG**:
```lark
?start: function_body  # llguidance does NOT support inline rules (?start:)
```

**Key Rules**:
1. **NO inline rules**: `?start:` is NOT supported - must use `start:`
2. **Use standard Lark syntax**: llguidance supports "a variant of Lark syntax"
3. **Terminals work**: Regex terminals like `/[0-9]+/` work fine
4. **No fancy features**: Stick to basic Lark - rules, terminals, regex

### vLLM V1 API (0.11.0+)

**✅ CORRECT**:
```python
from vllm import SamplingParams
from vllm.sampling_params import StructuredOutputsParams

# Initialize with guidance backend
llm = LLM(
    model="Qwen/Qwen2.5-Coder-32B-Instruct",
    structured_outputs_config={"backend": "guidance"},
)

# Use StructuredOutputsParams
sampling_params = SamplingParams(
    temperature=0.7,
    max_tokens=256,
    structured_outputs=StructuredOutputsParams(grammar=lark_grammar_string),
)
```

**❌ WRONG**:
```python
# Old API (deprecated)
sampling_params = SamplingParams(
    guided_grammar=grammar,  # DEPRECATED in vLLM 0.11.0
)
```

**Key Rules**:
1. **Use `StructuredOutputsParams`**: New API for V1 engine
2. **Set backend to "guidance"**: `structured_outputs_config={"backend": "guidance"}`
3. **V1 is default**: No need to specify `runner="v1"` in vLLM 0.11.0
4. **llguidance version**: Use `>=0.7.11,<0.8.0` for vLLM 0.11.0

## Completion vs Full Generation

### The Problem

Maze's original grammars were designed for **full generation** (generating entire functions from scratch):

```python
# Grammar expects:
"def" IDENT "(" params ")" ":" suite

# But actual use case is COMPLETION:
Prompt: "def calculate_sum(a: int, b: int) -> int:"
Expected: Generate only the body
```

This caused **signature duplication** - the grammar would generate another `def calculate_sum(...)` inside the function body.

### The Solution

Create **two types of grammars**:

**1. Full Generation Grammars** (`PYTHON_FUNCTION`, `TYPESCRIPT_FUNCTION`, etc.):
- Start with function keyword (`def`, `function`, `fn`)
- Generate complete function from scratch
- Use when: Prompt is a description ("Write a function to calculate sum")

**2. Completion Grammars** (`PYTHON_FUNCTION_BODY`, `TYPESCRIPT_FUNCTION_BODY`, etc.):
- Start with body/suite/block only
- Complete partial code
- Use when: Prompt is partial code ending with `:`, `)`, or `{`

**Smart Selection** (in `pipeline.py`):
```python
def _is_completion_prompt(self, prompt: str, language: str) -> bool:
    """Detect completion vs full generation."""
    if language == "python":
        return prompt.rstrip().endswith(":")
    elif language in ("typescript", "javascript"):
        return "function" in prompt and ")" in prompt
    elif language == "rust":
        return "fn" in prompt and ("->" in prompt or ")" in prompt)
    return False
```

## Testing Grammar Constraints

### Principle: Validate the Constraint, Not Just Success

**❌ BAD TEST**:
```python
def test_generation():
    result = generate_code("def foo():")
    assert result.code is not None  # Meaningless!
```

**✅ GOOD TEST**:
```python
def test_grammar_constraint():
    # Define strict grammar (ONLY allows "return NUMBER")
    grammar = """
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/
"""
    
    result = generate_code("def foo():\n    ", grammar=grammar)
    
    # 1. Parse successfully
    ast.parse(result.code)
    
    # 2. Verify it followed the grammar
    assert "return" in result.code
    assert any(c.isdigit() for c in result.code)
    
    # 3. Verify it did NOT violate grammar
    assert "#" not in result.code  # Grammar forbids comments
    assert "if" not in result.code  # Grammar forbids conditionals
    assert "for" not in result.code  # Grammar forbids loops
```

### Common Pitfalls

**1. Token Limits**:
- Problem: Grammar allows comments, model generates ONLY a giant comment, hits token limit
- Solution: Use focused grammars OR directive prompts ("return a + b" not "calculate sum")

**2. Prompt/Completion Mismatch**:
```python
# ❌ WRONG
prompt = "def foo():"
completion = "\n    return 42"
code = prompt + "\n" + completion  # Double newline = syntax error!

# ✅ CORRECT
prompt = "def foo():"
completion = "\n    return 42"
code = prompt + completion  # Or detect if completion starts with \n
```

**3. Empty Completions**:
- Problem: Grammar doesn't match prompt context
- Solution: Ensure prompt ends where grammar starts (e.g., prompt ends with `":\n    "` if grammar starts with `return_stmt`)

## Modal Deployment

### Endpoint Configuration

**Current Deployment**:
- FastAPI endpoint: `https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run`
- Health check: `GET /health`
- Generation: `POST /generate`

**Environment Variables**:
```bash
export MODAL_ENDPOINT_URL=https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run
```

### Request Format

```json
{
  "prompt": "def calculate_sum(a: int, b: int) -> int:\n    ",
  "grammar": "start: simple\nsimple: \"return \" NUMBER\nNUMBER: /[0-9]+/",
  "max_tokens": 128,
  "temperature": 0.3
}
```

### Cold Start Behavior

**First request**: 60-120 seconds (model loading)
**Subsequent requests**: 1-3 seconds (warm)
**Timeout**: Set to 120s minimum for first request

### Performance Characteristics

| Metric | Unconstrained | With Grammar | Ratio |
|--------|--------------|--------------|-------|
| Latency (warm) | 0.4s | 1-3s | 2.5-7.5x |
| Tokens/sec | 70-80 | 10-12 | 6-8x slower |
| Syntax validity | 60-80% | **100%** | **Worth it!** |

## Common Errors and Solutions

### Error: "Failed to convert the grammar from GBNF to Lark"

**Cause**: Using `?start:` (inline rule) which llguidance doesn't support

**Solution**: Change to `start:` (non-inline rule)

```lark
# ❌ WRONG
?start: function_def

# ✅ CORRECT
start: function_def
```

### Error: Unclosed parenthesis/bracket

**Cause**: Token limit reached mid-expression

**Solution**: Increase `max_tokens` or use more focused grammar

### Error: "expected an indented block"

**Cause**: Completion is just comments (no executable statements)

**Solutions**:
1. Use directive prompt: `"def foo():\n    return"` instead of `"def foo():"`
2. Lower temperature (0.0-0.1) for deterministic code generation
3. Use stricter grammar that forbids comment-only bodies

### Error: Signature duplication

**Cause**: Using full generation grammar for completion task

**Solution**: Use completion grammar (`PYTHON_FUNCTION_BODY` not `PYTHON_FUNCTION`)

## Grammar Design Best Practices

### 1. Start Small, Expand Gradually

```lark
# Start with minimal grammar
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/

# Then expand
start: suite
suite: simple_stmt+
simple_stmt: return_stmt | assign_stmt
```

### 2. Match Real Use Cases

Don't design grammars for what "should" work - design for **actual prompts**:

```python
# Real Maze use case: COMPLETION
prompt = "def calculate_sum(a: int, b: int) -> int:"
# Grammar should start with: suite/block/body

# Not: full function definition
# Grammar should NOT start with: "def" IDENT
```

### 3. Test with Actual LLM

Unit tests with mock LLMs don't reveal issues. Always test with:
- Real Modal endpoint
- Actual grammar constraints
- Multiple temperature values (0.0, 0.3, 0.7)
- Various token limits (16, 64, 256)

### 4. Grammar Hierarchy

**Level 1: Minimal** (for testing)
```lark
start: "return " NUMBER
```

**Level 2: Basic** (for simple completions)
```lark
start: return_stmt | assign_stmt
```

**Level 3: Full** (for complex generation)
```lark
start: suite
suite: statement+
statement: return_stmt | if_stmt | for_stmt | ...
```

## References

- **llguidance docs**: https://github.com/guidance-ai/llguidance/blob/main/docs/syntax.md
- **vLLM V1 structured outputs**: https://docs.vllm.ai/en/stable/api/vllm/v1/structured_output/backend_guidance.html
- **Lark grammar syntax**: https://lark-parser.readthedocs.io/en/latest/grammar.html
- **Modal deployment**: `deployment/modal/modal_app.py`

## Changelog

- **2025-11-12**: Initial documentation after completing completion-focused grammars
  - Documented `?start:` incompatibility with llguidance
  - Documented completion vs full generation pattern
  - Documented vLLM V1 API requirements
  - Documented Modal endpoint configuration
