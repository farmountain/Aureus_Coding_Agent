"""
Collaboration CLI Commands

Commands for multi-agent collaboration sessions.
"""

import argparse
import sys
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.coordination.coordinator import AgentCoordinator
from src.coordination.agent_protocol import (
    AgentRole, TaskRequest, Proposal, VoteType, TaskStatus
)
from src.agents.collaborative import PlannerAgent, DesignerAgent, ReviewerAgent, create_agent


# Global coordinator instance (singleton pattern)
_coordinator: Optional[AgentCoordinator] = None


def get_coordinator() -> AgentCoordinator:
    """Get or create the global coordinator instance."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AgentCoordinator(max_concurrent_agents=5)
        
        # Register some default agents
        planner = PlannerAgent()
        designer = DesignerAgent()
        reviewer = ReviewerAgent()
        
        _coordinator.register_agent(planner, AgentRole.PLANNER)
        _coordinator.register_agent(designer, AgentRole.DESIGNER)
        _coordinator.register_agent(reviewer, AgentRole.REVIEWER)
    
    return _coordinator


class CollaborateCommand:
    """Base class for collaboration commands."""
    
    @staticmethod
    def format_agent_role(role: AgentRole) -> str:
        """Format agent role for display."""
        role_icons = {
            AgentRole.COORDINATOR: "🎯",
            AgentRole.PLANNER: "📋",
            AgentRole.DESIGNER: "🎨",
            AgentRole.BUILDER: "🔨",
            AgentRole.REVIEWER: "🔍",
            AgentRole.TESTER: "🧪",
            AgentRole.DEBUGGER: "🐛"
        }
        icon = role_icons.get(role, "🤖")
        return f"{icon} {role.value.title()}"
    
    @staticmethod
    def format_status(status: TaskStatus) -> str:
        """Format task status for display."""
        status_icons = {
            TaskStatus.PENDING: "⏳",
            TaskStatus.ASSIGNED: "📌",
            TaskStatus.IN_PROGRESS: "🔄",
            TaskStatus.REVIEW: "👀",
            TaskStatus.COMPLETED: "✅",
            TaskStatus.FAILED: "❌",
            TaskStatus.BLOCKED: "🚫"
        }
        icon = status_icons.get(status, "❓")
        return f"{icon} {status.value.upper()}"


class StartSessionCommand(CollaborateCommand):
    """Start a new collaboration session."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute start-session command.
        
        Args:
            args: Parsed command arguments
        
        Returns:
            Exit code (0 = success)
        """
        coordinator = get_coordinator()
        
        print("[*] Starting collaboration session...")
        
        # Parse goals
        goals = args.goals if hasattr(args, 'goals') and args.goals else ["Complete development task"]
        if isinstance(goals, str):
            goals = [g.strip() for g in goals.split(',')]
        
        # Create session
        coordinator_id = str(uuid.uuid4())
        session = coordinator.create_session(coordinator_id, goals)
        
        # Add participating agents
        roles_to_add = [AgentRole.PLANNER, AgentRole.DESIGNER, AgentRole.REVIEWER]
        for role in roles_to_add:
            agent_id = coordinator.get_agent_by_role(role)
            if agent_id:
                coordinator.add_agent_to_session(session.session_id, agent_id)
        
        print(f"[+] Session created: {session.session_id}")
        print(f"\n📋 Goals:")
        for i, goal in enumerate(goals, 1):
            print(f"  {i}. {goal}")
        
        print(f"\n👥 Participating agents:")
        for agent_id, role in session.participating_agents.items():
            print(f"  - {self.format_agent_role(role)}")
        
        print(f"\n💡 Use 'aureus collaborate assign-task {session.session_id} <description>' to delegate tasks")
        
        return 0


class AssignTaskCommand(CollaborateCommand):
    """Assign a task to an agent in a session."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute assign-task command.
        
        Args:
            args: Parsed command arguments
        
        Returns:
            Exit code (0 = success)
        """
        coordinator = get_coordinator()
        
        session_id = args.session_id
        description = args.description
        role = args.role if hasattr(args, 'role') and args.role else None
        
        print(f"[*] Assigning task in session {session_id[:8]}...")
        
        # Get session
        session = coordinator.get_session(session_id)
        if not session:
            print(f"[!] Session not found: {session_id}")
            return 1
        
        # Parse role
        target_role = None
        if role:
            try:
                target_role = AgentRole[role.upper()]
            except KeyError:
                print(f"[!] Invalid role: {role}")
                print(f"    Available roles: {', '.join([r.value for r in AgentRole])}")
                return 1
        else:
            # Auto-select based on task description
            if "plan" in description.lower() or "design" in description.lower():
                target_role = AgentRole.PLANNER if "plan" in description.lower() else AgentRole.DESIGNER
            else:
                target_role = AgentRole.PLANNER  # Default
        
        # Create task request
        task_request = TaskRequest(
            task_id=str(uuid.uuid4()),
            task_type="collaborative_task",
            description=description,
            requirements=[],
            context={}
        )
        
        # Delegate task
        try:
            agent_id = coordinator.delegate_task(session_id, task_request, target_role=target_role)
            
            if agent_id:
                print(f"[+] Task assigned to {self.format_agent_role(target_role)}")
                print(f"    Task ID: {task_request.task_id}")
                print(f"    Description: {description}")
                
                # Execute task immediately (simplified)
                print(f"\n[*] Executing task...")
                response = coordinator.execute_task(agent_id, task_request, session_id)
                
                if response.status == TaskStatus.COMPLETED:
                    print(f"[+] Task completed successfully")
                    if response.result:
                        print(f"\n📊 Result:")
                        for key, value in response.result.items():
                            print(f"   {key}: {value}")
                else:
                    print(f"[!] Task failed:")
                    for error in response.errors:
                        print(f"   - {error}")
                    return 1
            else:
                print(f"[!] Failed to assign task")
                return 1
                
        except Exception as e:
            print(f"[!] Error assigning task: {e}")
            return 1
        
        return 0


class ShowStatusCommand(CollaborateCommand):
    """Show status of a collaboration session."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute show-status command.
        
        Args:
            args: Parsed command arguments
        
        Returns:
            Exit code (0 = success)
        """
        coordinator = get_coordinator()
        
        session_id = args.session_id
        
        print(f"[*] Fetching session status...")
        
        # Get session status
        status = coordinator.get_session_status(session_id)
        
        if "error" in status:
            print(f"[!] {status['error']}")
            return 1
        
        print(f"\n📊 Session Status: {session_id[:8]}...")
        print(f"   Coordinator: {status['coordinator_id'][:8]}...")
        print(f"   Agents: {status['agents']}")
        print(f"   Messages: {status['messages']}")
        print(f"   Active Proposals: {status['active_proposals']}")
        print(f"   Active Tasks: {status['active_tasks']}")
        print(f"   Completed Tasks: {status['completed_tasks']}")
        print(f"   Completed: {'Yes' if status['completed'] else 'No'}")
        
        if status['agent_roles']:
            print(f"\n👥 Agents:")
            for agent_id, role_value in status['agent_roles'].items():
                role = AgentRole(role_value)
                print(f"   - {self.format_agent_role(role)} ({agent_id[:8]}...)")
        
        # Get session details
        session = coordinator.get_session(session_id)
        if session and session.shared_context:
            context = session.shared_context
            if context.goals:
                print(f"\n🎯 Goals:")
                for goal in context.goals:
                    print(f"   - {goal}")
            
            if context.decisions:
                print(f"\n📝 Decisions:")
                for decision in context.decisions[-5:]:  # Show last 5
                    print(f"   - {decision['decision']} (by {decision['decider']})")
        
        return 0


class ProposeCommand(CollaborateCommand):
    """Create a proposal for consensus voting."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute propose command.
        
        Args:
            args: Parsed command arguments
        
        Returns:
            Exit code (0 = success)
        """
        coordinator = get_coordinator()
        
        session_id = args.session_id
        title = args.title
        description = args.description if hasattr(args, 'description') else title
        rationale = args.rationale if hasattr(args, 'rationale') else "No rationale provided"
        
        print(f"[*] Creating proposal...")
        
        # Get session
        session = coordinator.get_session(session_id)
        if not session:
            print(f"[!] Session not found: {session_id}")
            return 1
        
        # Create proposal
        proposer_id = session.coordinator_id
        proposal = coordinator.create_proposal(
            session_id=session_id,
            proposer_id=proposer_id,
            title=title,
            description=description,
            rationale=rationale
        )
        
        print(f"[+] Proposal created: {proposal.proposal_id}")
        print(f"\n📋 {title}")
        print(f"   Description: {description}")
        print(f"   Rationale: {rationale}")
        print(f"\n💡 Agents will vote on this proposal")
        print(f"   Use 'aureus collaborate vote {session_id} {proposal.proposal_id} approve/reject' to vote")
        
        return 0


class VoteCommand(CollaborateCommand):
    """Vote on a proposal."""
    
    def execute(self, args: argparse.Namespace) -> int:
        """
        Execute vote command.
        
        Args:
            args: Parsed command arguments
        
        Returns:
            Exit code (0 = success)
        """
        coordinator = get_coordinator()
        
        session_id = args.session_id
        proposal_id = args.proposal_id
        vote_str = args.vote.lower()
        
        # Parse vote
        vote_map = {
            "approve": VoteType.APPROVE,
            "reject": VoteType.REJECT,
            "abstain": VoteType.ABSTAIN
        }
        vote = vote_map.get(vote_str)
        if not vote:
            print(f"[!] Invalid vote: {vote_str}")
            print(f"    Valid options: approve, reject, abstain")
            return 1
        
        print(f"[*] Recording vote...")
        
        # Get session
        session = coordinator.get_session(session_id)
        if not session:
            print(f"[!] Session not found: {session_id}")
            return 1
        
        # Vote (using coordinator as voter for simplicity)
        voter_id = session.coordinator_id
        success = coordinator.vote_on_proposal(session_id, proposal_id, voter_id, vote)
        
        if not success:
            print(f"[!] Failed to record vote")
            return 1
        
        print(f"[+] Vote recorded: {vote.value}")
        
        # Check consensus
        consensus, vote_counts = coordinator.check_consensus(session_id, proposal_id)
        
        print(f"\n📊 Vote counts:")
        for vote_type, count in vote_counts.items():
            print(f"   {vote_type.value}: {count}")
        
        if consensus:
            print(f"\n✅ Consensus reached! Proposal approved.")
        else:
            print(f"\n⏳ Consensus not yet reached (need 66% approval)")
        
        return 0


# ============================================================================
# CLI Parser Setup
# ============================================================================

def add_collaborate_parser(subparsers: argparse._SubParsersAction) -> None:
    """
    Add 'collaborate' command group to CLI parser.
    
    Args:
        subparsers: argparse subparsers action
    """
    collaborate_parser = subparsers.add_parser(
        'collaborate',
        help='Multi-agent collaboration commands',
        description='Manage collaborative sessions with multiple agents'
    )
    
    collab_subparsers = collaborate_parser.add_subparsers(
        dest='collab_command',
        help='Collaboration subcommand'
    )
    
    # start-session
    start_parser = collab_subparsers.add_parser(
        'start-session',
        help='Start a new collaboration session'
    )
    start_parser.add_argument(
        '--goals',
        type=str,
        help='Comma-separated list of goals for the session'
    )
    
    # assign-task
    assign_parser = collab_subparsers.add_parser(
        'assign-task',
        help='Assign a task to an agent'
    )
    assign_parser.add_argument(
        'session_id',
        type=str,
        help='Session ID'
    )
    assign_parser.add_argument(
        'description',
        type=str,
        help='Task description'
    )
    assign_parser.add_argument(
        '--role',
        type=str,
        choices=['planner', 'designer', 'builder', 'reviewer', 'tester', 'debugger'],
        help='Target agent role (auto-selected if not specified)'
    )
    
    # show-status
    status_parser = collab_subparsers.add_parser(
        'show-status',
        help='Show collaboration session status'
    )
    status_parser.add_argument(
        'session_id',
        type=str,
        help='Session ID'
    )
    
    # propose
    propose_parser = collab_subparsers.add_parser(
        'propose',
        help='Create a proposal for consensus'
    )
    propose_parser.add_argument(
        'session_id',
        type=str,
        help='Session ID'
    )
    propose_parser.add_argument(
        'title',
        type=str,
        help='Proposal title'
    )
    propose_parser.add_argument(
        '--description',
        type=str,
        help='Detailed description'
    )
    propose_parser.add_argument(
        '--rationale',
        type=str,
        help='Rationale for proposal'
    )
    
    # vote
    vote_parser = collab_subparsers.add_parser(
        'vote',
        help='Vote on a proposal'
    )
    vote_parser.add_argument(
        'session_id',
        type=str,
        help='Session ID'
    )
    vote_parser.add_argument(
        'proposal_id',
        type=str,
        help='Proposal ID'
    )
    vote_parser.add_argument(
        'vote',
        type=str,
        choices=['approve', 'reject', 'abstain'],
        help='Vote (approve/reject/abstain)'
    )


def handle_collaborate_command(args: argparse.Namespace) -> int:
    """
    Handle collaborate commands.
    
    Args:
        args: Parsed command arguments
    
    Returns:
        Exit code (0 = success)
    """
    if not hasattr(args, 'collab_command') or not args.collab_command:
        print("[!] No collaboration subcommand specified")
        print("    Available: start-session, assign-task, show-status, propose, vote")
        return 1
    
    command_map = {
        'start-session': StartSessionCommand(),
        'assign-task': AssignTaskCommand(),
        'show-status': ShowStatusCommand(),
        'propose': ProposeCommand(),
        'vote': VoteCommand()
    }
    
    command = command_map.get(args.collab_command)
    if not command:
        print(f"[!] Unknown collaboration command: {args.collab_command}")
        return 1
    
    try:
        return command.execute(args)
    except Exception as e:
        print(f"[!] Error executing command: {e}")
        import traceback
        traceback.print_exc()
        return 1
