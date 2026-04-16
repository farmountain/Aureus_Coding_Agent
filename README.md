# AUREUS Coding Agent

**A semantic compiler for software intent**

Traditional AI coding agents generate code. AUREUS *compiles* intent — applying governance constraints, cost budgets, and verification passes the same way a compiler applies type checks and optimization.

```
Intent  ──→  [Parse]  ──→  [Plan]  ──→  [Generate]  ──→  Governed Software
```

[![License: BSL 1.1](https://img.shields.io/badge/License-BSL%201.1-yellow.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Status: Alpha](https://img.shields.io/badge/status-alpha-orange.svg)]()

---

## Why a compiler, not an agent?

| Concern | Traditional AI Agent | AUREUS |
|---|---|---|
| Governance | Weak / post-hoc | Policy-enforced at every stage |
| Code budgets | None | LOC / module / dependency limits |
| Rollback | Manual | Built-in |
| Model coupling | Tight | Pluggable (OpenAI, Anthropic, more) |
| Learning | None | Pattern extraction across sessions |
| Self-improvement | No | Authorized self-play |

AI agents optimize for local correctness — "does this code work right now?" AUREUS adds a second dimension: *does this code comply with the constraints I care about across my entire codebase?*

---

## How it works

AUREUS processes your intent through three stages:

**Stage 1 — Parse**  
Transforms natural language into bounded, typed specifications. Identifies what you asked for, what constraints apply, and what success looks like.

**Stage 2 — Plan**  
Cost-aware planning with alternatives. Applies your governance policy to select the lowest-cost implementation path that satisfies all constraints.

**Stage 3 — Generate**  
Governed code generation with built-in verification. Produces code, validates it against the Stage 1 spec, and surfaces rollback paths before writing anything.

---

## Quick start

```bash
git clone https://github.com/farmountain/Aureus_Coding_Agent.git
cd Aureus_Coding_Agent
python -m venv venv && source venv/bin/activate  # Windows: .\venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Set your provider:

```bash
# OpenAI
export AUREUS_MODEL_PROVIDER=openai
export AUREUS_MODEL_API_KEY=sk-...

# or Anthropic
export AUREUS_MODEL_PROVIDER=anthropic
export AUREUS_MODEL_API_KEY=sk-ant-...
```

Initialize and generate:

```bash
aureus init
aureus code "create a function that validates email addresses with tests"
```

---

## Configuration

Create `aureus-config.yaml` in your project root:

```yaml
environment: development

model:
  provider: openai        # openai | anthropic | mock
  api_key: ${AUREUS_MODEL_API_KEY}
  timeout: 30.0

governance:
  policy_path: .aureus/policy.yaml
  enforce_budgets: true
```

**Supported providers:**
| Provider | Models | Status |
|---|---|---|
| `openai` | GPT-4, GPT-3.5-turbo | ✅ Alpha |
| `anthropic` | Claude 3 (Opus, Sonnet, Haiku) | ✅ Alpha |
| `mock` | — | ✅ For testing |

---

## Current status

AUREUS is **alpha**. The architecture is production-grade; the rough edges are not.

**Working:**
- ✅ LLM integration (OpenAI + Anthropic)
- ✅ Code generation from natural language
- ✅ Governance policy framework (policy.yaml)
- ✅ 3-stage compilation pipeline (Parse → Plan → Generate)
- ✅ CLI (`aureus init`, `aureus code`, `aureus memory`)
- ✅ Memory: pattern extraction across sessions

**Rough edges (being fixed):**
- ⚠️ File placement sometimes lands in project root instead of correct directory
- ⚠️ LLM response parsing occasionally fragile
- ⚠️ Error messages in permission system need polish
- ⚠️ Real LLM integration not yet covered by test suite

Use it, break it, open issues. That's the point of alpha.

---

## Governance policy

AUREUS enforces coding constraints via a policy file. Example `.aureus/policy.yaml`:

```yaml
budgets:
  max_lines_per_file: 300
  max_dependencies: 10
  max_nesting_depth: 4

constraints:
  require_tests: true
  require_docstrings: public_api
  disallow_patterns:
    - "eval("
    - "exec("

rollback:
  enabled: true
  strategy: git_stash
```

The planning stage respects these constraints *before* generating code — not as a post-hoc lint pass.

---

## Architecture

```
aureus/
├── core/
│   ├── parse/          # Intent parsing and specification
│   ├── plan/           # Cost-aware planning
│   └── generate/       # Governed code generation
├── providers/          # LLM backends (OpenAI, Anthropic, Mock)
├── governance/         # Policy engine
├── memory/             # Session pattern extraction
├── security/           # Sandbox and boundary enforcement
└── cli/                # Command-line interface
```

Full design docs:
- [architecture.md](architecture.md) — system design and execution flow
- [solution.md](solution.md) — engineering specification
- [roadmap.md](roadmap.md) — development phases

---

## Roadmap

- [ ] **v0.2** — Stable file placement, robust response parsing
- [ ] **v0.3** — Real LLM integration test suite
- [ ] **v0.4** — Extended memory: cross-project pattern library
- [ ] **v1.0** — Production-ready governance enforcement

---

## License

**Business Source License 1.1**

Free for development, testing, and non-production use.  
Converts to Apache 2.0 on **February 27, 2029**.  
For commercial production use before 2029: farmountain@gmail.com

---

## Contributing

Read [architecture.md](architecture.md) first — AUREUS has strong opinions about code separation and governance that contributors should understand before sending a PR.

```bash
pytest tests/ -v          # run the test suite
aureus code "your intent" # try it
```

Issues and PRs welcome.
