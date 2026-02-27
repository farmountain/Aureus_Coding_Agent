# Repository Indexer - Architectural Decision Record

**Date**: February 27, 2026  
**Status**: Decided  
**Decision Maker**: Architecture Team  
**Context**: Phase 1 MVP scope definition

---

## Problem Statement

The architecture specifies a "Repository Indexer" component for building symbol tables and dependency graphs to improve context quality. This component could range from 100 LOC (simple) to 1000+ LOC (sophisticated), significantly impacting Phase 1 scope.

**Three options considered**:

### Option A: External Library (tree-sitter + tree-sitter-graph)
**Pros**:
- Industrial-strength parsing (supports 50+ languages)
- Accurate symbol extraction (functions, classes, variables)
- Dependency graph built-in
- Battle-tested by GitHub CodeNav

**Cons**:
- Heavy dependency (~5MB + language grammars)
- Complex integration (C bindings via Python)
- Steeper learning curve
- Overkill for MVP

**LOC Estimate**: ~150 LOC (wrapper only)  
**Dependencies**: `tree-sitter`, `tree-sitter-python`, `tree-sitter-graph`  
**Implementation Time**: 2-3 days

---

### Option B: Simple Ripgrep + Regex
**Pros**:
- Lightweight (ripgrep already fast)
- Minimal code (pure Python)
- Easy to understand and maintain
- Sufficient for MVP (Python-only initially)

**Cons**:
- Limited accuracy (regex misses edge cases)
- No semantic understanding
- Language-specific (need separate regex per language)
- Fragile (breaks on unusual syntax)

**LOC Estimate**: ~200 LOC (regex patterns + parsing)  
**Dependencies**: `ripgrep` (system binary)  
**Implementation Time**: 1-2 days

---

### Option C: Defer to Phase 3 ✅ **SELECTED**
**Pros**:
- Keeps Phase 1 minimal (4k LOC target)
- Can gather real usage data first
- Can choose right solution after MVP validation
- Simple file traversal sufficient for MVP

**Cons**:
- Phase 1 context quality lower (no symbol awareness)
- Users must manually specify hot files
- Less intelligent working set management

**LOC Estimate**: ~50 LOC (basic file tree traversal)  
**Dependencies**: None (stdlib only)  
**Implementation Time**: Half day

---

## Decision: **Option C - Defer to Phase 3**

### Rationale

1. **MVP Scope Management**: Phase 1 target is 3.5-4k LOC. A sophisticated indexer risks scope creep.

2. **Incremental Value**: Basic file traversal provides 80% of the value with 20% of the complexity.

3. **Learning Opportunity**: Real usage data will inform whether we need Option A or B in Phase 3.

4. **Graceful Degradation**: Users can manually specify important files via policy:
   ```yaml
   context:
     hot_files:
       - src/core.py
       - src/models.py
       - src/api.py
   ```

5. **Precedent**: Even sophisticated tools like Cursor started with simple file traversal.

---

## Phase 1 Implementation (Minimal)

```python
# src/context/file_tree.py (~50 LOC)

class FileTree:
    """Simple file tree traversal for Phase 1."""
    
    def __init__(self, root: Path, ignore_patterns: list[str]):
        self.root = root
        self.ignore_patterns = ignore_patterns  # From .gitignore
    
    def get_all_files(self, extensions: list[str]) -> list[Path]:
        """Get all files matching extensions."""
        files = []
        for ext in extensions:
            files.extend(self.root.rglob(f"*{ext}"))
        return self._filter_ignored(files)
    
    def get_file_size(self, path: Path) -> int:
        """Get file size in LOC."""
        return len(path.read_text().splitlines())
    
    def get_imports(self, path: Path) -> list[str]:
        """Simple regex-based import detection (Python only)."""
        content = path.read_text()
        imports = []
        
        # Match: import foo, from foo import bar
        for line in content.splitlines():
            if line.strip().startswith(('import ', 'from ')):
                imports.append(line.strip())
        
        return imports
    
    def _filter_ignored(self, files: list[Path]) -> list[Path]:
        """Filter files matching .gitignore patterns."""
        # Simple implementation - can improve later
        filtered = []
        for file in files:
            if not any(pattern in str(file) for pattern in self.ignore_patterns):
                filtered.append(file)
        return filtered
```

**Features Supported**:
- ✅ File discovery (by extension)
- ✅ LOC counting
- ✅ Simple import detection (Python)
- ✅ .gitignore respect

**Features Deferred to Phase 3**:
- ⏳ Symbol table (functions, classes)
- ⏳ Dependency graph
- ⏳ Call graph
- ⏳ Multi-language support
- ⏳ Semantic understanding

---

## Phase 3 Enhancement (Sophisticated)

When we revisit in Phase 3, we'll have data to decide:

**If users need better context quality**, implement **Option A** (tree-sitter):
```python
# Phase 3: Add tree-sitter integration
class SymbolIndexer:
    """Tree-sitter-based symbol extraction."""
    
    def build_symbol_table(self, root: Path) -> SymbolTable:
        """Extract all functions, classes, variables."""
        pass
    
    def build_dependency_graph(self, root: Path) -> DependencyGraph:
        """Build import dependency graph."""
        pass
```

**If simple is sufficient**, enhance **Option B** (better regex):
```python
# Phase 3: Improve regex patterns
class SimpleIndexer:
    """Enhanced regex-based indexing."""
    
    PYTHON_FUNCTION = re.compile(r'^def\s+(\w+)\s*\(')
    PYTHON_CLASS = re.compile(r'^class\s+(\w+).*:')
    # ... more patterns
```

---

## Acceptance Criteria for Phase 3 Enhancement

Only implement sophisticated indexer if:

1. **User feedback indicates context is insufficient**
   - Users complain about missing relevant files
   - Working set doesn't include obvious dependencies
   - Manual hot file specification is tedious

2. **Performance data shows need**
   - > 30% of sessions need manual context adjustments
   - Context budget frequently exceeded due to including too many files

3. **Multi-language support needed**
   - Users request TypeScript/JavaScript support
   - Users request Go/Rust support

**Until then, keep it simple.**

---

## Impact on Other Components

### Context Manager
```python
# Phase 1: Simple file-based context
class ContextManager:
    def __init__(self, project_path: Path):
        self.file_tree = FileTree(project_path, ignore_patterns=['.git', 'node_modules'])
    
    def get_working_set(self, hot_files: list[Path]) -> WorkingSet:
        """Build working set from explicitly specified hot files."""
        
        working_set = set(hot_files)
        
        # Add imports (1 level deep)
        for file in hot_files:
            imports = self.file_tree.get_imports(file)
            # Resolve imports to file paths (simple heuristic)
            for imp in imports:
                resolved = self._resolve_import(imp)
                if resolved:
                    working_set.add(resolved)
        
        return WorkingSet(files=working_set)
```

### Memory Subsystem
```python
# Phase 1: Store hot files in policy
# .aureus/policy.yaml
context:
  hot_files:  # User-specified important files
    - src/core.py
    - src/models.py
  
  # Phase 3: Add auto-detected hot files
  auto_hot_files:  # System-learned from usage
    - src/helpers.py  # Imported by core.py
    - src/config.py   # Used frequently
```

---

## Risks & Mitigations

### Risk 1: Context Quality Too Low
**Mitigation**: 
- Provide clear error messages when context is insufficient
- Add `aureus context add <file>` command to manually expand context
- Track context sufficiency metrics in telemetry

### Risk 2: Users Frustrated by Manual File Selection
**Mitigation**:
- Learn frequently accessed files automatically
- Suggest files to add based on imports
- Provide `aureus context auto` to include import closure

### Risk 3: Phase 3 Indexer Too Complex
**Mitigation**:
- Set hard LOC limit (400 LOC max for indexer)
- Prefer external library over custom implementation
- Only add features with proven user need

---

## Testing Strategy

### Phase 1 Tests
```python
def test_file_tree_discovers_python_files():
    """File tree finds all .py files."""
    tree = FileTree(Path("./test_project"), ignore_patterns=[])
    files = tree.get_all_files([".py"])
    assert len(files) == 5

def test_file_tree_respects_gitignore():
    """File tree ignores .gitignore patterns."""
    tree = FileTree(Path("./test_project"), ignore_patterns=["__pycache__"])
    files = tree.get_all_files([".py"])
    assert not any("__pycache__" in str(f) for f in files)

def test_simple_import_detection():
    """Simple regex import detection works."""
    tree = FileTree(Path("./test_project"), ignore_patterns=[])
    imports = tree.get_imports(Path("./test_project/main.py"))
    assert "import os" in imports
    assert "from typing import List" in imports
```

### Phase 3 Tests (when enhanced)
```python
def test_symbol_table_extraction():
    """Symbol table extracts functions and classes."""
    indexer = SymbolIndexer(Path("./test_project"))
    symbols = indexer.build_symbol_table()
    assert "main" in symbols.functions
    assert "Config" in symbols.classes

def test_dependency_graph_construction():
    """Dependency graph captures imports correctly."""
    indexer = SymbolIndexer(Path("./test_project"))
    graph = indexer.build_dependency_graph()
    assert graph.has_edge("main.py", "config.py")
```

---

## Documentation Updates Required

### Update solution.md
```markdown
## Module 2: Context Manager

**Phase 1 Implementation**:
- Simple file tree traversal
- Basic import detection (Python only)
- Manual hot file specification

**Phase 3 Enhancement** (if needed):
- Tree-sitter symbol extraction
- Multi-language support
- Auto-detected working sets
```

### Update architecture.md
```markdown
## 1.2 Session & Context Manager

**Phase 1**: File-based context with manual hot file selection
**Phase 3**: Symbol-aware context with dependency graph

Repository Indexer: Deferred to Phase 3 based on MVP feedback.
```

---

## Conclusion

**Decision**: Defer sophisticated repository indexer to Phase 3.

**Phase 1 Implementation**: Simple file tree traversal (~50 LOC)

**Rationale**: Keep MVP minimal, gather usage data, choose right solution later.

**Success Metrics**: 
- Phase 1 ships under 4k LOC target ✅
- Users can work effectively with manual hot file selection ✅
- Phase 3 enhancement decision informed by real data ✅

**Approval**: Architectural decision approved for Phase 1 implementation.
