"""
Task and dependency graph management for the LLM Swarm system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any
from enum import Enum
import logging


class TaskStatus(Enum):
    """Status of a task in the execution pipeline."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AgentType(Enum):
    """Types of specialized agents available."""
    FRONTEND = "frontend"
    BACKEND = "backend"
    DATABASE = "database"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    DEVOPS = "devops"
    SECURITY = "security"


@dataclass
class Task:
    """
    Represents a single task in the project generation pipeline.
    """
    id: str
    name: str
    description: str
    agent_type: AgentType
    dependencies: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    output: Optional[Any] = None
    error: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher number = higher priority
    estimated_duration: Optional[int] = None  # in minutes
    
    def __post_init__(self):
        """Validate task after initialization."""
        if not self.id:
            raise ValueError("Task ID cannot be empty")
        if not self.name:
            raise ValueError("Task name cannot be empty")
        if not isinstance(self.agent_type, AgentType):
            raise ValueError(f"Invalid agent type: {self.agent_type}")
    
    def is_ready(self, completed_tasks: Set[str]) -> bool:
        """
        Check if this task is ready to execute based on dependencies.
        
        Args:
            completed_tasks: Set of completed task IDs
            
        Returns:
            True if all dependencies are satisfied
        """
        return all(dep_id in completed_tasks for dep_id in self.dependencies)
    
    def mark_completed(self, output: Any = None):
        """Mark task as completed with optional output."""
        self.status = TaskStatus.COMPLETED
        self.output = output
        
    def mark_failed(self, error: str):
        """Mark task as failed with error message."""
        self.status = TaskStatus.FAILED
        self.error = error


class DependencyGraph:
    """
    Manages task dependencies and execution order.
    """
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_task(self, task: Task) -> None:
        """
        Add a task to the dependency graph.
        
        Args:
            task: Task to add
            
        Raises:
            ValueError: If task ID already exists
        """
        if task.id in self.tasks:
            raise ValueError(f"Task with ID '{task.id}' already exists")
        
        self.tasks[task.id] = task
        self.logger.debug(f"Added task: {task.id} ({task.name})")
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """
        Get all tasks that are ready to execute (dependencies satisfied).
        
        Returns:
            List of tasks ready for execution, sorted by priority
        """
        completed_tasks = {
            task_id for task_id, task in self.tasks.items() 
            if task.status == TaskStatus.COMPLETED
        }
        
        ready_tasks = [
            task for task in self.tasks.values()
            if task.status == TaskStatus.PENDING and task.is_ready(completed_tasks)
        ]
        
        # Sort by priority (higher first), then by dependency count (fewer first)
        ready_tasks.sort(key=lambda t: (-t.priority, len(t.dependencies)))
        
        return ready_tasks
    
    def get_execution_order(self) -> List[Task]:
        """
        Get the optimal execution order for all tasks using topological sort.
        
        Returns:
            List of tasks in execution order
            
        Raises:
            ValueError: If circular dependencies are detected
        """
        # Kahn's algorithm for topological sorting
        in_degree = {task_id: 0 for task_id in self.tasks}
        
        # Calculate in-degrees
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    raise ValueError(f"Task '{task.id}' depends on non-existent task '{dep_id}'")
                in_degree[task.id] += 1
        
        # Find tasks with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort by priority for consistent ordering
            queue.sort(key=lambda tid: -self.tasks[tid].priority)
            current_id = queue.pop(0)
            current_task = self.tasks[current_id]
            result.append(current_task)
            
            # Update in-degrees for dependent tasks
            for task in self.tasks.values():
                if current_id in task.dependencies:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task.id)
        
        # Check for circular dependencies
        if len(result) != len(self.tasks):
            remaining = set(self.tasks.keys()) - {t.id for t in result}
            raise ValueError(f"Circular dependencies detected involving tasks: {remaining}")
        
        return result
    
    def validate_dependencies(self) -> List[str]:
        """
        Validate all task dependencies.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        for task in self.tasks.values():
            for dep_id in task.dependencies:
                if dep_id not in self.tasks:
                    errors.append(f"Task '{task.id}' depends on non-existent task '{dep_id}'")
                elif dep_id == task.id:
                    errors.append(f"Task '{task.id}' cannot depend on itself")
        
        # Check for circular dependencies
        try:
            self.get_execution_order()
        except ValueError as e:
            errors.append(str(e))
        
        return errors
    
    def get_status_summary(self) -> Dict[TaskStatus, int]:
        """Get a summary of task statuses."""
        summary = {status: 0 for status in TaskStatus}
        for task in self.tasks.values():
            summary[task.status] += 1
        return summary
    
    def get_critical_path(self) -> List[Task]:
        """
        Calculate the critical path (longest path through dependencies).
        
        Returns:
            List of tasks on the critical path
        """
        # Simple implementation - can be enhanced with actual duration estimates
        execution_order = self.get_execution_order()
        
        # For now, return the longest dependency chain
        max_depth = 0
        critical_tasks = []
        
        def get_depth(task_id: str, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            if task_id in visited:
                return 0  # Avoid infinite recursion
            
            visited.add(task_id)
            task = self.tasks[task_id]
            
            if not task.dependencies:
                return 1
            
            max_dep_depth = max(
                get_depth(dep_id, visited.copy()) 
                for dep_id in task.dependencies
            )
            return max_dep_depth + 1
        
        for task in execution_order:
            depth = get_depth(task.id)
            if depth > max_depth:
                max_depth = depth
                # Rebuild critical path
                critical_tasks = self._build_critical_path(task.id)
        
        return critical_tasks
    
    def _build_critical_path(self, task_id: str) -> List[Task]:
        """Build the critical path ending at the given task."""
        path = []
        current_id = task_id
        
        while current_id:
            current_task = self.tasks[current_id]
            path.insert(0, current_task)
            
            # Find the dependency with the longest path
            if current_task.dependencies:
                next_id = max(
                    current_task.dependencies,
                    key=lambda dep_id: self._get_task_depth(dep_id)
                )
                current_id = next_id
            else:
                current_id = None
        
        return path
    
    def _get_task_depth(self, task_id: str) -> int:
        """Get the depth of a task in the dependency graph."""
        task = self.tasks[task_id]
        if not task.dependencies:
            return 1
        return max(self._get_task_depth(dep_id) for dep_id in task.dependencies) + 1