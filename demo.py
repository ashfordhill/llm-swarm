#!/usr/bin/env python3
"""
Demo script to showcase LLM Swarm capabilities.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging


def main():
    """Run the demo."""
    setup_logging()
    
    print("🎉 LLM Swarm Demo")
    print("=" * 60)
    print()
    
    print("🤖 Multi-Agent Code Generation System")
    print("Transform natural language specifications into complete software projects!")
    print()
    
    print("✨ What's Implemented:")
    print("  ✅ Orchestrator Agent (GPT-4/Claude)")
    print("  ✅ Frontend Agent (React/HTML/CSS)")
    print("  ✅ Backend Agent (APIs/Server Logic)")
    print("  ✅ Database Agent (Schema/Models)")
    print("  ✅ Testing Agent (Unit/Integration Tests)")
    print("  ✅ Documentation Agent (README/Docs)")
    print()
    
    print("🚀 Ready to Use:")
    print("  • Task planning and dependency resolution")
    print("  • Complete CLI interface")
    print("  • Configuration management")
    print("  • Dry-run mode for testing")
    print("  • API integration (OpenAI/Anthropic)")
    print("  • Local model support")
    print()
    
    print("📋 Try These Commands:")
    print()
    print("  # Validate your setup")
    print("  python main.py config --validate")
    print()
    print("  # List available agents")
    print("  python main.py agents")
    print()
    print("  # See execution plan (dry run)")
    print('  python main.py generate --spec "Create a simple web app" --output ./test --dry-run')
    print()
    print("  # Generate actual project (requires API key)")
    print('  python main.py generate --spec "Create a CLI tool" --output ./my-tool')
    print()
    
    print("🔧 Setup Requirements:")
    print("  1. Set API key: export OPENAI_API_KEY='your-key'")
    print("  2. Install deps: pip install -r requirements.txt")
    print("  3. Optional: pip install transformers torch (for local models)")
    print()
    
    print("📚 Documentation:")
    print("  • README.md - Quick start guide")
    print("  • INSTALL.md - Detailed installation")
    print("  • USAGE.md - Usage examples")
    print("  • STATUS.md - Implementation status")
    print("  • DESIGN.md - Original design document")
    print()
    
    print("🎯 System Status: MVP Complete and Ready!")
    print("=" * 60)
    
    # Quick system check
    try:
        from utils.config_loader import ConfigLoader
        config_loader = ConfigLoader("models/config.yaml")
        
        print(f"📊 Configuration: {len(config_loader.config.models)} models, {len(config_loader.config.agents)} agents")
        
        enabled_agents = config_loader.get_enabled_agents()
        print(f"🤖 Enabled Agents: {len(enabled_agents)} ({', '.join(enabled_agents)})")
        
        errors = config_loader.validate_config()
        if errors:
            print(f"⚠️  Config Issues: {len(errors)} warnings")
        else:
            print("✅ Configuration Valid")
            
    except Exception as e:
        print(f"❌ System Check Failed: {e}")
        return 1
    
    print()
    print("Ready to generate your next project! 🚀")
    return 0


if __name__ == "__main__":
    sys.exit(main())