import networkx as nx
from typing import Any
from src.schema import BaseNode, BaseEdge

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.nodes: dict[str, BaseNode] = {}
        self.edges: list[BaseEdge] = []

    def add_node(self, node: BaseNode) -> None:
        self.nodes[node.id] = node
        self.graph.add_node(node.id, **node.model_dump())

    def add_edge(self, edge: BaseEdge) -> None:
        self.edges.append(edge)
        self.graph.add_edge(
            edge.source,
            edge.target,
            key=len(self.graph.get_edge_data(edge.source, edge.target) or []),
            **edge.model_dump(),
        )

    def add_nodes(self, nodes: list[BaseNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def add_edges(self, edges: list[BaseEdge]) -> None:
        for edge in edges:
            self.add_edge(edge)

    def get_node(self, node_id: str) -> BaseNode | None:
        return self.nodes.get(node_id)

    def get_edges(self, source: str, target: str) -> list[BaseEdge]:
        return [e for e in self.edges if e.source == source and e.target == target]

    def to_dict(self) -> dict[str, Any]:
        return {
            "nodes": [n.model_dump() for n in self.nodes.values()],
            "edges": [e.model_dump() for e in self.edges],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "KnowledgeGraph":
        kg = cls()
        for node_data in data.get("nodes", []):
            node = BaseNode.model_validate(node_data)
            kg.add_node(node)
        for edge_data in data.get("edges", []):
            kg.add_edge(BaseEdge.model_validate(edge_data))
        return kg


def load_graph(path) -> KnowledgeGraph:
    import json
    from pathlib import Path

    graph_path = Path(path)
    if not graph_path.exists():
        raise FileNotFoundError(f"Knowledge graph not found: {graph_path}")
    return KnowledgeGraph.from_dict(json.loads(graph_path.read_text(encoding="utf-8")))


def build_graph(
    pep_nodes: list,
    concept_nodes: list = None,
    construct_nodes: list = None,
    objection_nodes: list = None,
    argument_nodes: list = None,
    alternative_nodes: list = None,
    decision_nodes: list = None,
    person_nodes: list = None,
    version_nodes: list = None,
    edges: list = None,
) -> KnowledgeGraph:
    kg = KnowledgeGraph()

    all_nodes = []
    all_nodes.extend(pep_nodes or [])
    all_nodes.extend(concept_nodes or [])
    all_nodes.extend(construct_nodes or [])
    all_nodes.extend(objection_nodes or [])
    all_nodes.extend(argument_nodes or [])
    all_nodes.extend(alternative_nodes or [])
    all_nodes.extend(decision_nodes or [])
    all_nodes.extend(person_nodes or [])
    all_nodes.extend(version_nodes or [])

    kg.add_nodes(all_nodes)
    if edges:
        kg.add_edges(edges)

    return kg


if __name__ == "__main__":
    kg = KnowledgeGraph()
    print("KnowledgeGraph class ready")