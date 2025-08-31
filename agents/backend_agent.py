"""
Backend specialized agent for the LLM Swarm system.
"""

from .base_agent import SMEAgent
from utils.dependency_graph import AgentType


class BackendAgent(SMEAgent):
    """
    Specialized agent for backend development tasks.
    Handles server-side logic, APIs, and business functionality.
    """
    
    def __init__(self, config, model_config):
        """Initialize the backend agent."""
        super().__init__(
            name="Backend Agent",
            agent_type=AgentType.BACKEND,
            config=config,
            model_config=model_config
        )
    
    def _guess_file_extension(self) -> str:
        """Backend-specific file extension guessing."""
        # Default to Python for backend logic
        return "py"
    
    def _parse_response(self, response: str, task):
        """Enhanced parsing for backend-specific files."""
        output = super()._parse_response(response, task)
        
        # Post-process backend files
        processed_files = {}
        for filename, content in output.files.items():
            # Ensure proper file extensions for backend files
            if not any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go', '.rs', '.php']):
                # Guess extension based on content
                if any(py_keyword in content for py_keyword in ['def ', 'import ', 'from ', 'class ']):
                    filename = filename.rsplit('.', 1)[0] + '.py'
                elif any(js_keyword in content for js_keyword in ['const ', 'let ', 'var ', 'function ', 'require(']):
                    filename = filename.rsplit('.', 1)[0] + '.js'
                elif 'package ' in content and 'public class' in content:
                    filename = filename.rsplit('.', 1)[0] + '.java'
            
            processed_files[filename] = content
        
        output.files = processed_files
        return output