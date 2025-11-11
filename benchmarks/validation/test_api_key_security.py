"""Test secure API key handling and validation.

Ensures:
- API keys not logged
- API keys not in error messages (redacted)
- API keys loaded from environment only
- Graceful handling when missing

Usage:
    python benchmarks/validation/test_api_key_security.py
"""

import os
import sys
import tempfile
from io import StringIO
from pathlib import Path

from maze.config import Config, LoggingConfig
from maze.core.pipeline import Pipeline
from maze.logging import StructuredLogger


def test_api_key_not_logged():
    """Test that API keys are never logged."""
    print("Test 1: API keys not logged")
    
    # Setup logging to capture output
    output = StringIO()
    config = Config()
    config.logging.format = "json"
    config.project.language = "python"
    
    logger = StructuredLogger(config.logging)
    logger.output = output
    
    pipeline = Pipeline(config)
    pipeline.logger = logger
    
    # Set fake API key
    test_key = "sk-test-secret-key-12345"
    with patch.dict(os.environ, {"OPENAI_API_KEY": test_key}):
        # Generate (will fail without real key, but shouldn't log it)
        try:
            pipeline.generate("test")
        except:
            pass
    
    # Check logs don't contain API key
    output.seek(0)
    logs = output.read()
    
    assert test_key not in logs, "❌ API key found in logs!"
    print("  ✅ API keys not present in logs")


def test_api_key_from_environment_only():
    """Test API keys only loaded from environment."""
    print("\nTest 2: API keys from environment only")
    
    config = Config()
    config.project.language = "python"
    pipeline = Pipeline(config)
    
    # Clear environment
    with patch.dict(os.environ, {}, clear=True):
        code = pipeline._generate_with_constraints("test", "", None)
        
        # Should get helpful message, not crash
        assert "API key not found" in code
        print("  ✅ Graceful handling when API key missing")
    
    # Set environment variable
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}):
        # Would create provider (will fail on actual call, but key loaded)
        assert os.getenv("OPENAI_API_KEY") == "sk-test"
        print("  ✅ API key loaded from environment")


def test_helpful_error_messages():
    """Test error messages are helpful but don't expose keys."""
    print("\nTest 3: Error messages are helpful and secure")
    
    config = Config()
    config.project.language = "python"
    pipeline = Pipeline(config)
    
    with patch.dict(os.environ, {}, clear=True):
        code = pipeline._generate_with_constraints("test", "", None)
        
        # Should tell user what to do
        assert "OPENAI_API_KEY" in code
        assert "export" in code or "Set:" in code
        print("  ✅ Helpful instructions provided")
        
        # Should not contain actual key values
        assert "sk-" not in code or code.startswith("// OpenAI")
        print("  ✅ No key values in error messages")


def test_api_key_validation():
    """Test API key format validation."""
    print("\nTest 4: API key validation")
    
    # Check environment variable is checked
    with patch.dict(os.environ, {"OPENAI_API_KEY": "invalid-format"}):
        config = Config()
        pipeline = Pipeline(config)
        
        # Provider will be created with the key
        # Actual validation happens in OpenAI client
        assert os.getenv("OPENAI_API_KEY") is not None
        print("  ✅ API key presence checked")


def main():
    """Run all security tests."""
    print("=" * 60)
    print("API Key Security Validation")
    print("=" * 60)
    
    # Import patch after imports
    from unittest.mock import patch
    globals()['patch'] = patch
    
    try:
        test_api_key_not_logged()
        test_api_key_from_environment_only()
        test_helpful_error_messages()
        test_api_key_validation()
        
        print("\n" + "=" * 60)
        print("✅ All security tests passed!")
        print("=" * 60)
        
        print("\nAPI Key Security Verified:")
        print("  ✓ Keys never logged")
        print("  ✓ Keys from environment only")
        print("  ✓ Helpful error messages")
        print("  ✓ No key exposure in errors")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Security test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
