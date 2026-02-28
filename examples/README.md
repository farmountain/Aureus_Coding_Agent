# AUREUS Examples

This directory contains example scripts demonstrating AUREUS usage.

## Quick Start Examples

### 1. Mock Provider (No API Key Required)

**File**: `example_mock_provider.py`

Demonstrates the complete GVUFD → SPK → UVUAS pipeline using the MockProvider (no API key needed).

```bash
python examples/example_mock_provider.py
```

**What it does**:
- Loads policy from `.aureus/policy.yaml`
- Generates specification from intent
- Calculates cost with budget enforcement
- Creates mock implementation
- Saves file to `workspace/`

**Use this to**:
- Verify AUREUS installation works
- Test the 3-tier intelligence flow
- Understand the basic API

---

### 2. OpenAI Provider (Requires API Key)

**File**: `example_openai_provider.py`

Demonstrates real code generation using OpenAI's GPT-4.

```bash
# Set your API key
$env:OPENAI_API_KEY="sk-your-key-here"

# Run example
python examples/example_openai_provider.py
```

**What it does**:
- Uses real GPT-4 to generate code
- Creates a calculator class with methods
- Shows actual LLM-powered implementation

**Use this to**:
- Test real code generation
- See LLM integration in action
- Validate your API key works

---

## Policy Examples

### Simple API Policy

**File**: `policy-simple-api.yaml`

Minimal policy for a simple REST API project.

**Use this for**:
- Small web services
- API microservices
- Simple CRUD applications

### Enterprise Policy

**File**: `policy-enterprise.yaml`

Comprehensive policy with strict governance.

**Use this for**:
- Large enterprise applications
- Security-critical systems
- Multi-team projects

---

## Running Examples

All examples can be run from the project root:

```bash
# Mock provider (no API key)
python examples/example_mock_provider.py

# OpenAI provider (requires key)
$env:OPENAI_API_KEY="your-key"
python examples/example_openai_provider.py
```

---

## Example Output

**Successful run**:
```
Success: True
Budget status: approved
Files created: ['D:\\...\\workspace\\generated_code.py']

✓ File created: D:\...\workspace\generated_code.py
Content:
def add(a, b):
    return a + b
```

**Budget exceeded**:
```
Success: False
Budget status: rejected
Error: Budget exceeded: rejected. Alternatives: 6
```

---

## Troubleshooting

### "No module named 'src'"

Run from project root:
```bash
cd D:\All_Projects\Aureus_Coding_Agent
python examples/example_mock_provider.py
```

### "Policy file not found"

Ensure `.aureus/policy.yaml` exists:
```bash
aureus init
```

### "OPENAI_API_KEY not set"

For OpenAI example:
```bash
$env:OPENAI_API_KEY="sk-your-actual-key"
```

---

## Next Steps

After running examples:

1. **Try the CLI**: `aureus code "your intent here"`
2. **Customize policy**: Edit `.aureus/policy.yaml`
3. **Read architecture**: See `architecture.md`
4. **Run tests**: `pytest tests/ -v`

---

**See also**:
- [README.md](../README.md) - Main documentation
- [architecture.md](../architecture.md) - System design
- [docs/cli-examples.md](../docs/cli-examples.md) - CLI usage
