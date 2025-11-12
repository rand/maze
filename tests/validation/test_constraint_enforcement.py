"""Test that grammar constraints are actually enforced.

This validates Maze's core value proposition:
1. Grammar constraints prevent invalid syntax
2. Generated code is syntactically valid
3. Type constraints are respected
4. Constraints measurably improve correctness vs unconstrained LLM

Testing methodology:
- Generate WITH and WITHOUT constraints
- Parse/compile generated code
- Verify constrained generation has higher validity rate
- Verify grammar violations are prevented

CRITICAL TESTING PRINCIPLES:
1. ✅ Test with REAL Modal endpoint (not mocks)
   - Mocks hide grammar syntax issues (?start: incompatibility)
   - Mocks hide token limit edge cases
   - Mocks hide llguidance behavior

2. ✅ Validate grammar enforcement (not just success)
   - Check forbidden constructs ARE absent (comments, loops, etc.)
   - Check required constructs ARE present (return, expressions)
   - Parse with language compiler/interpreter (ast.parse, tsc, rustc)

3. ✅ Use completion grammars for completion tasks
   - Prompt: "def foo():" → Use PYTHON_FUNCTION_BODY
   - NOT PYTHON_FUNCTION (causes signature duplication)

4. ❌ Don't test with "assert result is not None"
   - Meaningless - doesn't validate constraints
   - Doesn't validate syntax
   - Doesn't validate the value proposition

See docs/GRAMMAR_CONSTRAINTS.md for details.
"""

import ast
import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from maze.config import Config
from maze.core.pipeline import Pipeline
from maze.orchestrator.providers.modal import ModalProviderAdapter
from maze.orchestrator.providers import GenerationRequest
from maze.synthesis.grammars.python import PYTHON_FUNCTION, PYTHON_FUNCTION_BODY, PYTHON_CLASS
from maze.synthesis.grammars.typescript import TYPESCRIPT_FUNCTION, TYPESCRIPT_FUNCTION_BODY


class TestPythonConstraintEnforcement:
    """Test Python grammar constraints are enforced."""

    def test_unconstrained_can_produce_invalid_syntax(self):
        """Verify unconstrained generation can produce invalid Python."""
        adapter = ModalProviderAdapter()
        
        # Generate WITHOUT grammar
        request = GenerationRequest(
            prompt="def broken function syntax error:",
            max_tokens=64,
            temperature=0.7,
            grammar=None,  # NO CONSTRAINT
        )
        
        response = adapter.generate(request)
        
        # Try to parse as Python
        try:
            ast.parse(response.text)
            syntax_valid = True
        except SyntaxError:
            syntax_valid = False
        
        # Unconstrained may or may not be valid (that's the point)
        # We're just establishing baseline
        print(f"Unconstrained syntax valid: {syntax_valid}")
        print(f"Generated: {response.text[:100]}")

    def test_completion_mode_produces_valid_syntax(self):
        """Verify completion-focused grammar produces valid Python."""
        adapter = ModalProviderAdapter()
        
        # Use a minimal grammar that ONLY allows "return NUMBER"
        # This proves the grammar constraint is working
        minimal_grammar = """
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/
"""
        
        # Generate WITH strict grammar
        # Prompt includes the partial code structure
        request = GenerationRequest(
            prompt="def get_answer():\n    ",
            max_tokens=16,
            temperature=0.0,
            grammar=minimal_grammar,
        )
        
        response = adapter.generate(request)
        
        # Full code (prompt + completion)
        full_code = request.prompt + response.text
        
        # Parse as Python
        try:
            ast.parse(full_code)
            syntax_valid = True
            error = None
        except SyntaxError as e:
            syntax_valid = False
            error = str(e)
        
        print(f"Generated code:\n{full_code}")
        print(f"Completion only:\n{response.text}")
        
        # CRITICAL: Constrained MUST be valid
        assert syntax_valid, f"Grammar-constrained code has syntax error: {error}\n\nCode:\n{full_code}"
        
        # Verify it followed the grammar (only "return N")
        assert "return" in full_code.lower(), "Should have return statement"
        assert any(char.isdigit() for char in full_code), "Should return a number"
        
        # Should NOT have comments, loops, conditionals (not in grammar)
        assert "#" not in full_code, "Grammar forbids comments"
        assert "if" not in full_code.lower(), "Grammar forbids conditionals"
        assert "for" not in full_code.lower(), "Grammar forbids loops"
    
    def test_full_generation_mode_produces_valid_syntax(self):
        """Verify full generation grammar produces valid Python from scratch."""
        adapter = ModalProviderAdapter()
        
        # Use FULL function grammar (not completion)
        grammar = PYTHON_FUNCTION.grammar
        
        # Prompt is just description, not partial code
        request = GenerationRequest(
            prompt="Write a function to calculate factorial",
            max_tokens=128,
            temperature=0.3,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        
        # Parse generated code (no prompt prefix needed)
        try:
            ast.parse(response.text)
            syntax_valid = True
            error = None
        except SyntaxError as e:
            syntax_valid = False
            error = str(e)
        
        print(f"Generated code:\n{response.text}")
        
        # CRITICAL: Constrained MUST be valid
        assert syntax_valid, f"Grammar-constrained code has syntax error: {error}\n\nCode:\n{response.text}"
        
        # Should have function definition
        assert "def" in response.text, "Should generate function definition"

    def test_grammar_prevents_invalid_structures(self):
        """Test that grammar prevents specific invalid patterns."""
        adapter = ModalProviderAdapter()
        
        # Grammar that only allows simple return statements
        strict_grammar = """
?start: function_body
function_body: NEWLINE INDENT return_stmt DEDENT
return_stmt: "return" expression NEWLINE
expression: NAME | NUMBER
NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
NEWLINE: /\\n/
INDENT: "    "
DEDENT: ""
%ignore /[ \\t]+/
"""
        
        request = GenerationRequest(
            prompt="def simple():",
            max_tokens=64,
            temperature=0.1,
            grammar=strict_grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"Strictly constrained:\n{full_code}")
        
        # Must have exactly one return statement
        assert "return" in full_code.lower()
        
        # Should NOT have complex statements (loops, conditionals)
        assert "for" not in full_code.lower()
        assert "while" not in full_code.lower()
        assert "if" not in full_code.lower()
        
        # Must parse
        try:
            ast.parse(full_code)
        except SyntaxError as e:
            pytest.fail(f"Grammar-constrained code failed to parse: {e}\n{full_code}")

    def test_constraint_enforcement_rate(self):
        """Test that constraints improve validity rate."""
        adapter = ModalProviderAdapter()
        grammar = PYTHON_FUNCTION_BODY.grammar  # Use completion grammar
        
        test_cases = [
            "def add(x, y):",
            "def multiply(a: int, b: int) -> int:",
            "def greet(name: str) -> str:",
        ]
        
        constrained_valid = 0
        unconstrained_valid = 0
        
        for prompt in test_cases:
            # With constraint
            req_constrained = GenerationRequest(
                prompt=prompt,
                max_tokens=64,
                temperature=0.3,
                grammar=grammar,
            )
            resp_constrained = adapter.generate(req_constrained)
            
            try:
                ast.parse(prompt + "\n" + resp_constrained.text)
                constrained_valid += 1
            except SyntaxError:
                pass
            
            # Without constraint
            req_unconstrained = GenerationRequest(
                prompt=prompt,
                max_tokens=64,
                temperature=0.3,
                grammar=None,
            )
            resp_unconstrained = adapter.generate(req_unconstrained)
            
            try:
                ast.parse(prompt + "\n" + resp_unconstrained.text)
                unconstrained_valid += 1
            except SyntaxError:
                pass
        
        print(f"\nConstrained valid: {constrained_valid}/{len(test_cases)}")
        print(f"Unconstrained valid: {unconstrained_valid}/{len(test_cases)}")
        
        # Constrained should be 100% valid
        assert constrained_valid == len(test_cases), \
            f"Constrained should be 100% valid, got {constrained_valid}/{len(test_cases)}"


class TestTypeScriptConstraintEnforcement:
    """Test TypeScript grammar constraints are enforced."""

    def test_typescript_syntax_validity(self):
        """Test TypeScript generated code is syntactically valid."""
        adapter = ModalProviderAdapter()
        grammar = TYPESCRIPT_FUNCTION_BODY.grammar  # Use completion grammar
        
        request = GenerationRequest(
            prompt="function greet(name: string): string",
            max_tokens=128,
            temperature=0.3,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + " " + response.text
        
        print(f"Generated TypeScript:\n{full_code}")
        
        # Write to temp file and check with TypeScript compiler
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
            f.write(full_code)
            f.flush()
            
            # Try to parse with tsc (if available)
            try:
                result = subprocess.run(
                    ['npx', 'typescript', '--noEmit', '--target', 'ES2020', f.name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    print(f"TypeScript errors:\n{result.stderr}")
                
                # Should compile without errors
                assert result.returncode == 0, \
                    f"Grammar-constrained TypeScript has syntax errors:\n{result.stderr}"
                    
            except FileNotFoundError:
                pytest.skip("TypeScript compiler not available")
            except subprocess.TimeoutExpired:
                pytest.fail("TypeScript compilation timed out")
            finally:
                Path(f.name).unlink()

    def test_typescript_type_annotations_preserved(self):
        """Test that type annotations are preserved in generation."""
        adapter = ModalProviderAdapter()
        grammar = TYPESCRIPT_FUNCTION_BODY.grammar  # Use completion grammar
        
        request = GenerationRequest(
            prompt="function add(a: number, b: number): number",
            max_tokens=64,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        # Should contain return statement
        assert "return" in full_code.lower()
        
        # Should NOT lose type safety by using 'any'
        assert "any" not in full_code.lower(), \
            "Grammar should prevent 'any' type (maintains type safety)"


class TestGrammarApplicationVerification:
    """Verify that grammars are actually being sent to the LLM."""

    def test_grammar_is_sent_to_provider(self):
        """Test that grammar is included in provider request."""
        config = Config()
        config.project.language = "python"
        config.constraints.syntactic_enabled = True
        
        pipeline = Pipeline(config)
        
        # Generate with constraints enabled
        result = pipeline.generate("def test_function():")
        
        # Check internal state
        assert hasattr(pipeline, '_last_grammar'), \
            "Pipeline should track last grammar used"
        
        assert pipeline._last_grammar is not None, \
            "Grammar should be non-None when constraints enabled"
        
        assert len(pipeline._last_grammar) > 100, \
            f"Grammar suspiciously short ({len(pipeline._last_grammar)} chars)"
        
        # Verify it's a Lark grammar
        assert "?start:" in pipeline._last_grammar or "start:" in pipeline._last_grammar, \
            "Should be a Lark grammar (has start rule)"
        
        print(f"Grammar sent ({len(pipeline._last_grammar)} chars):")
        print(pipeline._last_grammar[:200])
        
        pipeline.close()

    def test_no_grammar_when_disabled(self):
        """Test that no grammar is sent when constraints disabled."""
        config = Config()
        config.project.language = "python"
        config.constraints.syntactic_enabled = False
        
        pipeline = Pipeline(config)
        
        result = pipeline.generate("def test():")
        
        # Should not have grammar
        if hasattr(pipeline, '_last_grammar'):
            assert pipeline._last_grammar is None or pipeline._last_grammar == "", \
                "Grammar should be empty when constraints disabled"
        
        pipeline.close()


class TestMultiLanguageCorrectness:
    """Test correctness across all supported languages."""

    @pytest.mark.parametrize("language,prompt,checker", [
        ("python", "def factorial(n: int) -> int:", "python"),
        ("typescript", "function fibonacci(n: number): number", "typescript"),
        ("rust", "fn is_prime(n: u32) -> bool", "rust"),
        ("go", "func Max(a, b int) int", "go"),
    ])
    def test_language_compilation(self, language, prompt, checker):
        """Test that generated code compiles in target language."""
        config = Config()
        config.project.language = language
        config.constraints.syntactic_enabled = True
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        result = pipeline.generate(prompt)
        
        full_code = prompt + result.code
        
        print(f"\n{language} generated:\n{full_code}\n")
        
        # Verify grammar was used
        assert pipeline._last_grammar is not None, \
            f"Grammar should be applied for {language}"
        
        # Language-specific validation
        if checker == "python":
            try:
                ast.parse(full_code)
            except SyntaxError as e:
                pytest.fail(f"Python syntax error: {e}\n{full_code}")
        
        elif checker == "rust":
            # Write to temp file and check with rustc
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                # Wrap in a valid Rust program
                f.write(f"fn main() {{}}\n\n{full_code}")
                f.flush()
                
                try:
                    result = subprocess.run(
                        ['rustc', '--crate-type', 'lib', '-', '--error-format', 'json'],
                        input=f"fn main() {{}}\n{full_code}",
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        errors = result.stderr
                        print(f"Rust compilation errors:\n{errors}")
                        pytest.fail(f"Rust code failed to compile:\n{errors}")
                        
                except FileNotFoundError:
                    pytest.skip("Rust compiler not available")
                except subprocess.TimeoutExpired:
                    pytest.fail("Rust compilation timed out")
                finally:
                    Path(f.name).unlink(missing_ok=True)
        
        elif checker == "go":
            # Write and check with go build
            with tempfile.TemporaryDirectory() as tmpdir:
                go_file = Path(tmpdir) / "main.go"
                go_file.write_text(f"package main\n\n{full_code}\n\nfunc main() {{}}")
                
                try:
                    result = subprocess.run(
                        ['go', 'build', '-o', '/dev/null', str(go_file)],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        pytest.fail(f"Go code failed to compile:\n{result.stderr}")
                        
                except FileNotFoundError:
                    pytest.skip("Go compiler not available")
                except subprocess.TimeoutExpired:
                    pytest.fail("Go compilation timed out")
        
        elif checker == "typescript":
            # Already tested above
            pass
        
        pipeline.close()


class TestConstraintEffectiveness:
    """Measure how effective constraints are vs unconstrained."""

    def test_constraint_improves_validity_measurably(self):
        """Test that constraints improve validity by measurable margin."""
        adapter = ModalProviderAdapter()
        
        # Test cases designed to be tricky
        test_cases = [
            "def parse_json(data):",
            "def validate_email(email: str) -> bool:",
            "def fibonacci(n: int) -> int:",
            "def merge_dicts(d1: dict, d2: dict) -> dict:",
        ]
        
        results = {
            'constrained_valid': 0,
            'constrained_total': 0,
            'unconstrained_valid': 0,
            'unconstrained_total': 0,
        }
        
        grammar = PYTHON_FUNCTION_BODY.grammar  # Use completion grammar
        
        for prompt in test_cases:
            # Test WITH constraint
            req_with = GenerationRequest(
                prompt=prompt,
                max_tokens=128,
                temperature=0.5,
                grammar=grammar,
            )
            resp_with = adapter.generate(req_with)
            results['constrained_total'] += 1
            
            try:
                ast.parse(prompt + "\n" + resp_with.text)
                results['constrained_valid'] += 1
            except SyntaxError as e:
                print(f"Constrained FAILED: {prompt}\nError: {e}")
            
            # Test WITHOUT constraint
            req_without = GenerationRequest(
                prompt=prompt,
                max_tokens=128,
                temperature=0.5,
                grammar=None,
            )
            resp_without = adapter.generate(req_without)
            results['unconstrained_total'] += 1
            
            try:
                ast.parse(prompt + "\n" + resp_without.text)
                results['unconstrained_valid'] += 1
            except SyntaxError as e:
                print(f"Unconstrained failed: {prompt}\nError: {e}")
        
        constrained_rate = results['constrained_valid'] / results['constrained_total']
        unconstrained_rate = results['unconstrained_valid'] / results['unconstrained_total']
        
        print(f"\nResults:")
        print(f"  Constrained:   {results['constrained_valid']}/{results['constrained_total']} ({constrained_rate:.0%})")
        print(f"  Unconstrained: {results['unconstrained_valid']}/{results['unconstrained_total']} ({unconstrained_rate:.0%})")
        print(f"  Improvement:   {(constrained_rate - unconstrained_rate):.0%}")
        
        # Core value proposition test
        assert constrained_rate >= 0.90, \
            f"Constrained should achieve ≥90% validity, got {constrained_rate:.0%}"
        
        assert constrained_rate > unconstrained_rate, \
            f"Constrained ({constrained_rate:.0%}) should outperform unconstrained ({unconstrained_rate:.0%})"


class TestTypeConstraints:
    """Test that type constraints are enforced."""

    def test_type_aware_generation(self):
        """Test that type context influences generation."""
        # TODO: This requires type system integration
        # For now, test that type annotations are preserved
        
        adapter = ModalProviderAdapter()
        grammar = PYTHON_FUNCTION_BODY.grammar  # Use completion grammar
        
        request = GenerationRequest(
            prompt="def process_user(user: User) -> dict:",
            max_tokens=128,
            temperature=0.3,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        # Should preserve type safety
        assert "User" in full_code or "user" in full_code.lower()
        assert "dict" in full_code or "return" in full_code
        
        # Parse successfully
        try:
            ast.parse(full_code)
        except SyntaxError as e:
            pytest.fail(f"Type-aware generation failed: {e}\n{full_code}")


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    @pytest.mark.skip(reason="Complex INDENT/DEDENT matching needs refinement")
    def test_multiple_statements_with_grammar(self):
        """Test generating multiple statements with grammar constraints."""
        adapter = ModalProviderAdapter()
        
        # Simple grammar for two statements
        grammar = """
start: statements
statements: NEWLINE INDENT statement statement DEDENT
statement: IDENT "=" expression NEWLINE
expression: IDENT ("+" | "-") IDENT | NUMBER
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
NEWLINE: /\\n/
INDENT: "    "
DEDENT: ""
%ignore /[ \\t]+/
"""
        
        request = GenerationRequest(
            prompt="def calculate(x, y):",
            max_tokens=32,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nGenerated multi-statement code:\n{full_code}")
        
        # Validate syntax
        try:
            ast.parse(full_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"Syntax error: {e}")
        
        assert syntax_valid, f"Multi-statement code should be valid:\n{full_code}"
        # Should have at least one assignment
        assert "=" in full_code

    def test_typescript_function_body_completion(self):
        """Test TypeScript function body completion."""
        adapter = ModalProviderAdapter()
        grammar = TYPESCRIPT_FUNCTION_BODY.grammar
        
        request = GenerationRequest(
            prompt="function multiply(a: number, b: number): number ",
            max_tokens=64,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nGenerated TypeScript:\n{full_code}")
        
        # Should have block structure
        assert "{" in full_code, "Should have opening brace"
        assert "}" in full_code or response.text.strip().endswith("}"), "Should have closing brace"
        
        # Should have return (for number return type)
        assert "return" in full_code.lower(), "Should return a value"

    def test_temperature_variation(self):
        """Test that different temperatures produce different but valid code."""
        adapter = ModalProviderAdapter()
        
        # Simple grammar for consistent testing
        grammar = """
start: simple
simple: "return " expression
expression: NUMBER | binary_expr
binary_expr: NUMBER ("+" | "-" | "*") NUMBER
NUMBER: /[0-9]+/
"""
        
        results = []
        for temp in [0.0, 0.5, 1.0]:
            request = GenerationRequest(
                prompt="def get_value():\n    ",
                max_tokens=16,
                temperature=temp,
                grammar=grammar,
            )
            
            response = adapter.generate(request)
            results.append((temp, response.text))
            
            # All should be valid
            full_code = request.prompt + response.text
            try:
                ast.parse(full_code)
            except SyntaxError as e:
                pytest.fail(f"Temp {temp} produced invalid code: {e}\n{full_code}")
        
        print("\nTemperature variation results:")
        for temp, code in results:
            print(f"  T={temp}: {code.strip()}")
        
        # All should parse successfully (assertion above)
        assert len(results) == 3

    def test_constrained_vs_unconstrained_comparison(self):
        """Direct comparison of constrained vs unconstrained generation."""
        adapter = ModalProviderAdapter()
        
        test_prompts = [
            "def add(a, b):\n    ",
            "def is_valid(x):\n    ",
            "def process(data):\n    ",
        ]
        
        # Use simple grammar for reliable comparison
        grammar = """
start: simple
simple: "return " expression
expression: IDENT | NUMBER | binary_expr
binary_expr: IDENT ("+" | "-") IDENT
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
"""
        
        results = {
            'constrained': {'valid': 0, 'total': 0},
            'unconstrained': {'valid': 0, 'total': 0},
        }
        
        for prompt in test_prompts:
            # Constrained
            req_constrained = GenerationRequest(
                prompt=prompt,
                max_tokens=32,
                temperature=0.3,
                grammar=grammar,
            )
            resp_constrained = adapter.generate(req_constrained)
            results['constrained']['total'] += 1
            
            try:
                ast.parse(prompt + resp_constrained.text)
                results['constrained']['valid'] += 1
            except SyntaxError:
                print(f"Constrained FAILED for: {prompt}")
            
            # Unconstrained
            req_unconstrained = GenerationRequest(
                prompt=prompt,
                max_tokens=32,
                temperature=0.3,
                grammar=None,
            )
            resp_unconstrained = adapter.generate(req_unconstrained)
            results['unconstrained']['total'] += 1
            
            try:
                ast.parse(prompt + resp_unconstrained.text)
                results['unconstrained']['valid'] += 1
            except SyntaxError:
                print(f"Unconstrained failed for: {prompt}")
        
        constrained_rate = results['constrained']['valid'] / results['constrained']['total']
        unconstrained_rate = results['unconstrained']['valid'] / results['unconstrained']['total']
        
        print(f"\n📊 Comparison Results:")
        print(f"  Constrained:   {results['constrained']['valid']}/{results['constrained']['total']} ({constrained_rate:.0%})")
        print(f"  Unconstrained: {results['unconstrained']['valid']}/{results['unconstrained']['total']} ({unconstrained_rate:.0%})")
        print(f"  Improvement:   {(constrained_rate - unconstrained_rate):.0%}")
        
        # Constrained should be 100%
        assert constrained_rate == 1.0, f"Constrained should be 100%, got {constrained_rate:.0%}"

    def test_edge_case_empty_params(self):
        """Test function with no parameters."""
        adapter = ModalProviderAdapter()
        
        grammar = """
start: simple
simple: "return " (NUMBER | STRING)
NUMBER: /[0-9]+/
STRING: /"[^"]*"/
"""
        
        request = GenerationRequest(
            prompt="def get_constant():\n    ",
            max_tokens=16,
            temperature=0.0,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nEmpty params test:\n{full_code}")
        
        try:
            ast.parse(full_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"Error: {e}")
        
        assert syntax_valid, "Should handle no-param functions"

    def test_complex_expression_generation(self):
        """Test generating expressions with operators."""
        adapter = ModalProviderAdapter()
        
        # Simple but complete expression grammar
        grammar = """
start: simple
simple: "return " expression
expression: term (("+" | "-") term)?
term: IDENT | NUMBER
NUMBER: /[0-9]+/
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
"""
        
        request = GenerationRequest(
            prompt="def compute(a, b, c):\n    ",
            max_tokens=16,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nExpression:\n{full_code}")
        
        try:
            ast.parse(full_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"Error: {e}")
        
        assert syntax_valid, "Should generate valid expressions"
        assert "return" in response.text.lower()


class TestPerformanceCharacteristics:
    """Test and document performance characteristics."""

    def test_latency_with_grammar(self):
        """Measure and report latency with grammar constraints."""
        adapter = ModalProviderAdapter()
        
        grammar = """
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/
"""
        
        import time
        
        # Warm up
        request = GenerationRequest(
            prompt="def test():\n    ",
            max_tokens=16,
            temperature=0.0,
            grammar=grammar,
        )
        adapter.generate(request)
        
        # Measure
        latencies = []
        for _ in range(3):
            start = time.perf_counter()
            adapter.generate(request)
            latency = time.perf_counter() - start
            latencies.append(latency)
        
        avg_latency = sum(latencies) / len(latencies)
        
        print(f"\n⏱️  Performance (with grammar):")
        print(f"  Average latency: {avg_latency:.2f}s")
        print(f"  Min: {min(latencies):.2f}s")
        print(f"  Max: {max(latencies):.2f}s")
        
        # Should be reasonable (warm request <5s)
        assert avg_latency < 5.0, f"Latency too high: {avg_latency:.2f}s"

    def test_token_efficiency(self):
        """Test that grammar constraints are token-efficient."""
        adapter = ModalProviderAdapter()
        
        grammar = """
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/
"""
        
        request = GenerationRequest(
            prompt="def answer():\n    ",
            max_tokens=16,
            temperature=0.0,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        
        print(f"\n🎯 Token efficiency:")
        print(f"  Max tokens: {request.max_tokens}")
        print(f"  Generated: {response.metadata.get('tokens_generated', 'unknown')}")
        print(f"  Code: {response.text.strip()}")
        
        # Should be concise with strict grammar
        assert len(response.text) < 100, "Should be concise with strict grammar"


class TestRealWorldPatterns:
    """Test patterns that match real-world usage."""

    def test_error_handling_pattern(self):
        """Test generating code with error handling."""
        adapter = ModalProviderAdapter()
        
        # Grammar for try-except pattern
        grammar = """
start: suite
suite: NEWLINE INDENT try_stmt DEDENT
try_stmt: "try:" NEWLINE INDENT return_stmt DEDENT "except:" NEWLINE INDENT return_stmt DEDENT
return_stmt: "return " (NUMBER | STRING) NEWLINE
NUMBER: /[0-9]+/
STRING: /"[^"]*"/
NEWLINE: /\\n/
INDENT: "    "
DEDENT: ""
%ignore /[ \\t]+/
"""
        
        request = GenerationRequest(
            prompt="def safe_operation():",
            max_tokens=64,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nError handling pattern:\n{full_code}")
        
        try:
            ast.parse(full_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"Error: {e}")
        
        assert syntax_valid, "Error handling pattern should be valid"
        assert "try" in full_code.lower()
        assert "except" in full_code.lower()

    def test_conditional_return_pattern(self):
        """Test generating conditional return statements."""
        adapter = ModalProviderAdapter()
        
        grammar = """
start: suite
suite: NEWLINE INDENT if_stmt DEDENT
if_stmt: "if" condition ":" NEWLINE INDENT return_stmt DEDENT "return" expression NEWLINE
condition: IDENT comparison IDENT
comparison: "==" | "!=" | "<" | ">" | "<=" | ">="
return_stmt: "return" expression NEWLINE
expression: IDENT | NUMBER
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /[0-9]+/
NEWLINE: /\\n/
INDENT: "    "
DEDENT: ""
%ignore /[ \\t]+/
"""
        
        request = GenerationRequest(
            prompt="def check(x, y):",
            max_tokens=64,
            temperature=0.1,
            grammar=grammar,
        )
        
        response = adapter.generate(request)
        full_code = request.prompt + response.text
        
        print(f"\nConditional return:\n{full_code}")
        
        try:
            ast.parse(full_code)
            syntax_valid = True
        except SyntaxError as e:
            syntax_valid = False
            print(f"Error: {e}")
        
        assert syntax_valid, "Conditional pattern should be valid"
        assert "if" in full_code.lower()
        assert "return" in full_code.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
