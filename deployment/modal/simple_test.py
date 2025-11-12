"""Minimal Modal test to verify vLLM + llguidance works.

This is a simplified version to test the core functionality.
"""

import modal

app = modal.App("maze-test-simple")

# Simple image with vLLM
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.12")
    .apt_install("git", "wget")
    .uv_pip_install(
        "vllm==0.11.0",
        "transformers==4.55.2",
        "llguidance>=0.7.11,<0.8.0",
    )
)

@app.function(
    gpu="a100-80gb",
    image=image,
    timeout=1800,  # 30 minutes
    secrets=[modal.Secret.from_name("huggingface")],
)
def test_vllm_simple():
    """Test vLLM loads and generates."""
    from vllm import LLM, SamplingParams
    
    print("Loading model...")
    llm = LLM(
        model="Qwen/Qwen2.5-Coder-7B-Instruct",  # Smaller model for testing
        trust_remote_code=True,
        dtype="bfloat16",
        max_model_len=2048,
    )
    
    print("✅ Model loaded")
    
    # Test simple generation
    prompts = ["def add(a, b):"]
    sampling_params = SamplingParams(temperature=0.3, max_tokens=64)
    
    outputs = llm.generate(prompts, sampling_params)
    
    result = outputs[0].outputs[0].text
    print(f"Generated: {result[:200]}")
    
    return {"success": True, "code": result}


@app.local_entrypoint()
def main():
    result = test_vllm_simple.remote()
    print(f"\n✅ Test complete: {result}")
