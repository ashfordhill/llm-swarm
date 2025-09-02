#!/usr/bin/env python3
"""
Test script to verify the Phase 2.1 context fix works correctly.
This tests that agents receive proper tech stack information and generate correct framework code.
"""

import os
import sys
import json
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from designer.chunk_executor import ChunkExecutor
from designer.models import ProjectBlueprint
from utils.config_loader import ConfigLoader

def setup_logging():
    """Setup logging for the test"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def create_test_blueprint():
    """Create a test blueprint with React tech stack"""
    return ProjectBlueprint(
        project_name="TestReactApp",
        description="A test React application to verify context passing",
        architecture={
            "pattern": "MVC",
            "components": ["UI", "Controller", "Model"]
        },
        features=[
            {
                "name": "Like Button",
                "description": "A button component that allows users to like posts",
                "priority": "medium",
                "complexity": "simple"
            }
        ],
        tech_stack={
            "frontend": ["HTML", "CSS", "JavaScript", "React"],
            "backend": ["Node.js", "Express"],
            "database": ["MongoDB"]
        },
        file_structure={
            "src": {
                "components": {},
                "App.js": {}
            }
        },
        dependencies=["react", "react-dom"],
        estimated_complexity="simple"
    )

def create_test_chunk():
    """Create a test chunk for frontend component"""
    return {
        "id": "test_chunk_1",
        "name": "Create Like Button Component",
        "description": "Create a React component for liking posts with proper state management",
        "scope": ["src/components/LikeButton.jsx"],
        "adapter_required": "frontend_react",
        "inputs": ["project_requirements"],
        "outputs": ["like_button_component"],
        "dependencies": [],
        "estimated_effort": "small",
        "priority": "medium"
    }

def create_test_context_serialization():
    """Create test context serialization"""
    return {
        "global_context": {
            "project_overview": {
                "name": "TestReactApp",
                "description": "A test React application to verify context passing",
                "tech_stack": {
                    "frontend": ["HTML", "CSS", "JavaScript", "React"],
                    "backend": ["Node.js", "Express"],
                    "database": ["MongoDB"]
                }
            }
        },
        "chunk_contexts": {
            "test_chunk_1": {
                "chunk_scope": ["src/components/LikeButton.jsx"],
                "constraints": ["React knowledge"]
            }
        }
    }

def test_context_creation():
    """Test that context is created correctly with framework information"""
    print("🧪 Testing context creation...")
    
    # Load config
    config_loader = ConfigLoader()
    config = config_loader.config
    
    # Create chunk executor
    executor = ChunkExecutor(config)
    
    # Create test data
    blueprint = create_test_blueprint()
    chunk = create_test_chunk()
    context_serialization = create_test_context_serialization()
    
    # Test context creation
    context = executor._create_chunk_context(chunk, blueprint, context_serialization)
    
    # Verify context contains tech stack info
    assert 'tech_stack' in context, "Context missing tech_stack"
    assert 'framework_context' in context, "Context missing framework_context"
    
    tech_stack = context['tech_stack']
    framework_context = context['framework_context']
    
    print(f"✅ Tech stack: {tech_stack}")
    print(f"✅ Framework context: {framework_context}")
    
    # Verify React is properly identified
    assert 'React' in tech_stack['frontend'], "React not found in frontend tech stack"
    assert framework_context['primary_frameworks']['frontend'] == 'React', "React not identified as primary frontend framework"
    
    # Verify React-specific instructions are present
    instructions = framework_context['specific_instructions']
    react_instructions = [inst for inst in instructions if 'React' in inst or 'JSX' in inst]
    assert len(react_instructions) > 0, "No React-specific instructions found"
    
    print("✅ Context creation test passed!")
    return context

def test_enhanced_context_formatting():
    """Test that the enhanced context is formatted correctly for agents"""
    print("\n🧪 Testing enhanced context formatting...")
    
    # Load config and create a mock agent
    config_loader = ConfigLoader()
    config = config_loader.config
    
    # Import here to avoid circular imports
    from agents.frontend_agent import FrontendAgent
    from utils.config_loader import ModelConfig
    
    model_config = ModelConfig(
        name="test_model",
        type="api",
        model_id="gpt-3.5-turbo",
        max_tokens=2000,
        temperature=0.7
    )
    
    agent = FrontendAgent(config, model_config)
    
    # Create test context (same as above)
    executor = ChunkExecutor(config)
    blueprint = create_test_blueprint()
    chunk = create_test_chunk()
    context_serialization = create_test_context_serialization()
    context = executor._create_chunk_context(chunk, blueprint, context_serialization)
    
    # Test enhanced context creation
    enhanced_context = agent._create_enhanced_context(context)
    
    print(f"Enhanced context:\n{enhanced_context}")
    
    # Verify key information is present
    assert "React" in enhanced_context, "React not mentioned in enhanced context"
    assert "Frontend: HTML, CSS, JavaScript, React" in enhanced_context, "Tech stack not properly formatted"
    assert "Use JSX syntax, not Vue template syntax" in enhanced_context, "React-specific instruction missing"
    
    print("✅ Enhanced context formatting test passed!")
    return enhanced_context

def main():
    """Run all tests"""
    print("🚀 Testing Phase 2.1 Context Fix")
    print("=" * 50)
    
    setup_logging()
    
    try:
        # Test 1: Context creation
        context = test_context_creation()
        
        # Test 2: Enhanced context formatting
        enhanced_context = test_enhanced_context_formatting()
        
        print("\n" + "=" * 50)
        print("🎉 All tests passed! Context fix is working correctly.")
        print("\nKey improvements:")
        print("✅ Tech stack information is properly extracted from blueprint")
        print("✅ Framework-specific context is created with React instructions")
        print("✅ Enhanced context includes React examples and constraints")
        print("✅ Agents will now receive proper framework guidance")
        
        print(f"\nNext step: Test with real execution:")
        print("python main.py design project -p 'Build a simple React todo app' -o ./test_context_fix")
        print("python main.py design execute ./test_context_fix")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()