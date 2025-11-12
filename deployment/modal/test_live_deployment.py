"""Test live Modal deployment with proper timeout handling.

This script handles long cold starts (3-5 minutes) and runs actual tests.
"""

import json
import sys
import time
from pathlib import Path

import requests

ENDPOINT = "https://rand--maze-inference-mazeinferenceserver-fastapi-app.modal.run"
TIMEOUT = 600  # 10 minutes for cold start


def test_health(max_retries=20, retry_delay=15):
    """Test health endpoint with retries for cold start."""
    print("=" * 70)
    print("Test 1: Health Check (waiting for cold start)")
    print("=" * 70)
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries}...")
            response = requests.get(f"{ENDPOINT}/health", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check successful!")
                print(json.dumps(data, indent=2))
                return True
            else:
                print(f"Status: {response.status_code}, retrying...")
                
        except requests.exceptions.Timeout:
            print(f"Timeout, retrying in {retry_delay}s...")
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}, retrying in {retry_delay}s...")
        except Exception as e:
            print(f"Error: {e}, retrying in {retry_delay}s...")
        
        if attempt < max_retries:
            time.sleep(retry_delay)
    
    print("❌ Health check failed after all retries")
    return False


def test_simple_generation():
    """Test simple code generation."""
    print("\n" + "=" * 70)
    print("Test 2: Simple Python Generation")
    print("=" * 70)
    
    payload = {
        "prompt": "def add(a: int, b: int) -> int:\n    ",
        "language": "python",
        "max_tokens": 64,
        "temperature": 0.3,
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Sending request (may take 30-60s for first generation)...")
    
    start = time.time()
    
    try:
        response = requests.post(
            f"{ENDPOINT}/generate",
            json=payload,
            timeout=TIMEOUT,
        )
        
        duration = time.time() - start
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Generation successful in {duration:.1f}s")
            print(f"Success: {data.get('success')}")
            print(f"Tokens: {data.get('metadata', {}).get('tokens_generated')}")
            print(f"\nGenerated code:")
            print("-" * 70)
            print(data.get('code', '')[:500])
            print("-" * 70)
            return data
        else:
            print(f"❌ Status: {response.status_code}")
            print(response.text)
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Timeout after {TIMEOUT}s")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_with_grammar():
    """Test generation with grammar constraint."""
    print("\n" + "=" * 70)
    print("Test 3: Generation with Grammar Constraint")
    print("=" * 70)
    
    # Simple Python function grammar
    grammar = """
?start: function_def
function_def: "def" IDENT "(" params ")" ":" suite
params: IDENT ("," IDENT)*
suite: NEWLINE INDENT statement+ DEDENT
statement: "return" expression NEWLINE
expression: IDENT "+" IDENT
IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
NEWLINE: /\\n/
INDENT: "    "
DEDENT: ""
%ignore /[ \\t]+/
"""
    
    payload = {
        "prompt": "def add(a, b):",
        "grammar": grammar,
        "language": "python",
        "max_tokens": 32,
        "temperature": 0.1,
    }
    
    print(f"Prompt: {payload['prompt']}")
    print(f"Grammar: <{len(grammar)} chars>")
    print(f"Sending request...")
    
    try:
        response = requests.post(
            f"{ENDPOINT}/generate",
            json=payload,
            timeout=TIMEOUT,
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Constrained generation successful")
            print(f"Grammar applied: {data.get('metadata', {}).get('grammar_applied')}")
            print(f"\nGenerated code:")
            print("-" * 70)
            print(data.get('code', ''))
            print("-" * 70)
            return data
        else:
            print(f"❌ Status: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def test_multiple_languages():
    """Test generation across multiple languages."""
    print("\n" + "=" * 70)
    print("Test 4: Multi-Language Generation")
    print("=" * 70)
    
    test_cases = [
        ("python", "def hello() -> str:"),
        ("typescript", "function hello(): string"),
        ("rust", "fn hello() -> String"),
        ("go", "func Hello() string"),
    ]
    
    results = []
    
    for lang, prompt in test_cases:
        print(f"\n{lang.upper()}:")
        print(f"  Prompt: {prompt}")
        
        try:
            response = requests.post(
                f"{ENDPOINT}/generate",
                json={
                    "prompt": prompt,
                    "language": lang,
                    "max_tokens": 64,
                    "temperature": 0.3,
                },
                timeout=120,
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  ✅ Success ({len(data.get('code', ''))} chars)")
                results.append((lang, True, data))
            else:
                print(f"  ❌ Failed: {response.status_code}")
                results.append((lang, False, None))
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
            results.append((lang, False, None))
    
    return results


def main():
    """Run all tests."""
    print("=" * 70)
    print("MAZE MODAL DEPLOYMENT VALIDATION")
    print("=" * 70)
    print(f"Endpoint: {ENDPOINT}")
    print(f"Timeout: {TIMEOUT}s")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    results = {
        "endpoint": ENDPOINT,
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "tests": {}
    }
    
    # Test 1: Health check with cold start handling
    health_ok = test_health()
    results["tests"]["health"] = health_ok
    
    if not health_ok:
        print("\n❌ Health check failed - cannot proceed with generation tests")
        return 1
    
    # Test 2: Simple generation
    gen_result = test_simple_generation()
    results["tests"]["simple_generation"] = gen_result is not None
    
    # Test 3: Grammar-constrained generation
    grammar_result = test_with_grammar()
    results["tests"]["grammar_generation"] = grammar_result is not None
    
    # Test 4: Multi-language
    lang_results = test_multiple_languages()
    results["tests"]["languages"] = {
        lang: success for lang, success, _ in lang_results
    }
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"Health: {'✅' if results['tests']['health'] else '❌'}")
    print(f"Simple generation: {'✅' if results['tests']['simple_generation'] else '❌'}")
    print(f"Grammar generation: {'✅' if results['tests']['grammar_generation'] else '❌'}")
    print(f"Languages tested: {len(lang_results)}")
    
    for lang, success, _ in lang_results:
        print(f"  {lang}: {'✅' if success else '❌'}")
    
    # Save results
    output_file = Path(__file__).parent / "live_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {output_file}")
    
    # Return code
    all_passed = (
        results["tests"]["health"]
        and results["tests"]["simple_generation"]
        and all(success for _, success, _ in lang_results)
    )
    
    if all_passed:
        print("\n✅ ALL TESTS PASSED!")
        return 0
    else:
        print("\n⚠️  Some tests failed (see details above)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
