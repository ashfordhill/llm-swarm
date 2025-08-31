"""
Frontend specialized agent for the LLM Swarm system.
"""

from .base_agent import SMEAgent
from utils.dependency_graph import AgentType


class FrontendAgent(SMEAgent):
    """
    Specialized agent for frontend development tasks.
    Handles UI/UX, React, HTML/CSS, and client-side logic.
    """
    
    def __init__(self, config, model_config):
        """Initialize the frontend agent."""
        super().__init__(
            name="Frontend Agent",
            agent_type=AgentType.FRONTEND,
            config=config,
            model_config=model_config
        )
    
    def _guess_file_extension(self) -> str:
        """Frontend-specific file extension guessing."""
        # Default to JSX for React components
        return "jsx"
    
    def _parse_response(self, response: str, task):
        """Enhanced parsing for frontend-specific files."""
        output = super()._parse_response(response, task)
        
        # Post-process frontend files
        processed_files = {}
        for filename, content in output.files.items():
            # Ensure proper file extensions for frontend files
            if not any(filename.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx', '.html', '.css', '.scss']):
                # Guess extension based on content
                if 'import React' in content or 'export default' in content:
                    filename = filename.rsplit('.', 1)[0] + '.jsx'
                elif '<html' in content or '<!DOCTYPE' in content:
                    filename = filename.rsplit('.', 1)[0] + '.html'
                elif any(css_keyword in content for css_keyword in ['@media', 'display:', 'margin:', 'padding:']):
                    filename = filename.rsplit('.', 1)[0] + '.css'
            
            processed_files[filename] = content
        
        output.files = processed_files
        return output