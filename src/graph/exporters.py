import json
from pathlib import Path
import networkx as nx
from src.graph.builder import KnowledgeGraph


def export_json(kg: KnowledgeGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = kg.to_dict()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def export_graphml(kg: KnowledgeGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    import copy
    g = copy.deepcopy(kg.graph)
    for node_id, attrs in g.nodes(data=True):
        for key, value in list(attrs.items()):
            if isinstance(value, (dict, list)):
                attrs[key] = json.dumps(value, ensure_ascii=False)
    for u, v, key, attrs in g.edges(keys=True, data=True):
        for attr_key, value in list(attrs.items()):
            if isinstance(value, (dict, list)):
                attrs[attr_key] = json.dumps(value, ensure_ascii=False)
    nx.write_graphml(g, path)


def export_mermaid(kg: KnowledgeGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["graph TD"]

    pep_nodes = [n for n in kg.nodes.values() if n.type == "pep"]
    concept_nodes = [n for n in kg.nodes.values() if n.type == "concept"]

    concept_by_id = {c.id: c for c in concept_nodes}
    pep_by_id = {p.id: p for p in pep_nodes}

    for edge in kg.edges:
        if edge.type == "introduces" and edge.attributes.get("role") == "origin":
            source_pep = pep_by_id.get(edge.source)
            target_concept = concept_by_id.get(edge.target)
            if source_pep and target_concept:
                lines.append(f'  {edge.source}["{source_pep.label}"] --> {edge.target}["{target_concept.label}"]')

    for edge in kg.edges:
        if edge.type in ("supersedes", "replaces", "depends_on", "extends", "conflicts_with"):
            source_pep = pep_by_id.get(edge.source)
            target_pep = pep_by_id.get(edge.target)
            if source_pep and target_pep:
                lines.append(f'  {edge.source}["{source_pep.label}"] --{edge.type}--> {edge.target}["{target_pep.label}"]')

    path.write_text("\n".join(lines), encoding="utf-8")


def export_schema_md(kg: KnowledgeGraph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    node_counts: dict[str, int] = {}
    edge_counts: dict[str, int] = {}

    for node in kg.nodes.values():
        node_counts[node.type] = node_counts.get(node.type, 0) + 1

    for edge in kg.edges:
        edge_counts[edge.type] = edge_counts.get(edge.type, 0) + 1

    lines = [
        "# Knowledge Graph Schema",
        "",
        "## Node Types",
        "",
        "| Type | Count | Description |",
        "|------|-------|-------------|",
    ]

    descriptions = {
        "pep": "A Python Enhancement Proposal",
        "concept": "A typing domain concept (abstract)",
        "construct": "A concrete syntax or mechanism",
        "objection": "A raised concern/objection during debate",
        "argument": "A rationale/argument supporting a decision",
        "alternative": "A rejected or withdrawn approach",
        "decision": "An explicit outcome on a proposal",
        "person": "Author, sponsor, BDFL-delegate, SC member",
        "python_version": "A Python version milestone",
    }

    for ntype, count in sorted(node_counts.items()):
        lines.append(f"| {ntype} | {count} | {descriptions.get(ntype, '')} |")

    lines.extend([
        "",
        "## Edge Types",
        "",
        "| Type | Count | Description |",
        "|------|-------|-------------|",
    ])

    edge_descriptions = {
        "supersedes": "Authoritative replacement (from Superseded-By header)",
        "replaces": "Syntactic/migration replacement (from Replaces header)",
        "depends_on": "Dependency (from Requires header or cross-reference)",
        "extends": "Feature extension via a concept",
        "conflicts_with": "Explicit incompatibility",
        "introduces": "PEP introduces/uses a Concept or Construct (role=origin/uses)",
        "raised_objection": "PEP raises an Objection",
        "rejected_alternative": "PEP rejects an Alternative",
        "resolved_by": "Objection resolved by Argument/Decision",
        "motivated_by": "PEP/Construct motivated by Argument",
        "authored_by": "PEP authored by Person",
        "targets_version": "PEP targets Python version",
        "implements": "Construct implements Concept",
    }

    for etype, count in sorted(edge_counts.items()):
        lines.append(f"| {etype} | {count} | {edge_descriptions.get(etype, '')} |")

    lines.extend([
        "",
        "## Extraction Methods",
        "",
        "| Method | Count |",
        "|--------|-------|",
    ])

    method_counts: dict[str, int] = {}
    for edge in kg.edges:
        method_counts[edge.extraction_method] = method_counts.get(edge.extraction_method, 0) + 1

    for method, count in sorted(method_counts.items()):
        lines.append(f"| {method} | {count} |")

    path.write_text("\n".join(lines), encoding="utf-8")


def export_all(kg: KnowledgeGraph, base_dir: Path = Path("knowledge_state")) -> None:
    export_json(kg, base_dir / "graph.json")
    print(f"Exported knowledge state to {base_dir / 'graph.json'}")


if __name__ == "__main__":
    print("Exporters ready")