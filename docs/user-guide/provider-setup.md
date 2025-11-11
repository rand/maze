# Provider Setup Guide

Configure LLM providers for Maze code generation.

## Supported Providers

Maze supports multiple LLM providers:

| Provider | Status | Grammar Support | API Key Required |
|----------|--------|-----------------|------------------|
| **OpenAI** | ✅ Production | Via JSON Schema | Yes |
| **vLLM** | ✅ Production | Native | No (self-hosted) |
| **SGLang** | ✅ Production | Native | No (self-hosted) |
| **llama.cpp** | ✅ Production | Native | No (local) |

## OpenAI Setup

### 1. Get API Key

Sign up at https://platform.openai.com and create an API key.

### 2. Set Environment Variable

```bash
export OPENAI_API_KEY=sk-your-key-here
```

### 3. Configure Maze

```python
from maze.config import Config

config = Config()
config.generation.provider = "openai"
config.generation.model = "gpt-4"  # or "gpt-3.5-turbo"
config.generation.temperature = 0.7
config.generation.max_tokens = 2048
```

Or via CLI:

```bash
maze config set generation.provider openai
maze config set generation.model gpt-4
```

### 4. Test Connection

```bash
export OPENAI_API_KEY=sk-...
maze generate "Create a hello world function"
```

## vLLM Setup (Self-Hosted)

### 1. Install vLLM

```bash
pip install vllm
```

### 2. Start vLLM Server

```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3-8B \
    --port 8000
```

### 3. Configure Maze

```python
config = Config()
config.generation.provider = "vllm"
config.generation.model = "meta-llama/Llama-3-8B"
```

### 4. Generate

```bash
maze config set generation.provider vllm
maze generate "Create a function"
```

## SGLang Setup

Similar to vLLM but with SGLang server:

```bash
python -m sglang.launch_server \
    --model-path meta-llama/Llama-3-8B \
    --port 8000
```

## llama.cpp Setup (Local)

### 1. Install llama.cpp Python bindings

```bash
pip install llama-cpp-python
```

### 2. Download Model

```bash
# Download GGUF model
wget https://huggingface.co/.../model.gguf
```

### 3. Configure

```python
config = Config()
config.generation.provider = "llamacpp"
config.generation.model = "path/to/model.gguf"
```

## Provider Configuration Options

### Retry Configuration

```python
config.generation.retry_attempts = 3  # Default: 3
# Retry with exponential backoff: 1s, 2s, 4s
```

### Timeout Configuration

```python
config.generation.timeout_seconds = 30  # Default: 30
```

### Model Parameters

```python
config.generation.temperature = 0.7  # Creativity (0.0-2.0)
config.generation.max_tokens = 2048  # Max output length
```

## Error Handling

### Missing API Key

```bash
$ maze generate "test"
// OpenAI API key not found in OPENAI_API_KEY
// Set: export OPENAI_API_KEY=sk-...
```

### Transient Errors

Maze automatically retries on:
- Network timeouts
- Rate limits
- Server errors

No retry on:
- Authentication errors
- Invalid API keys
- Malformed requests

### Retry Behavior

```python
# Attempt 1: Immediate
# Attempt 2: Wait 1 second
# Attempt 3: Wait 2 seconds
# Attempt 4: Wait 4 seconds
# Give up after max_retries
```

## Provider Selection

Maze selects provider from configuration:

```python
# Priority order:
# 1. CLI argument: --provider openai
# 2. Project config: .maze/config.toml
# 3. Global config: ~/.config/maze/config.toml
# 4. Default: openai
```

## Performance Tuning

### For Speed

```python
config.generation.provider = "vllm"  # Faster than OpenAI
config.generation.temperature = 0.0  # More deterministic
config.generation.max_tokens = 512   # Shorter outputs
```

### For Quality

```python
config.generation.provider = "openai"
config.generation.model = "gpt-4"    # Better model
config.generation.temperature = 0.8  # More creative
config.constraints.type_enabled = True  # Stricter constraints
```

## Monitoring

### Check Provider Calls

```bash
maze stats --show-performance
```

Shows:
- Provider call latency (mean, p95, p99)
- Success rate
- Retry statistics

### Metrics Export

```python
prometheus_metrics = pipeline.metrics.export_prometheus()
# Includes: maze_latency_ms{operation="provider_call"}
```

## Troubleshooting

### Provider Timeout

```bash
# Increase timeout
maze config set generation.timeout_seconds 60
```

### Rate Limits

```bash
# Reduce temperature for more deterministic (cacheable) outputs
maze config set generation.temperature 0.5

# Or switch to self-hosted vLLM (no rate limits)
maze config set generation.provider vllm
```

### Authentication Errors

```bash
# Verify API key
echo $OPENAI_API_KEY

# Re-export if needed
export OPENAI_API_KEY=sk-...

# Test
maze generate "test"
```

## Next Steps

- [Getting Started](getting-started.md) - Quick start guide
- [Best Practices](best-practices.md) - Optimization tips
- [Examples](../../examples/) - Working examples
