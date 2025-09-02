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
    
    # Learning command
    learning_parser = subparsers.add_parser(
        "learning",
        help="Adaptive learning system management"
    )
    learning_subparsers = learning_parser.add_subparsers(dest="learning_command", help="Learning commands")
    
    # Learning status
    learning_subparsers.add_parser(
        "status",
        help="Show learning system status"
    )
    
    # Run learning cycle
    cycle_parser = learning_subparsers.add_parser(
        "cycle",
        help="Run adaptive learning cycle"
    )
    cycle_parser.add_argument(
        "--force",
        action="store_true",
        help="Force learning even if conditions aren't met"
    )
    
    # Train specific agent
    train_parser = learning_subparsers.add_parser(
        "train",
        help="Train specific agent"
    )
    train_parser.add_argument(
        "agent_type",
        choices=["frontend", "backend", "database", "testing", "documentation"],
        help="Agent type to train"
    )
    
    # View feedback
    learning_subparsers.add_parser(
        "feedback",
        help="View collected feedback data"
    )
    
    # Designer command
    designer_parser = subparsers.add_parser(
        "design",
        help="Designer LLM system for breaking down projects"
    )
    designer_subparsers = designer_parser.add_subparsers(dest="design_command", help="Designer commands")
    
    # Design project
    design_project_parser = designer_subparsers.add_parser(
        "project",
        help="Design a project from high-level prompt"
    )
    design_project_parser.add_argument(
        "--prompt", "-p",
        required=True,
        help="High-level description of what to build"
    )
    design_project_parser.add_argument(
        "--requirements", "-r",
        action="append",
        help="Additional requirements (can be used multiple times)"
    )
    design_project_parser.add_argument(
        "--constraints", "-c",
        action="append", 
        help="Constraints or limitations (can be used multiple times)"
    )
    design_project_parser.add_argument(
        "--tech-stack", "-t",
        help="Preferred technology stack (JSON format)"
    )
    design_project_parser.add_argument(
        "--output", "-o",
        default="./design_output",
        help="Output directory for design files"
    )
    
    # Show design
    show_design_parser = designer_subparsers.add_parser(
        "show",
        help="Show details of a design"
    )
    show_design_parser.add_argument(
        "design_path",
        help="Path to design directory"
    )
    
    # Train adapters
    train_adapters_parser = designer_subparsers.add_parser(
        "train-adapters",
        help="Train LoRA adapters for a design"
    )
    train_adapters_parser.add_argument(
        "design_path",
        help="Path to design directory"
    )
    train_adapters_parser.add_argument(
        "--adapter", "-a",
        help="Train specific adapter only"
    )
    train_adapters_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force retrain existing adapters"
    )
    
    # Execute design
    execute_design_parser = designer_subparsers.add_parser(
        "execute",
        help="Execute the work plan for a design"
    )
    execute_design_parser.add_argument(
        "design_path",
        help="Path to design directory"
    )
    execute_design_parser.add_argument(
        "--chunk", "-c",
        help="Execute specific chunk only"
    )
    execute_design_parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Show what would be executed without running"
    )
    
    # List designs
    designer_subparsers.add_parser(
        "list",
        help="List all available designs"
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


def cmd_learning(args):
    """Handle learning command."""
    try:
        # Import learning system
        try:
            from learning.learning_manager import LearningManager
            from utils.dependency_graph import AgentType
        except ImportError as e:
            print(f"❌ Learning system not available: {e}")
            print("Make sure all learning dependencies are installed.")
            return 1
        
        # Initialize learning manager
        learning_manager = LearningManager()
        
        if args.learning_command == "status":
            # Show learning system status
            print("🧠 Adaptive Learning System Status")
            print("=" * 50)
            
            status = learning_manager.get_learning_status()
            
            print(f"Auto Learning: {'✅ Enabled' if status['auto_learning_enabled'] else '❌ Disabled'}")
            print(f"System Ready: {'✅ Yes' if status['system_ready'] else '❌ No'}")
            print(f"Total Projects: {status['total_feedback_projects']}")
            
            if status['last_learning_cycle']:
                print(f"Last Cycle: {status['last_learning_cycle']}")
            else:
                print("Last Cycle: Never")
            
            if status['next_learning_cycle']:
                print(f"Next Cycle: {status['next_learning_cycle']}")
            
            print("\nAgent Metrics:")
            for agent_name, metrics in status['agent_metrics'].items():
                print(f"  {agent_name}:")
                print(f"    Tasks: {metrics['total_tasks']} (Success: {metrics['success_rate']:.1%})")
                print(f"    Avg Time: {metrics['average_time']:.2f}s")
            
            print("\nLearning Opportunities:")
            for agent_name, opportunity in status['learning_opportunities'].items():
                ready = "✅" if opportunity['ready_for_training'] else "❌"
                print(f"  {agent_name}: {ready} ({opportunity['samples_available']} samples)")
                if 'reason' in opportunity:
                    print(f"    Reason: {opportunity['reason']}")
            
            return 0
        
        elif args.learning_command == "cycle":
            # Run learning cycle
            print("🚀 Running adaptive learning cycle...")
            
            results = learning_manager.run_learning_cycle(force=args.force)
            
            print(f"Status: {results['status']}")
            
            if results['status'] == 'completed':
                print(f"Agents Analyzed: {results['agents_analyzed']}")
                print(f"Agents Trained: {results['agents_trained']}")
                print(f"New Adapters: {len(results['new_adapters'])}")
                print(f"Deployed Adapters: {len(results['deployed_adapters'])}")
                print(f"Duration: {results['duration']:.2f}s")
                
                if results['new_adapters']:
                    print("\nNew Adapters Created:")
                    for adapter in results['new_adapters']:
                        print(f"  - {adapter}")
                
                if results['errors']:
                    print("\nErrors:")
                    for error in results['errors']:
                        print(f"  - {error}")
            
            elif results['status'] == 'skipped':
                print(f"Reason: {results['reason']}")
                if 'next_cycle' in results:
                    print(f"Next Cycle: {results['next_cycle']}")
            
            else:
                print(f"Error: {results.get('error', 'Unknown error')}")
                return 1
            
            return 0
        
        elif args.learning_command == "train":
            # Train specific agent
            agent_type_map = {
                'frontend': AgentType.FRONTEND,
                'backend': AgentType.BACKEND,
                'database': AgentType.DATABASE,
                'testing': AgentType.TESTING,
                'documentation': AgentType.DOCUMENTATION
            }
            
            agent_type = agent_type_map[args.agent_type]
            
            print(f"🎯 Training {args.agent_type} agent...")
            
            results = learning_manager.force_learning_for_agent(agent_type)
            
            if results['status'] == 'success':
                print(f"✅ Training completed successfully!")
                print(f"New Adapter: {results['adapter_name']}")
            else:
                print(f"❌ Training failed: {results['error']}")
                return 1
            
            return 0
        
        elif args.learning_command == "feedback":
            # View feedback data
            print("📊 Feedback Data Summary")
            print("=" * 50)
            
            # Get project feedback count
            project_count = learning_manager.feedback_collector._count_feedback_projects()
            print(f"Total Projects: {project_count}")
            
            # Get agent metrics
            agent_metrics = learning_manager.feedback_collector.get_agent_metrics()
            
            if agent_metrics:
                print("\nAgent Performance:")
                for agent_name, metrics in agent_metrics.items():
                    print(f"  {agent_name}:")
                    print(f"    Total Tasks: {metrics['total_tasks']}")
                    print(f"    Success Rate: {metrics['success_rate']:.1%}")
                    print(f"    Average Time: {metrics['average_time']:.2f}s")
                    print(f"    Last Updated: {metrics['last_updated']}")
            else:
                print("No agent metrics available yet.")
            
            # Show learning opportunities
            opportunities = learning_manager.adaptive_trainer.analyze_learning_opportunities()
            
            print("\nLearning Readiness:")
            for agent_name, opportunity in opportunities.items():
                status = "Ready" if opportunity['ready_for_training'] else "Not Ready"
                print(f"  {agent_name}: {status}")
                print(f"    Samples: {opportunity['samples_available']}")
                if 'high_quality_samples' in opportunity:
                    print(f"    High Quality: {opportunity['high_quality_samples']}")
                if 'recommended_action' in opportunity:
                    print(f"    Action: {opportunity['recommended_action']}")
            
            return 0
        
        else:
            print("❌ Unknown learning command")
            return 1
            
    except Exception as e:
        logging.error(f"Learning command failed: {e}")
        return 1


def cmd_design(args):
    """Handle design command."""
    try:
        from designer.project_designer import ProjectDesigner
        import json
        
        if args.design_command == "project":
            # Design a new project
            preferences = {}
            if args.tech_stack:
                try:
                    preferences['tech_stack'] = json.loads(args.tech_stack)
                except json.JSONDecodeError:
                    print("❌ Invalid JSON format for tech-stack")
                    return 1
            
            designer = ProjectDesigner(args.config)
            
            print(f"🎯 Starting design process for: {args.prompt}")
            result = designer.design_project(
                prompt=args.prompt,
                requirements=args.requirements or [],
                constraints=args.constraints or [],
                preferences=preferences
            )
            
            designer.save_design(result, args.output)
            
            print(f"\n✅ Design Complete!")
            print(f"📁 Output saved to: {args.output}")
            print(f"📋 Project: {result.blueprint.project_name}")
            print(f"🔧 Adapters needed: {len(result.adapter_plan.required_adapters)}")
            print(f"📦 Work chunks: {len(result.work_plan.chunks)}")
            print(f"⏱️  Estimated time: {result.adapter_plan.estimated_training_time}")
            
            print(f"\n🚀 Next Steps:")
            print(f"1. Review the design: {args.output}/design_result.json")
            print(f"2. Train adapters: python main.py design train-adapters {args.output}")
            print(f"3. Execute work plan: python main.py design execute {args.output}")
            
            return 0
        
        elif args.design_command == "show":
            # Show design details
            designer = ProjectDesigner()
            result = designer.load_design(args.design_path)
            
            if not result:
                print(f"❌ No design found at {args.design_path}")
                return 1
            
            print(f"\n📋 Project: {result.blueprint.project_name}")
            print(f"📝 Description: {result.blueprint.description}")
            print(f"🏗️  Architecture: {result.blueprint.architecture.get('pattern', 'unknown')}")
            print(f"⚡ Complexity: {result.blueprint.estimated_complexity}")
            
            print(f"\n🛠️  Tech Stack:")
            for category, technologies in result.blueprint.tech_stack.items():
                print(f"  {category}: {', '.join(technologies)}")
            
            print(f"\n✨ Features ({len(result.blueprint.features)}):")
            for feature in result.blueprint.features:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(feature.get('priority', 'medium'), "⚡")
                print(f"  {priority_emoji} {feature.get('name', 'Unknown')}: {feature.get('description', 'No description')}")
            
            print(f"\n🧠 Required Adapters ({len(result.adapter_plan.required_adapters)}):")
            for adapter in result.adapter_plan.required_adapters:
                priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(adapter.get('priority', 'medium'), "⚡")
                print(f"  {priority_emoji} {adapter.get('name', 'Unknown')}: {adapter.get('specialization', 'No description')}")
            
            print(f"\n📦 Work Chunks ({len(result.work_plan.chunks)}):")
            for chunk in result.work_plan.chunks:
                effort_emoji = {"small": "🟢", "medium": "🟡", "large": "🔴"}.get(chunk.get('estimated_effort', 'medium'), "🟡")
                print(f"  {effort_emoji} {chunk.get('name', 'Unknown')}: {chunk.get('description', 'No description')}")
            
            return 0
        
        elif args.design_command == "train-adapters":
            # Train adapters for design
            designer = ProjectDesigner()
            result = designer.load_design(args.design_path)
            
            if not result:
                print(f"❌ No design found at {args.design_path}")
                return 1
            
            from lora.trainer import LoRATrainer
            from lora.dataset_curator import DatasetCurator
            
            trainer = LoRATrainer()
            curator = DatasetCurator()
            
            adapters_to_train = result.adapter_plan.required_adapters
            if args.adapter:
                adapters_to_train = [a for a in adapters_to_train if a['name'] == args.adapter]
                if not adapters_to_train:
                    print(f"❌ Adapter '{args.adapter}' not found in design")
                    return 1
            
            print(f"🚀 Training {len(adapters_to_train)} adapters...")
            
            for adapter_info in adapters_to_train:
                adapter_name = adapter_info['name']
                print(f"\n🧠 Training adapter: {adapter_name}")
                
                dataset_name = f"{adapter_name}_dataset"
                if not curator.dataset_exists(dataset_name) or args.force:
                    print(f"📊 Creating dataset: {dataset_name}")
                    curator.create_dataset(
                        name=dataset_name,
                        domain=adapter_info['domain'],
                        data_types=adapter_info.get('training_data_types', [])
                    )
                
                print(f"⚡ Training adapter: {adapter_name}")
                trainer.train_adapter(
                    adapter_name=adapter_name,
                    dataset_name=dataset_name,
                    base_model="microsoft/DialoGPT-medium",
                    force_retrain=args.force
                )
                
                print(f"✅ Adapter {adapter_name} trained successfully")
            
            print(f"\n🎉 All adapters trained successfully!")
            return 0
        
        elif args.design_command == "execute":
            # Execute work plan using enhanced execution system
            from designer.chunk_executor import ChunkExecutor
            
            # Load configuration
            config_loader = ConfigLoader(args.config)
            
            designer = ProjectDesigner()
            result = designer.load_design(args.design_path)
            
            if not result:
                print(f"❌ No design found at {args.design_path}")
                return 1
            
            # Filter chunks if specific chunk requested
            work_plan = result.work_plan
            if args.chunk:
                filtered_chunks = [c for c in work_plan.chunks if c['id'] == args.chunk]
                if not filtered_chunks:
                    print(f"❌ Chunk '{args.chunk}' not found in work plan")
                    return 1
                # Create a new work plan with filtered chunks
                from designer.models import WorkPlan
                work_plan = WorkPlan(
                    chunks=filtered_chunks,
                    execution_order=[args.chunk],
                    dependencies={},
                    estimated_duration=work_plan.estimated_duration
                )
            
            if args.dry_run:
                print(f"🔍 Dry run - would execute {len(work_plan.chunks)} chunks:")
                executor = ChunkExecutor(config_loader.config)
                dry_results = executor.execute_chunks(
                    work_plan, result.blueprint, result.context_serialization,
                    output_dir="", dry_run=True
                )
                
                for chunk_id, chunk_result in dry_results['results'].items():
                    print(f"  📦 {chunk_result['chunk_name']} (agent: {chunk_result['agent_type']})")
                    if chunk_result.get('files_to_generate'):
                        print(f"    📄 Files: {', '.join(chunk_result['files_to_generate'])}")
                return 0
            
            print(f"🚀 Executing {len(work_plan.chunks)} work chunks with specialized agents...")
            
            project_dir = os.path.join(args.design_path, 'generated_project')
            
            # Use enhanced execution system
            executor = ChunkExecutor(config_loader.config)
            execution_results = executor.execute_chunks(
                work_plan, result.blueprint, result.context_serialization,
                project_dir, dry_run=False
            )
            
            # Display results
            print(f"\n📊 Execution Summary:")
            print(f"  ✅ Successful chunks: {execution_results['successful_chunks']}")
            print(f"  ❌ Failed chunks: {execution_results['failed_chunks']}")
            print(f"  📁 Output directory: {execution_results['output_directory']}")
            
            # Show detailed results
            for chunk_id, result_info in execution_results['results'].items():
                if result_info['success']:
                    files = result_info.get('files_generated', [])
                    print(f"  ✅ {chunk_id}: Generated {len(files)} files")
                else:
                    print(f"  ❌ {chunk_id}: {result_info.get('error', 'Unknown error')}")
            
            if execution_results['failed_chunks'] == 0:
                print(f"\n🎉 All chunks executed successfully! Project generated in: {project_dir}")
                return 0
            else:
                print(f"\n⚠️  Execution completed with {execution_results['failed_chunks']} failures.")
                return 1
        
        elif args.design_command == "list":
            # List designs
            from pathlib import Path
            
            current_dir = Path('.')
            design_dirs = []
            
            for item in current_dir.iterdir():
                if item.is_dir() and (item / 'design_result.json').exists():
                    design_dirs.append(item)
            
            if not design_dirs:
                print("📭 No designs found in current directory")
                return 0
            
            print(f"📋 Found {len(design_dirs)} designs:")
            
            for design_dir in design_dirs:
                try:
                    designer = ProjectDesigner()
                    result = designer.load_design(str(design_dir))
                    
                    if result:
                        print(f"  📁 {design_dir.name}: {result.blueprint.project_name}")
                        print(f"     📝 {result.blueprint.description[:80]}...")
                        print(f"     🧠 {len(result.adapter_plan.required_adapters)} adapters, {len(result.work_plan.chunks)} chunks")
                    else:
                        print(f"  📁 {design_dir.name}: (invalid design)")
                except Exception:
                    print(f"  📁 {design_dir.name}: (error loading)")
            
            return 0
        
        else:
            print("❌ Unknown design command")
            return 1
            
    except Exception as e:
        logging.error(f"Design command failed: {e}")
        print(f"❌ Design command failed: {e}")
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
    elif args.command == "learning":
        return cmd_learning(args)
    elif args.command == "design":
        return cmd_design(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())