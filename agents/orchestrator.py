"""
Orchestrator agent for the LLM Swarm system.
Central controller that manages task planning and agent coordination.
"""

import json
import logging
import time
from typing import Dict, List, Any, Optional
from pathlib import Path

from utils.config_loader import ConfigLoader
from utils.dependency_graph import DependencyGraph, Task, TaskStatus, AgentType
from utils.file_manager import FileManager
from utils.prompt_templates import PromptTemplates
from .base_agent import AgentOutput
from .frontend_agent import FrontendAgent
from .backend_agent import BackendAgent
from .database_agent import DatabaseAgent
from .testing_agent import TestingAgent
from .documentation_agent import DocumentationAgent


class APIAgent:
    """
    Agent that uses API-based models (OpenAI, Anthropic, etc.)
    """
    
    def __init__(self, model_config):
        self.model_config = model_config
        self.logger = logging.getLogger(__name__)
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the API client based on model configuration."""
        try:
            if "gpt" in self.model_config.model_id.lower():
                # OpenAI client
                import openai
                import os
                
                api_key = os.getenv(self.model_config.api_key_env)
                if not api_key:
                    raise ValueError(f"API key not found in environment variable: {self.model_config.api_key_env}")
                
                self.client = openai.OpenAI(
                    api_key=api_key,
                    base_url=self.model_config.api_base
                )
                self.client_type = "openai"
                
            elif "claude" in self.model_config.model_id.lower():
                # Anthropic client
                import anthropic
                import os
                
                api_key = os.getenv(self.model_config.api_key_env)
                if not api_key:
                    raise ValueError(f"API key not found in environment variable: {self.model_config.api_key_env}")
                
                self.client = anthropic.Anthropic(
                    api_key=api_key,
                    base_url=self.model_config.api_base
                )
                self.client_type = "anthropic"
                
            else:
                raise ValueError(f"Unsupported API model: {self.model_config.model_id}")
                
            self.logger.info(f"Initialized {self.client_type} client for {self.model_config.model_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API client: {e}")
            raise
    
    def generate(self, prompt: str) -> str:
        """Generate response using the API model."""
        try:
            if self.client_type == "openai":
                response = self.client.chat.completions.create(
                    model=self.model_config.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.model_config.max_tokens,
                    temperature=self.model_config.temperature,
                    timeout=self.model_config.timeout
                )
                return response.choices[0].message.content
                
            elif self.client_type == "anthropic":
                response = self.client.messages.create(
                    model=self.model_config.model_id,
                    max_tokens=self.model_config.max_tokens,
                    temperature=self.model_config.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
                
        except Exception as e:
            self.logger.error(f"API generation failed: {e}")
            raise


class Orchestrator:
    """
    Central orchestrator that manages the multi-agent system.
    """
    
    def __init__(self, config_path: str, output_dir: str):
        """
        Initialize the orchestrator.
        
        Args:
            config_path: Path to configuration file
            output_dir: Directory for generated project
        """
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.config_loader = ConfigLoader(config_path)
        config_errors = self.config_loader.validate_config()
        if config_errors:
            for error in config_errors:
                self.logger.error(f"Config error: {error}")
            raise ValueError("Configuration validation failed")
        
        # Initialize components
        self.file_manager = FileManager(output_dir)
        self.dependency_graph = DependencyGraph()
        self.prompt_templates = PromptTemplates()
        
        # Initialize API agent for orchestrator
        orchestrator_config = self.config_loader.get_orchestrator_config()
        orchestrator_model_config = self.config_loader.get_model_config(orchestrator_config.model)
        self.api_agent = APIAgent(orchestrator_model_config)
        
        # Initialize SME agents
        self.agents = self._initialize_agents()
        
        # Track execution state
        self.project_context = {}
        self.execution_log = []
        
        self.logger.info("Orchestrator initialized successfully")
    
    def _initialize_agents(self) -> Dict[str, Any]:
        """Initialize all SME agents."""
        agents = {}
        
        agent_classes = {
            "frontend": FrontendAgent,
            "backend": BackendAgent,
            "database": DatabaseAgent,
            "testing": TestingAgent,
            "documentation": DocumentationAgent
        }
        
        for agent_name in self.config_loader.get_enabled_agents():
            agent_config = self.config_loader.get_agent_config(agent_name)
            model_config = self.config_loader.get_model_config(agent_config.model)
            
            if agent_config.agent_type in agent_classes:
                agent_class = agent_classes[agent_config.agent_type]
                
                try:
                    agent = agent_class(agent_config, model_config)
                    agents[agent_name] = agent
                    self.logger.info(f"Initialized agent: {agent_name}")
                except Exception as e:
                    self.logger.error(f"Failed to initialize agent {agent_name}: {e}")
            else:
                self.logger.warning(f"Unknown agent type: {agent_config.agent_type}")
        
        return agents
    
    def run(self, project_spec: str, dry_run: bool = False) -> bool:
        """
        Run the complete project generation process.
        
        Args:
            project_spec: Project specification
            dry_run: If True, only plan tasks without executing
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info("🚀 Starting project generation")
            
            # Store project specification
            self.project_context = {
                "description": project_spec,
                "start_time": time.time(),
                "dry_run": dry_run
            }
            
            # Step 1: Plan tasks
            self.logger.info("📋 Planning project tasks...")
            tasks = self.plan_tasks(project_spec)
            
            if not tasks:
                self.logger.error("No tasks generated from project specification")
                return False
            
            self.logger.info(f"Generated {len(tasks)} tasks")
            
            # Step 2: Build dependency graph
            for task in tasks:
                self.dependency_graph.add_task(task)
            
            # Validate dependencies
            validation_errors = self.dependency_graph.validate_dependencies()
            if validation_errors:
                for error in validation_errors:
                    self.logger.error(f"Dependency error: {error}")
                return False
            
            # Step 3: Execute tasks (unless dry run)
            if dry_run:
                self.logger.info("🔍 Dry run mode - showing execution plan:")
                self._show_execution_plan()
                return True
            else:
                success = self.execute_plan()
                
                if success:
                    self._finalize_project()
                
                return success
                
        except Exception as e:
            self.logger.error(f"Project generation failed: {e}")
            return False
    
    def plan_tasks(self, project_spec: str) -> List[Task]:
        """
        Plan tasks for the project using the orchestrator LLM.
        
        Args:
            project_spec: Project specification
            
        Returns:
            List of planned tasks
        """
        try:
            # Prepare planning prompt
            prompt = self.prompt_templates.render_template(
                "orchestrator_planning",
                project_spec=project_spec
            )
            
            # Generate plan using API model
            self.logger.debug("Sending planning request to orchestrator model...")
            response = self.api_agent.generate(prompt)
            
            # Parse response into tasks
            tasks = self._parse_task_plan(response)
            
            self.logger.info(f"Planned {len(tasks)} tasks")
            return tasks
            
        except Exception as e:
            self.logger.error(f"Task planning failed: {e}")
            return []
    
    def _parse_task_plan(self, response: str) -> List[Task]:
        """Parse the orchestrator's response into Task objects."""
        tasks = []
        
        try:
            # Look for JSON in the response
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                task_data = json.loads(json_str)
                
                for i, task_info in enumerate(task_data):
                    try:
                        # Map agent type string to enum
                        agent_type_str = task_info.get("agent_type", "backend")
                        agent_type = AgentType(agent_type_str)
                        
                        task = Task(
                            id=task_info.get("id", f"task_{i+1:03d}"),
                            name=task_info.get("name", f"Task {i+1}"),
                            description=task_info.get("description", ""),
                            agent_type=agent_type,
                            dependencies=task_info.get("dependencies", []),
                            priority=task_info.get("priority", 5)
                        )
                        
                        tasks.append(task)
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to parse task {i}: {e}")
                        continue
            
            else:
                self.logger.warning("No valid JSON found in planning response")
                # Fallback: create a simple default plan
                tasks = self._create_fallback_plan()
            
        except json.JSONDecodeError as e:
            self.logger.warning(f"JSON parsing failed: {e}")
            tasks = self._create_fallback_plan()
        
        return tasks
    
    def _create_fallback_plan(self) -> List[Task]:
        """Create a simple fallback plan if LLM planning fails."""
        return [
            Task(
                id="setup",
                name="Project Setup",
                description="Create basic project structure and configuration",
                agent_type=AgentType.BACKEND,
                dependencies=[],
                priority=10
            ),
            Task(
                id="database",
                name="Database Schema",
                description="Design and implement database schema",
                agent_type=AgentType.DATABASE,
                dependencies=["setup"],
                priority=9
            ),
            Task(
                id="backend",
                name="Backend Implementation",
                description="Implement server-side logic and APIs",
                agent_type=AgentType.BACKEND,
                dependencies=["database"],
                priority=8
            ),
            Task(
                id="frontend",
                name="Frontend Implementation", 
                description="Implement user interface and client-side logic",
                agent_type=AgentType.FRONTEND,
                dependencies=["backend"],
                priority=7
            ),
            Task(
                id="testing",
                name="Test Implementation",
                description="Create comprehensive test suite",
                agent_type=AgentType.TESTING,
                dependencies=["backend", "frontend"],
                priority=6
            ),
            Task(
                id="documentation",
                name="Documentation",
                description="Create project documentation and README",
                agent_type=AgentType.DOCUMENTATION,
                dependencies=["testing"],
                priority=5
            )
        ]
    
    def execute_plan(self) -> bool:
        """Execute the planned tasks."""
        try:
            execution_order = self.dependency_graph.get_execution_order()
            self.logger.info(f"Executing {len(execution_order)} tasks in order")
            
            completed_tasks = set()
            
            for i, task in enumerate(execution_order, 1):
                self.logger.info(f"📝 [{i}/{len(execution_order)}] Executing: {task.name}")
                
                # Find appropriate agent
                agent = self._get_agent_for_task(task)
                if not agent:
                    self.logger.error(f"No agent available for task: {task.name}")
                    task.mark_failed("No suitable agent found")
                    continue
                
                # Prepare task context with completed dependencies
                task.context["completed_dependencies"] = [
                    {
                        "name": dep_task.name,
                        "output_summary": dep_task.output.summary if dep_task.output else ""
                    }
                    for dep_id in task.dependencies
                    for dep_task in [self.dependency_graph.get_task(dep_id)]
                    if dep_task and dep_task.status == TaskStatus.COMPLETED
                ]
                
                # Execute task
                task.status = TaskStatus.IN_PROGRESS
                output = agent.run_task(task, self.project_context)
                
                if output.success:
                    # Save generated files
                    if output.files:
                        written_files = self.file_manager.write_files(output.files)
                        self.logger.info(f"Generated {len(written_files)} files")
                    
                    task.mark_completed(output)
                    completed_tasks.add(task.id)
                    
                    # Log execution
                    self.execution_log.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "agent": agent.name,
                        "status": "completed",
                        "files_generated": len(output.files),
                        "timestamp": time.time()
                    })
                    
                else:
                    task.mark_failed(output.error or "Unknown error")
                    self.logger.error(f"Task failed: {task.name} - {output.error}")
                    
                    # Log failure
                    self.execution_log.append({
                        "task_id": task.id,
                        "task_name": task.name,
                        "agent": agent.name,
                        "status": "failed",
                        "error": output.error,
                        "timestamp": time.time()
                    })
            
            # Check overall success
            status_summary = self.dependency_graph.get_status_summary()
            success = status_summary[TaskStatus.FAILED] == 0
            
            self.logger.info(f"Execution complete: {status_summary[TaskStatus.COMPLETED]} completed, {status_summary[TaskStatus.FAILED]} failed")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Plan execution failed: {e}")
            return False
    
    def _get_agent_for_task(self, task: Task):
        """Get the appropriate agent for a task."""
        # Map agent types to agent names
        agent_type_mapping = {
            AgentType.FRONTEND: "frontend",
            AgentType.BACKEND: "backend", 
            AgentType.DATABASE: "database",
            AgentType.TESTING: "testing",
            AgentType.DOCUMENTATION: "documentation"
        }
        
        agent_name = agent_type_mapping.get(task.agent_type)
        return self.agents.get(agent_name)
    
    def _show_execution_plan(self):
        """Show the execution plan for dry run mode."""
        execution_order = self.dependency_graph.get_execution_order()
        
        print("\n" + "="*60)
        print("EXECUTION PLAN")
        print("="*60)
        
        for i, task in enumerate(execution_order, 1):
            agent_name = self._get_agent_for_task(task)
            agent_name = agent_name.name if agent_name else "No Agent"
            
            print(f"\n{i:2d}. {task.name}")
            print(f"    ID: {task.id}")
            print(f"    Agent: {agent_name}")
            print(f"    Priority: {task.priority}")
            print(f"    Dependencies: {', '.join(task.dependencies) if task.dependencies else 'None'}")
            print(f"    Description: {task.description}")
        
        print("\n" + "="*60)
    
    def _finalize_project(self):
        """Finalize the generated project."""
        try:
            # Generate project summary
            summary = self._generate_project_summary()
            self.file_manager.write_file("PROJECT_SUMMARY.md", summary)
            
            # Generate execution log
            log_content = json.dumps(self.execution_log, indent=2)
            self.file_manager.write_file("generation_log.json", log_content)
            
            # Get project statistics
            size_info = self.file_manager.get_size_info()
            
            self.logger.info("✅ Project generation completed successfully!")
            self.logger.info(f"📊 Generated {size_info['file_count']} files ({size_info['total_size_mb']} MB)")
            self.logger.info(f"📁 Project location: {self.file_manager.output_dir}")
            
        except Exception as e:
            self.logger.error(f"Project finalization failed: {e}")
    
    def _generate_project_summary(self) -> str:
        """Generate a summary of the generated project."""
        status_summary = self.dependency_graph.get_status_summary()
        size_info = self.file_manager.get_size_info()
        
        summary = f"""# Project Generation Summary

## Overview
- **Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **Total Files**: {size_info['file_count']}
- **Total Size**: {size_info['total_size_mb']} MB
- **Tasks Completed**: {status_summary[TaskStatus.COMPLETED]}
- **Tasks Failed**: {status_summary[TaskStatus.FAILED]}

## Project Specification
{self.project_context.get('description', 'No description provided')}

## Generated Structure
"""
        
        # Add file structure
        structure = self.file_manager.get_project_structure()
        for directory, files in structure.items():
            if directory:
                summary += f"\n### {directory}/\n"
            else:
                summary += f"\n### Root Directory\n"
            
            for file in files:
                summary += f"- {file}\n"
        
        # Add agent statistics
        summary += "\n## Agent Performance\n"
        for agent_name, agent in self.agents.items():
            stats = agent.get_stats()
            summary += f"\n### {agent_name}\n"
            summary += f"- Tasks Completed: {stats['tasks_completed']}\n"
            summary += f"- Tasks Failed: {stats['tasks_failed']}\n"
            summary += f"- Average Execution Time: {stats['average_execution_time']:.2f}s\n"
        
        return summary