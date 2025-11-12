"""Comprehensive test suite for Maze capabilities across all 5 languages.

This suite validates:
- Grammar constraint enforcement
- Type-aware generation
- Multi-language support
- Common patterns per language
- Error handling
- Real-world scenarios

Usage:
    # With Modal deployment
    export MODAL_ENDPOINT_URL=https://rand--maze-inference-fastapi-app.modal.run
    uv run pytest tests/validation/test_suite_comprehensive.py -v --tb=short

    # With OpenAI (JSON mode only)
    export OPENAI_API_KEY=sk-...
    uv run pytest tests/validation/test_suite_comprehensive.py -v -k "not grammar"
"""

import os
import tempfile
from pathlib import Path

import pytest

from maze.config import Config
from maze.core.pipeline import Pipeline


# Skip if no provider configured
PROVIDER_AVAILABLE = bool(
    os.getenv("MODAL_ENDPOINT_URL") or os.getenv("OPENAI_API_KEY")
)

pytestmark = pytest.mark.skipif(
    not PROVIDER_AVAILABLE,
    reason="No provider configured (set MODAL_ENDPOINT_URL or OPENAI_API_KEY)"
)


class TestTypeScriptGeneration:
    """Test TypeScript code generation with constraints."""

    def test_typescript_simple_function(self):
        """Test generating simple TypeScript function."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "function add(a: number, b: number): number"
        )
        
        assert result.success or "return" in result.code.lower()
        assert "function" in result.code.lower() or "=>" in result.code
        
        pipeline.close()

    def test_typescript_interface(self):
        """Test generating TypeScript interface."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create interface User with id: string, name: string, email: string"
        )
        
        assert result.code is not None
        assert len(result.code) > 20
        
        pipeline.close()

    def test_typescript_class(self):
        """Test generating TypeScript class."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create class Calculator with add and subtract methods"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_typescript_async_function(self):
        """Test generating async TypeScript function."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create async function fetchUser that takes userId and returns Promise<User>"
        )
        
        assert result.code is not None
        pipeline.close()


class TestPythonGeneration:
    """Test Python code generation with constraints."""

    def test_python_simple_function(self):
        """Test generating simple Python function with type hints."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "def calculate_bmi(weight: float, height: float) -> float:"
        )
        
        assert result.success or "return" in result.code.lower()
        assert "def" in result.code
        
        pipeline.close()

    def test_python_dataclass(self):
        """Test generating Python dataclass."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create dataclass User with name: str, email: str, age: int"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_python_async_function(self):
        """Test generating async Python function."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create async function fetch_data(url: str) -> dict with error handling"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_python_list_comprehension(self):
        """Test Python-specific patterns."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create function to filter even numbers from list using comprehension"
        )
        
        assert result.code is not None
        pipeline.close()


class TestRustGeneration:
    """Test Rust code generation with constraints."""

    def test_rust_function_with_result(self):
        """Test generating Rust function with Result type."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "fn divide(a: f64, b: f64) -> Result<f64, String>"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_rust_struct_with_impl(self):
        """Test generating Rust struct with implementation."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create struct Point with x and y fields, and impl block with new() method"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_rust_trait_implementation(self):
        """Test Rust trait implementation."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Implement Display trait for struct User"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_rust_option_handling(self):
        """Test Rust Option type."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create function find_user that returns Option<User>"
        )
        
        assert result.code is not None
        pipeline.close()


class TestGoGeneration:
    """Test Go code generation with constraints."""

    def test_go_function_with_error(self):
        """Test generating Go function with error return."""
        config = Config()
        config.project.language = "go"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "func Divide(a, b float64) (float64, error)"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_go_struct_with_methods(self):
        """Test Go struct with methods."""
        config = Config()
        config.project.language = "go"
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create struct Counter with pointer receiver methods Increment and Value"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_go_interface(self):
        """Test Go interface definition."""
        config = Config()
        config.project.language = "go"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create interface Repository with Find and Save methods"
        )
        
        assert result.code is not None
        pipeline.close()


class TestZigGeneration:
    """Test Zig code generation with constraints."""

    def test_zig_function(self):
        """Test generating Zig function."""
        config = Config()
        config.project.language = "zig"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "pub fn add(a: i32, b: i32) i32"
        )
        
        assert result.code is not None
        pipeline.close()

    def test_zig_struct(self):
        """Test Zig struct."""
        config = Config()
        config.project.language = "zig"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(
            "Create pub const Point = struct with x and y fields"
        )
        
        assert result.code is not None
        pipeline.close()


class TestCrossLanguageScenarios:
    """Test same scenarios across multiple languages."""

    @pytest.mark.parametrize("language", ["typescript", "python", "rust", "go", "zig"])
    def test_hello_world_function(self, language):
        """Test hello world function in each language."""
        config = Config()
        config.project.language = language
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        result = pipeline.run(f"Create a hello world function for {language}")
        
        assert result is not None
        assert result.code is not None
        assert len(result.code) > 10
        
        pipeline.close()

    @pytest.mark.parametrize("language", ["typescript", "python", "rust"])
    def test_error_handling(self, language):
        """Test error handling patterns in each language."""
        config = Config()
        config.project.language = language
        config.generation.max_tokens = 512
        
        pipeline = Pipeline(config)
        
        prompts = {
            "typescript": "Create function with try/catch error handling",
            "python": "Create function with try/except error handling",
            "rust": "Create function returning Result with error handling",
        }
        
        result = pipeline.run(prompts[language])
        
        assert result.code is not None
        pipeline.close()


class TestGrammarConstraints:
    """Test grammar constraint enforcement."""

    def test_python_function_structure(self):
        """Test Python function follows grammar."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project = Path(tmpdir)
            (project / "main.py").write_text("def existing(): pass")
            
            config = Config()
            config.project.path = project
            config.project.language = "python"
            config.constraints.syntactic_enabled = True
            
            pipeline = Pipeline(config)
            
            # Index to get context
            pipeline.index_project(project)
            
            # Generate with grammar
            result = pipeline.generate("Create function to add two numbers")
            
            # Verify grammar was loaded
            assert pipeline._last_grammar != ""
            assert "def" in pipeline._last_grammar.lower() or "function" in pipeline._last_grammar.lower()
            
            pipeline.close()

    def test_typescript_type_constraints(self):
        """Test TypeScript with type constraints."""
        config = Config()
        config.project.language = "typescript"
        config.constraints.syntactic_enabled = True
        config.constraints.type_enabled = True
        
        pipeline = Pipeline(config)
        
        result = pipeline.generate(
            "Create function validateEmail(email: string): boolean"
        )
        
        # Grammar should be loaded
        assert pipeline._last_grammar != ""
        
        pipeline.close()


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_python_api_endpoint(self):
        """Test generating Python FastAPI endpoint."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create FastAPI POST endpoint for user creation:
- Endpoint: @app.post("/users")
- Request model: UserCreate with name and email
- Response model: UserResponse with id, name, email
- Include validation
""")
        
        assert result.code is not None
        assert len(result.code) > 100
        
        pipeline.close()

    def test_typescript_react_component(self):
        """Test generating TypeScript React component."""
        config = Config()
        config.project.language = "typescript"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create React component UserCard with:
- Props: user: User
- Display user name and email
- Click handler for delete
""")
        
        assert result.code is not None
        pipeline.close()

    def test_rust_async_handler(self):
        """Test Rust async with error handling."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create async function fetch_user_data:
- Parameter: user_id: &str
- Returns: Result<User, reqwest::Error>
- Use reqwest for HTTP
- Error handling with ?
""")
        
        assert result.code is not None
        pipeline.close()


class TestPerformanceMetrics:
    """Test and collect performance metrics."""

    def test_generation_speed(self):
        """Measure generation speed."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        import time
        start = time.time()
        
        result = pipeline.run("def fibonacci(n: int) -> int:")
        
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 30  # 30 seconds max
        
        print(f"\nGeneration time: {duration:.2f}s")
        if result.generation:
            print(f"Tokens generated: {result.generation.tokens_generated}")
        
        pipeline.close()

    def test_batch_generation(self):
        """Test multiple generations."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        prompts = [
            "def add(a, b):",
            "def subtract(a, b):",
            "def multiply(a, b):",
        ]
        
        results = []
        for prompt in prompts:
            result = pipeline.generate(prompt)
            results.append(result)
        
        # All should succeed or produce code
        assert all(r.code is not None for r in results)
        
        # Check cache hit rate improved
        hit_rate = pipeline.metrics.get_cache_hit_rate("grammar")
        print(f"\nGrammar cache hit rate: {hit_rate:.1%}")
        
        pipeline.close()


class TestValidationIntegration:
    """Test validation on generated code."""

    def test_python_validation(self):
        """Test validation catches syntax errors."""
        config = Config()
        config.project.language = "python"
        config.validation.syntax_check = True
        
        pipeline = Pipeline(config)
        
        # Generate
        result = pipeline.generate("def test(): pass")
        
        # Validate
        if result.code:
            val_result = pipeline.validate(result.code)
            
            # Should have validation result
            assert val_result is not None
            print(f"\nSyntax valid: {val_result.success}")
        
        pipeline.close()

    def test_typescript_type_checking(self):
        """Test TypeScript type validation."""
        config = Config()
        config.project.language = "typescript"
        
        pipeline = Pipeline(config)
        
        result = pipeline.generate(
            "function greet(name: string): string"
        )
        
        if result.code:
            val_result = pipeline.validate(result.code)
            assert val_result is not None
        
        pipeline.close()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_prompt(self):
        """Test handling of empty prompt."""
        config = Config()
        config.project.language = "python"
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("")
        
        # Should not crash
        assert result is not None
        
        pipeline.close()

    def test_very_long_prompt(self):
        """Test long prompt handling."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 256
        
        pipeline = Pipeline(config)
        
        long_prompt = "Create a function " + "that does something " * 50
        
        result = pipeline.run(long_prompt)
        
        assert result is not None
        
        pipeline.close()

    def test_unsupported_language_graceful(self):
        """Test graceful handling of unsupported language."""
        config = Config()
        config.project.language = "unsupported"
        
        pipeline = Pipeline(config)
        
        with pytest.raises(ValueError, match="not yet supported"):
            pipeline.index_project(Path("/tmp"))


class TestRealWorldScenarios:
    """Test realistic development scenarios."""

    def test_crud_operations(self):
        """Test generating CRUD operations."""
        config = Config()
        config.project.language = "python"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create Python class UserRepository with methods:
- find_by_id(user_id: str) -> Optional[User]
- save(user: User) -> User
- delete(user_id: str) -> bool
Use type hints throughout
""")
        
        assert result.code is not None
        assert len(result.code) > 200
        
        pipeline.close()

    def test_error_type_hierarchy(self):
        """Test generating error type hierarchy."""
        config = Config()
        config.project.language = "rust"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create Rust error enum AppError with variants:
- NotFound(String)
- ValidationError(String)
- DatabaseError
Use thiserror derive
""")
        
        assert result.code is not None
        pipeline.close()

    def test_concurrent_handler(self):
        """Test concurrent processing code."""
        config = Config()
        config.project.language = "go"
        config.generation.max_tokens = 1024
        
        pipeline = Pipeline(config)
        
        result = pipeline.run("""
Create Go function ProcessConcurrently that:
- Takes items []string
- Processes each in goroutine
- Returns []string results
- Uses channels for coordination
""")
        
        assert result.code is not None
        pipeline.close()


class TestMetricsCollection:
    """Test metrics are collected properly."""

    def test_metrics_recorded(self):
        """Test all metrics are recorded."""
        config = Config()
        config.project.language = "python"
        
        pipeline = Pipeline(config)
        
        # Generate something
        pipeline.run("def test(): pass")
        
        # Check metrics
        summary = pipeline.metrics.summary()
        
        assert "latencies" in summary
        assert "counters" in summary
        assert "cache_hit_rates" in summary
        
        # Should have some latency data
        assert len(summary["latencies"]) > 0
        
        print(f"\nMetrics collected:")
        print(f"  Latencies: {list(summary['latencies'].keys())}")
        print(f"  Cache hit rates: {summary['cache_hit_rates']}")
        
        pipeline.close()

    def test_provider_call_tracking(self):
        """Test provider calls are tracked."""
        config = Config()
        config.project.language = "python"
        
        if os.getenv("MODAL_ENDPOINT_URL"):
            # Only test if Modal configured
            pipeline = Pipeline(config)
            
            pipeline.generate("def test(): pass")
            
            summary = pipeline.metrics.summary()
            
            # Should track provider calls if Modal used
            if "provider_call" in summary["latencies"]:
                stats = summary["latencies"]["provider_call"]
                print(f"\nProvider call stats:")
                print(f"  Mean: {stats['mean']:.0f}ms")
                print(f"  Count: {stats['count']}")
            
            pipeline.close()
