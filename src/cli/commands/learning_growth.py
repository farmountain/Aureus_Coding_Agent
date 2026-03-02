"""
Phase 5 — Learning & Growth Commands

Commands for ADR management, skills library, and continuous learning.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

from src.memory.adr import ADRGenerator, ArchitecturalDecision
from src.extensions.skills import SkillExtension, Skill
from src.memory.trajectory import TrajectoryStore
from src.cli.base_command import BaseCommand


class ADRCommand(BaseCommand):
    """Manage Architecture Decision Records."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.adr_dir = self.project_root / "docs" / "adrs"
        self.generator = ADRGenerator(self.adr_dir)
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict:
        """Execute ADR command."""
        if not args:
            return self._format_error(ValueError("Missing arguments"), "ADR command")
        
        self._verbose_print(f"ADR action: {args.adr_action}")
        
        if args.adr_action == "list":
            return self._handle_execution(
                self._list_adrs, args.status,
                context="List ADRs"
            )
        elif args.adr_action == "show":
            return self._handle_execution(
                self._show_adr, args.adr_id,
                context="Show ADR"
            )
        elif args.adr_action == "create":
            return self._handle_execution(
                self._create_adr, args,
                context="Create ADR"
            )
        elif args.adr_action == "search":
            return self._handle_execution(
                self._search_adrs, args.query,
                context="Search ADRs"
            )
        else:
            return self._format_error(
                ValueError(f"Unknown action: {args.adr_action}"),
                "ADR command"
            )
    
    def _list_adrs(self, status_filter: Optional[str]) -> Dict:
        """List all ADRs."""
        print("[*] Listing Architecture Decision Records...\n")
        
        adr_files = sorted(self.adr_dir.glob("*.md"))
        
        if not adr_files:
            print("[!] No ADRs found")
            return {"status": "success", "count": 0, "adrs": []}
        
        adrs = []
        for adr_file in adr_files:
            # Extract ADR number and title from filename
            # Format: NNNN-title-slug.md
            name_parts = adr_file.stem.split('-', 1)
            if len(name_parts) == 2:
                adr_num = name_parts[0]
                title = name_parts[1].replace('-', ' ').title()
                
                # Read status from file if needed
                with open(adr_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if "Status: superseded" in content.lower():
                        status = "superseded"
                    elif "Status: deprecated" in content.lower():
                        status = "deprecated"
                    else:
                        status = "accepted"
                
                if status_filter and status != status_filter:
                    continue
                
                adrs.append({
                    "number": adr_num,
                    "title": title,
                    "status": status,
                    "file": str(adr_file.relative_to(self.project_root))
                })
                
                print(f"ADR-{adr_num}: {title} [{status.upper()}]")
        
        print(f"\n[+] Found {len(adrs)} ADR(s)")
        return {"status": "success", "count": len(adrs), "adrs": adrs}
    
    def _show_adr(self, adr_id: str) -> Dict:
        """Show specific ADR."""
        adr_files = list(self.adr_dir.glob(f"{adr_id}-*.md"))
        
        if not adr_files:
            print(f"[-] ADR-{adr_id} not found")
            return {"status": "error", "message": f"ADR-{adr_id} not found"}
        
        adr_file = adr_files[0]
        
        with open(adr_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(content)
        
        return {"status": "success", "adr_id": adr_id, "file": str(adr_file)}
    
    def _create_adr(self, args: argparse.Namespace) -> Dict:
        """Create new ADR."""
        print(f"[*] Creating ADR: {args.title}...\n")
        
        decision = ArchitecturalDecision(
            title=args.title,
            context=args.context,
            decision=args.decision,
            consequences=args.consequences.split(';') if args.consequences else [],
            alternatives=args.alternatives.split(';') if args.alternatives else [],
            status=args.status or "accepted"
        )
        
        adr_path = self.generator.generate(decision)
        
        print(f"[+] Created: {adr_path.relative_to(self.project_root)}")
        
        return {
            "status": "success",
            "file": str(adr_path.relative_to(self.project_root))
        }
    
    def _search_adrs(self, query: str) -> Dict:
        """Search ADRs."""
        print(f"[*] Searching for: '{query}'...\n")
        
        adr_files = list(self.adr_dir.glob("*.md"))
        results = []
        
        for adr_file in adr_files:
            with open(adr_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if query.lower() in content.lower():
                # Extract title
                title_line = content.split('\n')[0]
                if '#' in title_line:
                    title = title_line.split('#')[-1].strip()
                else:
                    title = adr_file.stem
                
                results.append({
                    "file": str(adr_file.relative_to(self.project_root)),
                    "title": title
                })
                
                print(f"  {adr_file.stem}: {title}")
        
        print(f"\n[+] Found {len(results)} matching ADR(s)")
        
        return {"status": "success", "count": len(results), "results": results}


class SkillsCommand(BaseCommand):
    """Manage skill library."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.skills_dir = self.project_root / "memory" / "skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.skills_file = self.skills_dir / "skills.json"
        self._load_skills()
    
    def _load_skills(self):
        """Load skills from storage."""
        if self.skills_file.exists():
            with open(self.skills_file, 'r', encoding='utf-8') as f:
                self.skills = json.load(f)
        else:
            self.skills = {}
    
    def _save_skills(self):
        """Save skills to storage."""
        with open(self.skills_file, 'w', encoding='utf-8') as f:
            json.dump(self.skills, f, indent=2)
    
    def execute(self, args: Optional[argparse.Namespace] = None) -> Dict:
        """Execute skills command."""
        if not args:
            return self._format_error(ValueError("Missing arguments"), "Skills command")
        
        self._verbose_print(f"Skills action: {args.skill_action}")
        
        if args.skill_action == "list":
            return self._handle_execution(
                self._list_skills, args.category,
                context="List skills"
            )
        elif args.skill_action == "show":
            return self._handle_execution(
                self._show_skill, args.skill_name,
                context="Show skill"
            )
        elif args.skill_action == "add":
            return self._handle_execution(
                self._add_skill, args,
                context="Add skill"
            )
        elif args.skill_action == "remove":
            return self._handle_execution(
                self._remove_skill, args.skill_name,
                context="Remove skill"
            )
        else:
            return self._format_error(
                ValueError(f"Unknown action: {args.skill_action}"),
                "Skills command"
            )
    
    def _list_skills(self, category: Optional[str]) -> Dict:
        """List all skills."""
        print("[*] Available Skills:\n")
        
        if not self.skills:
            print("[!] No skills found. Learn skills by running successful builds.")
            return {"status": "success", "count": 0, "skills": []}
        
        filtered_skills = self.skills
        if category:
            filtered_skills = {k: v for k, v in self.skills.items() 
                             if v.get("category") == category}
        
        for name, skill in filtered_skills.items():
            category_str = f"[{skill.get('category', 'general')}]"
            usage_count = skill.get('usage_count', 0)
            success_rate = skill.get('success_rate', 0.0) * 100
            
            print(f"  {name} {category_str}")
            print(f"    {skill.get('description', 'No description')}")
            print(f"    Used: {usage_count} times | Success: {success_rate:.1f}%")
            print()
        
        print(f"[+] Total: {len(filtered_skills)} skill(s)")
        
        return {
            "status": "success",
            "count": len(filtered_skills),
            "skills": list(filtered_skills.keys())
        }
    
    def _show_skill(self, skill_name: str) -> Dict:
        """Show skill details."""
        if skill_name not in self.skills:
            print(f"[-] Skill '{skill_name}' not found")
            return {"status": "error", "message": f"Skill '{skill_name}' not found"}
        
        skill = self.skills[skill_name]
        
        print(f"[*] Skill: {skill_name}\n")
        print(f"Description: {skill.get('description', 'N/A')}")
        print(f"Category: {skill.get('category', 'general')}")
        print(f"Usage Count: {skill.get('usage_count', 0)}")
        print(f"Success Rate: {skill.get('success_rate', 0.0) * 100:.1f}%")
        
        if 'pattern' in skill:
            print(f"\nPattern:\n{json.dumps(skill['pattern'], indent=2)}")
        
        if 'examples' in skill:
            print(f"\nExamples:")
            for ex in skill['examples']:
                print(f"  - {ex}")
        
        return {"status": "success", "skill": skill}
    
    def _add_skill(self, args: argparse.Namespace) -> Dict:
        """Add new skill."""
        skill_name = args.skill_name
        
        if skill_name in self.skills:
            print(f"[!] Skill '{skill_name}' already exists. Use --force to overwrite.")
            if not args.force:
                return {"status": "error", "message": "Skill already exists"}
        
        skill_data = {
            "description": args.description,
            "category": args.category or "general",
            "usage_count": 0,
            "success_rate": 0.0,
            "pattern": json.loads(args.pattern) if args.pattern else {},
            "created": args.created or None
        }
        
        self.skills[skill_name] = skill_data
        self._save_skills()
        
        print(f"[+] Added skill: {skill_name}")
        
        return {"status": "success", "skill_name": skill_name}
    
    def _remove_skill(self, skill_name: str) -> Dict:
        """Remove skill."""
        if skill_name not in self.skills:
            print(f"[-] Skill '{skill_name}' not found")
            return {"status": "error", "message": "Skill not found"}
        
        del self.skills[skill_name]
        self._save_skills()
        
        print(f"[+] Removed skill: {skill_name}")
        
        return {"status": "success", "skill_name": skill_name}


class LearnCommand(BaseCommand):
    """Analyze trajectories and extract patterns."""
    
    def __init__(self, project_root: Optional[Path] = None, verbose: bool = False):
        super().__init__(project_root=project_root, verbose=verbose, dry_run=False)
        self.memory_dir = self.project_root / "memory"
        self.trajectory_store = TrajectoryStore(str(self.memory_dir))
    
    def execute(self, args: argparse.Namespace) -> Dict:
        """Execute learn command."""
        try:
            if args.learn_action == "analyze":
                return self._analyze_trajectories(args.last)
            elif args.learn_action == "extract":
                return self._extract_patterns(args.session_id)
            elif args.learn_action == "stats":
                return self._show_stats()
            else:
                return {"status": "error", "message": f"Unknown action: {args.learn_action}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _analyze_trajectories(self, last_n: int) -> Dict:
        """Analyze recent trajectories."""
        print(f"[*] Analyzing last {last_n} trajectories...\n")
        
        # List trajectory files directly
        trajectory_dir = self.memory_dir / "trajectories"
        if not trajectory_dir.exists():
            print("[!] No trajectories found")
            return {"status": "success", "analyzed": 0}
        
        trajectory_files = sorted(trajectory_dir.glob("*.json"), 
                                 key=lambda x: x.stat().st_mtime,
                                 reverse=True)[:last_n]
        
        if not trajectory_files:
            print("[!] No trajectories found")
            return {"status": "success", "analyzed": 0}
        
        trajectories = []
        for traj_file in trajectory_files:
            with open(traj_file, 'r', encoding='utf-8') as f:
                trajectories.append(json.load(f))
        
        total = len(trajectories)
        successful = sum(1 for t in trajectories if t.get("outcome") == "success")
        failed = total - successful
        
        print(f"Total Trajectories: {total}")
        print(f"Successful: {successful} ({successful/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        
        # Analyze patterns
        intents = {}
        for traj in trajectories:
            intent = traj.get("intent", "unknown")
            if intent not in intents:
                intents[intent] = {"total": 0, "success": 0}
            intents[intent]["total"] += 1
            if traj.get("outcome") == "success":
                intents[intent]["success"] += 1
        
        print("\n[*] Success by Intent:")
        for intent, stats in sorted(intents.items(), key=lambda x: x[1]["success"], reverse=True)[:10]:
            success_rate = stats["success"] / stats["total"] * 100
            print(f"  {intent[:50]}: {stats['success']}/{stats['total']} ({success_rate:.1f}%)")
        
        return {
            "status": "success",
            "analyzed": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0
        }
    
    def _extract_patterns(self, session_id: str) -> Dict:
        """Extract patterns from specific session."""
        print(f"[*] Extracting patterns from session {session_id}...\n")
        
        # Load trajectory file directly
        traj_file = self.memory_dir / "trajectories" / f"{session_id}.json"
        
        if not traj_file.exists():
            print(f"[-] Session {session_id} not found")
            return {"status": "error", "message": "Session not found"}
        
        with open(traj_file, 'r', encoding='utf-8') as f:
            trajectory = json.load(f)
        
        # Extract patterns
        patterns = self._identify_patterns(trajectory)
        
        if not patterns:
            print("[!] No patterns identified")
            return {"status": "success", "patterns": []}
        
        print(f"[+] Identified {len(patterns)} pattern(s):\n")
        for i, pattern in enumerate(patterns, 1):
            print(f"{i}. {pattern['type']}: {pattern['description']}")
            if 'confidence' in pattern:
                print(f"   Confidence: {pattern['confidence'] * 100:.1f}%")
        
        return {"status": "success", "patterns": patterns}
    
    def _show_stats(self) -> Dict:
        """Show learning statistics."""
        print("[*] Learning Statistics\n")
        
        trajectory_dir = self.memory_dir / "trajectories"
        if not trajectory_dir.exists():
            print("[!] No learning data available")
            return {"status": "success", "stats": {}}
        
        trajectory_files = list(trajectory_dir.glob("*.json"))
        total = len(trajectory_files)
        
        if total == 0:
            print("[!] No learning data available")
            return {"status": "success", "stats": {}}
        
        # Load and analyze all trajectories
        successful = 0
        for traj_file in trajectory_files:
            try:
                with open(traj_file, 'r', encoding='utf-8') as f:
                    traj = json.load(f)
                    if traj.get("outcome") == "success":
                        successful += 1
            except:
                continue
        
        print(f"Total Sessions: {total}")
        print(f"Success Rate: {successful/total*100:.1f}%")
        print(f"Storage Location: {self.memory_dir}")
        
        # Skills learned
        skills_dir = self.project_root / "memory" / "skills"
        skills_file = skills_dir / "skills.json"
        
        if skills_file.exists():
            with open(skills_file, 'r', encoding='utf-8') as f:
                skills = json.load(f)
            print(f"Skills Learned: {len(skills)}")
        else:
            print("Skills Learned: 0")
        
        # ADRs created
        adr_dir = self.project_root / "docs" / "adrs"
        if adr_dir.exists():
            adr_count = len(list(adr_dir.glob("*.md")))
            print(f"ADRs Created: {adr_count}")
        else:
            print("ADRs Created: 0")
        
        return {
            "status": "success",
            "stats": {
                "total_sessions": total,
                "success_rate": successful / total if total > 0 else 0
            }
        }
    
    def _identify_patterns(self, trajectory: Dict) -> List[Dict]:
        """Identify patterns in trajectory."""
        patterns = []
        
        # Pattern 1: Repeated successful actions
        if trajectory.get("outcome") == "success":
            patterns.append({
                "type": "success_pattern",
                "description": f"Successful completion: {trajectory.get('intent', 'unknown')[:50]}",
                "confidence": 0.9
            })
        
        # Pattern 2: File operations
        if "file_operations" in trajectory:
            file_ops = trajectory["file_operations"]
            if len(file_ops) > 3:
                patterns.append({
                    "type": "multi_file_change",
                    "description": f"Multiple file operations ({len(file_ops)} files)",
                    "confidence": 0.8
                })
        
        # Pattern 3: Error recovery
        if "error_recovery" in trajectory and trajectory["error_recovery"]:
            patterns.append({
                "type": "error_recovery",
                "description": "Successful error recovery",
                "confidence": 0.85
            })
        
        return patterns


# CLI Parsers

def add_adr_parser(subparsers):
    """Add ADR command parser."""
    parser = subparsers.add_parser(
        "adr",
        help="Manage Architecture Decision Records"
    )
    
    subparsers_adr = parser.add_subparsers(dest="adr_action", required=True)
    
    # List
    list_parser = subparsers_adr.add_parser("list", help="List all ADRs")
    list_parser.add_argument("--status", choices=["accepted", "superseded", "deprecated"],
                            help="Filter by status")
    
    # Show
    show_parser = subparsers_adr.add_parser("show", help="Show specific ADR")
    show_parser.add_argument("adr_id", help="ADR number (e.g., 0001)")
    
    # Create
    create_parser = subparsers_adr.add_parser("create", help="Create new ADR")
    create_parser.add_argument("title", help="ADR title")
    create_parser.add_argument("--context", required=True, help="Problem context")
    create_parser.add_argument("--decision", required=True, help="Decision made")
    create_parser.add_argument("--consequences", help="Consequences (semicolon-separated)")
    create_parser.add_argument("--alternatives", help="Alternatives considered (semicolon-separated)")
    create_parser.add_argument("--status", choices=["accepted", "proposed"],
                              default="accepted", help="ADR status")
    
    # Search
    search_parser = subparsers_adr.add_parser("search", help="Search ADRs")
    search_parser.add_argument("query", help="Search query")


def add_skills_parser(subparsers):
    """Add skills command parser."""
    parser = subparsers.add_parser(
        "skills",
        help="Manage skill library"
    )
    
    subparsers_skills = parser.add_subparsers(dest="skill_action", required=True)
    
    # List
    list_parser = subparsers_skills.add_parser("list", help="List all skills")
    list_parser.add_argument("--category", help="Filter by category")
    
    # Show
    show_parser = subparsers_skills.add_parser("show", help="Show skill details")
    show_parser.add_argument("skill_name", help="Skill name")
    
    # Add
    add_parser = subparsers_skills.add_parser("add", help="Add new skill")
    add_parser.add_argument("skill_name", help="Skill name")
    add_parser.add_argument("--description", required=True, help="Skill description")
    add_parser.add_argument("--category", help="Skill category")
    add_parser.add_argument("--pattern", help="Pattern JSON")
    add_parser.add_argument("--force", action="store_true", help="Overwrite if exists")
    add_parser.add_argument("--created", help="Creation date")
    
    # Remove
    remove_parser = subparsers_skills.add_parser("remove", help="Remove skill")
    remove_parser.add_argument("skill_name", help="Skill name")


def add_learn_parser(subparsers):
    """Add learn command parser."""
    parser = subparsers.add_parser(
        "learn",
        help="Analyze trajectories and extract patterns"
    )
    
    subparsers_learn = parser.add_subparsers(dest="learn_action", required=True)
    
    # Analyze
    analyze_parser = subparsers_learn.add_parser("analyze", help="Analyze trajectories")
    analyze_parser.add_argument("--last", type=int, default=10,
                               help="Number of recent trajectories to analyze")
    
    # Extract
    extract_parser = subparsers_learn.add_parser("extract", help="Extract patterns")
    extract_parser.add_argument("session_id", help="Session ID to analyze")
    
    # Stats
    subparsers_learn.add_parser("stats", help="Show learning statistics")


def handle_adr_command(args, project_root: Path) -> int:
    """Handle ADR command execution."""
    command = ADRCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] == "success" else 1


def handle_skills_command(args, project_root: Path) -> int:
    """Handle skills command execution."""
    command = SkillsCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] == "success" else 1


def handle_learn_command(args, project_root: Path) -> int:
    """Handle learn command execution."""
    command = LearnCommand(project_root)
    result = command.execute(args)
    return 0 if result["status"] == "success" else 1
