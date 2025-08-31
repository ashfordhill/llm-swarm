#!/usr/bin/env python3
"""
LLM Swarm Setup Checker - Quick diagnostic and setup guide.
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def print_status(message, status):
    """Print a status message with emoji."""
    emoji = "✅" if status else "❌"
    print(f"{emoji} {message}")

def check_python():
    """Check Python version."""
    version = sys.version_info
    compatible = version.major >= 3 and version.minor >= 8
    print_status(f"Python {version.major}.{version.minor}.{version.micro}", compatible)
    return compatible

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "openai", "anthropic", "yaml", "jinja2", "rich", "click"
    ]
    
    missing = []
    for package in required_packages:
        try:
            importlib.import_module(package)
            print_status(f"Package: {package}", True)
        except ImportError:
            print_status(f"Package: {package}", False)
            missing.append(package)
    
    return missing

def check_api_keys():
    """Check for API keys."""
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    print_status(f"OpenAI API Key", bool(openai_key))
    print_status(f"Anthropic API Key", bool(anthropic_key))
    
    return bool(openai_key or anthropic_key)

def check_config():
    """Check if configuration file exists."""
    config_file = Path("models/config.yaml")
    exists = config_file.exists()
    print_status("Configuration file", exists)
    return exists

def test_basic_functionality():
    """Test basic system functionality."""
    try:
        result = subprocess.run([
            sys.executable, "main.py", "--version"
        ], capture_output=True, text=True, timeout=5)
        
        working = result.returncode == 0
        print_status("Basic CLI functionality", working)
        return working
        
    except Exception:
        print_status("Basic CLI functionality", False)
        return False

def main():
    print("🔍 LLM Swarm Setup Checker")
    print("=" * 40)
    print()
    
    # Check Python
    print("🐍 Python Environment:")
    python_ok = check_python()
    print()
    
    # Check dependencies
    print("📦 Dependencies:")
    missing_deps = check_dependencies()
    print()
    
    # Check API keys
    print("🔑 API Keys:")
    has_api_key = check_api_keys()
    print()
    
    # Check config
    print("⚙️  Configuration:")
    has_config = check_config()
    print()
    
    # Test functionality
    print("🧪 System Test:")
    system_works = test_basic_functionality()
    print()
    
    # Summary and instructions
    print("📋 Setup Status:")
    print("=" * 40)
    
    if not python_ok:
        print("❌ CRITICAL: Upgrade to Python 3.8+")
        return 1
    
    if missing_deps:
        print("📦 INSTALL DEPENDENCIES:")
        print("   pip install -r requirements.txt")
        print()
    
    if not has_api_key:
        print("🔑 SET API KEY:")
        print("   Get a key from:")
        print("   • OpenAI: https://platform.openai.com/api-keys")
        print("   • Anthropic: https://console.anthropic.com/")
        print()
        print("   Then set environment variable:")
        if os.name == 'nt':  # Windows
            print("   $env:OPENAI_API_KEY = \"your-key-here\"")
        else:
            print("   export OPENAI_API_KEY=\"your-key-here\"")
        print()
    
    if not has_config:
        print("⚙️  CREATE CONFIG:")
        print("   python main.py config --create-default")
        print()
    
    # Final status
    ready = python_ok and not missing_deps and has_api_key and has_config
    
    if ready:
        print("🎉 READY TO USE!")
        print("Try this command:")
        print("   python main.py generate --spec \"Create a simple CLI tool\" --output ./test --dry-run")
    else:
        print("⚠️  SETUP NEEDED")
        print("Complete the steps above, then run this checker again.")
    
    print()
    print("📚 Documentation:")
    print("   • README.md - Quick start guide")
    print("   • INSTALL.md - Detailed installation")
    print("   • USAGE.md - Usage examples")
    
    return 0 if ready else 1

if __name__ == "__main__":
    sys.exit(main())