"""
DAG Definition and Execution Engine
Defines pipeline dependencies and executes nodes in order
"""
import logging
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any, Optional
from enum import Enum

from orchestrator.context import RunContext
from orchestrator.errors import AgentExecutionError

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    """Node execution status"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class DAGNode:
    """
    Represents a single node in the pipeline DAG
    
    Attributes:
        name: Node identifier
        fn: Callable to execute (receives RunContext, returns result dict)
        dependencies: List of node names that must complete first
        status: Current execution status
        result: Execution result
        error: Error message if failed
    """
    name: str
    fn: Callable[[RunContext], Dict[str, Any]]
    dependencies: List[str] = field(default_factory=list)
    status: NodeStatus = NodeStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    def can_run(self, completed_nodes: set) -> bool:
        """Check if all dependencies are met"""
        return all(dep in completed_nodes for dep in self.dependencies)
    
    def execute(self, ctx: RunContext) -> Dict[str, Any]:
        """Execute the node function"""
        self.status = NodeStatus.RUNNING
        logger.info(f"[{ctx.correlation_id[:8]}] Executing node: {self.name}")
        
        try:
            self.result = self.fn(ctx)
            self.status = NodeStatus.SUCCESS
            logger.info(f"[{ctx.correlation_id[:8]}] Node {self.name} completed successfully")
            return self.result
        
        except Exception as e:
            self.status = NodeStatus.FAILED
            self.error = str(e)
            logger.error(f"[{ctx.correlation_id[:8]}] Node {self.name} failed: {e}", exc_info=True)
            raise AgentExecutionError(self.name, str(e))


class DAG:
    """
    Directed Acyclic Graph for pipeline orchestration
    """
    
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
    
    def add_node(self, node: DAGNode) -> None:
        """Add a node to the DAG"""
        if node.name in self.nodes:
            raise ValueError(f"Node {node.name} already exists")
        self.nodes[node.name] = node
        logger.debug(f"Added node: {node.name} (deps: {node.dependencies})")
    
    def validate(self) -> None:
        """
        Validate DAG structure
        - All dependencies exist
        - No cycles
        """
        # Check dependencies exist
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Node {node.name} depends on non-existent node {dep}")
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node_name: str) -> bool:
            visited.add(node_name)
            rec_stack.add(node_name)
            
            for dep in self.nodes[node_name].dependencies:
                if dep not in visited:
                    if has_cycle(dep):
                        return True
                elif dep in rec_stack:
                    return True
            
            rec_stack.remove(node_name)
            return False
        
        for node_name in self.nodes:
            if node_name not in visited:
                if has_cycle(node_name):
                    raise ValueError("DAG contains a cycle")
    
    def get_execution_order(self) -> List[str]:
        """
        Get topological sort of nodes for execution order
        
        Returns:
            List of node names in execution order
        """
        # Kahn's algorithm
        in_degree = {name: 0 for name in self.nodes}
        
        for node in self.nodes.values():
            for dep in node.dependencies:
                in_degree[dep] = in_degree.get(dep, 0)  # Ensure dep exists
        
        # Count incoming edges (reverse dependencies)
        for node in self.nodes.values():
            for dep in node.dependencies:
                in_degree[node.name] += 1
        
        # Queue nodes with no incoming edges
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort for deterministic order when multiple nodes available
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            # Reduce in-degree for dependents
            for node in self.nodes.values():
                if current in node.dependencies:
                    in_degree[node.name] -= 1
                    if in_degree[node.name] == 0:
                        queue.append(node.name)
        
        if len(result) != len(self.nodes):
            raise ValueError("DAG contains a cycle (topological sort failed)")
        
        return result
    
    def execute(self, ctx: RunContext, fail_fast: bool = False) -> Dict[str, Any]:
        """
        Execute all nodes in topological order
        
        Args:
            ctx: Run context
            fail_fast: If True, stop on first failure; if False, skip dependents
            
        Returns:
            Summary dict with node statuses
        """
        self.validate()
        execution_order = self.get_execution_order()
        
        logger.info(f"[{ctx.correlation_id[:8]}] Execution order: {' → '.join(execution_order)}")
        
        completed = set()
        failed = set()
        
        for node_name in execution_order:
            node = self.nodes[node_name]
            
            # Skip if dependencies failed
            if any(dep in failed for dep in node.dependencies):
                node.status = NodeStatus.SKIPPED
                logger.warning(f"[{ctx.correlation_id[:8]}] Skipping {node_name} (dependency failed)")
                continue
            
            # Execute
            try:
                node.execute(ctx)
                completed.add(node_name)
            
            except AgentExecutionError as e:
                failed.add(node_name)
                ctx.add_error(node_name, str(e))
                
                if fail_fast:
                    logger.error(f"[{ctx.correlation_id[:8]}] Fail-fast enabled, stopping execution")
                    break
                else:
                    logger.warning(f"[{ctx.correlation_id[:8]}] Continuing despite failure in {node_name}")
        
        # Summary
        summary = {
            'total_nodes': len(self.nodes),
            'completed': len(completed),
            'failed': len(failed),
            'skipped': sum(1 for n in self.nodes.values() if n.status == NodeStatus.SKIPPED),
            'node_statuses': {name: node.status.value for name, node in self.nodes.items()},
            'execution_order': execution_order
        }
        
        logger.info(
            f"[{ctx.correlation_id[:8]}] DAG execution complete: "
            f"{summary['completed']} completed, {summary['failed']} failed, {summary['skipped']} skipped"
        )
        
        return summary

