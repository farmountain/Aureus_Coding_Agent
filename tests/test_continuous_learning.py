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

print("=" * 70)
print("TESTING ENHANCED 3-TIER INTELLIGENCE WITH CONTINUOUS LEARNING")
print("=" * 70)

# Test 1: Generate queue class
print("\n[Test 1] Generate queue class...")
result1 = agent.build('create a queue class with enqueue, dequeue, and is_empty methods')
print(f"Success: {result1.success} | Files: {len(result1.files_created)} | Attempts: {result1.metadata.get('attempts', 1)}")

# Test 2: Generate similar data structure (should benefit from memory)
print("\n[Test 2] Generate deque class (should learn from queue)...")
result2 = agent.build('create a deque class with add_front, add_rear, remove_front, remove_rear')
print(f"Success: {result2.success} | Files: {len(result2.files_created)} | Attempts: {result2.metadata.get('attempts', 1)}")

# Test 3: Check memory statistics
print("\n[Memory Statistics]")
stats = agent.memory.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")

# Test 4: Generate something different
print("\n[Test 3] Generate linked list...")
result3 = agent.build('create a linked list with insert, delete, and search methods')
print(f"Success: {result3.success} | Files: {len(result3.files_created)} | Attempts: {result3.metadata.get('attempts', 1)}")

# Final stats
print("\n[Final Memory Statistics]")
final_stats = agent.memory.get_statistics()
for key, value in final_stats.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 70)
print("CONTINUOUS LEARNING DEMONSTRATION COMPLETE")
print("=" * 70)
print(f"\nMemory location: {agent.memory.memory_file}")
print("Memory persists across sessions for continuous improvement!")
