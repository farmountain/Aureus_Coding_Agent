import sys
sys.path.insert(0, '.')

from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider.openai_provider import OpenAIProvider
import os
from pathlib import Path

policy = PolicyLoader().load(Path('.aureus/policy.yaml'))
provider = OpenAIProvider(api_key=os.getenv('OPENAI_API_KEY'))
agent = BuilderAgent(policy=policy, model_provider=provider)

print("Testing reflection loop with validation...")
result = agent.build('create a simple stack class with push, pop, and peek methods')

print(f"\n[OK] Success: {result.success}")
print(f"Files: {result.files_created}")
print(f"Tests passed: {result.tests_passed}")
print(f"Attempts: {result.metadata.get('attempts', 1)}")

if result.files_created:
    print(f"\nGenerated code:")
    with open(result.files_created[0], 'r') as f:
        print(f.read())
