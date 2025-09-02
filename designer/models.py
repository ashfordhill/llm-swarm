"""
Designer data models

Shared data classes for the Designer LLM system to avoid circular imports.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
from datetime import datetime


@dataclass
class DesignRequest:
    """User's design request"""
    prompt: str
    requirements: List[str]
    constraints: List[str]
    preferences: Dict[str, Any]
    timestamp: str


@dataclass
class ProjectBlueprint:
    """Complete project blueprint"""
    project_name: str
    description: str
    architecture: Dict[str, Any]
    features: List[Dict[str, Any]]
    tech_stack: Dict[str, List[str]]
    file_structure: Dict[str, Any]
    dependencies: List[str]
    estimated_complexity: str


@dataclass
class AdapterPlan:
    """Plan for LoRA adapters needed"""
    required_adapters: List[Dict[str, Any]]
    adapter_dependencies: Dict[str, List[str]]
    training_priority: List[str]
    estimated_training_time: str


@dataclass
class WorkPlan:
    """Chunked work plan for specialized agents"""
    chunks: List[Dict[str, Any]]
    execution_order: List[str]
    dependencies: Dict[str, List[str]]
    estimated_duration: str


@dataclass
class DesignResult:
    """Complete design result"""
    request: DesignRequest
    blueprint: ProjectBlueprint
    adapter_plan: AdapterPlan
    work_plan: WorkPlan
    context_serialization: Dict[str, Any]
    orchestration_plan: Dict[str, Any]