"""
Test Global Value Function Alignment

Demonstrates how the global value function governs all agent decisions
and prevents drift from global goals.
"""

import sys
sys.path.insert(0, '.')

from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider.openai_provider import OpenAIProvider
from src.memory.global_value_function import GoalType
import os
from pathlib import Path

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def main():
    # Initialize system
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    provider = OpenAIProvider(api_key=os.getenv('OPENAI_API_KEY'))
    agent = BuilderAgent(policy=policy, model_provider=provider)
    
    print_section("GLOBAL VALUE FUNCTION SYSTEM")
    
    # Get global value function
    global_vf = agent.global_value_memory.get_global_value_function()
    
    print("\nGlobal Goals:")
    for goal in global_vf.goals:
        print(f"  [{goal.goal_type.value}]")
        print(f"    Weight: {goal.weight}")
        print(f"    Threshold: {goal.threshold}")
        print(f"    Description: {goal.description}")
    
    print(f"\nOptimization Target: {global_vf.optimization_target}")
    print(f"Constraints: {global_vf.constraints}")
    
    print_section("Test 1: Well-Aligned Code Generation")
    print("Generating code that should align with global goals...")
    
    result1 = agent.build("create a simple data validator class with type checking")
    
    print(f"\nResult:")
    print(f"  Success: {result1.success}")
    print(f"  Attempts: {result1.metadata.get('attempts', 1)}")
    print(f"  Files: {result1.files_created}")
    
    # Check alignment stats
    stats = agent.global_value_memory.get_alignment_statistics()
    if stats:
        print(f"\nAlignment Statistics:")
        print(f"  Total actions validated: {stats['total_actions']}")
        print(f"  Aligned actions: {stats['aligned_actions']}/{stats['total_actions']}")
        print(f"  Alignment rate: {stats['alignment_rate'] * 100:.1f}%")
        print(f"  Avg alignment score: {stats['avg_alignment_score']:.2f}")
        print(f"  Drift events: {stats['drift_events']}")
    
    print_section("Test 2: Generate Complex Code (Monitoring Alignment)")
    print("Generating more complex code to test alignment checking...")
    
    result2 = agent.build("create a caching decorator with TTL and size limits")
    
    print(f"\nResult:")
    print(f"  Success: {result2.success}")
    print(f"  Attempts: {result2.metadata.get('attempts', 1)}")
    
    # Updated alignment stats
    stats = agent.global_value_memory.get_alignment_statistics()
    if stats:
        print(f"\nUpdated Alignment Statistics:")
        print(f"  Total actions: {stats['total_actions']}")
        print(f"  Alignment rate: {stats['alignment_rate'] * 100:.1f}%")
        print(f"  Avg score: {stats['avg_alignment_score']:.2f}")
        
        if stats['drift_events'] > 0:
            print(f"\n  ⚠️ DRIFT EVENTS DETECTED: {stats['drift_events']}")
            if stats['last_drift']:
                print(f"  Last drift: {stats['last_drift']['timestamp']}")
                print(f"  Alignment score: {stats['last_drift']['alignment_score']:.2f}")
                print(f"  Warnings: {stats['last_drift']['warnings']}")
        else:
            print(f"\n  ✓ NO DRIFT: All agents aligned with global goals")
    
    print_section("Global Value Function Benefits")
    print("""
  1. ALIGNMENT: All agents optimize for the same global goals
  2. NO DRIFT: Local agent decisions are validated against global function
  3. GOVERNANCE: Enforces project-wide standards automatically
  4. TRANSPARENCY: Clear visibility into what the system optimizes for
  5. ADAPTABILITY: Global goals can be adjusted without changing agents
    """)
    
    print_section("Goal Weight Adjustment Example")
    print("Increasing weight for CODE_QUALITY goal...")
    
    agent.global_value_memory.update_global_goal(GoalType.CODE_QUALITY, 0.4)
    
    print("\nUpdated global value function will now:")
    print("  - Place higher priority on type hints, docstrings")
    print("  - Enforce stricter quality gates")
    print("  - Generate more detailed code")
    print("  - All future builds will respect this adjustment")
    
    print_section("Summary")
    
    final_stats = agent.global_value_memory.get_alignment_statistics()
    
    print(f"""
  Global Value Function: ACTIVE
  Total Validations: {final_stats.get('total_actions', 0)}
  Alignment Rate: {final_stats.get('alignment_rate', 0) * 100:.1f}%
  Drift Events: {final_stats.get('drift_events', 0)}
  
  Status: {'✓ ALIGNED' if final_stats.get('drift_events', 0) == 0 else '⚠️ DRIFT DETECTED'}
  
  Memory Location: {agent.global_value_memory.memory_file}
  
  The global value function ensures:
  - All agent actions align with project goals
  - No local optimization conflicts with global objectives
  - Consistent quality across all generated code
  - Automatic drift detection and correction
    """)
    
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
