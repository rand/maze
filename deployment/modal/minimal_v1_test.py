"""Minimal test of vLLM V1 with grammar constraints."""

import modal

app = modal.App("test-vllm-v1-grammar")

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "wget")
    .uv_pip_install("vllm==0.11.0", "transformers==4.55.2", "llguidance>=0.7.11,<0.8.0")
)

@app.function(gpu="a100-40gb", image=image, timeout=1800)
def test_v1_with_grammar():
    """Test vLLM V1 with minimal Lark grammar."""
    from vllm import LLM, SamplingParams
    from vllm.sampling_params import StructuredOutputsParams
    
    print("=" * 80)
    print("TESTING vLLM V1 WITH GRAMMAR")
    print("=" * 80)
    
    # Simple Lark grammar (from llguidance docs)
    lark_grammar = """
start: simple
simple: "return " NUMBER
NUMBER: /[0-9]+/
"""
    
    print(f"Grammar:\n{lark_grammar}\n")
    
    # Initialize with V1 (enabled by default) and guidance backend
    print("Loading model with V1 engine (default)...")
    llm = LLM(
        model="Qwen/Qwen2.5-Coder-7B-Instruct",
        max_model_len=2048,
        structured_outputs_config={"backend": "guidance"},
    )
    print("✅ Model loaded\n")
    
    # Test WITHOUT grammar first
    print("Test 1: Without grammar")
    params_no_grammar = SamplingParams(
        temperature=0.0,
        max_tokens=32,
    )
    
    outputs = llm.generate(["def test():"], params_no_grammar)
    result_no_grammar = outputs[0].outputs[0].text
    print(f"Generated: {result_no_grammar[:100]}")
    print(f"Has markdown fence: {'```' in result_no_grammar}\n")
    
    # Test WITH grammar
    print("Test 2: With grammar (should only generate 'return N')")
    params_with_grammar = SamplingParams(
        temperature=0.0,
        max_tokens=32,
        structured_outputs=StructuredOutputsParams(grammar=lark_grammar),
    )
    
    try:
        outputs = llm.generate(["def test():"], params_with_grammar)
        result_with_grammar = outputs[0].outputs[0].text
        print(f"Generated: {result_with_grammar[:100]}")
        print(f"Matches grammar: {result_with_grammar.strip().startswith('return ')}")
        print(f"Has markdown fence: {'```' in result_with_grammar}")
        
        return {
            "success": True,
            "without_grammar": result_no_grammar[:200],
            "with_grammar": result_with_grammar[:200],
            "constraint_enforced": result_with_grammar.strip().startswith("return"),
        }
    except Exception as e:
        print(f"❌ Failed with grammar: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}

@app.local_entrypoint()
def main():
    result = test_v1_with_grammar.remote()
    print(f"\n{'='*80}")
    print("RESULT:")
    print(f"{'='*80}")
    for k, v in result.items():
        print(f"{k}: {v}")
