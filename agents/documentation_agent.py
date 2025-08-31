"""
Documentation specialized agent for the LLM Swarm system.
"""

from .base_agent import SMEAgent
from utils.dependency_graph import AgentType


class DocumentationAgent(SMEAgent):
    """
    Specialized agent for documentation tasks.
    Handles README files, API docs, and user guides.
    """
    
    def __init__(self, config, model_config):
        """Initialize the documentation agent."""
        super().__init__(
            name="Documentation Agent",
            agent_type=AgentType.DOCUMENTATION,
            config=config,
            model_config=model_config
        )
    
    def _guess_file_extension(self) -> str:
        """Documentation-specific file extension guessing."""
        # Default to Markdown for documentation
        return "md"
    
    def _parse_response(self, response: str, task):
        """Enhanced parsing for documentation-specific files."""
        output = super()._parse_response(response, task)
        
        # Post-process documentation files
        processed_files = {}
        for filename, content in output.files.items():
            # Ensure proper file extensions for documentation files
            if not any(filename.endswith(ext) for ext in ['.md', '.rst', '.txt', '.html', '.pdf']):
                # Guess extension based on content
                if any(md_indicator in content for md_indicator in ['# ', '## ', '### ', '- ', '* ', '```']):
                    filename = filename.rsplit('.', 1)[0] + '.md'
                elif content.startswith('=') or '.. ' in content:
                    filename = filename.rsplit('.', 1)[0] + '.rst'
                elif '<html' in content or '<!DOCTYPE' in content:
                    filename = filename.rsplit('.', 1)[0] + '.html'
                else:
                    filename = filename.rsplit('.', 1)[0] + '.md'  # Default to markdown
            
            # Ensure proper naming for common documentation files
            base_name = filename.rsplit('.', 1)[0].lower()
            extension = filename.rsplit('.', 1)[1] if '.' in filename else 'md'
            
            # Standardize common documentation file names
            if base_name in ['readme', 'read_me']:
                filename = f"README.{extension}"
            elif base_name in ['changelog', 'change_log']:
                filename = f"CHANGELOG.{extension}"
            elif base_name in ['license', 'licence']:
                filename = f"LICENSE.{extension}"
            elif base_name in ['contributing', 'contribute']:
                filename = f"CONTRIBUTING.{extension}"
            
            processed_files[filename] = content
        
        output.files = processed_files
        return output