# Installation Guide

This guide will help you set up the LLM Swarm system for automated code generation.

## Prerequisites

- Python 3.8 or higher
- Git
- At least 8GB RAM (16GB recommended for local models)
- GPU with CUDA support (optional, for faster local model inference)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/llm-swarm.git
cd llm-swarm
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Configuration

The system will create a default configuration file on first run, but you can create it manually:

```bash
python main.py config --create-default
```

### 5. Configure API Keys

For the orchestrator to work, you need to set up API keys for either OpenAI or Anthropic:

#### Option A: OpenAI (Recommended)

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Set the environment variable:

```bash
# Windows
set OPENAI_API_KEY=your_api_key_here

# macOS/Linux
export OPENAI_API_KEY=your_api_key_here
```

#### Option B: Anthropic Claude

1. Get an API key from [Anthropic](https://console.anthropic.com/)
2. Set the environment variable:

```bash
# Windows
set ANTHROPIC_API_KEY=your_api_key_here

# macOS/Linux
export ANTHROPIC_API_KEY=your_api_key_here
```

3. Update the configuration to use Claude:

Edit `models/config.yaml` and change the orchestrator model:

```yaml
orchestrator:
  model: "orchestrator_claude"  # Change from "orchestrator"
```

### 6. Test Installation

Run a simple test to verify everything is working:

```bash
python main.py config --validate
```

If successful, try a dry run:

```bash
python example.py
```

## Local Models Setup (Optional)

For cost-effective operation, you can use local models for the SME agents. This requires additional setup:

### 1. Install Additional Dependencies

```bash
pip install torch transformers accelerate bitsandbytes
```

### 2. Download Models

The system will automatically download models on first use, but you can pre-download them:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Example: Download CodeLlama
model_id = "codellama/CodeLlama-7b-Instruct-hf"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
```

### 3. Update Configuration

Edit `models/config.yaml` to use better local models:

```yaml
models:
  local_coder:
    name: "local_coder"
    type: "local"
    model_id: "codellama/CodeLlama-7b-Instruct-hf"  # Better coding model
    max_tokens: 2048
    temperature: 0.7
    device: "auto"
    quantization: "4bit"  # Reduces memory usage
```

## Configuration Options

### Model Types

- **API Models**: Use external APIs (OpenAI, Anthropic) - more powerful but costs money
- **Local Models**: Run on your machine - free but requires more resources

### Agent Configuration

You can enable/disable specific agents in `models/config.yaml`:

```yaml
agents:
  frontend:
    enabled: true    # Set to false to disable
  backend:
    enabled: true
  database:
    enabled: true
  testing:
    enabled: false   # Disable if not needed
  documentation:
    enabled: true
```

### Performance Tuning

For better performance with local models:

1. **Use GPU**: Ensure CUDA is available
2. **Quantization**: Enable 4-bit or 8-bit quantization
3. **Memory Management**: Set appropriate `max_memory` limits

```yaml
models:
  local_coder:
    device: "cuda"           # Use GPU
    quantization: "4bit"     # Reduce memory usage
    max_memory: "6GB"        # Limit memory usage
```

## Troubleshooting

### Common Issues

#### 1. "No module named 'transformers'"

```bash
pip install transformers torch
```

#### 2. "CUDA out of memory"

- Enable quantization in config
- Reduce `max_tokens`
- Use CPU instead of GPU

#### 3. "API key not found"

Make sure environment variables are set correctly:

```bash
echo $OPENAI_API_KEY  # Should show your key
```

#### 4. "Model download failed"

- Check internet connection
- Ensure you have enough disk space
- Try a smaller model

### Getting Help

1. Check the logs in `logs/llm-swarm.log`
2. Run with debug logging: `python main.py --log-level DEBUG`
3. Validate configuration: `python main.py config --validate`
4. Open an issue on GitHub

## Next Steps

Once installed, check out:

- [Usage Guide](USAGE.md) - How to use the system
- [Configuration Reference](CONFIG.md) - Detailed configuration options
- [Examples](examples/) - Sample projects and specifications

## Development Setup

If you want to contribute to the project:

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run linting
flake8 .
black .
```