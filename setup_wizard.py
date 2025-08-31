#!/usr/bin/env python3
"""
LLM Swarm Setup Wizard - Automated setup for the multi-agent system.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional

# Rich imports for better UI
try:
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("Installing rich for better UI...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.prompt import Prompt, Confirm
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

console = Console()


class SetupWizard:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.is_windows = platform.system() == "Windows"
        self.api_key = None
        self.api_provider = None
        self.install_local_models = False
        
    def welcome(self):
        """Display welcome message."""
        console.print(Panel.fit(
            "[bold blue]🚀 LLM Swarm Setup Wizard[/bold blue]\n\n"
            "This wizard will help you set up the multi-agent code generation system.\n"
            "It will:\n"
            "• Install required dependencies\n"
            "• Configure API keys\n"
            "• Set up local models (optional)\n"
            "• Validate your installation\n"
            "• Run a test generation",
            title="Welcome",
            border_style="blue"
        ))
        console.print()
        
    def check_python_version(self):
        """Check if Python version is compatible."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            console.print("[red]❌ Python 3.8+ is required. You have Python {}.{}.{}[/red]".format(
                version.major, version.minor, version.micro
            ))
            return False
        
        console.print(f"[green]✅ Python {version.major}.{version.minor}.{version.micro} - Compatible[/green]")
        return True
        
    def install_dependencies(self):
        """Install required dependencies."""
        console.print("\n[bold]📦 Installing Dependencies[/bold]")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            console.print("[red]❌ requirements.txt not found![/red]")
            return False
            
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Installing basic dependencies...", total=None)
            
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
                ], capture_output=True, text=True, check=True)
                
                progress.update(task, description="✅ Basic dependencies installed")
                console.print("[green]✅ Successfully installed basic dependencies[/green]")
                return True
                
            except subprocess.CalledProcessError as e:
                progress.update(task, description="❌ Failed to install dependencies")
                console.print(f"[red]❌ Failed to install dependencies: {e.stderr}[/red]")
                return False
                
    def setup_api_key(self):
        """Set up API key for the orchestrator."""
        console.print("\n[bold]🔑 API Key Setup[/bold]")
        console.print("The orchestrator needs an API key from either OpenAI or Anthropic.")
        
        # Check if keys already exist
        existing_openai = os.getenv("OPENAI_API_KEY")
        existing_anthropic = os.getenv("ANTHROPIC_API_KEY")
        
        if existing_openai:
            console.print(f"[green]✅ Found existing OpenAI API key: {existing_openai[:8]}...[/green]")
            if Confirm.ask("Use existing OpenAI key?"):
                self.api_provider = "openai"
                self.api_key = existing_openai
                return True
                
        if existing_anthropic:
            console.print(f"[green]✅ Found existing Anthropic API key: {existing_anthropic[:8]}...[/green]")
            if Confirm.ask("Use existing Anthropic key?"):
                self.api_provider = "anthropic"
                self.api_key = existing_anthropic
                return True
        
        # Ask user to choose provider
        console.print("\n[bold]Choose your API provider:[/bold]")
        console.print("1. OpenAI (GPT-4) - Recommended")
        console.print("2. Anthropic (Claude)")
        
        choice = Prompt.ask("Enter choice", choices=["1", "2"], default="1")
        
        if choice == "1":
            self.api_provider = "openai"
            console.print("\n[blue]Get your OpenAI API key from: https://platform.openai.com/api-keys[/blue]")
            self.api_key = Prompt.ask("Enter your OpenAI API key", password=True)
            
        else:
            self.api_provider = "anthropic"
            console.print("\n[blue]Get your Anthropic API key from: https://console.anthropic.com/[/blue]")
            self.api_key = Prompt.ask("Enter your Anthropic API key", password=True)
            
        # Set environment variable
        if self.api_key:
            if self.api_provider == "openai":
                os.environ["OPENAI_API_KEY"] = self.api_key
                env_var = "OPENAI_API_KEY"
            else:
                os.environ["ANTHROPIC_API_KEY"] = self.api_key
                env_var = "ANTHROPIC_API_KEY"
                
            console.print(f"[green]✅ API key set for this session[/green]")
            
            # Show how to make it permanent
            console.print(f"\n[yellow]💡 To make this permanent, add to your environment:[/yellow]")
            if self.is_windows:
                console.print(f"[dim]PowerShell: $env:{env_var} = \"{self.api_key}\"[/dim]")
                console.print(f"[dim]Command Prompt: set {env_var}={self.api_key}[/dim]")
            else:
                console.print(f"[dim]export {env_var}=\"{self.api_key}\"[/dim]")
                console.print(f"[dim]Add to ~/.bashrc or ~/.zshrc for persistence[/dim]")
                
            return True
            
        return False
        
    def setup_local_models(self):
        """Ask about local model setup."""
        console.print("\n[bold]🤖 Local Models Setup[/bold]")
        console.print("Local models can reduce API costs but require more system resources.")
        console.print("Recommended: 8GB+ RAM, GPU with CUDA support (optional)")
        
        self.install_local_models = Confirm.ask("Install local model support?", default=False)
        
        if self.install_local_models:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Installing transformers and PyTorch...", total=None)
                
                try:
                    # Install transformers and related packages
                    subprocess.run([
                        sys.executable, "-m", "pip", "install", 
                        "transformers", "torch", "accelerate", "bitsandbytes"
                    ], capture_output=True, text=True, check=True)
                    
                    progress.update(task, description="✅ Local model support installed")
                    console.print("[green]✅ Local model support installed successfully[/green]")
                    
                    # Update config to use better models
                    self.update_config_for_local_models()
                    
                except subprocess.CalledProcessError as e:
                    progress.update(task, description="❌ Failed to install local model support")
                    console.print(f"[yellow]⚠️  Local model installation failed: {e.stderr}[/yellow]")
                    console.print("[yellow]You can still use API-only mode[/yellow]")
                    self.install_local_models = False
                    
    def update_config_for_local_models(self):
        """Update configuration to use better local models."""
        config_file = self.project_root / "models" / "config.yaml"
        
        if not config_file.exists():
            return
            
        try:
            # Read current config
            with open(config_file, 'r') as f:
                content = f.read()
                
            # Replace the model ID with a better coding model
            updated_content = content.replace(
                'model_id: "microsoft/DialoGPT-medium"',
                'model_id: "codellama/CodeLlama-7b-Instruct-hf"'
            )
            
            # Write back
            with open(config_file, 'w') as f:
                f.write(updated_content)
                
            console.print("[green]✅ Updated configuration for better local models[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not update config: {e}[/yellow]")
            
    def update_config_for_anthropic(self):
        """Update configuration to use Anthropic if selected."""
        if self.api_provider != "anthropic":
            return
            
        config_file = self.project_root / "models" / "config.yaml"
        
        if not config_file.exists():
            return
            
        try:
            # Read current config
            with open(config_file, 'r') as f:
                content = f.read()
                
            # Update orchestrator to use Claude
            updated_content = content.replace(
                'model: "orchestrator"',
                'model: "orchestrator_claude"'
            )
            
            # Write back
            with open(config_file, 'w') as f:
                f.write(updated_content)
                
            console.print("[green]✅ Updated configuration for Anthropic Claude[/green]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not update config: {e}[/yellow]")
            
    def validate_installation(self):
        """Validate the installation."""
        console.print("\n[bold]🔍 Validating Installation[/bold]")
        
        tests = [
            ("Configuration validation", self.test_config),
            ("Agent initialization", self.test_agents),
            ("API connection", self.test_api_connection),
        ]
        
        results = []
        for test_name, test_func in tests:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"Testing {test_name}...", total=None)
                
                try:
                    success = test_func()
                    status = "✅ Passed" if success else "❌ Failed"
                    progress.update(task, description=f"{status} - {test_name}")
                    results.append((test_name, success))
                except Exception as e:
                    progress.update(task, description=f"❌ Error - {test_name}")
                    results.append((test_name, False))
                    console.print(f"[red]Error in {test_name}: {e}[/red]")
                    
        # Show results table
        table = Table(title="Validation Results")
        table.add_column("Test", style="cyan")
        table.add_column("Status", style="bold")
        
        all_passed = True
        for test_name, success in results:
            status = "[green]✅ Passed[/green]" if success else "[red]❌ Failed[/red]"
            table.add_row(test_name, status)
            if not success:
                all_passed = False
                
        console.print(table)
        return all_passed
        
    def test_config(self):
        """Test configuration validation."""
        try:
            result = subprocess.run([
                sys.executable, "main.py", "config", "--validate"
            ], cwd=self.project_root, capture_output=True, text=True)
            return result.returncode == 0
        except Exception:
            return False
            
    def test_agents(self):
        """Test agent listing."""
        try:
            result = subprocess.run([
                sys.executable, "main.py", "agents"
            ], cwd=self.project_root, capture_output=True, text=True)
            return result.returncode == 0 and "Frontend Agent" in result.stdout
        except Exception:
            return False
            
    def test_api_connection(self):
        """Test API connection with a simple dry run."""
        try:
            result = subprocess.run([
                sys.executable, "main.py", "generate", 
                "--spec", "Create a simple hello world script",
                "--output", "./test_setup",
                "--dry-run"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=60)
            return result.returncode == 0 and "Execution Plan" in result.stdout
        except Exception:
            return False
            
    def run_demo(self):
        """Run a demo generation."""
        console.print("\n[bold]🎯 Demo Generation[/bold]")
        
        if not Confirm.ask("Run a demo project generation?", default=True):
            return
            
        console.print("\n[blue]Generating a simple CLI tool as demonstration...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating demo project...", total=None)
            
            try:
                result = subprocess.run([
                    sys.executable, "main.py", "generate",
                    "--spec", "examples/simple-cli-spec.txt",
                    "--output", "./demo_output",
                    "--dry-run"
                ], cwd=self.project_root, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    progress.update(task, description="✅ Demo completed successfully")
                    console.print("[green]✅ Demo generation completed![/green]")
                    console.print(f"[dim]Check the output above for the execution plan[/dim]")
                else:
                    progress.update(task, description="❌ Demo failed")
                    console.print(f"[red]❌ Demo failed: {result.stderr}[/red]")
                    
            except subprocess.TimeoutExpired:
                progress.update(task, description="⏱️ Demo timed out")
                console.print("[yellow]⚠️  Demo timed out - this might indicate API issues[/yellow]")
            except Exception as e:
                progress.update(task, description="❌ Demo error")
                console.print(f"[red]❌ Demo error: {e}[/red]")
                
    def show_next_steps(self):
        """Show next steps to the user."""
        console.print("\n[bold green]🎉 Setup Complete![/bold green]")
        
        console.print(Panel.fit(
            "[bold]Next Steps:[/bold]\n\n"
            "1. Generate your first project:\n"
            "   [cyan]python main.py generate --spec \"Create a REST API\" --output ./my-api[/cyan]\n\n"
            "2. Try a dry run first:\n"
            "   [cyan]python main.py generate --spec \"Your idea\" --output ./test --dry-run[/cyan]\n\n"
            "3. Check the documentation:\n"
            "   • [cyan]README.md[/cyan] - Quick start guide\n"
            "   • [cyan]USAGE.md[/cyan] - Detailed usage examples\n"
            "   • [cyan]examples/[/cyan] - Sample project specifications\n\n"
            "4. Customize the system:\n"
            "   • Edit [cyan]models/config.yaml[/cyan] to adjust settings\n"
            "   • Add new agents or modify existing ones",
            title="Ready to Use!",
            border_style="green"
        ))
        
        if self.api_key and not os.getenv(f"{'OPENAI' if self.api_provider == 'openai' else 'ANTHROPIC'}_API_KEY"):
            console.print(f"\n[yellow]💡 Remember to set your API key permanently:[/yellow]")
            env_var = f"{'OPENAI' if self.api_provider == 'openai' else 'ANTHROPIC'}_API_KEY"
            if self.is_windows:
                console.print(f"[dim]$env:{env_var} = \"{self.api_key}\"[/dim]")
            else:
                console.print(f"[dim]export {env_var}=\"{self.api_key}\"[/dim]")
                
    def run(self):
        """Run the complete setup wizard."""
        self.welcome()
        
        # Check Python version
        if not self.check_python_version():
            return 1
            
        # Install dependencies
        if not self.install_dependencies():
            return 1
            
        # Setup API key
        if not self.setup_api_key():
            console.print("[red]❌ API key setup failed. Cannot continue.[/red]")
            return 1
            
        # Update config for Anthropic if needed
        self.update_config_for_anthropic()
        
        # Setup local models
        self.setup_local_models()
        
        # Validate installation
        if not self.validate_installation():
            console.print("[yellow]⚠️  Some validation tests failed, but you can still try using the system[/yellow]")
            
        # Run demo
        self.run_demo()
        
        # Show next steps
        self.show_next_steps()
        
        return 0


def main():
    """Main entry point."""
    wizard = SetupWizard()
    return wizard.run()


if __name__ == "__main__":
    sys.exit(main())