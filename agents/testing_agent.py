"""
Testing specialized agent for the LLM Swarm system.
"""

from .base_agent import SMEAgent
from utils.dependency_graph import AgentType


class TestingAgent(SMEAgent):
    """
    Specialized agent for testing tasks.
    Handles unit tests, integration tests, and test automation.
    """
    
    def __init__(self, config, model_config):
        """Initialize the testing agent."""
        super().__init__(
            name="Testing Agent",
            agent_type=AgentType.TESTING,
            config=config,
            model_config=model_config
        )
    
    def _guess_file_extension(self) -> str:
        """Testing-specific file extension guessing."""
        # Default to Python for test files
        return "py"
    
    def _parse_response(self, response: str, task):
        """Enhanced parsing for testing-specific files."""
        output = super()._parse_response(response, task)
        
        # Post-process test files
        processed_files = {}
        for filename, content in output.files.items():
            # Ensure proper file extensions and naming for test files
            if not any(filename.endswith(ext) for ext in ['.py', '.js', '.ts', '.java', '.go']):
                # Guess extension based on content
                if any(py_keyword in content for py_keyword in ['def test_', 'import pytest', 'import unittest', 'assert ']):
                    filename = filename.rsplit('.', 1)[0] + '.py'
                elif any(js_keyword in content for js_keyword in ['describe(', 'it(', 'test(', 'expect(']):
                    filename = filename.rsplit('.', 1)[0] + '.js'
                elif '@Test' in content or 'import org.junit' in content:
                    filename = filename.rsplit('.', 1)[0] + '.java'
            
            # Ensure test files have proper naming convention
            base_name = filename.rsplit('.', 1)[0]
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'py'
            
            if not any(test_prefix in base_name.lower() for test_prefix in ['test_', '_test', 'test']):
                if not base_name.lower().startswith('test'):
                    base_name = f"test_{base_name}"
            
            filename = f"{base_name}.{extension}"
            processed_files[filename] = content
        
        output.files = processed_files
        return output