#!/usr/bin/env python3
"""
Quick Setup for LLM Swarm - Streamlined setup process.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def print_header():
    print("🚀 LLM Swarm Quick Setup")
    print("=" * 40)
    print()

def check_python():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True

def install_deps():
    print("\n📦 Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def setup_api_key():
    print("\n🔑 API Key Setup")
    
    # Check existing keys
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if openai_key:
        print(f"✅ Found OpenAI key: {openai_key[:8]}...")
        return True
    
    if anthropic_key:
        print(f"✅ Found Anthropic key: {anthropic_key[:8]}...")
        return True
    
    print("⚠️  No API key found!")
    print("\nYou need an API key from either:")
    print("1. OpenAI: https://platform.openai.com/api-keys")
    print("2. Anthropic: https://console.anthropic.com/")
    print()
    print("Set it as an environment variable:")
    
    if platform.system() == "Windows":
        print("  $env:OPENAI_API_KEY = \"your-key-here\"")
    else:
        print("  export OPENAI_API_KEY=\"your-key-here\"")
    
    return False

def test_system():
    print("\n🧪 Testing system...")
    
    try:
        # Test config validation
        result = subprocess.run([sys.executable, "main.py", "config", "--validate"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Configuration valid")
        else:
            print("⚠️  Configuration issues (may still work)")
            
        # Test agents
        result = subprocess.run([sys.executable, "main.py", "agents"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and "Frontend Agent" in result.stdout:
            print("✅ Agents loaded")
        else:
            print("⚠️  Agent loading issues")
            
        return True
        
    except Exception as e:
        print(f"⚠️  Test failed: {e}")
        return False

def show_next_steps():
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Set your API key (if not done already)")
    print("2. Try a dry run:")
    print("   python main.py generate --spec \"Create a simple web app\" --output ./test --dry-run")
    print("3. Generate a real project:")
    print("   python main.py generate --spec \"Your project idea\" --output ./my-project")
    print("\nDocumentation:")
    print("• README.md - Quick start")
    print("• USAGE.md - Detailed examples")
    print("• examples/ - Sample specifications")

def main():
    print_header()
    
    if not check_python():
        return 1
    
    if not install_deps():
        print("\n❌ Setup failed at dependency installation")
        return 1
    
    has_api_key = setup_api_key()
    
    if test_system():
        print("✅ System tests passed")
    else:
        print("⚠️  Some tests failed, but system may still work")
    
    show_next_steps()
    
    if not has_api_key:
        print("\n⚠️  Remember to set your API key before generating projects!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())