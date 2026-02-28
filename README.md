# 🟡 AUREUS Coding Agent

**Not just an agent — a semantic compiler for software intent**

AUREUS is an AI coding agent that operates as a **semantic compiler**, transforming human intent into governed, optimized software systems.

Unlike traditional AI coding agents that optimize for local correctness, AUREUS operates as a **compiler with governance constraints**:

- **Semantic parsing (GVUFD)** — Intent → bounded specifications
- **Optimization passes (SPK)** — Cost-aware planning with alternatives
- **Code generation (UVUAS)** — Governed implementation with verification
- **Memory & Learning** — Pattern extraction from successful sessions
- **Deterministic constraints** — Type-safe governance enforced at compile-time
- **Guaranteed properties** — Budget compliance, termination, rollback safety

Just as traditional compilers transform code → machine instructions, AUREUS transforms intent → governed software.

**Current Status:** Phase 4 - Basic LLM Integration Working (Alpha)  
**State:** Core functionality operational but needs refinement  
**Providers:** OpenAI ✅ | Anthropic ✅ | Mock ✅  
**Known Issues:** File placement, error handling, response parsing need improvement

## Key Features

**Working (Alpha Quality):**
- ✅ **LLM Integration**: OpenAI and Anthropic providers functional (basic)
- ✅ **Code Generation**: Generates Python code from natural language (needs refinement)
- ✅ **Governance Framework**: Policy-driven architecture
- ✅ **3-Tier Architecture**: GVUFD → SPK → UVUAS pipeline
- ✅ **CLI**: Basic command-line interface

**Needs Work:**
- ⚠️ **File Organization**: Currently creates files in root (should use proper directories)
- ⚠️ **Error Handling**: Multiple bugs in permission system, parsing, etc.
- ⚠️ **Response Parsing**: LLM output parsing is fragile
- ⚠️ **Test Coverage**: Tests exist but don't cover real LLM integration
- ⚠️ **Memory System**: Framework exists but needs integration with real generation

**This is experimental alpha software, not production ready.**

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/aureus-coding-agent.git
cd aureus-coding-agent

# Create and activate virtual environment (recommended)
python -m venv venv
# On Windows:
.\venv\Scripts\Activate.ps1
# On Linux/Mac:
# source venv/bin/activate

# Install with dev dependencies (includes pytest)
pip install -e ".[dev]"

# Verify installation
pytest tests/ -v
```

### Basic Usage
**AUREUS now generates real code using OpenAI or Anthropic!**

1. **Initialize a project with governance policy:**

```bash
aureus init
```

2. **Generate code with AI (requires API key):**

```bash
# Set your API key
$env:AUREUS_MODEL_PROVIDER="openai"      # or "anthropic"
$env:AUREUS_MODEL_API_KEY="your-key-here"

# Generate code!
aureus code "create a function that adds two numbers"
```

**Real output example:**
```
🤖 Using OpenAI provider: gpt-4
✓ SUCCESS: Build completed
```

Generated file `generated_create_a_function_that_adds.py`:
```python
def add(a: int, b: int) -> int:
    """
    Add two numbers and return the result.
    
    Args:
        a: First number
        b: Second number
    
    Returns:
        Sum of a and b
    """
    return a + bvailable)
aureus memory list-sessions
```

3. **View memory and learned patterns:**

```bash
# List all sessions
aureus memory list-sessions
**Required:** Set your LLM provider and API key to enable code generation.

#### Environment Variables (Recommended)

```bash
# Windows PowerShell:
$env:AUREUS_MODEL_PROVIDER="openai"
$env:AUREUS_MODEL_API_KEY="sk-your-openai-key"

# Or use Anthropic:
$env:AUREUS_MODEL_PROVIDER="anthropic"
$env:AUREUS_MODEL_API_KEY="sk-ant-your-anthropic-key"

# Linux/Mac:
export AUREUS_MODEL_PROVIDER=openai
export AUREUS_MODEL_API_KEY=your-key
```

#### Configuration File

Create `aureus-config.yaml` in your project root:

```yaml
environment: development

model:
  provider: openai  # or anthropic, mock
  api_key: ${AUREUS_MODEL_API_KEY}
  timeout: 30.0

governance:
  policy_path: .aureus/policy.yaml
  enforce_budgets: true
```

**Supported Providers:**
- ✅ `openai` — GPT-4, GPT-3.5-turbo (requires `openai` package + API key)
- ✅ `anthropic` — Claude 3 (Opus, Sonnet, Haiku) (requires `anthropic` package + API key)
- ✅ `mock` — For testing (no API key needed, generates placeholder code
  policy_path: .aureus/policy.yaml
  enforce_budgets: true

self_play:
  enabled: false
  require_tests_pass: true
```

**Provider Roadmap:**
- ✅ `mock` — Currently implemented (for architecture testing)
- ⏳ `anthropic` — Planned for Phase 4 (Claude models)
- ⏳ `openai` — Planned for Phase 4 (GPT models)
- ⏳ `google` — Planned for Phase 4 (Gemini models)

---

## Documentation

### Core Documentation
- 📖 [Architecture Overview](architecture.md) — 3-tier system design, execution flow
- 📖 [Solution Specification](solution.md) — Engineering details, module interfaces
- 📖 [Code Separation Boundaries](docs/CODE_SEPARATION_BOUNDARIES.md) — Agent vs workspace separation
- 📖 [Design Decisions](docs/design-decisions.md) — Architectural choices and rationale

### Reports & Assessments
- 📊 [Phase 3+ Complete Report](PHASE_3_PLUS_COMPLETE_REPORT.md) — Production infrastructure implementation
- 📊 [Phase 3++ Complete Report](PHASE_3_PLUSPLUS_COMPLETE.md) — Placeholder removal and full E2E implementation
- 📊 [Project Summary](PROJECT_SUMMARY.md) — Complete metrics and achievements

### Guides
- 🚀 [Roadmap](roadmap.md) — Development phases and milestones
- 🎯 [CLI Examples](docs/cli-examples.md) — Command-line usage patterns
- 🔒 [Security & Sandbox](src/security/) — Boundary enforcement implementation

---

## Architecture Comparison

| Feature | Traditional AI Agent | AUREUS |
|---------|---------------------|--------|
| Governance | Weak/None | Policy-enforced |
| Code Separation | Unclear | Formal boundaries |
| Budgets | No | LOC/Module/Dependency |
| Learning | Limited | Pattern extraction |
| Self-Improvement | No | Authorized self-play |
| Model Dependency | Coupled | Pluggable |
| Rollback | Limited | Built-in |
| Monitoring | Basic | Production-grade |

---

## Contributing

We welcome contributions that align with AUREUS's governance-first philosophy.

**Before contributing:**
1. Read [architecture.md](architecture.md) to understand the 3-tier system
2. Review [Code Separation Boundaries](docs/CODE_SEPARATION_BOUNDARIES.md)
3. Ensure all tests pass: `pytest tests/ -v`

**Contribution guidelines:**
- ✅ Respect architectural budgets (see `aureus-self-policy.yaml`)
- ✅ Include tests for all new features
- ✅ Add docstrings to public APIs
- ✅ Update documentation for user-facing changes
- ✅ Follow existing code style and patterns
- ✅ Keep changes focused and atomic

**Pull Request Process:**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run full test suite: `pytest tests/ -v`
5. Update documentation as needed
6. Submit PR with clear description

---

## License

**Business Source License 1.1** (BSL 1.1)

- ✅ Free for development, testing, and non-production use
- ✅ Converts to Apache 2.0 on **February 27, 2029**
- ✅ See [LICENSE](LICENSE) for complete terms

For commercial production use before 2029, contact for licensing options.

---

## Community & Support

- 🐛 **Issues**: Report bugs or request features via GitHub Issues
- 💬 **Discussions**: Join discussions about architecture and features
- 📧 **Contact**: farmountain@gmail.com

---

**AUREUS** — A semantic compiler that transforms intent into governed software with formal constraints and continuous learning.
