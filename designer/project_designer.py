"""
Project Designer - The main Designer LLM

Takes high-level user prompts and orchestrates the design process:
1. Analyzes the user's request
2. Creates a project blueprint
3. Identifies required LoRA adapters
4. Breaks work into LLM-friendly chunks
5. Coordinates specialized agents
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional
from dataclasses import asdict
from datetime import datetime

from .models import DesignRequest, ProjectBlueprint, AdapterPlan, WorkPlan, DesignResult
from .blueprint_generator import BlueprintGenerator
from .adapter_planner import AdapterPlanner
from .work_chunker import WorkChunker
from utils.config_loader import ConfigLoader
import logging


class ProjectDesigner:
    """
    Main Designer LLM that orchestrates the entire design process
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        config_loader = ConfigLoader(config_path)
        self.config = config_loader.config
        
        # Initialize sub-components
        self.blueprint_generator = BlueprintGenerator(self.config)
        self.adapter_planner = AdapterPlanner(self.config)
        self.work_chunker = WorkChunker(self.config)
        
        # Designer LLM prompt templates
        self.design_prompts = {
            'analyze_request': """
You are a Senior Software Architect and Project Designer. Your job is to analyze user requests and create comprehensive project designs.

User Request: "{prompt}"

Additional Requirements: {requirements}
Constraints: {constraints}
Preferences: {preferences}

Please analyze this request and provide:

1. PROJECT UNDERSTANDING:
   - What is the user trying to build?
   - What are the core functionalities?
   - What is the target audience/use case?
   - What is the estimated complexity level?

2. TECHNICAL ANALYSIS:
   - What technologies would be most appropriate?
   - What architectural patterns should be used?
   - What are the main technical challenges?
   - What external dependencies are needed?

3. FEATURE BREAKDOWN:
   - List all major features/components
   - Identify which features can be developed independently
   - Determine feature dependencies and relationships
   - Estimate development complexity for each feature

4. SPECIALIZATION NEEDS:
   - What types of specialized knowledge/skills are needed?
   - Which parts require domain-specific expertise?
   - What patterns/frameworks will be heavily used?

Respond in JSON format with your analysis.
""",
            
            'create_orchestration_plan': """
You are the Orchestrator LLM responsible for coordinating all specialized agents and tying the project together.

Project Blueprint: {blueprint}
Work Chunks: {work_chunks}
Adapter Plan: {adapter_plan}

Create a detailed orchestration plan that includes:

1. INTEGRATION STRATEGY:
   - How will individual features be integrated?
   - What are the integration points between components?
   - How will data flow between different parts?

2. COORDINATION PLAN:
   - In what order should work chunks be executed?
   - Which chunks can be done in parallel?
   - What are the critical dependencies?

3. QUALITY ASSURANCE:
   - How will consistency be maintained across features?
   - What integration tests are needed?
   - How will the final product be validated?

4. CONTEXT MANAGEMENT:
   - What context does each specialized agent need?
   - How will context be serialized and provided?
   - What information should be kept from the orchestrator?

Respond in JSON format with your orchestration plan.
"""
        }
    
    def design_project(self, prompt: str, requirements: List[str] = None, 
                      constraints: List[str] = None, preferences: Dict[str, Any] = None) -> DesignResult:
        """
        Main design method that orchestrates the entire design process
        
        Args:
            prompt: High-level user prompt describing what they want to build
            requirements: Additional specific requirements
            constraints: Any constraints or limitations
            preferences: User preferences for technologies, patterns, etc.
            
        Returns:
            DesignResult containing complete design plan
        """
        self.logger.info(f"Starting project design for: {prompt[:100]}...")
        
        # Create design request
        request = DesignRequest(
            prompt=prompt,
            requirements=requirements or [],
            constraints=constraints or [],
            preferences=preferences or {},
            timestamp=datetime.now().isoformat()
        )
        
        # Step 1: Analyze the request and create blueprint
        self.logger.info("Step 1: Analyzing request and creating blueprint...")
        blueprint = self.blueprint_generator.create_blueprint(request)
        
        # Step 2: Plan required LoRA adapters
        self.logger.info("Step 2: Planning LoRA adapters...")
        adapter_plan = self.adapter_planner.plan_adapters(blueprint, request)
        
        # Step 3: Break work into chunks
        self.logger.info("Step 3: Breaking work into chunks...")
        work_plan = self.work_chunker.create_work_chunks(blueprint, adapter_plan)
        
        # Step 4: Create context serialization plan
        self.logger.info("Step 4: Creating context serialization...")
        context_serialization = self._create_context_serialization(blueprint, work_plan)
        
        # Step 5: Create orchestration plan
        self.logger.info("Step 5: Creating orchestration plan...")
        orchestration_plan = self._create_orchestration_plan(blueprint, work_plan, adapter_plan)
        
        # Create final design result
        result = DesignResult(
            request=request,
            blueprint=blueprint,
            adapter_plan=adapter_plan,
            work_plan=work_plan,
            context_serialization=context_serialization,
            orchestration_plan=orchestration_plan
        )
        
        self.logger.info("Project design complete!")
        return result
    
    def _create_context_serialization(self, blueprint: ProjectBlueprint, work_plan: WorkPlan) -> Dict[str, Any]:
        """
        Create a plan for how context will be serialized and provided to specialized agents
        """
        return {
            'global_context': {
                'project_overview': {
                    'name': blueprint.project_name,
                    'description': blueprint.description,
                    'architecture': blueprint.architecture,
                    'tech_stack': blueprint.tech_stack
                },
                'file_structure': blueprint.file_structure,
                'dependencies': blueprint.dependencies
            },
            'chunk_contexts': {
                chunk['id']: {
                    'chunk_scope': chunk['scope'],
                    'related_features': chunk.get('related_features', []),
                    'required_knowledge': chunk.get('required_knowledge', []),
                    'input_interfaces': chunk.get('inputs', []),
                    'output_interfaces': chunk.get('outputs', []),
                    'constraints': chunk.get('constraints', [])
                }
                for chunk in work_plan.chunks
            },
            'serialization_format': 'json',
            'context_compression': 'enabled',
            'context_versioning': 'enabled'
        }
    
    def _create_orchestration_plan(self, blueprint: ProjectBlueprint, work_plan: WorkPlan, 
                                 adapter_plan: AdapterPlan) -> Dict[str, Any]:
        """
        Create the orchestration plan - currently returns a simple plan
        TODO: Integrate with actual orchestrator agent in Phase 2
        """
        # For now, create a simple orchestration plan
        # This will be enhanced in Phase 2 with actual agent integration
        return self._create_fallback_orchestration_plan(work_plan)
    
    def _create_fallback_orchestration_plan(self, work_plan: WorkPlan) -> Dict[str, Any]:
        """Create a basic orchestration plan if LLM fails"""
        return {
            'integration_strategy': {
                'approach': 'sequential_integration',
                'integration_points': ['api_interfaces', 'data_models', 'ui_components'],
                'data_flow': 'request_response_pattern'
            },
            'coordination_plan': {
                'execution_order': work_plan.execution_order,
                'parallel_chunks': [],
                'critical_dependencies': work_plan.dependencies
            },
            'quality_assurance': {
                'consistency_checks': ['code_style', 'naming_conventions', 'api_contracts'],
                'integration_tests': ['unit_tests', 'integration_tests', 'e2e_tests'],
                'validation_steps': ['functionality', 'performance', 'security']
            },
            'context_management': {
                'agent_context': 'minimal_required_only',
                'context_serialization': 'json_format',
                'orchestrator_visibility': 'full_project_context'
            },
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'fallback_plan': True,
                'total_chunks': len(work_plan.chunks)
            }
        }
    
    def save_design(self, result: DesignResult, output_path: str):
        """Save the complete design result to disk"""
        import os
        os.makedirs(output_path, exist_ok=True)
        
        # Save main design file
        design_file = os.path.join(output_path, 'design_result.json')
        with open(design_file, 'w', encoding='utf-8') as f:
            # Convert dataclasses to dict for JSON serialization
            result_dict = {
                'request': asdict(result.request),
                'blueprint': asdict(result.blueprint),
                'adapter_plan': asdict(result.adapter_plan),
                'work_plan': asdict(result.work_plan),
                'context_serialization': result.context_serialization,
                'orchestration_plan': result.orchestration_plan
            }
            json.dump(result_dict, f, indent=2, ensure_ascii=False)
        
        # Save individual components
        components_dir = os.path.join(output_path, 'components')
        os.makedirs(components_dir, exist_ok=True)
        
        # Save blueprint
        with open(os.path.join(components_dir, 'blueprint.json'), 'w') as f:
            json.dump(asdict(result.blueprint), f, indent=2)
        
        # Save adapter plan
        with open(os.path.join(components_dir, 'adapter_plan.json'), 'w') as f:
            json.dump(asdict(result.adapter_plan), f, indent=2)
        
        # Save work plan
        with open(os.path.join(components_dir, 'work_plan.json'), 'w') as f:
            json.dump(asdict(result.work_plan), f, indent=2)
        
        # Save context serialization
        with open(os.path.join(components_dir, 'context_serialization.json'), 'w') as f:
            json.dump(result.context_serialization, f, indent=2)
        
        # Save orchestration plan
        with open(os.path.join(components_dir, 'orchestration_plan.json'), 'w') as f:
            json.dump(result.orchestration_plan, f, indent=2)
        
        self.logger.info(f"Design saved to {output_path}")
    
    def load_design(self, design_path: str) -> Optional[DesignResult]:
        """Load a previously saved design"""
        design_file = os.path.join(design_path, 'design_result.json')
        
        if not os.path.exists(design_file):
            return None
        
        try:
            with open(design_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstruct dataclasses
            result = DesignResult(
                request=DesignRequest(**data['request']),
                blueprint=ProjectBlueprint(**data['blueprint']),
                adapter_plan=AdapterPlan(**data['adapter_plan']),
                work_plan=WorkPlan(**data['work_plan']),
                context_serialization=data['context_serialization'],
                orchestration_plan=data['orchestration_plan']
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error loading design: {e}")
            return None