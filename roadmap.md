# AUREUS Coding Agent — Roadmap

This document outlines the phased development plan for AUREUS, from MVP to enterprise-grade features.

---

## Development Philosophy

AUREUS development follows its own governance principles:

* **Incremental releases** — Each phase delivers working software
* **Budget-conscious** — No feature creep beyond architectural budget
* **Test-driven** — Governance tests validate each phase
* **Community-driven** — Open-source contributions welcome after MVP

---

## Phase 1 — Core MVP (Target: 8-10 weeks)

**Goal**: Minimum viable governance runtime

### Deliverables

#### 1.1 CLI Runtime
- Basic command parser (`aureus code`, `aureus init`)
- Configuration loader (`.aureus/policy.yaml`)
- Session initialization/teardown
- Formatted output (colored, structured)

#### 1.2 Policy System
- Policy schema (YAML)
- Budget definitions (LOC, modules, dependencies)
- Forbidden pattern definitions (simple rules)
- Permission matrix (tool allow/deny)

#### 1.3 Tier 1: GVUFD (Simplified)
- Intent → Specification converter
- Success criteria generation
- Budget allocation
- Basic acceptance test templates

#### 1.4 Tier 2: Pricing Kernel
- Linear pricing model
- Cost calculation (ΔLOC, deps, abstractions)
- Budget enforcement (warning/rejection thresholds)
- Cost logging

#### 1.5 Tool Bus (Basic)
- File read/write tools
- Permission gate (allow/deny)
- Basic rollback (Git-based)
- Tool result validation

#### 1.6 Single Agent Loop
- Simple orchestrator (no full swarm yet)
- Plan → Execute → Verify cycle
- Integration with one model provider (Anthropic or OpenAI)

#### 1.7 Memory (Minimal)
- Policy persistence
- Session trajectory logs (JSON)
- Cost ledger (simple append-only)

### Success Metrics
- ✓ Can initialize new project with policy
- ✓ Can execute simple coding task (e.g., "add function")
- ✓ Budget enforcement blocks over-budget actions
- ✓ Rollback works for file changes
- ✓ < 4k LOC total

**Timeline**: Weeks 1-10  
**Dependencies**: 7 core libraries  
**LOC Target**: 3500-4000

---

## Phase 2 — Memory Stabilization (Target: 4 weeks)

**Goal**: Persistent learnings and architectural decisions

### Deliverables

#### 2.1 Architecture Decision Records (ADR)
- ADR schema (Markdown)
- Automatic ADR generation for architectural changes
- ADR browsing/search (`aureus adr list`)

#### 2.2 Trajectory Summarization
- Session trajectory compression
- Pattern extraction from trajectories
- Multi-session context loading

#### 2.3 Cost Model Refinement
- Non-linear pricing experiments
- Risk weighting calibration
- Cost prediction accuracy metrics

#### 2.4 Forbidden Pattern Library
- Pre-defined pattern rules
- Custom pattern DSL (simple)
- Pattern detection accuracy tests

### Success Metrics
- ✓ ADRs generated for all architectural decisions
- ✓ Multi-session context persists correctly
- ✓ Cost predictions within 20% accuracy
- ✓ Pattern detection ≥ 85% accuracy

**Timeline**: Weeks 11-14  
**Dependencies**: +1 (pattern matching library)  
**LOC Target**: 4500-5000

---

## Phase 3 — Agent Swarm Expansion (Target: 6 weeks)

**Goal**: Full Tier 3 agent swarm with specialization

### Deliverables

#### 3.1 Planner Agent (Enhanced)
- Multi-step task decomposition
- Dependency analysis
- Parallel action identification
- Cost optimization (greedy/heuristic)

#### 3.2 Builder Agent
- Precise file editing
- Code generation from templates
- Incremental builds
- Error recovery

#### 3.3 Tester Agent
- Acceptance test generation
- Test execution and validation
- Regression detection
- Coverage tracking

#### 3.4 Critic Agent
- Forbidden pattern detection
- Architectural compliance checking
- Code quality metrics
- Security vulnerability scanning (basic)

#### 3.5 Reflexion Agent
- Abstraction simplification
- Duplicate code consolidation
- Complexity reduction algorithms
- Inline trivial functions

#### 3.6 Agent Coordination
- Shared context protocol
- Turn-taking mechanism
- Conflict resolution
- Performance profiling

### Success Metrics
- ✓ All 5 agents operational
- ✓ Reflexion reduces complexity by ≥ 15%
- ✓ Critic catches ≥ 90% of forbidden patterns
- ✓ Planner optimizes costs effectively

**Timeline**: Weeks 15-20  
**Dependencies**: +1 (code analysis library)  
**LOC Target**: 6000-7000

---

## Phase 4 — Model Provider Ecosystem (Target: 4 weeks)

**Goal**: True model-agnostic brain

### Deliverables

#### 4.1 Provider Interface Standardization
- Unified LLM interface
- Prompt template system
- Token counting abstraction
- Streaming support

#### 4.2 Provider Adapters
- Anthropic (Claude)
- OpenAI (GPT-4, o1)
- Google (Gemini)
- Local LLMs (Ollama, LM Studio)

#### 4.3 Provider Selection
- Auto-detection based on config
- Fallback mechanism
- Cost-based provider selection
- Performance benchmarking

#### 4.4 Prompt Engineering
- Role-specific prompts (Planner, Builder, etc.)
- Few-shot examples
- Chain-of-thought templates
- Structured output parsing

### Success Metrics
- ✓ 4+ model providers working
- ✓ Seamless provider switching
- ✓ Consistent results across providers
- ✓ Adapter code ≤ 200 LOC each

**Timeline**: Weeks 21-24  
**Dependencies**: +3 (provider SDKs)  
**LOC Target**: 7000-7500

---

## Phase 5 — Advanced Tool Suite (Target: 6 weeks)

**Goal**: Rich tool ecosystem with safety

### Deliverables

#### 5.1 Shell Execution
- Command whitelisting/blacklisting
- Sandbox implementation (chroot/containers)
- Timeout enforcement
- Output streaming

#### 5.2 Git Integration (Advanced)
- Commit creation
- Branch management
- Diff analysis
- Merge conflict detection

#### 5.3 Code Search
- Semantic search (embeddings-based)
- Grep-style search (regex)
- Symbol navigation (go-to-definition)
- Cross-file refactoring

#### 5.4 Web Fetching (Optional)
- HTTP client with rate limiting
- Content extraction
- Link validation
- Security scanning

#### 5.5 Rollback Enhancement
- Transactional file operations
- Multi-step rollback
- Selective undo
- Rollback verification

### Success Metrics
- ✓ 10+ tools available
- ✓ All tools pass security tests
- ✓ Rollback success rate ≥ 95%
- ✓ Tool execution latency < 5s (p95)

**Timeline**: Weeks 25-30  
**Dependencies**: +2 (sandbox, code parser)  
**LOC Target**: 8000-9000 (approaching limit)

---

## Phase 6 — Extensions & Skills (Target: 4 weeks)

**Goal**: Reusable workflows and customization

### Deliverables

#### 6.1 Skills System
- Skill definition format (YAML/JSON)
- Skill executor
- Pre-packaged skills:
  - Refactor module
  - Add tests
  - Migrate API
  - Update documentation

#### 6.2 Hooks System
- Lifecycle hooks (pre/post actions)
- Custom validation hooks
- Notification hooks
- Integration hooks (Slack, email)

#### 6.3 MCP Integration
- Model Context Protocol connector
- MCP tool discovery
- MCP-to-AUREUS translation
- Permission gating for MCP tools

#### 6.4 Plugin Framework (Constrained)
- Compile-time plugins only
- No dynamic loading in core
- Plugin API documentation
- Example plugins

### Success Metrics
- ✓ 5+ skills available
- ✓ Hooks work reliably
- ✓ MCP tools integrate seamlessly
- ✓ Plugin system respects governance

**Timeline**: Weeks 31-34  
**Dependencies**: +1 (MCP SDK)  
**LOC Target**: 9000-10000 (at budget limit)

---

## Phase 7 — Enterprise Hardening (Target: 6 weeks)

**Goal**: Production-ready for teams

### Deliverables

#### 7.1 Role-Based Access Control (RBAC)
- User roles (admin, developer, auditor)
- Permission inheritance
- Policy override capabilities
- Audit trail per user

#### 7.2 Centralized Policy Management
- Policy templates library
- Policy inheritance (team → project)
- Policy versioning
- Policy compliance dashboard

#### 7.3 Audit & Compliance
- Comprehensive audit logs
- Compliance reports (SOC2, GDPR-ready)
- Cost analytics dashboard
- Architectural drift metrics

#### 7.4 Policy DSL
- Human-readable policy language
- Policy compiler to YAML
- Policy validation
- IDE support (syntax highlighting)

#### 7.5 CI/CD Integration
- GitHub Actions plugin
- GitLab CI integration
- Pre-commit hooks
- Automated compliance checks

#### 7.6 Sandboxed Execution (Advanced)
- Container-based isolation
- Network policy enforcement
- Resource limits (CPU, memory, disk)
- Multi-tenancy support

### Success Metrics
- ✓ RBAC works correctly
- ✓ Audit logs pass compliance review
- ✓ Policy DSL is usable
- ✓ CI/CD integrations functional

**Timeline**: Weeks 35-40  
**Dependencies**: +2 (container runtime, analytics)  
**LOC Target**: 11000-12000 (expanded scope)

---

## Phase 8 — Ecosystem Growth (Ongoing)

**Goal**: Community and adoption

### Deliverables

#### 8.1 Documentation
- Comprehensive user guide
- API reference
- Tutorial videos
- Architecture deep-dives

#### 8.2 Community
- Discord/Slack community
- GitHub Discussions
- Contribution guidelines
- Code of conduct

#### 8.3 Integrations
- VS Code extension
- JetBrains plugin
- Vim/Neovim integration
- Web UI (optional)

#### 8.4 Benchmarks & Case Studies
- Performance benchmarks
- Real-world case studies
- Comparison studies
- Academic papers

#### 8.5 Commercial Support (Optional)
- Enterprise licensing
- Professional support
- Custom policy consulting
- Training programs

---

## Architectural Budget Tracking

| Phase | LOC Target | Modules | Files | Dependencies |
|-------|-----------|---------|-------|--------------|
| 1 MVP | 4,000 | 6 | 20 | 7 |
| 2 Memory | 5,000 | 6 | 22 | 8 |
| 3 Agents | 7,000 | 6 | 25 | 9 |
| 4 Providers | 7,500 | 7 | 28 | 12 |
| 5 Tools | 9,000 | 7 | 32 | 14 |
| 6 Extensions | 10,000 | 8 | 35 | 15 |
| 7 Enterprise | 12,000 | 9 | 40 | 17 |

**Note**: Phase 7 expands budget due to enterprise requirements. Core runtime remains ≤ 8k LOC.

---

## Risk Management

### Technical Risks

| Risk | Mitigation |
|------|-----------|
| LOC budget overrun | Mandatory reflexion after Phase 3 |
| Dependency explosion | Strict dependency approval process |
| Performance degradation | Continuous benchmarking |
| Model provider lock-in | Provider abstraction from Phase 1 |
| Security vulnerabilities | Security audit after each phase |

### Project Risks

| Risk | Mitigation |
|------|-----------|
| Feature creep | Governance applies to AUREUS itself |
| Community fragmentation | Clear contribution guidelines |
| Insufficient adoption | Focus on real pain points |
| Competitive pressure | Open-source moat + governance uniqueness |

---

## Success Criteria

### Phase 1 Success (MVP)
- [ ] 10+ users successfully run AUREUS
- [ ] Budget enforcement prevents 1+ real-world architectural drift
- [ ] Documentation complete
- [ ] < 4k LOC

### Phase 7 Success (Enterprise)
- [ ] 3+ companies adopt AUREUS
- [ ] 100+ GitHub stars
- [ ] CI/CD integrations used in production
- [ ] Zero critical security issues

### Long-Term Success (1 year)
- [ ] 1000+ GitHub stars
- [ ] 50+ contributors
- [ ] 10+ enterprise customers
- [ ] Cited in academic papers

---

## Release Schedule

### Alpha Releases (Phases 1-3)
- `v0.1.0-alpha` — MVP (Phase 1)
- `v0.2.0-alpha` — Memory (Phase 2)
- `v0.3.0-alpha` — Agents (Phase 3)

### Beta Releases (Phases 4-6)
- `v0.4.0-beta` — Providers (Phase 4)
- `v0.5.0-beta` — Tools (Phase 5)
- `v0.6.0-beta` — Extensions (Phase 6)

### Production Releases (Phase 7+)
- `v1.0.0` — Enterprise (Phase 7)
- `v1.x.x` — Iterative improvements
- `v2.0.0` — Major architecture evolution (if needed)

---

## Community Participation

### How to Contribute (After MVP)

1. **Code Contributions**
   - Follow AUREUS governance (meta!)
   - Pass all governance tests
   - Documentation required
   - Sign CLA

2. **Skills & Plugins**
   - Create reusable skills
   - Share in community repository
   - Must respect core governance

3. **Model Providers**
   - Implement provider adapter
   - ≤ 200 LOC per adapter
   - Pass compatibility tests

4. **Documentation**
   - Tutorials, guides, videos
   - Translations
   - Case studies

5. **Testing**
   - Report bugs
   - Adversarial testing
   - Performance benchmarks

---

## Post-1.0 Vision

### AUREUS Ecosystem
- **AUREUS Coding Agent** (this project)
- **AUREUS Policy Studio** (visual policy editor)
- **AUREUS Cloud** (hosted governance service)
- **AUREUS Academy** (training & certification)

### Research Directions
- Machine learning-based cost prediction
- Adaptive governance (self-tuning budgets)
- Multi-project architectural coherence
- Formal verification of governance rules

---

This roadmap is a **living document** and will evolve based on:
- Community feedback
- Real-world usage patterns
- Technological advancements
- Competitive landscape

**AUREUS development is itself governed by AUREUS principles.**
