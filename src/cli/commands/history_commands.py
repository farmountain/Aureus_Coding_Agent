"""
CLI Commands for Undo/Redo Operations

Provides user-facing commands for operation history management:
- undo: Reverse recent operations
- redo: Restore undone operations
- history: View operation history
"""

import click
from pathlib import Path
from typing import Optional
from datetime import datetime

from src.infrastructure.undo_redo import UndoRedoStack, OperationType, OperationStatus


@click.group(name='history')
def history_commands():
    """Operation history and undo/redo management"""
    pass


@history_commands.command('show')
@click.option(
    '--limit',
    type=int,
    default=20,
    help='Maximum number of operations to show'
)
@click.option(
    '--type',
    type=click.Choice([t.value for t in OperationType]),
    help='Filter by operation type'
)
@click.option(
    '--format',
    type=click.Choice(['table', 'json', 'detailed']),
    default='table',
    help='Output format'
)
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus',
    help='Storage directory'
)
def show_history(limit: int, type: Optional[str], format: str, storage_dir: str):
    """
    Show operation history
    
    Examples:
        aureus history show
        aureus history show --limit 50
        aureus history show --type file_create
        aureus history show --format json
    """
    stack = UndoRedoStack(storage_dir=Path(storage_dir))
    
    op_type = OperationType(type) if type else None
    operations = stack.get_history(limit=limit, op_type=op_type)
    
    if not operations:
        click.echo("No operations in history.")
        return
    
    if format == 'json':
        import json
        data = [op.to_dict() for op in operations]
        click.echo(json.dumps(data, indent=2, default=str))
    elif format == 'detailed':
        _output_detailed_history(operations)
    else:  # table
        _output_history_table(operations)


@history_commands.command('undo')
@click.option(
    '--count',
    '-n',
    type=int,
    default=1,
    help='Number of operations to undo'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be undone without actually undoing'
)
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus',
    help='Storage directory'
)
def undo(count: int, dry_run: bool, storage_dir: str):
    """
    Undo recent operations
    
    Examples:
        aureus history undo
        aureus history undo --count 3
        aureus history undo --dry-run
    """
    stack = UndoRedoStack(storage_dir=Path(storage_dir))
    
    if not stack.can_undo():
        click.echo("[!] No operations to undo")
        return
    
    # Show what will be undone
    operations_to_undo = stack.undo_stack[-count:]
    
    click.echo(f"\n[i] Will undo {len(operations_to_undo)} operation(s):\n")
    for op in reversed(operations_to_undo):
        _print_operation_summary(op)
    
    if dry_run:
        click.echo("\n[DRY RUN] No changes made")
        return
    
    # Confirm if undoing multiple operations
    if count > 1:
        if not click.confirm(f"\nUndo {count} operations?"):
            click.echo("Cancelled")
            return
    
    # Perform undo
    try:
        undone = stack.undo(count=count)
        click.echo(f"\n[OK] Successfully undone {len(undone)} operation(s)")
        
        # Show what was undone
        for op in undone:
            click.echo(f"  - {op.description}")
        
        # Show remaining undo/redo counts
        click.echo(f"\nUndo stack: {len(stack.undo_stack)} | Redo stack: {len(stack.redo_stack)}")
        
    except ValueError as e:
        click.echo(f"[!] Error: {e}", err=True)
        return 1


@history_commands.command('redo')
@click.option(
    '--count',
    '-n',
    type=int,
    default=1,
    help='Number of operations to redo'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be redone without actually redoing'
)
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus',
    help='Storage directory'
)
def redo(count: int, dry_run: bool, storage_dir: str):
    """
    Redo previously undone operations
    
    Examples:
        aureus history redo
        aureus history redo --count 2
        aureus history redo --dry-run
    """
    stack = UndoRedoStack(storage_dir=Path(storage_dir))
    
    if not stack.can_redo():
        click.echo("[!] No operations to redo")
        return
    
    # Show what will be redone
    operations_to_redo = stack.redo_stack[-count:]
    
    click.echo(f"\n[i] Will redo {len(operations_to_redo)} operation(s):\n")
    for op in reversed(operations_to_redo):
        _print_operation_summary(op)
    
    if dry_run:
        click.echo("\n[DRY RUN] No changes made")
        return
    
    # Confirm if redoing multiple operations
    if count > 1:
        if not click.confirm(f"\nRedo {count} operations?"):
            click.echo("Cancelled")
            return
    
    # Perform redo
    try:
        redone = stack.redo(count=count)
        click.echo(f"\n[OK] Successfully redone {len(redone)} operation(s)")
        
        # Show what was redone
        for op in redone:
            click.echo(f"  - {op.description}")
        
        # Show remaining undo/redo counts
        click.echo(f"\nUndo stack: {len(stack.undo_stack)} | Redo stack: {len(stack.redo_stack)}")
        
    except ValueError as e:
        click.echo(f"[!] Error: {e}", err=True)
        return 1


@history_commands.command('stats')
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus',
    help='Storage directory'
)
def stats(storage_dir: str):
    """
    Show operation history statistics
    
    Examples:
        aureus history stats
    """
    stack = UndoRedoStack(storage_dir=Path(storage_dir))
    stats = stack.get_statistics()
    
    click.echo("\n===========================================")
    click.echo("     OPERATION HISTORY STATISTICS")
    click.echo("===========================================\n")
    
    click.echo(f"Total Operations:     {stats['total_operations']}")
    click.echo(f"Undoable Operations:  {stats['undoable_operations']}")
    click.echo(f"Undo Stack Size:      {stats['undo_stack_size']}")
    click.echo(f"Redo Stack Size:      {stats['redo_stack_size']}")
    click.echo(f"Total Cost:           {stats['total_cost']:.2f}")
    
    if stats['oldest_operation']:
        click.echo(f"Oldest Operation:     {stats['oldest_operation']}")
    if stats['newest_operation']:
        click.echo(f"Newest Operation:     {stats['newest_operation']}")
    
    click.echo("\nOperations by Type:")
    for op_type, count in stats['operations_by_type'].items():
        if count > 0:
            click.echo(f"  {op_type:20s}: {count}")
    
    click.echo("\nOperations by Status:")
    for status, count in stats['operations_by_status'].items():
        if count > 0:
            click.echo(f"  {status:20s}: {count}")
    
    click.echo("\n===========================================\n")


@history_commands.command('clear')
@click.option(
    '--keep-undo',
    is_flag=True,
    help='Keep undo stack (only clear history log)'
)
@click.option(
    '--storage-dir',
    type=click.Path(exists=True),
    default='.aureus',
    help='Storage directory'
)
@click.confirmation_option(
    prompt='This will clear operation history. Continue?'
)
def clear_history(keep_undo: bool, storage_dir: str):
    """
    Clear operation history
    
    Examples:
        aureus history clear
        aureus history clear --keep-undo
    """
    stack = UndoRedoStack(storage_dir=Path(storage_dir))
    stack.clear_history(keep_undo_stack=keep_undo)
    
    if keep_undo:
        click.echo("[OK] History cleared (undo stack preserved)")
    else:
        click.echo("[OK] All history cleared (undo and redo stacks cleared)")


# Helper functions for output formatting

def _output_history_table(operations):
    """Output operations as formatted table"""
    click.echo(f"\n{'Time':<20} {'Type':<15} {'Status':<12} {'Description':<50} {'Cost':<8}")
    click.echo("=" * 110)
    
    for op in operations:
        time_str = op.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        type_str = op.type.value
        status_str = op.status.value
        desc_str = op.description[:47] + "..." if len(op.description) > 50 else op.description
        cost_str = f"{op.cost:.1f}" if op.cost > 0 else "-"
        
        # Color code by status
        if op.status == OperationStatus.UNDONE:
            click.echo(click.style(
                f"{time_str:<20} {type_str:<15} {status_str:<12} {desc_str:<50} {cost_str:<8}",
                fg='yellow'
            ))
        elif op.status == OperationStatus.FAILED:
            click.echo(click.style(
                f"{time_str:<20} {type_str:<15} {status_str:<12} {desc_str:<50} {cost_str:<8}",
                fg='red'
            ))
        else:
            click.echo(f"{time_str:<20} {type_str:<15} {status_str:<12} {desc_str:<50} {cost_str:<8}")
    
    click.echo("")


def _output_detailed_history(operations):
    """Output operations with full details"""
    for i, op in enumerate(operations, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"Operation #{i}: {op.description}")
        click.echo(f"{'='*60}")
        click.echo(f"ID:          {op.id}")
        click.echo(f"Type:        {op.type.value}")
        click.echo(f"Status:      {op.status.value}")
        click.echo(f"Timestamp:   {op.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo(f"Cost:        {op.cost}")
        click.echo(f"Can Undo:    {op.can_undo}")
        
        if op.undo_reason:
            click.echo(f"Undo Reason: {op.undo_reason}")
        
        if op.files_affected:
            click.echo(f"Files:       {len(op.files_affected)}")
            for file_path in op.files_affected[:5]:  # Show first 5
                click.echo(f"  - {file_path}")
            if len(op.files_affected) > 5:
                click.echo(f"  ... and {len(op.files_affected) - 5} more")
        
        if op.intent:
            click.echo(f"Intent:      {op.intent}")
        
        if op.transaction_id:
            click.echo(f"Transaction: {op.transaction_id}")


def _print_operation_summary(op):
    """Print a single-line operation summary"""
    time_str = op.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    files_str = f" ({len(op.files_affected)} files)" if op.files_affected else ""
    click.echo(f"  [{time_str}] {op.type.value}: {op.description}{files_str}")


if __name__ == "__main__":
    history_commands()
