"""
Simple test to prove end-to-end flow actually works
"""
from pathlib import Path
from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider import MockProvider

# Setup
policy_path = Path(".aureus/policy.yaml")
loader = PolicyLoader()
policy = loader.load(policy_path)

# Use MockProvider (works without API key)
provider = MockProvider()
agent = BuilderAgent(policy=policy, model_provider=provider)

# Execute
result = agent.build("create a simple add function")

# Check results
print(f"Success: {result.success}")
print(f"Budget status: {result.cost.budget_status}")
print(f"Files created: {result.files_created}")
print(f"Files modified: {result.files_modified}")

# Verify file exists
if result.files_created:
    for filepath in result.files_created:
        p = Path(filepath)
        if p.exists():
            print(f"\n✓ File created: {filepath}")
            print(f"Content:\n{p.read_text()}")
        else:
            print(f"\n✗ File NOT found: {filepath}")
else:
    print("\n✗ NO FILES CREATED")
    print(f"Error: {result.error}")
    print(f"Execution log: {result.metadata.get('execution_log', [])}")
