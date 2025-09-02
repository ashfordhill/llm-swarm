"""
Adapter Planner

Plans what LoRA adapters are needed based on the project blueprint.
Identifies specialized knowledge domains and creates training plans.
"""

import json
import logging
import os
from typing import Dict, List, Any
from dataclasses import asdict

from .models import ProjectBlueprint, DesignRequest, AdapterPlan


class AdapterPlanner:
    """
    Plans LoRA adapters needed for specialized agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize API client for response generation
        self._init_api_client()
        
        # Common adapter types and their specializations
        self.adapter_templates = {
            'frontend_react': {
                'domain': 'frontend',
                'specialization': 'React components and patterns',
                'training_data_types': ['jsx_components', 'react_hooks', 'state_management'],
                'estimated_training_time': '2-4 hours'
            },
            'frontend_vue': {
                'domain': 'frontend',
                'specialization': 'Vue.js components and patterns',
                'training_data_types': ['vue_components', 'vue_composition', 'vuex_patterns'],
                'estimated_training_time': '2-4 hours'
            },
            'backend_fastapi': {
                'domain': 'backend',
                'specialization': 'FastAPI endpoints and patterns',
                'training_data_types': ['fastapi_routes', 'pydantic_models', 'async_patterns'],
                'estimated_training_time': '3-5 hours'
            },
            'backend_express': {
                'domain': 'backend',
                'specialization': 'Express.js routes and middleware',
                'training_data_types': ['express_routes', 'middleware_patterns', 'error_handling'],
                'estimated_training_time': '2-4 hours'
            },
            'database_sql': {
                'domain': 'database',
                'specialization': 'SQL queries and schema design',
                'training_data_types': ['sql_queries', 'schema_design', 'migrations'],
                'estimated_training_time': '2-3 hours'
            },
            'database_nosql': {
                'domain': 'database',
                'specialization': 'NoSQL patterns and queries',
                'training_data_types': ['nosql_queries', 'document_design', 'aggregations'],
                'estimated_training_time': '2-3 hours'
            },
            'auth_jwt': {
                'domain': 'authentication',
                'specialization': 'JWT authentication patterns',
                'training_data_types': ['jwt_implementation', 'auth_middleware', 'token_validation'],
                'estimated_training_time': '1-2 hours'
            },
            'testing_unit': {
                'domain': 'testing',
                'specialization': 'Unit testing patterns',
                'training_data_types': ['unit_tests', 'mocking_patterns', 'test_fixtures'],
                'estimated_training_time': '2-3 hours'
            },
            'api_rest': {
                'domain': 'api_design',
                'specialization': 'REST API patterns and best practices',
                'training_data_types': ['rest_endpoints', 'api_documentation', 'error_responses'],
                'estimated_training_time': '2-4 hours'
            }
        }
        
        self.adapter_planning_prompt = """
You are a LoRA Adapter Specialist responsible for identifying what specialized adapters are needed for a project.

Project Blueprint:
{blueprint}

User Requirements:
{requirements}

Based on this project, identify what LoRA adapters should be created or used. Consider:

1. TECHNOLOGY-SPECIFIC ADAPTERS:
   - What specific frameworks/libraries are being used?
   - What patterns are common in those technologies?
   - What specialized knowledge is needed?

2. DOMAIN-SPECIFIC ADAPTERS:
   - Authentication/authorization patterns
   - Database interaction patterns  
   - API design patterns
   - Testing patterns
   - UI/UX patterns specific to this project type

3. PROJECT-SPECIFIC ADAPTERS:
   - Are there unique patterns this project will need?
   - Custom business logic patterns
   - Integration patterns with external services

4. ADAPTER DEPENDENCIES:
   - Which adapters depend on others?
   - What's the training priority order?
   - Which adapters can be trained in parallel?

Respond with JSON in this format:
{{
  "required_adapters": [
    {{
      "name": "adapter_name",
      "domain": "domain_category", 
      "specialization": "what_it_specializes_in",
      "priority": "high|medium|low",
      "training_data_types": ["type1", "type2"],
      "estimated_training_time": "time_estimate",
      "justification": "why_this_adapter_is_needed"
    }}
  ],
  "adapter_dependencies": {{
    "adapter_name": ["dependency1", "dependency2"]
  }},
  "training_priority": ["adapter1", "adapter2", "adapter3"],
  "estimated_total_time": "total_time_estimate",
  "parallel_training_groups": [
    ["adapter1", "adapter2"],
    ["adapter3"]
  ]
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
            return '{"required_adapters": [{"name": "frontend_react", "domain": "frontend", "specialization": "React components", "priority": "high", "training_data_types": ["jsx_components"], "estimated_training_time": "2 hours", "justification": "React development needed"}], "adapter_dependencies": {}, "training_priority": ["frontend_react"], "estimated_total_time": "2 hours"}'
        
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
            return '{"required_adapters": [{"name": "frontend_react", "domain": "frontend", "specialization": "React components", "priority": "high", "training_data_types": ["jsx_components"], "estimated_training_time": "2 hours", "justification": "React development needed"}], "adapter_dependencies": {}, "training_priority": ["frontend_react"], "estimated_total_time": "2 hours"}'
    
    def plan_adapters(self, blueprint: ProjectBlueprint, request: DesignRequest) -> AdapterPlan:
        """
        Plan what LoRA adapters are needed for this project
        """
        self.logger.info("Planning LoRA adapters...")
        
        # Format prompt with blueprint data
        prompt = self.adapter_planning_prompt.format(
            blueprint=json.dumps(asdict(blueprint), indent=2),
            requirements=json.dumps(request.requirements)
        )
        
        try:
            # Get LLM response
            response = self.generate_response(prompt)
            
            # Parse JSON response
            plan_data = json.loads(response)
            
            # Create AdapterPlan object
            adapter_plan = AdapterPlan(
                required_adapters=plan_data.get('required_adapters', []),
                adapter_dependencies=plan_data.get('adapter_dependencies', {}),
                training_priority=plan_data.get('training_priority', []),
                estimated_training_time=plan_data.get('estimated_total_time', 'unknown')
            )
            
            # Enhance with template data
            adapter_plan = self._enhance_with_templates(adapter_plan)
            
            self.logger.info(f"Planned {len(adapter_plan.required_adapters)} adapters")
            return adapter_plan
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse adapter plan JSON: {e}")
            return self._create_fallback_adapter_plan(blueprint)
        except Exception as e:
            self.logger.error(f"Error planning adapters: {e}")
            return self._create_fallback_adapter_plan(blueprint)
    
    def _enhance_with_templates(self, adapter_plan: AdapterPlan) -> AdapterPlan:
        """
        Enhance adapter plan with template data for known adapter types
        """
        for adapter in adapter_plan.required_adapters:
            adapter_name = adapter.get('name', '')
            
            # Check if we have a template for this adapter
            if adapter_name in self.adapter_templates:
                template = self.adapter_templates[adapter_name]
                
                # Fill in missing data from template
                if not adapter.get('training_data_types'):
                    adapter['training_data_types'] = template['training_data_types']
                
                if not adapter.get('estimated_training_time'):
                    adapter['estimated_training_time'] = template['estimated_training_time']
                
                if not adapter.get('domain'):
                    adapter['domain'] = template['domain']
        
        return adapter_plan
    
    def _create_fallback_adapter_plan(self, blueprint: ProjectBlueprint) -> AdapterPlan:
        """
        Create a basic adapter plan based on tech stack if LLM fails
        """
        self.logger.warning("Creating fallback adapter plan")
        
        required_adapters = []
        training_priority = []
        
        # Analyze tech stack and create basic adapters
        tech_stack = blueprint.tech_stack
        
        # Frontend adapters
        if 'React' in tech_stack.get('frontend', []):
            required_adapters.append({
                'name': 'frontend_react',
                'domain': 'frontend',
                'specialization': 'React components and patterns',
                'priority': 'high',
                'training_data_types': ['jsx_components', 'react_hooks'],
                'estimated_training_time': '2-4 hours',
                'justification': 'React is the primary frontend framework'
            })
            training_priority.append('frontend_react')
        
        if 'Vue' in tech_stack.get('frontend', []):
            required_adapters.append({
                'name': 'frontend_vue',
                'domain': 'frontend', 
                'specialization': 'Vue.js components and patterns',
                'priority': 'high',
                'training_data_types': ['vue_components', 'vue_composition'],
                'estimated_training_time': '2-4 hours',
                'justification': 'Vue is the primary frontend framework'
            })
            training_priority.append('frontend_vue')
        
        # Backend adapters
        if 'FastAPI' in tech_stack.get('backend', []):
            required_adapters.append({
                'name': 'backend_fastapi',
                'domain': 'backend',
                'specialization': 'FastAPI endpoints and patterns',
                'priority': 'high',
                'training_data_types': ['fastapi_routes', 'pydantic_models'],
                'estimated_training_time': '3-5 hours',
                'justification': 'FastAPI is the primary backend framework'
            })
            training_priority.append('backend_fastapi')
        
        if 'Express' in tech_stack.get('backend', []):
            required_adapters.append({
                'name': 'backend_express',
                'domain': 'backend',
                'specialization': 'Express.js routes and middleware',
                'priority': 'high',
                'training_data_types': ['express_routes', 'middleware_patterns'],
                'estimated_training_time': '2-4 hours',
                'justification': 'Express is the primary backend framework'
            })
            training_priority.append('backend_express')
        
        # Database adapters
        if any(db in ['PostgreSQL', 'MySQL', 'SQLite'] for db in tech_stack.get('database', [])):
            required_adapters.append({
                'name': 'database_sql',
                'domain': 'database',
                'specialization': 'SQL queries and schema design',
                'priority': 'medium',
                'training_data_types': ['sql_queries', 'schema_design'],
                'estimated_training_time': '2-3 hours',
                'justification': 'SQL database is being used'
            })
            training_priority.append('database_sql')
        
        # Always include testing adapter
        required_adapters.append({
            'name': 'testing_unit',
            'domain': 'testing',
            'specialization': 'Unit testing patterns',
            'priority': 'medium',
            'training_data_types': ['unit_tests', 'test_fixtures'],
            'estimated_training_time': '2-3 hours',
            'justification': 'Testing is essential for code quality'
        })
        training_priority.append('testing_unit')
        
        return AdapterPlan(
            required_adapters=required_adapters,
            adapter_dependencies={},
            training_priority=training_priority,
            estimated_training_time=f"{len(required_adapters) * 3} hours"
        )