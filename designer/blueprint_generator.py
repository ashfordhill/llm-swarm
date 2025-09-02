"""
Blueprint Generator

Creates detailed project blueprints from user requests using LLM analysis.
"""

import json
import logging
import os
from typing import Dict, List, Any
from dataclasses import asdict

from .models import DesignRequest, ProjectBlueprint


class BlueprintGenerator:
    """
    Generates detailed project blueprints from user requests
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Initialize API client for response generation
        self._init_api_client()
        
        self.blueprint_prompt = """
You are a Senior Software Architect specializing in creating detailed project blueprints.

User Request: "{prompt}"
Requirements: {requirements}
Constraints: {constraints}
Preferences: {preferences}

Create a comprehensive project blueprint that includes:

1. PROJECT BASICS:
   - project_name: A clear, descriptive name
   - description: Detailed description of what this project does
   - estimated_complexity: "simple", "moderate", "complex", or "enterprise"

2. ARCHITECTURE:
   - pattern: The main architectural pattern (MVC, microservices, layered, etc.)
   - components: List of major system components
   - data_flow: How data moves through the system
   - scalability_considerations: How the system can scale

3. FEATURES:
   List each major feature with:
   - name: Feature name
   - description: What it does
   - priority: "high", "medium", "low"
   - complexity: "simple", "moderate", "complex"
   - dependencies: Other features this depends on
   - estimated_effort: "small", "medium", "large"

4. TECH_STACK:
   - frontend: List of frontend technologies
   - backend: List of backend technologies  
   - database: Database technologies
   - infrastructure: Deployment/hosting technologies
   - tools: Development tools and frameworks

5. FILE_STRUCTURE:
   Create a nested dictionary representing the project file structure

6. DEPENDENCIES:
   List all external dependencies/packages needed

Respond ONLY with valid JSON in this exact format:
{{
  "project_name": "string",
  "description": "string", 
  "estimated_complexity": "string",
  "architecture": {{
    "pattern": "string",
    "components": ["string"],
    "data_flow": "string",
    "scalability_considerations": "string"
  }},
  "features": [
    {{
      "name": "string",
      "description": "string", 
      "priority": "string",
      "complexity": "string",
      "dependencies": ["string"],
      "estimated_effort": "string"
    }}
  ],
  "tech_stack": {{
    "frontend": ["string"],
    "backend": ["string"],
    "database": ["string"], 
    "infrastructure": ["string"],
    "tools": ["string"]
  }},
  "file_structure": {{}},
  "dependencies": ["string"]
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
            return '{"project_name": "Test Project", "description": "A test project", "estimated_complexity": "simple", "architecture": {"pattern": "MVC", "components": ["frontend", "backend"], "data_flow": "client-server", "scalability_considerations": "basic"}, "features": [{"name": "basic feature", "description": "test feature", "priority": "high", "complexity": "simple", "dependencies": [], "estimated_effort": "small"}], "tech_stack": {"frontend": ["React"], "backend": ["Node.js"], "database": ["SQLite"], "infrastructure": ["local"], "tools": ["npm"]}, "file_structure": {}, "dependencies": ["react", "express"]}'
        
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
            return '{"project_name": "Test Project", "description": "A test project", "estimated_complexity": "simple", "architecture": {"pattern": "MVC", "components": ["frontend", "backend"], "data_flow": "client-server", "scalability_considerations": "basic"}, "features": [{"name": "basic feature", "description": "test feature", "priority": "high", "complexity": "simple", "dependencies": [], "estimated_effort": "small"}], "tech_stack": {"frontend": ["React"], "backend": ["Node.js"], "database": ["SQLite"], "infrastructure": ["local"], "tools": ["npm"]}, "file_structure": {}, "dependencies": ["react", "express"]}'
    
    def create_blueprint(self, request: DesignRequest) -> ProjectBlueprint:
        """
        Create a detailed project blueprint from the design request
        """
        self.logger.info("Generating project blueprint...")
        
        # Format the prompt with request details
        prompt = self.blueprint_prompt.format(
            prompt=request.prompt,
            requirements=json.dumps(request.requirements),
            constraints=json.dumps(request.constraints),
            preferences=json.dumps(request.preferences)
        )
        
        try:
            # Get LLM response
            response = self.generate_response(prompt)
            
            # Parse JSON response
            blueprint_data = json.loads(response)
            
            # Create ProjectBlueprint object
            blueprint = ProjectBlueprint(
                project_name=blueprint_data.get('project_name', 'Untitled Project'),
                description=blueprint_data.get('description', ''),
                architecture=blueprint_data.get('architecture', {}),
                features=blueprint_data.get('features', []),
                tech_stack=blueprint_data.get('tech_stack', {}),
                file_structure=blueprint_data.get('file_structure', {}),
                dependencies=blueprint_data.get('dependencies', []),
                estimated_complexity=blueprint_data.get('estimated_complexity', 'moderate')
            )
            
            self.logger.info(f"Blueprint created for: {blueprint.project_name}")
            return blueprint
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse blueprint JSON: {e}")
            return self._create_fallback_blueprint(request)
        except Exception as e:
            self.logger.error(f"Error creating blueprint: {e}")
            return self._create_fallback_blueprint(request)
    
    def _create_fallback_blueprint(self, request: DesignRequest) -> ProjectBlueprint:
        """
        Create a basic fallback blueprint if LLM fails
        """
        self.logger.warning("Creating fallback blueprint")
        
        # Extract project name from prompt (simple heuristic)
        prompt_words = request.prompt.lower().split()
        project_type = "application"
        
        if "api" in prompt_words:
            project_type = "api"
        elif "website" in prompt_words or "web" in prompt_words:
            project_type = "website"
        elif "app" in prompt_words:
            project_type = "application"
        elif "tool" in prompt_words:
            project_type = "tool"
        
        return ProjectBlueprint(
            project_name=f"Custom {project_type.title()}",
            description=f"A custom {project_type} based on user requirements: {request.prompt}",
            architecture={
                "pattern": "layered",
                "components": ["frontend", "backend", "database"],
                "data_flow": "request_response",
                "scalability_considerations": "horizontal scaling"
            },
            features=[
                {
                    "name": "core_functionality",
                    "description": "Main application functionality",
                    "priority": "high",
                    "complexity": "moderate",
                    "dependencies": [],
                    "estimated_effort": "large"
                }
            ],
            tech_stack={
                "frontend": ["React", "TypeScript"],
                "backend": ["Python", "FastAPI"],
                "database": ["PostgreSQL"],
                "infrastructure": ["Docker"],
                "tools": ["Git", "npm"]
            },
            file_structure={
                "src": {
                    "components": {},
                    "services": {},
                    "utils": {}
                },
                "tests": {},
                "docs": {}
            },
            dependencies=["react", "fastapi", "postgresql"],
            estimated_complexity="moderate"
        )