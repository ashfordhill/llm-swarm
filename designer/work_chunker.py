"""
Work Chunker

Breaks down the project into LLM-friendly work chunks that can be handled
by specialized agents with specific LoRA adapters.
"""

import json
import logging
import os
from typing import Dict, List, Any
from dataclasses import asdict

from .models import ProjectBlueprint, AdapterPlan, WorkPlan


class WorkChunker:
    """
    Breaks project work into manageable chunks for specialized agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize API client for response generation
        self._init_api_client()
        
        self.chunking_prompt = """
You are a Project Manager specializing in breaking down software projects into manageable work chunks.

Project Blueprint:
{blueprint}

Available Adapters:
{adapters}

Break this project into work chunks that:
1. Are small enough for a single specialized agent to handle (1-3 files typically)
2. Have clear, well-defined scope and deliverables
3. Can be worked on with minimal context about other chunks
4. Match the available LoRA adapter specializations
5. Have clear input/output interfaces

For each chunk, specify:
- id: unique identifier
- name: descriptive name
- description: what needs to be built
- scope: specific files/components to create
- adapter_required: which LoRA adapter should handle this
- inputs: what information/interfaces this chunk needs
- outputs: what this chunk will produce
- dependencies: other chunks this depends on
- estimated_effort: "small" (1-2 hours), "medium" (3-6 hours), "large" (1-2 days)
- priority: "high", "medium", "low"

Also provide:
- execution_order: recommended order to execute chunks
- parallel_groups: chunks that can be done in parallel

Respond with JSON in this format:
{{
  "chunks": [
    {{
      "id": "chunk_id",
      "name": "Chunk Name",
      "description": "What this chunk builds",
      "scope": ["file1.py", "file2.js"],
      "adapter_required": "adapter_name",
      "inputs": ["input1", "input2"],
      "outputs": ["output1", "output2"],
      "dependencies": ["chunk_id1", "chunk_id2"],
      "estimated_effort": "small|medium|large",
      "priority": "high|medium|low",
      "constraints": ["constraint1", "constraint2"]
    }}
  ],
  "execution_order": ["chunk1", "chunk2", "chunk3"],
  "parallel_groups": [
    ["chunk1", "chunk2"],
    ["chunk3"]
  ],
  "estimated_duration": "time_estimate"
}}
"""
    
    def _init_api_client(self):
        """Initialize API client for response generation"""
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.api_client = openai.OpenAI(api_key=api_key)
                self.logger.info("OpenAI API client initialized")
            else:
                self.api_client = None
                self.logger.warning("No OpenAI API key found")
        except ImportError:
            self.api_client = None
            self.logger.warning("OpenAI package not available")
    
    def generate_response(self, prompt: str) -> str:
        """Generate response using API client"""
        if not self.api_client:
            # Return a fallback response for testing
            return '{"chunks": [{"id": "chunk1", "name": "Setup Project", "description": "Initialize project structure", "scope": ["package.json", "src/"], "adapter_required": "frontend_react", "inputs": [], "outputs": ["project_structure"], "dependencies": [], "estimated_effort": "small", "priority": "high", "constraints": []}], "execution_order": ["chunk1"], "dependencies": {}, "estimated_duration": "1 hour"}'
        
        try:
            response = self.api_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.error(f"API call failed: {e}")
            # Return fallback response
            return '{"chunks": [{"id": "chunk1", "name": "Setup Project", "description": "Initialize project structure", "scope": ["package.json", "src/"], "adapter_required": "frontend_react", "inputs": [], "outputs": ["project_structure"], "dependencies": [], "estimated_effort": "small", "priority": "high", "constraints": []}], "execution_order": ["chunk1"], "dependencies": {}, "estimated_duration": "1 hour"}'
    
    def create_work_chunks(self, blueprint: ProjectBlueprint, adapter_plan: AdapterPlan) -> WorkPlan:
        """
        Break the project into manageable work chunks
        """
        self.logger.info("Creating work chunks...")
        
        # Format prompt with blueprint and adapter data
        prompt = self.chunking_prompt.format(
            blueprint=json.dumps(asdict(blueprint), indent=2),
            adapters=json.dumps(adapter_plan.required_adapters, indent=2)
        )
        
        try:
            # Get LLM response
            response = self.generate_response(prompt)
            
            # Parse JSON response
            work_data = json.loads(response)
            
            # Create WorkPlan object
            work_plan = WorkPlan(
                chunks=work_data.get('chunks', []),
                execution_order=work_data.get('execution_order', []),
                dependencies=self._extract_dependencies(work_data.get('chunks', [])),
                estimated_duration=work_data.get('estimated_duration', 'unknown')
            )
            
            # Validate and enhance chunks
            work_plan = self._validate_and_enhance_chunks(work_plan, blueprint, adapter_plan)
            
            self.logger.info(f"Created {len(work_plan.chunks)} work chunks")
            return work_plan
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse work plan JSON: {e}")
            return self._create_fallback_work_plan(blueprint, adapter_plan)
        except Exception as e:
            self.logger.error(f"Error creating work chunks: {e}")
            return self._create_fallback_work_plan(blueprint, adapter_plan)
    
    def _extract_dependencies(self, chunks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Extract dependency mapping from chunks"""
        dependencies = {}
        for chunk in chunks:
            chunk_id = chunk.get('id')
            chunk_deps = chunk.get('dependencies', [])
            if chunk_id and chunk_deps:
                dependencies[chunk_id] = chunk_deps
        return dependencies
    
    def _validate_and_enhance_chunks(self, work_plan: WorkPlan, blueprint: ProjectBlueprint, 
                                   adapter_plan: AdapterPlan) -> WorkPlan:
        """
        Validate chunks and enhance with additional metadata
        """
        adapter_names = {adapter['name'] for adapter in adapter_plan.required_adapters}
        
        for chunk in work_plan.chunks:
            # Ensure required adapter exists
            required_adapter = chunk.get('adapter_required')
            if required_adapter and required_adapter not in adapter_names:
                self.logger.warning(f"Chunk {chunk.get('id')} requires unknown adapter: {required_adapter}")
                # Try to find a suitable fallback
                chunk['adapter_required'] = self._find_fallback_adapter(required_adapter, adapter_names)
            
            # Add project context
            chunk['project_context'] = {
                'project_name': blueprint.project_name,
                'tech_stack': blueprint.tech_stack,
                'architecture_pattern': blueprint.architecture.get('pattern')
            }
            
            # Ensure all required fields exist
            chunk.setdefault('inputs', [])
            chunk.setdefault('outputs', [])
            chunk.setdefault('constraints', [])
            chunk.setdefault('estimated_effort', 'medium')
            chunk.setdefault('priority', 'medium')
        
        return work_plan
    
    def _find_fallback_adapter(self, required_adapter: str, available_adapters: set) -> str:
        """Find a suitable fallback adapter"""
        # Simple heuristic matching
        if 'frontend' in required_adapter.lower():
            for adapter in available_adapters:
                if 'frontend' in adapter.lower():
                    return adapter
        
        if 'backend' in required_adapter.lower():
            for adapter in available_adapters:
                if 'backend' in adapter.lower():
                    return adapter
        
        if 'database' in required_adapter.lower():
            for adapter in available_adapters:
                if 'database' in adapter.lower():
                    return adapter
        
        # Return first available adapter as last resort
        return list(available_adapters)[0] if available_adapters else 'general'
    
    def _create_fallback_work_plan(self, blueprint: ProjectBlueprint, adapter_plan: AdapterPlan) -> WorkPlan:
        """
        Create a basic work plan if LLM fails
        """
        self.logger.warning("Creating fallback work plan")
        
        chunks = []
        execution_order = []
        
        # Create basic chunks based on features
        for i, feature in enumerate(blueprint.features):
            chunk_id = f"feature_{i+1}"
            
            # Determine adapter based on feature characteristics
            adapter_required = self._determine_adapter_for_feature(feature, adapter_plan)
            
            chunk = {
                'id': chunk_id,
                'name': feature.get('name', f'Feature {i+1}'),
                'description': feature.get('description', 'Implement feature'),
                'scope': [f"{feature.get('name', 'feature').lower().replace(' ', '_')}.py"],
                'adapter_required': adapter_required,
                'inputs': ['project_requirements', 'tech_stack'],
                'outputs': ['implemented_feature', 'tests'],
                'dependencies': [],
                'estimated_effort': feature.get('estimated_effort', 'medium'),
                'priority': feature.get('priority', 'medium'),
                'constraints': [],
                'project_context': {
                    'project_name': blueprint.project_name,
                    'tech_stack': blueprint.tech_stack,
                    'architecture_pattern': blueprint.architecture.get('pattern', 'layered')
                }
            }
            
            chunks.append(chunk)
            execution_order.append(chunk_id)
        
        # Add testing chunk
        if chunks:
            test_chunk = {
                'id': 'testing',
                'name': 'Testing Suite',
                'description': 'Create comprehensive tests for all features',
                'scope': ['tests/'],
                'adapter_required': 'testing_unit',
                'inputs': ['implemented_features'],
                'outputs': ['test_suite', 'test_reports'],
                'dependencies': [chunk['id'] for chunk in chunks],
                'estimated_effort': 'medium',
                'priority': 'high',
                'constraints': [],
                'project_context': {
                    'project_name': blueprint.project_name,
                    'tech_stack': blueprint.tech_stack,
                    'architecture_pattern': blueprint.architecture.get('pattern', 'layered')
                }
            }
            chunks.append(test_chunk)
            execution_order.append('testing')
        
        dependencies = {chunk['id']: chunk['dependencies'] for chunk in chunks if chunk['dependencies']}
        
        return WorkPlan(
            chunks=chunks,
            execution_order=execution_order,
            dependencies=dependencies,
            estimated_duration=f"{len(chunks)} * 4 hours"
        )
    
    def _determine_adapter_for_feature(self, feature: Dict[str, Any], adapter_plan: AdapterPlan) -> str:
        """
        Determine which adapter should handle a feature
        """
        feature_name = feature.get('name', '').lower()
        feature_desc = feature.get('description', '').lower()
        
        # Simple heuristic matching
        if any(word in feature_name + feature_desc for word in ['ui', 'frontend', 'component', 'interface']):
            for adapter in adapter_plan.required_adapters:
                if adapter['domain'] == 'frontend':
                    return adapter['name']
        
        if any(word in feature_name + feature_desc for word in ['api', 'backend', 'server', 'endpoint']):
            for adapter in adapter_plan.required_adapters:
                if adapter['domain'] == 'backend':
                    return adapter['name']
        
        if any(word in feature_name + feature_desc for word in ['database', 'data', 'storage', 'model']):
            for adapter in adapter_plan.required_adapters:
                if adapter['domain'] == 'database':
                    return adapter['name']
        
        # Default to first available adapter
        return adapter_plan.required_adapters[0]['name'] if adapter_plan.required_adapters else 'general'