"""
Designer CLI

Command-line interface for the Designer LLM system.
"""

import click
import json
import os
from pathlib import Path
from typing import Optional

from .project_designer import ProjectDesigner
from ..utils.logger import setup_logger


@click.group()
def designer():
    """Designer LLM system for breaking down projects into specialized work chunks."""
    pass


@designer.command()
@click.option('--prompt', '-p', required=True, help='High-level description of what to build')
@click.option('--requirements', '-r', multiple=True, help='Additional requirements (can be used multiple times)')
@click.option('--constraints', '-c', multiple=True, help='Constraints or limitations (can be used multiple times)')
@click.option('--tech-stack', '-t', help='Preferred technology stack (JSON format)')
@click.option('--output', '-o', default='./design_output', help='Output directory for design files')
@click.option('--config', help='Path to configuration file')
def design(prompt: str, requirements: tuple, constraints: tuple, tech_stack: Optional[str], 
          output: str, config: Optional[str]):
    """
    Design a project from a high-level prompt.
    
    Example:
    python -m designer.cli design -p "Build a todo app with user authentication" -r "Must support mobile" -o ./my_design
    """
    logger = setup_logger(__name__)
    
    try:
        # Parse preferences
        preferences = {}
        if tech_stack:
            try:
                preferences['tech_stack'] = json.loads(tech_stack)
            except json.JSONDecodeError:
                logger.error("Invalid JSON format for tech-stack")
                return
        
        # Create designer
        designer = ProjectDesigner(config)
        
        # Run design process
        logger.info(f"Starting design process for: {prompt}")
        result = designer.design_project(
            prompt=prompt,
            requirements=list(requirements),
            constraints=list(constraints),
            preferences=preferences
        )
        
        # Save design
        designer.save_design(result, output)
        
        # Print summary
        click.echo(f"\n✅ Design Complete!")
        click.echo(f"📁 Output saved to: {output}")
        click.echo(f"📋 Project: {result.blueprint.project_name}")
        click.echo(f"🔧 Adapters needed: {len(result.adapter_plan.required_adapters)}")
        click.echo(f"📦 Work chunks: {len(result.work_plan.chunks)}")
        click.echo(f"⏱️  Estimated time: {result.adapter_plan.estimated_training_time}")
        
        # Show next steps
        click.echo(f"\n🚀 Next Steps:")
        click.echo(f"1. Review the design: {output}/design_result.json")
        click.echo(f"2. Train adapters: python -m designer.cli train-adapters {output}")
        click.echo(f"3. Execute work plan: python -m designer.cli execute {output}")
        
    except Exception as e:
        logger.error(f"Design failed: {e}")
        click.echo(f"❌ Design failed: {e}")


@designer.command()
@click.argument('design_path')
def show(design_path: str):
    """Show details of a design."""
    try:
        designer = ProjectDesigner()
        result = designer.load_design(design_path)
        
        if not result:
            click.echo(f"❌ No design found at {design_path}")
            return
        
        # Show design summary
        click.echo(f"\n📋 Project: {result.blueprint.project_name}")
        click.echo(f"📝 Description: {result.blueprint.description}")
        click.echo(f"🏗️  Architecture: {result.blueprint.architecture.get('pattern', 'unknown')}")
        click.echo(f"⚡ Complexity: {result.blueprint.estimated_complexity}")
        
        # Show tech stack
        click.echo(f"\n🛠️  Tech Stack:")
        for category, technologies in result.blueprint.tech_stack.items():
            click.echo(f"  {category}: {', '.join(technologies)}")
        
        # Show features
        click.echo(f"\n✨ Features ({len(result.blueprint.features)}):")
        for feature in result.blueprint.features:
            priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(feature.get('priority', 'medium'), "⚡")
            click.echo(f"  {priority_emoji} {feature.get('name', 'Unknown')}: {feature.get('description', 'No description')}")
        
        # Show adapters
        click.echo(f"\n🧠 Required Adapters ({len(result.adapter_plan.required_adapters)}):")
        for adapter in result.adapter_plan.required_adapters:
            priority_emoji = {"high": "🔥", "medium": "⚡", "low": "💡"}.get(adapter.get('priority', 'medium'), "⚡")
            click.echo(f"  {priority_emoji} {adapter.get('name', 'Unknown')}: {adapter.get('specialization', 'No description')}")
        
        # Show work chunks
        click.echo(f"\n📦 Work Chunks ({len(result.work_plan.chunks)}):")
        for chunk in result.work_plan.chunks:
            effort_emoji = {"small": "🟢", "medium": "🟡", "large": "🔴"}.get(chunk.get('estimated_effort', 'medium'), "🟡")
            click.echo(f"  {effort_emoji} {chunk.get('name', 'Unknown')}: {chunk.get('description', 'No description')}")
        
    except Exception as e:
        click.echo(f"❌ Error showing design: {e}")


@designer.command()
@click.argument('design_path')
@click.option('--adapter', '-a', help='Train specific adapter only')
@click.option('--force', '-f', is_flag=True, help='Force retrain existing adapters')
def train_adapters(design_path: str, adapter: Optional[str], force: bool):
    """Train LoRA adapters for a design."""
    try:
        designer = ProjectDesigner()
        result = designer.load_design(design_path)
        
        if not result:
            click.echo(f"❌ No design found at {design_path}")
            return
        
        # Import LoRA training system
        from ..lora.trainer import LoRATrainer
        from ..lora.dataset_curator import DatasetCurator
        
        trainer = LoRATrainer()
        curator = DatasetCurator()
        
        adapters_to_train = result.adapter_plan.required_adapters
        if adapter:
            adapters_to_train = [a for a in adapters_to_train if a['name'] == adapter]
            if not adapters_to_train:
                click.echo(f"❌ Adapter '{adapter}' not found in design")
                return
        
        click.echo(f"🚀 Training {len(adapters_to_train)} adapters...")
        
        for adapter_info in adapters_to_train:
            adapter_name = adapter_info['name']
            click.echo(f"\n🧠 Training adapter: {adapter_name}")
            
            # Create dataset if needed
            dataset_name = f"{adapter_name}_dataset"
            if not curator.dataset_exists(dataset_name) or force:
                click.echo(f"📊 Creating dataset: {dataset_name}")
                curator.create_dataset(
                    name=dataset_name,
                    domain=adapter_info['domain'],
                    data_types=adapter_info.get('training_data_types', [])
                )
            
            # Train adapter
            click.echo(f"⚡ Training adapter: {adapter_name}")
            trainer.train_adapter(
                adapter_name=adapter_name,
                dataset_name=dataset_name,
                base_model="microsoft/DialoGPT-medium",  # Default model
                force_retrain=force
            )
            
            click.echo(f"✅ Adapter {adapter_name} trained successfully")
        
        click.echo(f"\n🎉 All adapters trained successfully!")
        
    except Exception as e:
        click.echo(f"❌ Training failed: {e}")


@designer.command()
@click.argument('design_path')
@click.option('--chunk', '-c', help='Execute specific chunk only')
@click.option('--dry-run', '-d', is_flag=True, help='Show what would be executed without running')
def execute(design_path: str, chunk: Optional[str], dry_run: bool):
    """Execute the work plan for a design."""
    try:
        designer = ProjectDesigner()
        result = designer.load_design(design_path)
        
        if not result:
            click.echo(f"❌ No design found at {design_path}")
            return
        
        chunks_to_execute = result.work_plan.chunks
        if chunk:
            chunks_to_execute = [c for c in chunks_to_execute if c['id'] == chunk]
            if not chunks_to_execute:
                click.echo(f"❌ Chunk '{chunk}' not found in work plan")
                return
        
        if dry_run:
            click.echo(f"🔍 Dry run - would execute {len(chunks_to_execute)} chunks:")
            for chunk_info in chunks_to_execute:
                click.echo(f"  📦 {chunk_info['name']} (adapter: {chunk_info.get('adapter_required', 'unknown')})")
            return
        
        # Import execution system
        from ..agents.orchestrator import Orchestrator
        
        orchestrator = Orchestrator()
        
        click.echo(f"🚀 Executing {len(chunks_to_execute)} work chunks...")
        
        # Create project directory
        project_dir = os.path.join(design_path, 'generated_project')
        os.makedirs(project_dir, exist_ok=True)
        
        for chunk_info in chunks_to_execute:
            chunk_name = chunk_info['name']
            adapter_required = chunk_info.get('adapter_required', 'general')
            
            click.echo(f"\n📦 Executing chunk: {chunk_name}")
            click.echo(f"🧠 Using adapter: {adapter_required}")
            
            # Execute chunk (this would integrate with the existing orchestrator)
            # For now, just create placeholder files
            for file_path in chunk_info.get('scope', []):
                full_path = os.path.join(project_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                with open(full_path, 'w') as f:
                    f.write(f"# {chunk_name}\n")
                    f.write(f"# Generated by adapter: {adapter_required}\n")
                    f.write(f"# Description: {chunk_info.get('description', 'No description')}\n\n")
                    f.write("# TODO: Implement this chunk\n")
            
            click.echo(f"✅ Chunk {chunk_name} completed")
        
        click.echo(f"\n🎉 Execution complete! Project generated in: {project_dir}")
        
    except Exception as e:
        click.echo(f"❌ Execution failed: {e}")


@designer.command()
def list_designs():
    """List all available designs."""
    try:
        current_dir = Path('.')
        design_dirs = []
        
        for item in current_dir.iterdir():
            if item.is_dir() and (item / 'design_result.json').exists():
                design_dirs.append(item)
        
        if not design_dirs:
            click.echo("📭 No designs found in current directory")
            return
        
        click.echo(f"📋 Found {len(design_dirs)} designs:")
        
        for design_dir in design_dirs:
            try:
                designer = ProjectDesigner()
                result = designer.load_design(str(design_dir))
                
                if result:
                    click.echo(f"  📁 {design_dir.name}: {result.blueprint.project_name}")
                    click.echo(f"     📝 {result.blueprint.description[:80]}...")
                    click.echo(f"     🧠 {len(result.adapter_plan.required_adapters)} adapters, {len(result.work_plan.chunks)} chunks")
                else:
                    click.echo(f"  📁 {design_dir.name}: (invalid design)")
            except Exception:
                click.echo(f"  📁 {design_dir.name}: (error loading)")
        
    except Exception as e:
        click.echo(f"❌ Error listing designs: {e}")


if __name__ == '__main__':
    designer()