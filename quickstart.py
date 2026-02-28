#!/usr/bin/env python3
"""
QUICKSTART: Verify AUREUS works in 30 seconds

This script tests the complete user journey:
1. Load policy
2. Create agent  
3. Generate code
4. Verify it works

Run: python quickstart.py
"""

from pathlib import Path
from src.governance.policy import PolicyLoader
from src.agents.builder import BuilderAgent
from src.model_provider import MockProvider

print("🚀 AUREUS Quickstart Test\n")
print("=" * 50)

# Step 1: Load policy
print("\n1️⃣  Loading governance policy...")
try:
    policy = PolicyLoader().load(Path(".aureus/policy.yaml"))
    print(f"   ✓ Policy loaded: {policy.project_name}")
except Exception as e:
    print(f"   ✗ Failed to load policy: {e}")
    exit(1)

# Step 2: Create agent
print("\n2️⃣  Creating builder agent...")
try:
    agent = BuilderAgent(
        policy=policy, 
        model_provider=MockProvider()
    )
    print("   ✓ Agent created (using MockProvider)")
except Exception as e:
    print(f"   ✗ Failed to create agent: {e}")
    exit(1)

# Step 3: Generate code
print("\n3️⃣  Generating code from natural language...")
print('   Intent: "create a function that adds two numbers"')
try:
    result = agent.build("create a function that adds two numbers")
    
    if not result.success:
        print(f"   ✗ Build failed: {result.error}")
        exit(1)
    
    print(f"   ✓ Build succeeded")
    print(f"   ✓ Budget status: {result.cost.budget_status}")
    print(f"   ✓ Complexity cost: {result.cost.total:.0f} units")
    
except Exception as e:
    print(f"   ✗ Build error: {e}")
    exit(1)

# Step 4: Verify file created
print("\n4️⃣  Verifying generated code...")
if not result.files_created:
    print("   ✗ No files created")
    exit(1)

for filepath in result.files_created:
    file_path = Path(filepath)
    
    if not file_path.exists():
        print(f"   ✗ File not found: {filepath}")
        exit(1)
    
    size = file_path.stat().st_size
    content = file_path.read_text()
    lines = len(content.splitlines())
    
    print(f"   ✓ File created: {file_path.name}")
    print(f"   ✓ Location: {file_path.parent}")
    print(f"   ✓ Size: {size} bytes, {lines} lines")
    
    print(f"\n📄 Generated Code:")
    print("   " + "-" * 46)
    for line in content.splitlines()[:15]:  # First 15 lines
        print(f"   {line}")
    if lines > 15:
        print(f"   ... ({lines - 15} more lines)")
    print("   " + "-" * 46)

# Success!
print("\n✅ SUCCESS! AUREUS is working correctly.")
print("\n📚 Next Steps:")
print("   1. Set OPENAI_API_KEY or ANTHROPIC_API_KEY env variable")
print("   2. Run: aureus code 'your intent here'")
print("   3. Check the generated code in workspace/")
print("\n" + "=" * 50)
