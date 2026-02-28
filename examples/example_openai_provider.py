"""
Test with real OpenAI API
Set environment variable: OPENAI_API_KEY
"""
import os
from pathlib import Path
from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider import OpenAIProvider

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("ERROR: Set OPENAI_API_KEY environment variable")
    exit(1)

# Setup
policy_path = Path(".aureus/policy.yaml")
loader = PolicyLoader()
policy = loader.load(policy_path)

# Use OpenAI
provider = OpenAIProvider(api_key=api_key)
agent = BuilderAgent(policy=policy, model_provider=provider)

# Execute
print("Generating code with OpenAI GPT-4...")
result = agent.build("create a calculator class with add, subtract, multiply, divide methods")

# Check results
print(f"\nSuccess: {result.success}")
print(f"Budget status: {result.cost.budget_status}")
print(f"Files created: {result.files_created}")

# Verify file exists
if result.files_created:
    for filepath in result.files_created:
        p = Path(filepath)
        if p.exists():
            print(f"\n✓ File created: {filepath}")
            print(f"Size: {p.stat().st_size} bytes")
            print(f"\nFirst 500 chars:\n{p.read_text()[:500]}")
        else:
            print(f"\n✗ File NOT found: {filepath}")
else:
    print("\n✗ NO FILES CREATED")
    print(f"Error: {result.error}")
