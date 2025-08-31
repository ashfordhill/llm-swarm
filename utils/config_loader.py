"""
Configuration loading and management for the LLM Swarm system.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
import logging
from pydantic import BaseModel, Field, validator


class ModelConfig(BaseModel):
    """Configuration for a single model."""
    name: str
    type: str = Field(..., description="Type: 'api' or 'local'")
    model_id: str = Field(..., description="Model identifier or path")
    api_key_env: Optional[str] = Field(None, description="Environment variable for API key")
    api_base: Optional[str] = Field(None, description="API base URL")
    max_tokens: int = Field(2048, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")
    timeout: int = Field(60, description="Request timeout in seconds")
    
    # Local model specific settings
    device: str = Field("auto", description="Device for local models")
    quantization: Optional[str] = Field(None, description="Quantization method")
    max_memory: Optional[str] = Field(None, description="Maximum memory usage")
    
    @validator('type')
    def validate_type(cls, v):
        if v not in ['api', 'local']:
            raise ValueError("Model type must be 'api' or 'local'")
        return v


class AgentConfig(BaseModel):
    """Configuration for a specialized agent."""
    name: str
    agent_type: str
    model: str = Field(..., description="Model name to use")
    system_prompt_template: str = Field(..., description="System prompt template")
    max_retries: int = Field(3, description="Maximum retry attempts")
    enabled: bool = Field(True, description="Whether agent is enabled")


class OrchestratorConfig(BaseModel):
    """Configuration for the orchestrator."""
    model: str = Field(..., description="Model name to use")
    planning_prompt_template: str = Field(..., description="Planning prompt template")
    max_tasks: int = Field(50, description="Maximum number of tasks")
    parallel_execution: bool = Field(False, description="Enable parallel task execution")
    max_parallel_tasks: int = Field(3, description="Maximum parallel tasks")


class SystemConfig(BaseModel):
    """Main system configuration."""
    models: Dict[str, ModelConfig]
    agents: Dict[str, AgentConfig] 
    orchestrator: OrchestratorConfig
    output_settings: Dict[str, Any] = Field(default_factory=dict)
    logging: Dict[str, Any] = Field(default_factory=dict)


class ConfigLoader:
    """
    Loads and manages configuration for the LLM Swarm system.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the config loader.
        
        Args:
            config_path: Path to configuration file
        """
        self.logger = logging.getLogger(__name__)
        
        if config_path:
            self.config_path = Path(config_path)
        else:
            # Look for config in standard locations
            self.config_path = self._find_config_file()
        
        self.config: Optional[SystemConfig] = None
        self._load_config()
    
    def _find_config_file(self) -> Path:
        """Find configuration file in standard locations."""
        possible_paths = [
            Path("models/config.yaml"),
            Path("config.yaml"),
            Path("config/config.yaml"),
            Path.home() / ".llm-swarm" / "config.yaml"
        ]
        
        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Found config file: {path}")
                return path
        
        # Return default path if none found
        default_path = Path("models/config.yaml")
        self.logger.warning(f"No config file found, will create default at: {default_path}")
        return default_path
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path.exists():
            self.logger.warning(f"Config file not found: {self.config_path}")
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self.config = SystemConfig(**config_data)
            self.logger.info(f"Loaded configuration from: {self.config_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            self.logger.info("Creating default configuration...")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """Create a default configuration file."""
        default_config = {
            "models": {
                "orchestrator": {
                    "name": "orchestrator",
                    "type": "api",
                    "model_id": "gpt-4",
                    "api_key_env": "OPENAI_API_KEY",
                    "max_tokens": 4096,
                    "temperature": 0.3
                },
                "local_coder": {
                    "name": "local_coder", 
                    "type": "local",
                    "model_id": "microsoft/DialoGPT-medium",
                    "max_tokens": 2048,
                    "temperature": 0.7,
                    "device": "auto"
                }
            },
            "agents": {
                "frontend": {
                    "name": "Frontend Agent",
                    "agent_type": "frontend",
                    "model": "local_coder",
                    "system_prompt_template": "You are an expert frontend developer specializing in modern web technologies.",
                    "enabled": True
                },
                "backend": {
                    "name": "Backend Agent", 
                    "agent_type": "backend",
                    "model": "local_coder",
                    "system_prompt_template": "You are an expert backend developer specializing in server-side applications.",
                    "enabled": True
                },
                "database": {
                    "name": "Database Agent",
                    "agent_type": "database", 
                    "model": "local_coder",
                    "system_prompt_template": "You are an expert database developer specializing in schema design and queries.",
                    "enabled": True
                },
                "testing": {
                    "name": "Testing Agent",
                    "agent_type": "testing",
                    "model": "local_coder", 
                    "system_prompt_template": "You are an expert in software testing and quality assurance.",
                    "enabled": True
                },
                "documentation": {
                    "name": "Documentation Agent",
                    "agent_type": "documentation",
                    "model": "local_coder",
                    "system_prompt_template": "You are an expert technical writer specializing in software documentation.",
                    "enabled": True
                }
            },
            "orchestrator": {
                "model": "orchestrator",
                "planning_prompt_template": "You are a senior software architect. Analyze the project requirements and create a detailed implementation plan.",
                "max_tasks": 50,
                "parallel_execution": False
            },
            "output_settings": {
                "create_git_repo": True,
                "include_readme": True,
                "include_gitignore": True
            },
            "logging": {
                "level": "INFO",
                "file": "logs/llm-swarm.log"
            }
        }
        
        # Create directory if needed
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write default config
        with open(self.config_path, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        # Load the default config
        self.config = SystemConfig(**default_config)
        self.logger.info(f"Created default configuration at: {self.config_path}")
    
    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        if not self.config:
            return None
        return self.config.models.get(model_name)
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent."""
        if not self.config:
            return None
        return self.config.agents.get(agent_name)
    
    def get_orchestrator_config(self) -> Optional[OrchestratorConfig]:
        """Get orchestrator configuration."""
        if not self.config:
            return None
        return self.config.orchestrator
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent names."""
        if not self.config:
            return []
        return [
            name for name, config in self.config.agents.items()
            if config.enabled
        ]
    
    def validate_config(self) -> List[str]:
        """
        Validate the configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not self.config:
            errors.append("No configuration loaded")
            return errors
        
        # Check that orchestrator model exists
        orch_model = self.config.orchestrator.model
        if orch_model not in self.config.models:
            errors.append(f"Orchestrator model '{orch_model}' not found in models config")
        
        # Check that agent models exist
        for agent_name, agent_config in self.config.agents.items():
            if agent_config.model not in self.config.models:
                errors.append(f"Agent '{agent_name}' references non-existent model '{agent_config.model}'")
        
        # Check API keys for API models
        for model_name, model_config in self.config.models.items():
            if model_config.type == "api" and model_config.api_key_env:
                if not os.getenv(model_config.api_key_env):
                    errors.append(f"API key environment variable '{model_config.api_key_env}' not set for model '{model_name}'")
        
        return errors
    
    def reload_config(self) -> bool:
        """
        Reload configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self._load_config()
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload config: {e}")
            return False