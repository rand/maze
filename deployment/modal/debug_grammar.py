"""Debug script to test grammar constraint enforcement."""

import sys
sys.path.insert(0, '/Users/rand/src/maze/src')

from maze.orchestrator.providers.modal import ModalProviderAdapter
from maze.orchestrator.providers import GenerationRequest
from maze.synthesis.grammars.python import PYTHON_FUNCTION

def test_grammar_sent():
    """Test if grammar is being sent to Modal."""
    adapter = ModalProviderAdapter()
    
    grammar = PYTHON_FUNCTION.grammar
    
    print("=" * 80)
    print("TESTING GRAMMAR TRANSMISSION")
    print("=" * 80)
    print(f"Grammar length: {len(grammar)} chars")
    print(f"Grammar preview:\n{grammar[:300]}\n")
    print("=" * 80)
    
    request = GenerationRequest(
        prompt="def test():",
        max_tokens=32,
        temperature=0.1,
        grammar=grammar,
    )
    
    print(f"Request.grammar is set: {request.grammar is not None}")
    print(f"Request.grammar length: {len(request.grammar)}")
    print("=" * 80)
    
    print("Sending to Modal (check Modal logs for debug output)...")
    response = adapter.generate(request)
    
    print("=" * 80)
    print("RESPONSE RECEIVED")
    print("=" * 80)
    print(f"Success: {response.metadata.get('success', 'unknown')}")
    print(f"Text: {response.text[:200]}")
    print(f"Metadata: {response.metadata}")
    print("=" * 80)
    
    # Check Modal app logs now
    print("\nCheck Modal logs with:")
    print("  modal app logs maze-inference")

if __name__ == "__main__":
    test_grammar_sent()
