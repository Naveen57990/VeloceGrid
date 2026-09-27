"""
VeloceGrid: Deterministic DAG Mesh Router
Compiles agentic workflows into directed acyclic dependency graphs for concurrent dispatch
across NVIDIA Nemotron models hosted on Nebius Token Factory.
"""

from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass, field
import collections

@dataclass
class DAGNode:
    node_id: str
    task_name: str
    model_tier: str  # e.g., "nvidia/nemotron-4-340b", "nvidia/nemotron-3-8b"
    prompt_template: str
    dependencies: List[str] = field(default_factory=list)
    token_limit: int = 2048
    artifact_type: str = "text"  # text, python, json, sql
    speculative_verification: bool = True
    status: str = "PENDING"  # PENDING, QUEUED, RUNNING, COMPLETED, FAILED, SPECULATIVE_REJECTED
    output: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_used: int = 0

class CyclicDependencyError(Exception):
    pass

class NodeNotFoundError(Exception):
    pass

class MeshRouter:
    def __init__(self):
        self.nodes: Dict[str, DAGNode] = {}
        self.edges: Dict[str, List[str]] = collections.defaultdict(list)  # parent -> [children]
        self.reverse_edges: Dict[str, List[str]] = collections.defaultdict(list)  # child -> [parents]

    def add_node(self, node: DAGNode) -> None:
        self.nodes[node.node_id] = node
        for dep in node.dependencies:
            self.edges[dep].append(node.node_id)
            self.reverse_edges[node.node_id].append(dep)

    def validate_graph(self) -> bool:
        """Validates all dependencies exist and checks for cycles using Kahn's algorithm."""
        in_degree = {n_id: 0 for n_id in self.nodes}
        for n_id, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise NodeNotFoundError(f"Dependency '{dep}' required by '{n_id}' does not exist.")
                in_degree[n_id] += 1

        queue = collections.deque([n_id for n_id, deg in in_degree.items() if deg == 0])
        visited_count = 0

        while queue:
            curr = queue.popleft()
            visited_count += 1
            for child in self.edges[curr]:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if visited_count != len(self.nodes):
            raise CyclicDependencyError("Cycle detected in agentic workflow DAG.")
        return True

    def get_executable_nodes(self) -> List[DAGNode]:
        """Returns all nodes whose dependencies are satisfied and are ready for execution."""
        executable = []
        for n_id, node in self.nodes.items():
            if node.status == "PENDING":
                deps_satisfied = all(
                    self.nodes[dep].status == "COMPLETED" for dep in node.dependencies
                )
                if deps_satisfied:
                    executable.append(node)
        return executable

    def get_topological_batches(self) -> List[List[str]]:
        """Returns execution stages (batches of nodes that can execute in parallel)."""
        self.validate_graph()
        in_degree = {n_id: len(node.dependencies) for n_id, node in self.nodes.items()}
        current_layer = [n_id for n_id, deg in in_degree.items() if deg == 0]
        batches = []

        while current_layer:
            batches.append(current_layer)
            next_layer = []
            for n_id in current_layer:
                for child in self.edges[n_id]:
                    in_degree[child] -= 1
                    if in_degree[child] == 0:
                        next_layer.append(child)
            current_layer = next_layer

        return batches
