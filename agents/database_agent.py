"""
Database specialized agent for the LLM Swarm system.
"""

from .base_agent import SMEAgent
from utils.dependency_graph import AgentType


class DatabaseAgent(SMEAgent):
    """
    Specialized agent for database development tasks.
    Handles schema design, models, and database setup.
    """
    
    def __init__(self, config, model_config):
        """Initialize the database agent."""
        super().__init__(
            name="Database Agent",
            agent_type=AgentType.DATABASE,
            config=config,
            model_config=model_config
        )
    
    def _guess_file_extension(self) -> str:
        """Database-specific file extension guessing."""
        # Default to SQL for database schemas
        return "sql"
    
    def _parse_response(self, response: str, task):
        """Enhanced parsing for database-specific files."""
        output = super()._parse_response(response, task)
        
        # Post-process database files
        processed_files = {}
        for filename, content in output.files.items():
            # Ensure proper file extensions for database files
            if not any(filename.endswith(ext) for ext in ['.sql', '.py', '.js', '.ts', '.json']):
                # Guess extension based on content
                if any(sql_keyword in content.upper() for sql_keyword in ['CREATE TABLE', 'SELECT ', 'INSERT ', 'UPDATE ', 'DELETE ']):
                    filename = filename.rsplit('.', 1)[0] + '.sql'
                elif any(py_keyword in content for py_keyword in ['class ', 'def ', 'from sqlalchemy', 'from django']):
                    filename = filename.rsplit('.', 1)[0] + '.py'
                elif 'mongoose' in content or 'Schema' in content:
                    filename = filename.rsplit('.', 1)[0] + '.js'
            
            processed_files[filename] = content
        
        output.files = processed_files
        return output