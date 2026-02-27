"""
CLI Memory Commands

Provides user-facing commands for interacting with Aureus memory system:
- list-sessions: Show all stored sessions
- show-trajectory: Display detailed session trajectory
- show-patterns: View learned patterns
- export-adr: Export architectural decision records
- memory-stats: Show memory system statistics
"""

import click
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
from src.memory.trajectory import TrajectoryStore
from src.memory.summarization import TrajectorySummarizer, PatternExtractor


@click.group(name='memory')
def memory_commands():
    """Memory system commands for viewing and analyzing session history"""
    pass


@memory_commands.command('list-sessions')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus/memory',
    help='Memory storage directory'
)
@click.option(
    '--limit',
    type=int,
    default=None,
    help='Maximum number of sessions to show'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json', 'simple']),
    default='table',
    help='Output format'
)
def list_sessions(storage_dir: str, limit: Optional[int], format: str):
    """
    List all stored sessions
    
    Examples:
        aureus memory list-sessions
        aureus memory list-sessions --limit 10
        aureus memory list-sessions --format json
    """
    store = TrajectoryStore(storage_dir=Path(storage_dir))
    sessions = store.list_sessions(limit=limit)
    
    if not sessions:
        click.echo("No sessions found.")
        return
    
    if format == 'json':
        _output_json([s.to_dict() for s in sessions])
    elif format == 'simple':
        for session in sessions:
            click.echo(f"{session.session_id}: {session.intent}")
    else:  # table
        _output_sessions_table(sessions)


@memory_commands.command('show-trajectory')
@click.argument('session_id')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus/memory',
    help='Memory storage directory'
)
@click.option(
    '--format',
    type=click.Choice(['detailed', 'json', 'summary']),
    default='detailed',
    help='Output format'
)
@click.option(
    '--show-actions/--no-actions',
    default=True,
    help='Show individual actions'
)
def show_trajectory(
    session_id: str,
    storage_dir: str,
    format: str,
    show_actions: bool
):
    """
    Show detailed session trajectory
    
    Examples:
        aureus memory show-trajectory abc123
        aureus memory show-trajectory abc123 --format json
        aureus memory show-trajectory abc123 --no-actions
    """
    store = TrajectoryStore(storage_dir=Path(storage_dir))
    session = store.get_session(session_id)
    
    if not session:
        click.echo(f"Session {session_id} not found.", err=True)
        return
    
    if format == 'json':
        _output_json(session.to_dict())
    elif format == 'summary':
        _output_trajectory_summary(session)
    else:  # detailed
        _output_trajectory_detailed(session, show_actions=show_actions)


@memory_commands.command('show-patterns')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus/memory',
    help='Memory storage directory'
)
@click.option(
    '--min-frequency',
    type=int,
    default=2,
    help='Minimum pattern frequency'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json', 'detailed']),
    default='table',
    help='Output format'
)
def show_patterns(storage_dir: str, min_frequency: int, format: str):
    """
    Show learned patterns from successful sessions
    
    Examples:
        aureus memory show-patterns
        aureus memory show-patterns --min-frequency 3
        aureus memory show-patterns --format json
    """
    extractor = PatternExtractor(storage_dir=Path(storage_dir))
    patterns = extractor.extract_successful_patterns()
    
    if not patterns:
        click.echo("No patterns found.")
        return
    
    # Filter by frequency if dict-based patterns
    if patterns and isinstance(patterns[0], dict):
        patterns = [p for p in patterns if p.get('frequency', 1) >= min_frequency]
    
    if format == 'json':
        _output_json(patterns)
    elif format == 'detailed':
        _output_patterns_detailed(patterns)
    else:  # table
        _output_patterns_table(patterns)


@memory_commands.command('export-adr')
@click.argument('session_id')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus/memory',
    help='Memory storage directory'
)
@click.option(
    '--output',
    type=click.Path(),
    default=None,
    help='Output file (default: stdout)'
)
@click.option(
    '--format',
    type=click.Choice(['markdown', 'yaml', 'json']),
    default='markdown',
    help='ADR format'
)
def export_adr(
    session_id: str,
    storage_dir: str,
    output: Optional[str],
    format: str
):
    """
    Export Architectural Decision Record for a session
    
    Examples:
        aureus memory export-adr abc123
        aureus memory export-adr abc123 --output decisions/adr-001.md
        aureus memory export-adr abc123 --format yaml
    """
    store = TrajectoryStore(storage_dir=Path(storage_dir))
    session = store.get_session(session_id)
    
    if not session:
        click.echo(f"Session {session_id} not found.", err=True)
        return
    
    if format == 'markdown':
        adr_content = _generate_adr_markdown(session)
    elif format == 'yaml':
        adr_content = _generate_adr_yaml(session)
    else:  # json
        adr_content = _generate_adr_json(session)
    
    if output:
        Path(output).write_text(adr_content)
        click.echo(f"ADR exported to {output}")
    else:
        click.echo(adr_content)


@memory_commands.command('memory-stats')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus/memory',
    help='Memory storage directory'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format'
)
def memory_stats(storage_dir: str, format: str):
    """
    Show memory system statistics
    
    Examples:
        aureus memory memory-stats
        aureus memory memory-stats --format json
    """
    store = TrajectoryStore(storage_dir=Path(storage_dir))
    sessions = store.list_sessions()
    
    stats = _calculate_stats(sessions)
    
    if format == 'json':
        _output_json(stats)
    else:  # table
        _output_stats_table(stats)


# === Output Formatting Functions ===

def _output_json(data):
    """Output data as JSON"""
    click.echo(json.dumps(data, indent=2, default=str))


def _output_sessions_table(sessions):
    """Output sessions as formatted table"""
    click.echo(f"\n{'ID':<10} {'Intent':<40} {'Status':<10} {'Cost':<8} {'Time'}")
    click.echo("=" * 90)
    
    for session in sessions:
        status = "✓ Success" if session.success else "✗ Failed"
        cost = f"{session.total_cost:.1f}"
        time = session.start_time.strftime("%Y-%m-%d %H:%M")
        
        intent_short = session.intent[:37] + "..." if len(session.intent) > 40 else session.intent
        
        click.echo(f"{session.session_id[:8]:<10} {intent_short:<40} {status:<10} {cost:<8} {time}")
    
    click.echo(f"\nTotal sessions: {len(sessions)}")


def _output_trajectory_summary(session):
    """Output session trajectory summary"""
    click.echo(f"\n=== Session {session.session_id} ===\n")
    click.echo(f"Intent: {session.intent}")
    click.echo(f"Status: {'Success' if session.success else 'Failed'}")
    click.echo(f"Start Time: {session.start_time}")
    if session.end_time:
        duration = (session.end_time - session.start_time).total_seconds()
        click.echo(f"Duration: {duration:.1f}s")
    click.echo(f"Total Cost: {session.total_cost}")
    click.echo(f"Actions: {len(session.actions)}")
    if session.outcome:
        click.echo(f"Outcome: {session.outcome}")


def _output_trajectory_detailed(session, show_actions: bool):
    """Output detailed session trajectory"""
    _output_trajectory_summary(session)
    
    if show_actions and session.actions:
        click.echo(f"\n=== Actions ({len(session.actions)}) ===\n")
        for i, action in enumerate(session.actions, 1):
            click.echo(f"{i}. {action.action_type}")
            click.echo(f"   Tool: {action.tool_name}")
            click.echo(f"   Cost: {action.cost_incurred}")
            if action.result:
                result_str = str(action.result)[:80]
                click.echo(f"   Result: {result_str}...")
            click.echo()


def _output_patterns_table(patterns):
    """Output patterns as table"""
    if not patterns:
        return
    
    click.echo(f"\n{'Pattern':<50} {'Success Rate':<15} {'Avg Cost'}")
    click.echo("=" * 80)
    
    for pattern in patterns:
        if isinstance(pattern, dict):
            name = pattern.get('name', 'Unknown')[:47] + "..."
            success_rate = f"{pattern.get('success_rate', 0):.1%}"
            avg_cost = f"{pattern.get('avg_cost', 0):.1f}"
            click.echo(f"{name:<50} {success_rate:<15} {avg_cost}")
        else:
            click.echo(str(pattern))
    
    click.echo(f"\nTotal patterns: {len(patterns)}")


def _output_patterns_detailed(patterns):
    """Output detailed pattern information"""
    for i, pattern in enumerate(patterns, 1):
        click.echo(f"\n=== Pattern {i} ===")
        if isinstance(pattern, dict):
            for key, value in pattern.items():
                click.echo(f"{key}: {value}")
        else:
            click.echo(str(pattern))


def _generate_adr_markdown(session) -> str:
    """Generate ADR in Markdown format"""
    adr = f"""# ADR: {session.intent}

**Date**: {session.start_time.strftime("%Y-%m-%d")}  
**Status**: {'Accepted' if session.success else 'Rejected'}  
**Session ID**: {session.session_id}

## Context

{session.intent}

## Decision

"""
    
    if session.actions:
        adr += "### Actions Taken\n\n"
        for action in session.actions:
            adr += f"- {action.action_type} using {action.tool_name}\n"
    
    adr += f"\n## Consequences\n\n"
    adr += f"**Total Cost**: {session.total_cost} LOC\n"
    adr += f"**Success**: {session.success}\n"
    
    if session.outcome:
        adr += f"\n{session.outcome}\n"
    
    return adr


def _generate_adr_yaml(session) -> str:
    """Generate ADR in YAML format"""
    import yaml
    
    adr_data = {
        'title': session.intent,
        'date': session.start_time.isoformat(),
        'status': 'accepted' if session.success else 'rejected',
        'session_id': session.session_id,
        'context': session.intent,
        'decision': {
            'actions': [
                {
                    'type': a.action_type,
                    'tool': a.tool_name,
                    'cost': a.cost_incurred
                }
                for a in session.actions
            ]
        },
        'consequences': {
            'total_cost': session.total_cost,
            'success': session.success,
            'outcome': session.outcome
        }
    }
    
    return yaml.dump(adr_data, default_flow_style=False)


def _generate_adr_json(session) -> str:
    """Generate ADR in JSON format"""
    adr_data = {
        'title': session.intent,
        'date': session.start_time.isoformat(),
        'status': 'accepted' if session.success else 'rejected',
        'session_id': session.session_id,
        'context': session.intent,
        'decision': {
            'actions': [
                {
                    'type': a.action_type,
                    'tool': a.tool_name,
                    'cost': a.cost_incurred,
                    'result': str(a.result) if a.result else None
                }
                for a in session.actions
            ]
        },
        'consequences': {
            'total_cost': session.total_cost,
            'success': session.success,
            'outcome': session.outcome
        }
    }
    
    return json.dumps(adr_data, indent=2, default=str)


def _calculate_stats(sessions):
    """Calculate memory system statistics"""
    if not sessions:
        return {
            'total_sessions': 0,
            'successful_sessions': 0,
            'failed_sessions': 0,
            'success_rate': 0.0,
            'total_cost': 0.0,
            'avg_cost_per_session': 0.0,
            'total_actions': 0
        }
    
    successful = sum(1 for s in sessions if s.success)
    total_cost = sum(s.total_cost for s in sessions)
    total_actions = sum(len(s.actions) for s in sessions)
    
    return {
        'total_sessions': len(sessions),
        'successful_sessions': successful,
        'failed_sessions': len(sessions) - successful,
        'success_rate': successful / len(sessions) if sessions else 0.0,
        'total_cost': total_cost,
        'avg_cost_per_session': total_cost / len(sessions) if sessions else 0.0,
        'total_actions': total_actions,
        'avg_actions_per_session': total_actions / len(sessions) if sessions else 0.0
    }


def _output_stats_table(stats):
    """Output statistics as formatted table"""
    click.echo(f"\n=== Memory System Statistics ===\n")
    click.echo(f"Total Sessions:       {stats['total_sessions']}")
    click.echo(f"Successful Sessions:  {stats['successful_sessions']}")
    click.echo(f"Failed Sessions:      {stats['failed_sessions']}")
    click.echo(f"Success Rate:         {stats['success_rate']:.1%}")
    click.echo(f"Total Cost:           {stats['total_cost']:.1f} LOC")
    click.echo(f"Avg Cost/Session:     {stats['avg_cost_per_session']:.1f} LOC")
    click.echo(f"Total Actions:        {stats['total_actions']}")
    click.echo(f"Avg Actions/Session:  {stats['avg_actions_per_session']:.1f}")
