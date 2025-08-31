#!/usr/bin/env python3
"""
Main entry point for the LLM Swarm system.
Command-line interface for multi-agent code generation.
"""

import sys
import os
import argparse
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from agents.orchestrator import Orchestrator
from utils.logger import setup_logging
from utils.config_loader import ConfigLoader


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="LLM Swarm - Multi-Agent Code Generation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from project specification file
  llm-swarm generate --spec project.txt --output ./my-project

  # Generate with inline specification
  llm-swarm generate --spec "Create a REST API with user authentication" --output ./api-project

  # Dry run to see execution plan
  llm-swarm generate --spec project.txt --output ./test --dry-run

  # Use custom configuration
  llm-swarm generate --spec project.txt --output ./project --config custom-config.yaml

  # List available agents
  llm-swarm agents

  # Validate configuration
  llm-swarm config --validate
        """
    )
    
    parser.add_argument(
        "--version", 
        action="version", 
        version="LLM Swarm 0.1.0"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="models/config.yaml",
        help="Path to configuration file (default: models/config.yaml)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--log-file",
        type=str,
        help="Log file path (optional)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    generate_parser = subparsers.add_parser(
        "generate",
        help="Generate a project from specification"
    )
    generate_parser.add_argument(
        "--spec",
        type=str,
        required=True,
        help="Project specification (file path or inline text)"
    )
    generate_parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Output directory for generated project"
    )
    generate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show execution plan without generating code"
    )
    generate_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output directory"
    )
    
    # Agents command
    agents_parser = subparsers.add_parser(
        "agents",
        help="List available agents and their status"
    )
    
    # Config command
    config_parser = subparsers.add_parser(
        "config",
        help="Configuration management"
    )
    config_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate configuration file"
    )
    config_parser.add_argument(
        "--create-default",
        action="store_true",
        help="Create default configuration file"
    )
    
    return parser


def load_project_spec(spec_input: str) -> str:
    """
    Load project specification from file or return as-is if inline.
    
    Args:
        spec_input: File path or inline specification
        
    Returns:
        Project specification text
    """
    spec_path = Path(spec_input)
    
    if spec_path.exists() and spec_path.is_file():
        try:
            return spec_path.read_text(encoding="utf-8")
        except Exception as e:
            raise ValueError(f"Failed to read specification file {spec_path}: {e}")
    else:
        # Treat as inline specification
        return spec_input


def cmd_generate(args):
    """Handle the generate command."""
    try:
        # Load project specification
        project_spec = load_project_spec(args.spec)
        
        # Check output directory
        output_path = Path(args.output)
        if output_path.exists() and not args.force:
            if not args.dry_run:
                response = input(f"Output directory '{output_path}' exists. Overwrite? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("Generation cancelled.")
                    return 1
        
        # Initialize orchestrator
        print(f"🔧 Initializing orchestrator with config: {args.config}")
        orchestrator = Orchestrator(
            config_path=args.config,
            output_dir=str(output_path)
        )
        
        # Run generation
        if args.dry_run:
            print("🔍 Running in dry-run mode...")
        else:
            print("🚀 Starting project generation...")
        
        success = orchestrator.run(project_spec, dry_run=args.dry_run)
        
        if success:
            if args.dry_run:
                print("✅ Dry run completed successfully!")
            else:
                print("🎉 Project generated successfully!")
                print(f"📁 Output location: {output_path.absolute()}")
            return 0
        else:
            print("❌ Generation failed!")
            return 1
            
    except Exception as e:
        logging.error(f"Generation failed: {e}")
        return 1


def cmd_agents(args):
    """Handle the agents command."""
    try:
        config_loader = ConfigLoader(args.config)
        
        print("🤖 Available Agents")
        print("=" * 50)
        
        enabled_agents = config_loader.get_enabled_agents()
        
        for agent_name in config_loader.config.agents.keys():
            agent_config = config_loader.get_agent_config(agent_name)
            model_config = config_loader.get_model_config(agent_config.model)
            
            status = "✅ Enabled" if agent_name in enabled_agents else "❌ Disabled"
            model_type = model_config.type if model_config else "Unknown"
            model_id = model_config.model_id if model_config else "Unknown"
            
            print(f"\n{agent_config.name}")
            print(f"  Type: {agent_config.agent_type}")
            print(f"  Status: {status}")
            print(f"  Model: {agent_config.model} ({model_type})")
            print(f"  Model ID: {model_id}")
            print(f"  Max Retries: {agent_config.max_retries}")
        
        return 0
        
    except Exception as e:
        logging.error(f"Failed to list agents: {e}")
        return 1


def cmd_config(args):
    """Handle the config command."""
    try:
        if args.create_default:
            # Create default config
            config_path = Path(args.config)
            if config_path.exists():
                response = input(f"Config file '{config_path}' exists. Overwrite? (y/N): ")
                if response.lower() not in ['y', 'yes']:
                    print("Config creation cancelled.")
                    return 0
            
            # Force creation of default config
            config_path.parent.mkdir(parents=True, exist_ok=True)
            if config_path.exists():
                config_path.unlink()
            
            config_loader = ConfigLoader(str(config_path))
            print(f"✅ Created default configuration at: {config_path}")
            return 0
        
        elif args.validate:
            # Validate existing config
            config_loader = ConfigLoader(args.config)
            errors = config_loader.validate_config()
            
            if errors:
                print("❌ Configuration validation failed:")
                for error in errors:
                    print(f"  - {error}")
                return 1
            else:
                print("✅ Configuration is valid!")
                return 0
        
        else:
            # Show config info
            config_loader = ConfigLoader(args.config)
            
            print(f"📋 Configuration: {args.config}")
            print("=" * 50)
            
            print(f"Models: {len(config_loader.config.models)}")
            for name, model in config_loader.config.models.items():
                print(f"  - {name}: {model.model_id} ({model.type})")
            
            print(f"\nAgents: {len(config_loader.config.agents)}")
            enabled_count = len(config_loader.get_enabled_agents())
            print(f"  - Enabled: {enabled_count}")
            print(f"  - Disabled: {len(config_loader.config.agents) - enabled_count}")
            
            print(f"\nOrchestrator Model: {config_loader.config.orchestrator.model}")
            
            return 0
            
    except Exception as e:
        logging.error(f"Config command failed: {e}")
        return 1


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = getattr(logging, args.log_level)
    setup_logging(level=log_level, log_file=args.log_file)
    
    # Handle commands
    if args.command == "generate":
        return cmd_generate(args)
    elif args.command == "agents":
        return cmd_agents(args)
    elif args.command == "config":
        return cmd_config(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())