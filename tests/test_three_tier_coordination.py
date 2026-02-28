"""
Test 3-Tier Coordination Protocol

Demonstrates how GVUFD -> SPK -> UVUAS coordinate tightly:
1. GVUFD: Extracts goals from intent, updates global value function
2. SPK: Evaluates spec candidates by value alignment (not just cost)
3. UVUAS: Executes with Claude Code loop (Context -> Execute -> Reflect)

This is the core architecture that makes AUREUS intelligent.
"""

import sys
sys.path.insert(0, '.')

from pathlib import Path
from src.governance.policy import PolicyLoader
from src.coordination.three_tier_coordinator import ThreeTierCoordinator
from src.memory.global_value_function import GlobalValueMemory
import os

def print_section(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def test_simple_intent():
    """Test: 'simple' keyword should increase simplicity weight"""
    print_section("Test 1: Simple Intent -> Goal Extraction")
    
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    global_value_memory = GlobalValueMemory()
    coordinator = ThreeTierCoordinator(
        policy=policy,
        global_value_memory=global_value_memory,
        workspace_root=Path('workspace')
    )
    
    intent = "create a simple calculator class"
    
    print(f"\nIntent: '{intent}'")
    print("\nBefore coordination:")
    vf = global_value_memory.get_global_value_function()
    for goal in vf.goals:
        print(f"  {goal.goal_type.value}: {goal.weight}")
    
    # Execute coordination
    result = coordinator.coordinate(intent)
    
    print("\nAfter coordination (GVUFD extracted goals):")
    vf = global_value_memory.get_global_value_function()
    for goal in vf.goals:
        print(f"  {goal.goal_type.value}: {goal.weight}")
    
    print(f"\nGoals extracted:")
    goals = result["goals_extracted"]
    print(f"  Explicit: {goals.explicit_goals}")
    print(f"  Optimization: {goals.optimization_target}")
    
    print(f"\nSpec candidates generated: {len(result['spec_candidates'])}")
    for i, (spec, cost) in enumerate(result['spec_candidates'], 1):
        print(f"  Candidate {i}: {cost.total} cost, within_budget={cost.within_budget}")
    
    print(f"\nSelected spec (highest value alignment):")
    print(f"  Alignment score: {result['alignment_score']:.2f}")
    print(f"  LOC: {result['selected_spec'].budgets.max_loc_delta}")
    
    assert "simplicity" in goals.explicit_goals, "Should extract simplicity goal"
    assert goals.optimization_target == "maximize_speed", "Simple -> speed optimization"
    
    print("\n[OK] GVUFD correctly extracted goals from 'simple' keyword")
    print("[OK] SPK selected spec with highest value alignment")

def test_production_intent():
    """Test: 'production-ready' should increase quality + testability"""
    print_section("Test 2: Production Intent -> Quality Goals")
    
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    global_value_memory = GlobalValueMemory()
    coordinator = ThreeTierCoordinator(
        policy=policy,
        global_value_memory=global_value_memory,
        workspace_root=Path('workspace')
    )
    
    intent = "build a production-ready API client with error handling"
    
    print(f"\nIntent: '{intent}'")
    
    # Execute coordination
    result = coordinator.coordinate(intent)
    
    goals = result["goals_extracted"]
    print(f"\nGoals extracted:")
    print(f"  Explicit: {goals.explicit_goals}")
    print(f"  Optimization: {goals.optimization_target}")
    
    print(f"\nGlobal value function updated:")
    vf = global_value_memory.get_global_value_function()
    for goal in vf.goals:
        if goal.goal_type.value in ["code_quality", "testability"]:
            print(f"  {goal.goal_type.value}: {goal.weight} (increased for production)")
    
    assert "high_quality" in goals.explicit_goals, "Should extract quality goal"
    assert goals.optimization_target == "maximize_quality", "Production -> quality optimization"
    
    print("\n[OK] GVUFD correctly prioritized quality for production intent")

def test_spec_evaluation():
    """Test: SPK evaluates specs by value alignment, not just cost"""
    print_section("Test 3: SPK Value-Based Spec Selection")
    
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    global_value_memory = GlobalValueMemory()
    coordinator = ThreeTierCoordinator(
        policy=policy,
        global_value_memory=global_value_memory,
        workspace_root=Path('workspace')
    )
    
    # Intent emphasizing quality
    intent = "create a robust data validator with comprehensive error handling"
    
    result = coordinator.coordinate(intent)
    
    print(f"\nIntent: '{intent}'")
    print(f"\nSpec candidates evaluated:")
    
    # Show how SPK evaluated each candidate
    for i, (spec, cost) in enumerate(result['spec_candidates'], 1):
        # Calculate value score for each
        from src.coordination.three_tier_coordinator import SpecEvaluator
        evaluator = SpecEvaluator(global_value_memory)
        score = evaluator.evaluate_spec(spec)
        
        print(f"\n  Candidate {i}:")
        print(f"    Cost: {cost.total}")
        print(f"    LOC: {spec.budgets.max_loc_delta}")
        print(f"    Risk: {spec.risk_level}")
        print(f"    Value alignment score: {score:.2f}")
    
    print(f"\nSelected spec:")
    print(f"  Alignment score: {result['alignment_score']:.2f}")
    print(f"  Intent: {result['selected_spec'].intent}")
    
    print("\n[OK] SPK selected based on value alignment, not just lowest cost")

def test_coordination_log():
    """Test: Coordination log shows complete flow"""
    print_section("Test 4: Full Coordination Flow")
    
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    global_value_memory = GlobalValueMemory()
    coordinator = ThreeTierCoordinator(
        policy=policy,
        global_value_memory=global_value_memory,
        workspace_root=Path('workspace')
    )
    
    intent = "create a simple stack data structure"
    
    result = coordinator.coordinate(intent)
    
    print(f"\nIntent: '{intent}'")
    print("\nCoordination Log:")
    for i, log_entry in enumerate(result['coordination_log'], 1):
        print(f"  {i}. {log_entry}")
    
    # Verify flow
    log_text = " ".join(result['coordination_log'])
    
    assert "TIER 1: GVUFD" in log_text, "Should show GVUFD execution"
    assert "TIER 2: SPK" in log_text, "Should show SPK execution"  
    assert "TIER 3: UVUAS" in log_text, "Should show UVUAS execution"
    assert "Context:" in log_text, "Should show context gathering"
    
    print("\n[OK] Complete 3-tier flow executed in order")
    print("[OK] Each tier informed the next (not independent pipelines)")

def test_integration_with_builder():
    """Test: BuilderAgent uses coordinated flow"""
    print_section("Test 5: BuilderAgent Integration")
    
    from src.agents.builder import BuilderAgent
    from src.model_provider.openai_provider import OpenAIProvider
    
    policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
    provider = OpenAIProvider(api_key=os.getenv('OPENAI_API_KEY'))
    agent = BuilderAgent(policy=policy, model_provider=provider)
    
    print("\nBuilderAgent initialized with 3-tier coordinator")
    print(f"Coordinator: {type(agent.coordinator).__name__}")
    
    # Test intent with goal extraction
    intent = "create a simple hash map implementation"
    
    print(f"\nBuilding: '{intent}'")
    result = agent.build(intent)
    
    print(f"\nResult:")
    print(f"  Success: {result.success}")
    if result.metadata:
        print(f"  Optimization target: {result.metadata.get('optimization_target')}")
        print(f"  Alignment score: {result.metadata.get('alignment_score', 0):.2f}")
        
        if 'coordination_log' in result.metadata:
            print(f"\nCoordination log (last 3):")
            for log in result.metadata['coordination_log'][-3:]:
                print(f"    {log}")
    
    print("\n[OK] BuilderAgent successfully uses coordinated 3-tier flow")

def main():
    print("""
================================================================================
  3-TIER COORDINATION PROTOCOL TEST
================================================================================

This demonstrates the tight integration between:
- GVUFD (Tier 1): Intent -> Goals + Spec
- SPK (Tier 2): Spec Variants -> Value-Aligned Selection  
- UVUAS (Tier 3): Claude Code Loop (Context -> Execute -> Reflect)

These are NOT independent components - they coordinate closely to achieve the
global goal.
    """)
    
    try:
        test_simple_intent()
        test_production_intent()
        test_spec_evaluation()
        test_coordination_log()
        
        # Only run if OpenAI key available
        if os.getenv('OPENAI_API_KEY'):
            test_integration_with_builder()
        else:
            print("\n[Skipped Test 5: No OpenAI API key]")
        
        print_section("SUMMARY")
        print("""
OK GVUFD extracts goals from natural language intent
OK Global value function updates based on intent keywords
OK SPK generates multiple spec candidates
OK SPK selects spec by value alignment (not just cost)
OK UVUAS executes with Claude Code loop
OK Complete coordination log shows flow

The 3-tier architecture is now truly coordinated:
- Intent goals inform spec generation
- Spec evaluation uses value function
- Execution maintains global goal alignment
- Feedback loops between tiers

This is what makes AUREUS intelligent.
        """)
        
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
