"""
Semantic Search Tool - AST-based Code Search

Provides intelligent code search:
- Function/class name search
- Symbol references
- Import analysis
- Structure-based queries
"""

import ast
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass
import re


@dataclass
class SearchMatch:
    """A single search match"""
    file_path: str
    line_number: int
    match_type: str  # 'function', 'class', 'import', 'reference'
    name: str
    context: str  # Surrounding code


@dataclass
class SearchResult:
    """Search operation result"""
    success: bool
    matches: List[SearchMatch]
    error: Optional[str] = None


class SemanticSearchTool:
    """
    Semantic code search tool using AST analysis
    
    Provides intelligent code search beyond simple text matching:
    - Find function/class definitions
    - Find symbol references
    - Analyze imports
    - Structure-based queries
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize semantic search tool
        
        Args:
            project_root: Root directory of project
        """
        self.project_root = Path(project_root)
    
    def find_function(self, name: str, recursive: bool = True) -> SearchResult:
        """
        Find function definitions
        
        Args:
            name: Function name (supports wildcards)
            recursive: Search recursively in subdirectories
            
        Returns:
            SearchResult with matching functions
        """
        pattern = self._compile_pattern(name)
        matches = []
        
        # Search Python files
        py_files = self._find_python_files(recursive)
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if pattern.match(node.name):
                            matches.append(SearchMatch(
                                file_path=str(py_file.relative_to(self.project_root)),
                                line_number=node.lineno,
                                match_type='function',
                                name=node.name,
                                context=self._get_context(content, node.lineno)
                            ))
                            
            except (SyntaxError, UnicodeDecodeError):
                # Skip files with syntax errors or encoding issues
                continue
        
        return SearchResult(success=True, matches=matches)
    
    def find_class(self, name: str, recursive: bool = True) -> SearchResult:
        """
        Find class definitions
        
        Args:
            name: Class name (supports wildcards)
            recursive: Search recursively in subdirectories
            
        Returns:
            SearchResult with matching classes
        """
        pattern = self._compile_pattern(name)
        matches = []
        
        py_files = self._find_python_files(recursive)
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if pattern.match(node.name):
                            matches.append(SearchMatch(
                                file_path=str(py_file.relative_to(self.project_root)),
                                line_number=node.lineno,
                                match_type='class',
                                name=node.name,
                                context=self._get_context(content, node.lineno)
                            ))
                            
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        return SearchResult(success=True, matches=matches)
    
    def find_imports(
        self,
        module: str,
        recursive: bool = True
    ) -> SearchResult:
        """
        Find import statements
        
        Args:
            module: Module name to search for
            recursive: Search recursively
            
        Returns:
            SearchResult with files importing the module
        """
        matches = []
        py_files = self._find_python_files(recursive)
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if module in alias.name:
                                matches.append(SearchMatch(
                                    file_path=str(py_file.relative_to(self.project_root)),
                                    line_number=node.lineno,
                                    match_type='import',
                                    name=alias.name,
                                    context=self._get_context(content, node.lineno)
                                ))
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and module in node.module:
                            matches.append(SearchMatch(
                                file_path=str(py_file.relative_to(self.project_root)),
                                line_number=node.lineno,
                                match_type='import',
                                name=node.module,
                                context=self._get_context(content, node.lineno)
                            ))
                            
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        return SearchResult(success=True, matches=matches)
    
    def find_references(
        self,
        symbol: str,
        recursive: bool = True
    ) -> SearchResult:
        """
        Find references to a symbol
        
        Args:
            symbol: Symbol name to find
            recursive: Search recursively
            
        Returns:
            SearchResult with symbol references
        """
        matches = []
        py_files = self._find_python_files(recursive)
        
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content, filename=str(py_file))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id == symbol:
                        matches.append(SearchMatch(
                            file_path=str(py_file.relative_to(self.project_root)),
                            line_number=node.lineno,
                            match_type='reference',
                            name=symbol,
                            context=self._get_context(content, node.lineno)
                        ))
                        
            except (SyntaxError, UnicodeDecodeError):
                continue
        
        return SearchResult(success=True, matches=matches)
    
    def _find_python_files(self, recursive: bool) -> List[Path]:
        """Find all Python files in project"""
        if recursive:
            return list(self.project_root.rglob("*.py"))
        else:
            return list(self.project_root.glob("*.py"))
    
    def _compile_pattern(self, name: str) -> re.Pattern:
        """Convert wildcard pattern to regex"""
        # Convert * to .* for regex
        regex_pattern = name.replace('*', '.*')
        # Anchor pattern
        regex_pattern = f'^{regex_pattern}$'
        return re.compile(regex_pattern)
    
    def _get_context(self, content: str, line_number: int, context_lines: int = 2) -> str:
        """Get surrounding lines of context"""
        lines = content.splitlines()
        start = max(0, line_number - context_lines - 1)
        end = min(len(lines), line_number + context_lines)
        
        context = lines[start:end]
        return '\n'.join(context)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tool_name": "semantic_search",
            "project_root": str(self.project_root)
        }
