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

**Current Status:** Phase 3++ Complete ✅  
**Total:** 9,223 LOC | 302 tests (100% pass) | Production Ready

## Key Features

- ✅ **Governance-First**: Policy-driven development with budgets and constraints
- ✅ **3-Tier Architecture**: GVUFD → SPK → UVUAS semantic compilation pipeline
- ✅ **Code Separation**: Formal boundaries between agent and user workspace
- ✅ **Immutable Principles**: 7 user-facing guarantees (backed by 18 technical safety constants)
- ✅ **Self-Play Capability**: Authorized self-improvement with governance
- ✅ **Memory System**: Learn from past sessions, extract patterns
- ✅ **Model Agnostic**: Support for Anthropic, OpenAI, Google, local LLMs
- ✅ **Production Ready**: Complete logging, monitoring, configuration management

---

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/aureus-coding-agent.git
cd aureus-coding-agent

# Install dependencies
pip install -e .

# Verify installation
pytest tests/ -v
```

### Basic Usage

1. **Initialize a project with governance policy:**

```bash
aureus init --project-name "My API" --max-loc 1000
```

This creates `.aureus/policy.yaml` with your project constraints.

2. **Execute a coding task:**

```bash
aureus build --spec specification.yaml --policy .aureus/policy.yaml
```

3. **View memory and learned patterns:**

```bash
# List all sessions
aureus memory list-sessions

# Show session details
aureus memory show-trajectory SESSION_ID

# View learned patterns
aureus memory show-patterns

# Export Architecture Decision Record
aureus memory export-adr SESSION_ID --output decision.md
```

### Configuration

Create `aureus-config.yaml`:

```yaml
environment: development

logging:
  log_level: INFO
  log_dir: ./logs

model:
  provider: anthropic  # or openai, google, mock
  api_key: ${AUREUS_MODEL_API_KEY}
  timeout: 30.0

governance:
  policy_path: .aureus/policy.yaml
  enforce_budgets: true

self_play:
  enabled: false
  require_tests_pass: true
```

Or use environment variables:

```bash
export AUREUS_MODEL_PROVIDER=anthropic
export AUREUS_MODEL_API_KEY=your-api-key
export AUREUS_LOG_LEVEL=DEBUG
```

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
