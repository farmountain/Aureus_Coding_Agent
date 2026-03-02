"""
AUREUS Test Generation Commands

CLI commands for automated test generation using TestWriterAgent.
"""

from pathlib import Path
from typing import Any, Dict, Optional
import sys


class TestGenCommand:
    """Generate tests for existing code using TestWriterAgent."""
    
    def __init__(self, file_path: str, verbose: bool = False, output_path: Optional[str] = None):
        """
        Initialize test generation command.
        
        Args:
            file_path: Path to file to generate tests for
            verbose: Show detailed output
            output_path: Optional custom output path for test file
        """
        self.file_path = Path(file_path)
        self.verbose = verbose
        self.output_path = Path(output_path) if output_path else None
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute test generation.
        
        Returns:
            Result dictionary with generated test info
        """
        # Validate file exists
        if not self.file_path.exists():
            return {
                "status": "error",
                "message": f"File not found: {self.file_path}"
            }
        
        # Read source code
        try:
            source_code = self.file_path.read_text()
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to read file: {e}"
            }
        
        print(f"🧪 Generating tests for: {self.file_path}")
        
        try:
            from src.agents.swarm import TestWriterAgent, AgentTask, AgentRole
            from src.model_provider import OpenAIProvider, AnthropicProvider, MockProvider
            import os
            
            # Initialize model provider
            provider_name = os.getenv("AUREUS_MODEL_PROVIDER", "mock").lower()
            api_key = os.getenv("AUREUS_MODEL_API_KEY")
            
            if provider_name == "openai":
                if not api_key:
                    return {
                        "status": "error",
                        "message": "AUREUS_MODEL_API_KEY required for OpenAI"
                    }
                model_provider = OpenAIProvider(api_key=api_key)
            elif provider_name == "anthropic":
                if not api_key:
                    return {
                        "status": "error",
                        "message": "AUREUS_MODEL_API_KEY required for Anthropic"
                    }
                model_provider = AnthropicProvider(api_key=api_key)
            else:
                model_provider = MockProvider()
                print("⚠️  Using MockProvider (demo mode)")
            
            # Create TestWriter agent
            test_writer = TestWriterAgent(
                model_provider=model_provider,
                workspace_root=Path.cwd()
            )
            
            # Create task for test generation
            task = AgentTask(
                task_id="test_gen_cli",
                role=AgentRole.TEST_WRITER,
                description=f"Generate tests for {self.file_path}",
                inputs={
                    "task_2_codegen": {
                        "files": [{
                            "path": str(self.file_path),
                            "code": source_code
                        }]
                    }
                }
            )
            
            # Execute test generation
            result_task = test_writer.execute_task(task)
            
            if result_task.status == "failed":
                return {
                    "status": "error",
                    "message": f"Test generation failed: {result_task.error}"
                }
            
            # Extract test files
            test_files = result_task.result.get("test_files", [])
            
            if not test_files:
                return {
                    "status": "error",
                    "message": "No tests generated"
                }
            
            # Determine output path
            if self.output_path:
                output_path = self.output_path
            else:
                # Default: tests/test_<filename>.py
                test_dir = Path("tests")
                test_dir.mkdir(exist_ok=True)
                output_path = test_dir / f"test_{self.file_path.stem}.py"
            
            # Write test file
            test_content = test_files[0]["code"]
            output_path.write_text(test_content)
            
            print(f"✅ Tests generated: {output_path}")
            
            # Show test results if available
            test_results = result_task.result.get("test_results", {})
            if test_results and self.verbose:
                print(f"\n📊 Test Results:")
                print(f"  Total: {test_results.get('total', 0)}")
                print(f"  Passed: {test_results.get('passed', 0)}")
                print(f"  Failed: {test_results.get('failed', 0)}")
                print(f"  Coverage: {result_task.result.get('coverage', 'N/A')}%")
            
            return {
                "status": "success",
                "message": f"Tests generated successfully",
                "output_file": str(output_path),
                "test_count": test_results.get('total', 0),
                "all_passed": test_results.get("all_passed", False)
            }
            
        except ImportError as e:
            return {
                "status": "error",
                "message": f"Missing dependencies: {e}"
            }
        except Exception as e:
            if self.verbose:
                import traceback
                traceback.print_exc()
            return {
                "status": "error",
                "message": f"Test generation error: {e}"
            }


def parse_test_gen_args(args):
    """Parse test-gen command arguments."""
    import argparse
    
    parser = argparse.ArgumentParser(
        prog="aureus test-gen",
        description="Generate tests for existing code"
    )
    parser.add_argument("file", help="File to generate tests for")
    parser.add_argument("-o", "--output", help="Output path for test file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    return parser.parse_args(args)


def main_test_gen(args):
    """Main entry point for test-gen command."""
    parsed = parse_test_gen_args(args)
    
    cmd = TestGenCommand(
        file_path=parsed.file,
        verbose=parsed.verbose,
        output_path=parsed.output
    )
    
    result = cmd.execute()
    
    if result["status"] == "success":
        print(f"\n✅ {result['message']}")
        return 0
    else:
        print(f"\n❌ {result['message']}", file=sys.stderr)
        return 1
