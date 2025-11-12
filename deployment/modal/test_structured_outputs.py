"""Test if StructuredOutputsParams works in vLLM 0.11.0."""

import modal

app = modal.App("test-structured-outputs")

# Same image as main deployment
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "wget", "curl", "build-essential", "pkg-config", "libssl-dev")
    .run_commands(
        "curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y",
        "echo 'source $HOME/.cargo/env' >> $HOME/.bashrc",
    )
    .uv_pip_install(
        "vllm==0.11.0",
        "transformers==4.55.2",
        "llguidance>=1.3.0,<1.4.0",
    )
)

@app.function(gpu="a100-40gb", image=image, timeout=1800)
def test_api():
    """Test if the structured outputs API works."""
    print("Testing vLLM structured outputs API...")
    
    try:
        from vllm.sampling_params import StructuredOutputsParams
        print("✅ StructuredOutputsParams import successful")
    except ImportError as e:
        print(f"❌ Cannot import StructuredOutputsParams: {e}")
        return {"error": str(e)}
    
    # Test creating instance
    try:
        grammar = """
?start: simple
simple: "return" NUMBER
NUMBER: /[0-9]+/
"""
        so = StructuredOutputsParams(grammar=grammar)
        print(f"✅ Created StructuredOutputsParams: {so}")
        print(f"   Grammar set: {so.grammar is not None}")
    except Exception as e:
        print(f"❌ Cannot create StructuredOutputsParams: {e}")
        return {"error": str(e)}
    
    # Test with LLM
    try:
        from vllm import LLM, SamplingParams
        
        print("Loading 7B model for testing...")
        llm = LLM(
            model="Qwen/Qwen2.5-Coder-7B-Instruct",
            max_model_len=2048,
            structured_outputs_config={"backend": "guidance"},
        )
        print("✅ Model loaded")
        
        # Test generation with grammar
        sampling_params = SamplingParams(
            max_tokens=32,
            temperature=0.0,
            structured_outputs=StructuredOutputsParams(grammar=grammar),
        )
        
        outputs = llm.generate(["def test():"], sampling_params)
        result = outputs[0].outputs[0].text
        
        print(f"✅ Generated: {result}")
        print(f"   Valid (should only have 'return N'): {'return' in result and '```' not in result}")
        
        return {
            "success": True,
            "generated": result,
            "has_markdown": "```" in result,
            "has_return": "return" in result,
        }
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.local_entrypoint()
def main():
    result = test_api.remote()
    print(f"\n{'='*80}")
    print("RESULT:")
    print(f"{'='*80}")
    for k, v in result.items():
        print(f"{k}: {v}")
    print(f"{'='*80}")
