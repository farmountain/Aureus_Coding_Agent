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

# Generate something complex that can't be a template
result = agent.build('create a binary search tree with insert, search, delete, and in-order traversal methods')

if result.files_created:
    print(f"✅ Generated: {result.files_created[0]}")
    with open(result.files_created[0], 'r') as f:
        print(f.read())
else:
    print("❌ No files created")
