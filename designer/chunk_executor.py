"""
Chunk Executor - Enhanced execution system for work chunks

Connects the Designer LLM System to actual specialized agents for code generation.
This is the core of Phase 2: Enhanced Adapter Execution.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import asdict

from utils.dependency_graph import Task, TaskStatus, AgentType
from agents.frontend_agent import FrontendAgent
from agents.backend_agent import BackendAgent
from agents.database_agent import DatabaseAgent
from agents.testing_agent import TestingAgent
from agents.documentation_agent import DocumentationAgent
from utils.config_loader import AgentConfig, ModelConfig
from .models import WorkPlan, ProjectBlueprint


class ChunkExecutor:
    """
    Executes work chunks using specialized agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize agent mapping
        self.agent_mapping = {
            'frontend': AgentType.FRONTEND,
            'backend': AgentType.BACKEND,
            'database': AgentType.DATABASE,
            'testing': AgentType.TESTING,
            'documentation': AgentType.DOCUMENTATION,
        }
        
        # Agent class mapping
        self.agent_classes = {
            AgentType.FRONTEND: FrontendAgent,
            AgentType.BACKEND: BackendAgent,
            AgentType.DATABASE: DatabaseAgent,
            AgentType.TESTING: TestingAgent,
            AgentType.DOCUMENTATION: DocumentationAgent,
        }
        
        # Cache for initialized agents
        self.agents_cache = {}
    
    def execute_chunks(self, work_plan: WorkPlan, blueprint: ProjectBlueprint, 
                      context_serialization: Dict[str, Any], output_dir: str,
                      dry_run: bool = False) -> Dict[str, Any]:
        """
        Execute all work chunks using specialized agents
        """
        self.logger.info(f"Executing {len(work_plan.chunks)} work chunks...")
        
        if dry_run:
            return self._dry_run_execution(work_plan.chunks)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert chunks to tasks
        tasks = self._convert_chunks_to_tasks(work_plan.chunks, blueprint, context_serialization)
        
        # Execute tasks in dependency order
        execution_results = {}
        for task in self._sort_tasks_by_dependencies(tasks):
            result = self._execute_task(task, output_dir, execution_results)
            execution_results[task.id] = result
        
        return {
            'total_chunks': len(work_plan.chunks),
            'successful_chunks': sum(1 for r in execution_results.values() if r['success']),
            'failed_chunks': sum(1 for r in execution_results.values() if not r['success']),
            'results': execution_results,
            'output_directory': output_dir
        }
    
    def _dry_run_execution(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulate execution for dry run"""
        results = {}
        for chunk in chunks:
            agent_type = self._determine_agent_type(chunk)
            results[chunk['id']] = {
                'chunk_name': chunk['name'],
                'agent_type': agent_type.value if agent_type else 'unknown',
                'adapter_required': chunk.get('adapter_required', 'general'),
                'files_to_generate': chunk.get('scope', []),
                'dry_run': True
            }
        
        return {
            'total_chunks': len(chunks),
            'dry_run': True,
            'results': results
        }
    
    def _convert_chunks_to_tasks(self, chunks: List[Dict[str, Any]], 
                                blueprint: ProjectBlueprint,
                                context_serialization: Dict[str, Any]) -> List[Task]:
        """Convert work chunks to Task objects"""
        tasks = []
        
        for chunk in chunks:
            agent_type = self._determine_agent_type(chunk)
            if not agent_type:
                self.logger.warning(f"Could not determine agent type for chunk: {chunk['name']}")
                agent_type = AgentType.BACKEND  # Default fallback
            
            # Create context for this specific chunk
            chunk_context = self._create_chunk_context(chunk, blueprint, context_serialization)
            
            task = Task(
                id=chunk['id'],
                name=chunk['name'],
                description=chunk.get('description', ''),
                agent_type=agent_type,
                dependencies=chunk.get('dependencies', []),
                context=chunk_context,
                priority=self._calculate_priority(chunk),
                estimated_duration=self._estimate_duration(chunk)
            )
            
            tasks.append(task)
        
        return tasks
    
    def _determine_agent_type(self, chunk: Dict[str, Any]) -> Optional[AgentType]:
        """Determine which agent type should handle this chunk"""
        adapter_required = chunk.get('adapter_required', '').lower()
        chunk_name = chunk.get('name', '').lower()
        description = chunk.get('description', '').lower()
        scope = chunk.get('scope', [])
        
        # Check adapter name first
        if 'react' in adapter_required or 'frontend' in adapter_required:
            return AgentType.FRONTEND
        elif 'node' in adapter_required or 'express' in adapter_required or 'backend' in adapter_required:
            return AgentType.BACKEND
        elif 'mongodb' in adapter_required or 'database' in adapter_required or 'sql' in adapter_required:
            return AgentType.DATABASE
        elif 'test' in adapter_required:
            return AgentType.TESTING
        elif 'doc' in adapter_required:
            return AgentType.DOCUMENTATION
        
        # Enhanced keyword matching for chunk name and description
        frontend_keywords = ['ui', 'frontend', 'react', 'component', 'interface', 'client', 'view', 'page']
        backend_keywords = ['api', 'backend', 'server', 'endpoint', 'service', 'controller', 'authentication', 'auth', 'crud', 'route']
        database_keywords = ['database', 'schema', 'model', 'migration', 'query', 'collection', 'table']
        test_keywords = ['test', 'testing', 'spec', 'unit', 'integration']
        
        text_to_check = f"{chunk_name} {description}".lower()
        
        if any(keyword in text_to_check for keyword in frontend_keywords):
            return AgentType.FRONTEND
        elif any(keyword in text_to_check for keyword in backend_keywords):
            return AgentType.BACKEND
        elif any(keyword in text_to_check for keyword in database_keywords):
            return AgentType.DATABASE
        elif any(keyword in text_to_check for keyword in test_keywords):
            return AgentType.TESTING
        
        # Check file paths in scope for better detection
        if scope:
            frontend_paths = ['client/', 'src/components', 'public/', 'assets/', '.jsx', '.tsx', '.html', '.css', '.scss']
            backend_paths = ['server/', 'api/', 'controllers/', 'routes/', 'middleware/', '.js', '.py', '.java']
            database_paths = ['models/', 'schemas/', 'migrations/', 'database/']
            
            scope_text = ' '.join(scope).lower()
            
            if any(path in scope_text for path in frontend_paths):
                return AgentType.FRONTEND
            elif any(path in scope_text for path in backend_paths):
                return AgentType.BACKEND
            elif any(path in scope_text for path in database_paths):
                return AgentType.DATABASE
        
        # If we still can't determine, make educated guesses based on common patterns
        if 'authentication' in text_to_check or 'auth' in text_to_check:
            return AgentType.BACKEND  # Auth is typically backend
        elif 'crud' in text_to_check:
            return AgentType.BACKEND  # CRUD operations are typically backend
        elif 'comment' in text_to_check or 'like' in text_to_check:
            return AgentType.BACKEND  # Social features are typically backend
        
        return None
    
    def _create_chunk_context(self, chunk: Dict[str, Any], blueprint: ProjectBlueprint,
                             context_serialization: Dict[str, Any]) -> Dict[str, Any]:
        """Create context for a specific chunk with enhanced tech stack information"""
        # Extract tech stack details for better agent context
        tech_stack = blueprint.tech_stack
        
        # Create framework-specific context
        framework_context = self._create_framework_context(tech_stack, chunk)
        
        return {
            'chunk_info': chunk,
            'project_blueprint': asdict(blueprint),
            'global_context': context_serialization.get('global_context', {}),
            'chunk_context': context_serialization.get('chunk_contexts', {}).get(chunk['id'], {}),
            'project_name': blueprint.project_name,
            'description': blueprint.description,
            'tech_stack': tech_stack,
            'architecture': blueprint.architecture,
            'framework_context': framework_context,
            'dependencies': blueprint.dependencies,
            'file_structure': blueprint.file_structure
        }
    
    def _create_framework_context(self, tech_stack: Dict[str, Any], chunk: Dict[str, Any]) -> Dict[str, Any]:
        """Create framework-specific context to guide agents"""
        framework_context = {
            'primary_frameworks': {},
            'specific_instructions': [],
            'code_examples': {}
        }
        
        # Frontend framework context
        if 'frontend' in tech_stack:
            frontend_frameworks = tech_stack['frontend']
            if 'React' in frontend_frameworks:
                framework_context['primary_frameworks']['frontend'] = 'React'
                framework_context['specific_instructions'].append(
                    'Use React functional components with hooks (useState, useEffect)'
                )
                framework_context['specific_instructions'].append(
                    'Use JSX syntax, not Vue template syntax'
                )
                framework_context['code_examples']['react_component'] = '''
import React, { useState } from 'react';

function ComponentName() {
  const [state, setState] = useState(initialValue);
  
  return (
    <div>
      <button onClick={handleClick}>Click me</button>
    </div>
  );
}

export default ComponentName;'''
            elif 'Vue' in frontend_frameworks or 'Vue.js' in frontend_frameworks:
                framework_context['primary_frameworks']['frontend'] = 'Vue'
                framework_context['specific_instructions'].append(
                    'Use Vue 3 composition API with <script setup>'
                )
                framework_context['code_examples']['vue_component'] = '''
<template>
  <div>
    <button @click="handleClick">Click me</button>
  </div>
</template>

<script setup>
import { ref } from 'vue';
const state = ref(initialValue);
</script>'''
            elif 'Angular' in frontend_frameworks:
                framework_context['primary_frameworks']['frontend'] = 'Angular'
                framework_context['specific_instructions'].append(
                    'Use Angular components with TypeScript'
                )
        
        # Backend framework context
        if 'backend' in tech_stack:
            backend_frameworks = tech_stack['backend']
            if 'Node.js' in backend_frameworks or 'Express' in backend_frameworks:
                framework_context['primary_frameworks']['backend'] = 'Node.js/Express'
                framework_context['specific_instructions'].append(
                    'Use Express.js for REST API endpoints'
                )
                framework_context['code_examples']['express_route'] = '''
const express = require('express');
const router = express.Router();

router.get('/api/endpoint', (req, res) => {
  res.json({ message: 'Success' });
});

module.exports = router;'''
            elif 'FastAPI' in backend_frameworks:
                framework_context['primary_frameworks']['backend'] = 'FastAPI'
                framework_context['specific_instructions'].append(
                    'Use FastAPI with Python type hints'
                )
            elif 'Django' in backend_frameworks:
                framework_context['primary_frameworks']['backend'] = 'Django'
                framework_context['specific_instructions'].append(
                    'Use Django models and views'
                )
        
        # Database context
        if 'database' in tech_stack:
            database_systems = tech_stack['database']
            if 'MongoDB' in database_systems:
                framework_context['primary_frameworks']['database'] = 'MongoDB'
                framework_context['specific_instructions'].append(
                    'Use Mongoose for MongoDB object modeling'
                )
                framework_context['code_examples']['mongoose_model'] = '''
const mongoose = require('mongoose');

const schema = new mongoose.Schema({
  field: { type: String, required: true },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('ModelName', schema);'''
            elif 'PostgreSQL' in database_systems:
                framework_context['primary_frameworks']['database'] = 'PostgreSQL'
                framework_context['specific_instructions'].append(
                    'Use SQL with proper indexing and relationships'
                )
        
        return framework_context
    
    def _calculate_priority(self, chunk: Dict[str, Any]) -> int:
        """Calculate task priority based on chunk information"""
        priority_map = {
            'high': 10,
            'medium': 5,
            'low': 1
        }
        return priority_map.get(chunk.get('priority', 'medium'), 5)
    
    def _estimate_duration(self, chunk: Dict[str, Any]) -> int:
        """Estimate duration in minutes based on chunk complexity"""
        effort_map = {
            'small': 30,
            'medium': 60,
            'large': 120
        }
        return effort_map.get(chunk.get('estimated_effort', 'medium'), 60)
    
    def _sort_tasks_by_dependencies(self, tasks: List[Task]) -> List[Task]:
        """Sort tasks by their dependencies (topological sort)"""
        # Simple implementation - can be enhanced with proper topological sorting
        task_dict = {task.id: task for task in tasks}
        sorted_tasks = []
        processed = set()
        
        def process_task(task_id: str):
            if task_id in processed:
                return
            
            task = task_dict.get(task_id)
            if not task:
                return
            
            # Process dependencies first
            for dep_id in task.dependencies:
                if dep_id in task_dict:
                    process_task(dep_id)
            
            sorted_tasks.append(task)
            processed.add(task_id)
        
        # Process all tasks
        for task in tasks:
            process_task(task.id)
        
        return sorted_tasks
    
    def _execute_task(self, task: Task, output_dir: str, 
                     previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single task using the appropriate agent"""
        self.logger.info(f"Executing task: {task.name} (Agent: {task.agent_type.value})")
        
        try:
            # Get or create agent
            agent = self._get_agent(task.agent_type)
            
            # Add previous results to context
            task.context['previous_results'] = previous_results
            
            # Execute task
            result = agent.run_task(task, task.context)
            
            if result.success:
                # Save generated files
                self._save_generated_files(result.files, output_dir)
                
                self.logger.info(f"✅ Task {task.name} completed successfully")
                return {
                    'success': True,
                    'files_generated': list(result.files.keys()),
                    'summary': result.summary,
                    'agent_type': task.agent_type.value
                }
            else:
                self.logger.error(f"❌ Task {task.name} failed: {result.error}")
                return {
                    'success': False,
                    'error': result.error,
                    'agent_type': task.agent_type.value
                }
        
        except Exception as e:
            self.logger.error(f"❌ Task {task.name} failed with exception: {e}")
            return {
                'success': False,
                'error': str(e),
                'agent_type': task.agent_type.value if hasattr(task, 'agent_type') else 'unknown'
            }
    
    def _get_agent(self, agent_type: AgentType):
        """Get or create an agent of the specified type"""
        if agent_type in self.agents_cache:
            return self.agents_cache[agent_type]
        
        # Get model configuration from config
        model_config = self._get_model_config_for_agent(agent_type)
        
        # Create agent configuration with required fields
        agent_config = AgentConfig(
            name=f"{agent_type.value}_agent",
            agent_type=agent_type.value,
            model=model_config.model_id,
            system_prompt_template=self._get_system_prompt_for_agent(agent_type),
            max_retries=3,
            enabled=True
        )
        
        # Create agent
        agent_class = self.agent_classes.get(agent_type)
        if not agent_class:
            raise ValueError(f"No agent class found for type: {agent_type}")
        
        agent = agent_class(agent_config, model_config)
        self.agents_cache[agent_type] = agent
        
        return agent
    
    def _get_model_config_for_agent(self, agent_type: AgentType) -> ModelConfig:
        """Get model configuration for a specific agent type"""
        # Use API model for now - can be enhanced to use LoRA adapters
        if hasattr(self.config, 'models') and 'api_coder' in self.config.models:
            api_model_config = self.config.models['api_coder']
            return ModelConfig(
                name=f"{agent_type.value}_model",
                type="api",
                model_id=api_model_config.model_id,
                api_key_env=api_model_config.api_key_env,
                max_tokens=api_model_config.max_tokens,
                temperature=api_model_config.temperature,
                timeout=api_model_config.timeout
            )
        else:
            # Fallback configuration
            return ModelConfig(
                name=f"{agent_type.value}_model",
                type="api",
                model_id='gpt-3.5-turbo',
                api_key_env='OPENAI_API_KEY',
                max_tokens=2048,
                temperature=0.7,
                timeout=60
            )
    
    def _get_system_prompt_for_agent(self, agent_type: AgentType) -> str:
        """Get system prompt template for a specific agent type"""
        prompts = {
            AgentType.FRONTEND: """You are a frontend development expert specializing in React, HTML, CSS, and JavaScript.
Your task is to generate high-quality frontend code based on the given requirements.

Focus on:
- Clean, maintainable React components
- Modern JavaScript/TypeScript patterns
- Responsive CSS design
- User experience best practices
- Accessibility considerations

Generate complete, working code files that can be directly used in a project.""",
            
            AgentType.BACKEND: """You are a backend development expert specializing in Node.js, Express, and API development.
Your task is to generate high-quality backend code based on the given requirements.

Focus on:
- RESTful API design
- Proper error handling
- Security best practices
- Database integration
- Authentication and authorization
- Clean code architecture

Generate complete, working code files that can be directly used in a project.""",
            
            AgentType.DATABASE: """You are a database expert specializing in MongoDB, schema design, and data modeling.
Your task is to generate high-quality database code based on the given requirements.

Focus on:
- Efficient schema design
- Proper indexing strategies
- Data validation
- Migration scripts
- Query optimization
- Database security

Generate complete, working database schemas and models that can be directly used in a project.""",
            
            AgentType.TESTING: """You are a testing expert specializing in unit tests, integration tests, and test automation.
Your task is to generate comprehensive test suites based on the given requirements.

Focus on:
- Complete test coverage
- Clear test descriptions
- Proper test structure
- Mock and stub usage
- Edge case testing
- Performance testing

Generate complete, working test files that can be directly used in a project.""",
            
            AgentType.DOCUMENTATION: """You are a documentation expert specializing in technical writing and API documentation.
Your task is to generate clear, comprehensive documentation based on the given requirements.

Focus on:
- Clear explanations
- Code examples
- API documentation
- Setup instructions
- Usage guidelines
- Best practices

Generate complete, well-structured documentation that helps developers understand and use the code."""
        }
        
        return prompts.get(agent_type, "You are a software development expert. Generate high-quality code based on the given requirements.")
    
    def _save_generated_files(self, files: Dict[str, str], output_dir: str):
        """Save generated files to the output directory"""
        for filename, content in files.items():
            file_path = os.path.join(output_dir, filename)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.debug(f"Saved file: {file_path}")