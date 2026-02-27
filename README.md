# 🟡 AUREUS Coding Agent

**Not just an agent — a semantic compiler for software intent**

AUREUS is an AI coding agent that operates as a **semantic compiler**, transforming human intent into governed, optimized software systems.

Unlike traditional AI coding agents that optimize for local correctness, AUREUS operates as a **compiler with governance constraints**:

* **Semantic parsing** (GVUFD) — Intent → bounded specifications
* **Optimization passes** (SPK) — Cost-aware planning with alternatives
* **Code generation** (UVUAS) — Governed implementation with verification
* **Deterministic constraints** — Type-safe governance enforced at compile-time
* **Guaranteed properties** — Budget compliance, termination, rollback safety

Just as traditional compilers transform code → machine instructions, AUREUS transforms intent → governed software.

**Target**: 4k LOC core | **Hard Limit**: 6k LOC | **Architecture**: Compiler-grade with formal guarantees

---

## Core Philosophy

Most AI coding agents optimize for **local correctness** ("Does this function work?").

AUREUS optimizes for **global utility** ("Does this change improve the overall system?"):

1. **Global architectural coherence** — Every change maintains system-wide design integrity
2. **Bounded complexity growth** — Hard limits prevent uncontrolled expansion
3. **Cost-aware execution** — Every action has a measurable complexity cost
4. **Policy-enforced tool usage** — No tool executes without explicit permission
5. **Continuous simplification** — Reflexive agents remove unnecessary complexity

**The 3-tier system unifies local and global**: GVUFD translates global goals → local constraints, SPK prices local changes → global cost, UVUAS executes locally correct code → verified against global utility.

**Result**: Changes are both locally correct (pass tests, valid syntax) AND globally beneficial (improve architecture, stay within budgets).

---

## Architecture Overview

AUREUS follows a **3-Tier Compiler Architecture**:

### Tier 1 — Global Value Utility Function Designer (GVUFD)
**Semantic Parser & Type Checker**

Converts natural language intent into bounded specifications (semantic AST):

* Success definition
* Forbidden patterns (governance type system)
* LOC / module / dependency budgets (constraint enforcement)
* Acceptance tests
* Risk boundaries

Like a parser builds AST from code, GVUFD builds specifications from intent.

---

### Tier 2 — Self-Pricing Kernel (SPK)
**Optimizer & Cost Analyzer**

Performs multi-pass optimization on specifications:

* Cost calculation (ΔLOC, dependencies, abstractions)
* Budget enforcement (compile-time constraint checking)
* Alternative generation (optimization passes)
* Risk assessment (static analysis)

Like a compiler optimizer reduces instructions, SPK minimizes complexity cost.

---

### Tier 3 — Unified Value Utility Agent Swarm (UVUAS)
**Code Generator & Verifier**

Generates governed implementations with verification:

* **Planner** — Decomposes to intermediate representation (IR)
* **Builder** — Code generation from IR
* **Tester** — Runtime verification
* **Critic** — Static analysis for violations
* **Reflexion** — Peephole optimization (simplification)

Like a compiler backend, UVUAS emits correct, optimized output.

**Result**: Deterministic, governed software generation with formal guarantees.

---

## Compilation Pipeline

The semantic compilation flow:

1. **Context Loading** — Load project state, governance policy, memory (environment setup)
2. **Semantic Parsing** — GVUFD converts intent → specification (AST generation)
3. **Type Checking** — Validate against governance constraints (compile-time checks)
4. **Optimization** — SPK minimizes cost, generates alternatives (optimization passes)
5. **IR Generation** — Plan creation with priced actions (intermediate representation)
6. **Code Generation** — UVUAS implements from IR (backend codegen)
7. **Verification** — Test against acceptance criteria (runtime validation)
8. **Peephole Optimization** — Reflexion simplifies output (post-processing)
9. **Memory Persistence** — Log for learning and rollback (debugging symbols)

**Like a compiler**: Deterministic transformation with guaranteed properties.

---

## Model-Agnostic Brain

AUREUS supports:

* Anthropic models (Claude)
* OpenAI models (GPT-4, o1, etc.)
* Google models (Gemini)
* Local LLMs (Ollama, LM Studio, etc.)
* Future providers

**The harness owns correctness.**  
**The model is interchangeable.**

---

## Tool Bus

All tools are permission-gated and priced:

* File read/write
* Code search (semantic & grep)
* Shell execution
* Git operations
* Web fetch (optional)
* MCP connectors (optional)

Each tool call passes through:

1. **Policy Gate** — Permission check
2. **Pricing Gate** — Complexity budget check
3. **Permission Layer** — Sandbox enforcement
4. **Snapshot/rollback** — Safe execution with revert capability

---

## Memory System (Minimal & Structured)

AUREUS memory is intentionally lightweight:

1. **Project Policy Memory** (persistent YAML/JSON)
2. **Architecture Decisions** (ADR format)
3. **Session Trajectories** (structured logs)
4. **Cost/Evidence Logs** (audit trail)

No heavy vector DB required for MVP.

---

## Why AUREUS Exists

AI coding tools tend to:

* Inflate abstractions unnecessarily
* Add unnecessary architectural layers
* Introduce premature frameworks
* Re-invent solved problems
* Drift architecturally over sessions

**AUREUS prevents that by enforcing:**

* Hard architectural budgets
* Forbidden pattern lists
* Simplification-first reflexion
* Cost-aware governance

---

## Target Design Goals

* **4k LOC-class architecture** (core runtime)
* **≤ 6 modules** (high cohesion)
* **≤ 25 files** (core, excluding tests/examples)
* **≤ 15 dependencies** (minimal external reliance)
* **Deterministic governance core** (no randomness in policy)
* **Pluggable model providers** (swap LLMs seamlessly)

---

## Roadmap Highlights

See [roadmap.md](roadmap.md) for full details.

* **Phase 1**: CLI runtime, policy spec, pricing kernel, tool permission framework
* **Phase 2**: Memory stabilization, ADR writer, cost model refinement
* **Phase 3**: Skills system, hooks, MCP connector layer
* **Phase 4**: Enterprise hardening (RBAC, audit logs, policy DSL)

---

## Comparison

| Feature                  | Typical AI Coding Agent | AUREUS    |
| ------------------------ | ----------------------- | --------- |
| Model-coupled            | Yes                     | No        |
| Complexity governance    | Weak                    | Strong    |
| Architectural budgets    | No                      | Yes       |
| Reflexive simplification | Rare                    | Mandatory |
| Tool permission gating   | Partial                 | Explicit  |
| Cost-based planning      | No                      | Yes       |
| Forbidden patterns       | No                      | Enforced  |
| Rollback capability      | Limited                 | Built-in  |

---

## Documentation

* [Architecture Overview](architecture.md) — System layers, execution flow, governance invariants
* [Solution Specification](solution.md) — Engineering details, module interfaces, schemas
* [Roadmap](roadmap.md) — Development phases and milestones

---

## Contributing

AUREUS is an open-source project aligned with the broader **AUREUS ecosystem** of governance-first development tools.

Contributions should:
* Respect architectural budgets
* Pass governance checks
* Include tests and documentation
* Follow simplification-first principles

---

## License

Apache 2.0

---

## Project Status

**Current Phase**: Architecture & Specification  
**Target Implementation Language**: Python or TypeScript (TBD based on community feedback)

---

## Positioning

This project sits at the intersection of:

* Claude Code-style terminal agency
* Spec-driven development
* Complexity-aware architecture
* Reflexive simplification
* Safe tool orchestration

**AUREUS is not "another coding agent."**  
**It is a governed coding runtime.**
