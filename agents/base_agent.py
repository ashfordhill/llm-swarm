"""
Base agent classes for the LLM Swarm system.
"""

import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass
import re

from utils.dependency_graph import Task, TaskStatus, AgentType
from utils.prompt_templates import PromptTemplates
from utils.config_loader import ModelConfig, AgentConfig

# Import torch only when needed for local models
try:
    import torch
except ImportError:
    torch = None


@dataclass
class AgentOutput:
    """Output from an agent execution."""
    success: bool
    files: Dict[str, str] = None  # filename -> content
    summary: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.files is None:
            self.files = {}
        if self.metadata is None:
            self.metadata = {}


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the LLM Swarm system.
    """
    
    def __init__(self, name: str, agent_type: AgentType, config: AgentConfig, model_config: ModelConfig):
        """
        Initialize the base agent.
        
        Args:
            name: Agent name
            agent_type: Type of agent
            config: Agent configuration
            model_config: Model configuration
        """
        self.name = name
        self.agent_type = agent_type
        self.config = config
        self.model_config = model_config
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Initialize prompt templates
        self.prompt_templates = PromptTemplates()
        
        # Track execution statistics
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }
    
    @abstractmethod
    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response using the agent's model.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
        """
        pass
    
    def run_task(self, task: Task, project_context: Dict[str, Any] = None) -> AgentOutput:
        """
        Execute a task using this agent.
        
        Args:
            task: Task to execute
            project_context: Global project context
            
        Returns:
            Agent output with results
        """
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting task: {task.name}")
            
            # Validate that this agent can handle the task
            if task.agent_type != self.agent_type:
                error_msg = f"Agent type mismatch: task requires {task.agent_type}, agent is {self.agent_type}"
                self.logger.error(error_msg)
                return AgentOutput(success=False, error=error_msg)
            
            # Prepare the prompt
            prompt = self._prepare_prompt(task, project_context or {})
            
            # Generate response with retries
            response = self._generate_with_retries(prompt)
            
            # Parse the response into files
            output = self._parse_response(response, task)
            
            # Update statistics
            execution_time = time.time() - start_time
            self._update_stats(execution_time, success=True)
            
            self.logger.info(f"Completed task: {task.name} ({execution_time:.2f}s)")
            return output
            
        except Exception as e:
            execution_time = time.time() - start_time
            self._update_stats(execution_time, success=False)
            
            error_msg = f"Task execution failed: {str(e)}"
            self.logger.error(error_msg)
            return AgentOutput(success=False, error=error_msg)
    
    def _prepare_prompt(self, task: Task, project_context: Dict[str, Any]) -> str:
        """
        Prepare the prompt for the task.
        
        Args:
            task: Task to execute
            project_context: Global project context
            
        Returns:
            Formatted prompt
        """
        # Get system prompt template
        system_template_name = f"{self.agent_type.value}_system"
        system_prompt = self.prompt_templates.render_template(
            system_template_name,
            agent_name=self.name,
            agent_type=self.agent_type.value
        )
        
        # Get task prompt template
        task_template_name = f"{self.agent_type.value}_task"
        task_prompt = self.prompt_templates.render_template(
            task_template_name,
            task_description=task.description,
            project_context=project_context.get("description", ""),
            dependencies=task.context.get("completed_dependencies", [])
        )
        
        # Combine system and task prompts
        full_prompt = f"{system_prompt}\n\n{task_prompt}"
        
        self.logger.debug(f"Prepared prompt for task {task.id} ({len(full_prompt)} chars)")
        return full_prompt
    
    def _generate_with_retries(self, prompt: str) -> str:
        """
        Generate response with retry logic.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated response
            
        Raises:
            Exception: If all retries fail
        """
        max_retries = self.config.max_retries
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    self.logger.warning(f"Retry attempt {attempt}/{max_retries}")
                
                response = self._generate_response(prompt)
                
                if response and response.strip():
                    return response
                else:
                    raise ValueError("Empty response from model")
                    
            except Exception as e:
                last_error = e
                self.logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
        
        raise Exception(f"All {max_retries + 1} generation attempts failed. Last error: {last_error}")
    
    def _parse_response(self, response: str, task: Task) -> AgentOutput:
        """
        Parse the agent's response into structured output.
        
        Args:
            response: Raw response from the model
            task: Original task
            
        Returns:
            Parsed agent output
        """
        files = {}
        summary = ""
        
        # Look for code blocks with filenames
        # Pattern: ```filename: path/to/file.ext
        file_pattern = r'```filename:\s*([^\n]+)\n(.*?)```'
        matches = re.findall(file_pattern, response, re.DOTALL)
        
        if matches:
            for filename, content in matches:
                filename = filename.strip()
                content = content.strip()
                files[filename] = content
                self.logger.debug(f"Extracted file: {filename} ({len(content)} chars)")
        else:
            # Fallback: look for generic code blocks
            code_pattern = r'```(?:\w+)?\n(.*?)```'
            code_matches = re.findall(code_pattern, response, re.DOTALL)
            
            if code_matches:
                # If only one code block, use task name as filename
                if len(code_matches) == 1:
                    # Guess file extension based on agent type
                    ext = self._guess_file_extension()
                    filename = f"{task.name.lower().replace(' ', '_')}.{ext}"
                    files[filename] = code_matches[0].strip()
                else:
                    # Multiple code blocks, number them
                    ext = self._guess_file_extension()
                    for i, content in enumerate(code_matches):
                        filename = f"{task.name.lower().replace(' ', '_')}_{i+1}.{ext}"
                        files[filename] = content.strip()
        
        # Extract summary (text before first code block or entire response if no code)
        if files:
            # Find the first code block and use text before it as summary
            first_code_pos = response.find('```')
            if first_code_pos > 0:
                summary = response[:first_code_pos].strip()
        else:
            # No code blocks found, entire response is summary
            summary = response.strip()
        
        # Clean up summary
        if len(summary) > 500:
            summary = summary[:500] + "..."
        
        return AgentOutput(
            success=True,
            files=files,
            summary=summary or f"Completed {task.name}",
            metadata={
                "task_id": task.id,
                "agent_type": self.agent_type.value,
                "response_length": len(response),
                "files_generated": len(files)
            }
        )
    
    def _guess_file_extension(self) -> str:
        """Guess appropriate file extension based on agent type."""
        extensions = {
            AgentType.FRONTEND: "jsx",
            AgentType.BACKEND: "py",
            AgentType.DATABASE: "sql",
            AgentType.TESTING: "py",
            AgentType.DOCUMENTATION: "md"
        }
        return extensions.get(self.agent_type, "txt")
    
    def _update_stats(self, execution_time: float, success: bool) -> None:
        """Update execution statistics."""
        if success:
            self.stats["tasks_completed"] += 1
        else:
            self.stats["tasks_failed"] += 1
        
        self.stats["total_execution_time"] += execution_time
        
        total_tasks = self.stats["tasks_completed"] + self.stats["tasks_failed"]
        if total_tasks > 0:
            self.stats["average_execution_time"] = self.stats["total_execution_time"] / total_tasks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent execution statistics."""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """Reset execution statistics."""
        self.stats = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0
        }


class SMEAgent(BaseAgent):
    """
    Subject Matter Expert agent supporting both local and API models.
    """
    
    def __init__(self, name: str, agent_type: AgentType, config: AgentConfig, model_config: ModelConfig):
        """Initialize SME agent."""
        super().__init__(name, agent_type, config, model_config)
        self.model = None
        self.tokenizer = None
        self.api_client = None
        
        # Load model based on type
        if self.model_config.type == "local":
            self._load_local_model()
        elif self.model_config.type == "api":
            self._load_api_client()
        else:
            raise ValueError(f"Unsupported model type: {self.model_config.type}")
    
    def _load_local_model(self) -> None:
        """Load the local model for this agent."""
        try:
            self.logger.info(f"Loading local model: {self.model_config.model_id}")
            
            # Import here to avoid loading transformers if not needed
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_config.model_id,
                trust_remote_code=True
            )
            
            # Add pad token if missing
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Load model with appropriate settings
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": "auto"
            }
            
            if self.model_config.device == "auto":
                model_kwargs["device_map"] = "auto"
            
            if self.model_config.quantization:
                if self.model_config.quantization == "4bit":
                    from transformers import BitsAndBytesConfig
                    model_kwargs["quantization_config"] = BitsAndBytesConfig(
                        load_in_4bit=True,
                        bnb_4bit_compute_dtype="float16"
                    )
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_config.model_id,
                **model_kwargs
            )
            
            self.logger.info("Model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def _generate_response(self, prompt: str) -> str:
        """Generate response using the local model."""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt,
                return_tensors="pt",
                truncation=True,
                max_length=self.tokenizer.model_max_length - self.model_config.max_tokens
            )
            
            # Move to same device as model
            if hasattr(self.model, 'device'):
                inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.model_config.max_tokens,
                    temperature=self.model_config.temperature,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode response (skip the input tokens)
            input_length = inputs["input_ids"].shape[1]
            response_tokens = outputs[0][input_length:]
            response = self.tokenizer.decode(response_tokens, skip_special_tokens=True)
            
            return response.strip()
            
        except Exception as e:
            self.logger.error(f"Generation failed: {e}")
            raise
    
    def __del__(self):
        """Cleanup model resources."""
        if hasattr(self, 'model') and self.model is not None:
            del self.model
        if hasattr(self, 'tokenizer') and self.tokenizer is not None:
            del self.tokenizer