#!/usr/bin/env python3
"""
Example usage of the LLM Swarm system.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import Orchestrator
from utils.logger import setup_logging


def main():
    """Run a simple example."""
    # Setup logging
    setup_logging()
    
    # Example project specification
    project_spec = """
    Create a simple Python CLI tool that:
    1. Greets users by name
    2. Logs messages to a file
    3. Has a help command
    4. Includes basic error handling
    5. Has unit tests
    6. Includes a README with usage instructions
    
    The tool should be called 'greeter' and should be installable via pip.
    Use Python 3.8+ and follow best practices.
    """
    
    print("🚀 LLM Swarm Example")
    print("=" * 50)
    print(f"Project Spec: {project_spec.strip()}")
    print("=" * 50)
    
    try:
        # Initialize orchestrator
        orchestrator = Orchestrator(
            config_path="models/config.yaml",
            output_dir="./example_output"
        )
        
        # Run in dry-run mode first to see the plan
        print("\n🔍 Running in dry-run mode to show execution plan...")
        success = orchestrator.run(project_spec, dry_run=True)
        
        if success:
            print("\n✅ Dry run completed successfully!")
            
            # Ask user if they want to proceed with actual generation
            response = input("\nProceed with actual generation? (y/N): ").strip().lower()
            
            if response in ['y', 'yes']:
                print("\n🚀 Starting actual project generation...")
                success = orchestrator.run(project_spec, dry_run=False)
                
                if success:
                    print("\n🎉 Project generated successfully!")
                    print(f"📁 Check the output in: ./example_output")
                else:
                    print("\n❌ Project generation failed!")
                    return 1
            else:
                print("\n👋 Generation cancelled by user")
        else:
            print("\n❌ Dry run failed!")
            return 1
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())