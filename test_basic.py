#!/usr/bin/env python3
"""
Basic test to verify the LLM Swarm system components work.
"""

import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from utils.logger import setup_logging
from utils.config_loader import ConfigLoader
from utils.dependency_graph import DependencyGraph, Task, AgentType
from utils.file_manager import FileManager
from utils.prompt_templates import PromptTemplates


def test_config_loader():
    """Test configuration loading."""
    print("🧪 Testing ConfigLoader...")
    
    try:
        config_loader = ConfigLoader("models/config.yaml")
        
        # Test basic functionality
        assert config_loader.config is not None
        assert len(config_loader.config.models) > 0
        assert len(config_loader.config.agents) > 0
        
        # Test validation
        errors = config_loader.validate_config()
        if errors:
            print(f"⚠️  Config validation warnings: {errors}")
        
        print("✅ ConfigLoader test passed")
        return True
        
    except Exception as e:
        print(f"❌ ConfigLoader test failed: {e}")
        return False


def test_dependency_graph():
    """Test dependency graph functionality."""
    print("🧪 Testing DependencyGraph...")
    
    try:
        graph = DependencyGraph()
        
        # Create test tasks
        task1 = Task(
            id="task1",
            name="Setup",
            description="Setup project",
            agent_type=AgentType.BACKEND,
            dependencies=[],
            priority=10
        )
        
        task2 = Task(
            id="task2", 
            name="Database",
            description="Create database",
            agent_type=AgentType.DATABASE,
            dependencies=["task1"],
            priority=9
        )
        
        task3 = Task(
            id="task3",
            name="API",
            description="Create API",
            agent_type=AgentType.BACKEND,
            dependencies=["task2"],
            priority=8
        )
        
        # Add tasks
        graph.add_task(task1)
        graph.add_task(task2)
        graph.add_task(task3)
        
        # Test execution order
        execution_order = graph.get_execution_order()
        assert len(execution_order) == 3
        assert execution_order[0].id == "task1"
        assert execution_order[1].id == "task2"
        assert execution_order[2].id == "task3"
        
        # Test validation
        errors = graph.validate_dependencies()
        assert len(errors) == 0
        
        print("✅ DependencyGraph test passed")
        return True
        
    except Exception as e:
        print(f"❌ DependencyGraph test failed: {e}")
        return False


def test_file_manager():
    """Test file manager functionality."""
    print("🧪 Testing FileManager...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            file_manager = FileManager(temp_dir)
            
            # Test file writing
            test_content = "# Test File\nThis is a test."
            file_path = file_manager.write_file("test.md", test_content)
            
            assert file_path.exists()
            assert file_manager.file_exists("test.md")
            
            # Test file reading
            read_content = file_manager.read_file("test.md")
            assert read_content == test_content
            
            # Test multiple files
            files = {
                "src/main.py": "print('Hello, World!')",
                "README.md": "# My Project",
                "config.json": '{"name": "test"}'
            }
            
            written_files = file_manager.write_files(files)
            assert len(written_files) == 3
            
            # Test project structure
            structure = file_manager.get_project_structure()
            assert "src" in structure
            assert "main.py" in structure["src"]
            
            print("✅ FileManager test passed")
            return True
            
    except Exception as e:
        print(f"❌ FileManager test failed: {e}")
        return False


def test_prompt_templates():
    """Test prompt template functionality."""
    print("🧪 Testing PromptTemplates...")
    
    try:
        templates = PromptTemplates()
        
        # Test template loading
        template_names = templates.list_templates()
        assert len(template_names) > 0
        assert "orchestrator_planning" in template_names
        assert "frontend_system" in template_names
        
        # Test template rendering
        rendered = templates.render_template(
            "frontend_system",
            agent_name="Test Agent",
            agent_type="frontend"
        )
        
        assert len(rendered) > 0
        assert "frontend developer" in rendered.lower()
        
        print("✅ PromptTemplates test passed")
        return True
        
    except Exception as e:
        print(f"❌ PromptTemplates test failed: {e}")
        return False


def test_logging():
    """Test logging setup."""
    print("🧪 Testing logging...")
    
    try:
        import logging
        
        # Setup logging
        setup_logging()
        
        # Test logging
        logger = logging.getLogger("test")
        logger.info("Test log message")
        
        print("✅ Logging test passed")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Running LLM Swarm Basic Tests")
    print("=" * 50)
    
    tests = [
        test_logging,
        test_config_loader,
        test_dependency_graph,
        test_file_manager,
        test_prompt_templates
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())