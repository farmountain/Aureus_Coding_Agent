"""Test that 3-tier intelligence actually generates smart code"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider import OpenAIProvider

# Load policy
policy = PolicyLoader().load(Path('.aureus/policy.yaml'))

# Use OpenAI with real key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    print("Set it with: $env:OPENAI_API_KEY='your-key-here'")
    exit(1)

provider = OpenAIProvider(api_key=api_key)
agent = BuilderAgent(policy=policy, model_provider=provider)

# Test simple intent
print("=" * 60)
print("Testing: create a hello world function")
print("=" * 60)
result = agent.build("create a hello world function")

print(f"\nSuccess: {result.success}")
print(f"Files created: {result.files_created}")
print("\n=== GVUFD Spec (Tier 1) ===")
print(f"Intent: {result.specification.intent}")
print(f"Risk level: {result.specification.risk_level}")
print(f"Max LOC budget: {result.specification.budgets.max_loc_delta}")

print("\n=== SPK Cost (Tier 2) ===")
print(f"Total cost: {result.cost.total}")
print(f"LOC cost: {result.cost.loc}")
print(f"Within budget: {result.cost.within_budget}")

print("\n=== UVUAS Generated Code (Tier 3) ===")
if result.files_created:
    file_path = result.files_created[0]
    if Path(file_path).exists():
        with open(file_path, 'r') as f:
            code = f.read()
        print(code)
        
        # Check if it's actually a hello world function
        if "hello" in code.lower() and "world" in code.lower():
            print("\n✅ SUCCESS: Code contains 'hello world' - intelligence working!")
        else:
            print("\n❌ FAIL: Code doesn't contain 'hello world' - intelligence not working")
else:
    print("No file created")

print("\n" + "=" * 60)
print("Testing: create a calculator class with add and subtract methods")
print("=" * 60)
result2 = agent.build("create a calculator class with add and subtract methods")

print(f"\nSuccess: {result2.success}")
print(f"Files created: {result2.files_created}")
print(f"SPK Total cost: {result2.cost.total}")

if result2.files_created:
    file_path = result2.files_created[0]
    if Path(file_path).exists():
        with open(file_path, 'r') as f:
            code = f.read()
        print("\n=== Generated Code ===")
        print(code[:500])  # First 500 chars
        
        # Check if it's actually a calculator
        if "add" in code.lower() and "subtract" in code.lower() and "class" in code.lower():
            print("\n✅ SUCCESS: Code contains calculator with add/subtract - intelligence working!")
        else:
            print("\n❌ FAIL: Code doesn't implement calculator properly")
