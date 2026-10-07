import networkx as nx
from typing import Any

from src.graph.builder import KnowledgeGraph


def find_peps_by_concept(kg: KnowledgeGraph, concept_ids: list[str]) -> list[int]:
    pep_nums = set()
    for edge in kg.edges:
        if edge.type == "introduces" and edge.target in concept_ids:
            try:
                pep_num = int(edge.source.split("-")[1])
                pep_nums.add(pep_num)
            except (IndexError, ValueError):
                pass
    return sorted(pep_nums)


def find_concepts_by_pep(kg: KnowledgeGraph, pep_num: int) -> list[str]:
    concept_ids = []
    source = f"pep-{pep_num}"
    for edge in kg.edges:
        if edge.type == "introduces" and edge.source == source:
            concept_ids.append(edge.target)
    return concept_ids


def get_precedent_chain(kg: KnowledgeGraph, pep_num: int, max_depth: int = 5) -> list[int]:
    chain = []
    visited = set()
    current = pep_num

    for _ in range(max_depth):
        if current in visited:
            break
        visited.add(current)
        chain.append(current)

        source = f"pep-{current}"
        next_pep = None
        for edge in kg.edges:
            if edge.type == "supersedes" and edge.source == source:
                try:
                    next_pep = int(edge.target.split("-")[1])
                    break
                except (IndexError, ValueError):
                    pass
        if next_pep is None or next_pep in visited:
            break
        current = next_pep

    return chain


def get_objections_for_peps(kg: KnowledgeGraph, pep_nums: list[int]) -> list[dict]:
    objections = []
    for pep_num in pep_nums:
        source = f"pep-{pep_num}"
        for edge in kg.edges:
            if edge.type == "raised_objection" and edge.source == source:
                objection = kg.get_node(edge.target)
                if objection:
                    objections.append({
                        "pep": pep_num,
                        "objection_id": edge.target,
                        "summary": objection.attributes.get("summary", ""),
                        "category": objection.attributes.get("category", ""),
                        "section": edge.attributes.get("section", ""),
                        "resolved": edge.attributes.get("resolved", False),
                    })
    return objections


def get_alternatives_for_peps(kg: KnowledgeGraph, pep_nums: list[int]) -> list[dict]:
    alternatives = []
    for pep_num in pep_nums:
        source = f"pep-{pep_num}"
        for edge in kg.edges:
            if edge.type == "rejected_alternative" and edge.source == source:
                alt = kg.get_node(edge.target)
                if alt:
                    alternatives.append({
                        "pep": pep_num,
                        "alternative_id": edge.target,
                        "summary": alt.attributes.get("summary", ""),
                        "rejection_reason": alt.attributes.get("rejection_reason", ""),
                        "section": edge.attributes.get("section", ""),
                    })
    return alternatives


def get_conflicts_for_peps(kg: KnowledgeGraph, pep_nums: list[int]) -> list[dict]:
    conflicts = []
    for pep_num in pep_nums:
        source = f"pep-{pep_num}"
        for edge in kg.edges:
            if edge.type == "conflicts_with" and edge.source == source:
                try:
                    target_pep = int(edge.target.split("-")[1])
                    conflicts.append({
                        "pep": pep_num,
                        "conflicts_with": target_pep,
                        "conflict_type": edge.attributes.get("conflict_type", ""),
                        "flagged_for_review": edge.attributes.get("flagged_for_review", True),
                    })
                except (IndexError, ValueError):
                    pass
    return conflicts


def get_dependencies(kg: KnowledgeGraph, pep_nums: list[int]) -> list[dict]:
    deps = []
    for pep_num in pep_nums:
        source = f"pep-{pep_num}"
        for edge in kg.edges:
            if edge.type == "depends_on" and edge.source == source:
                try:
                    target_pep = int(edge.target.split("-")[1])
                    deps.append({
                        "pep": pep_num,
                        "depends_on": target_pep,
                        "hard": edge.attributes.get("hard", True),
                        "source": edge.attributes.get("source", "header"),
                    })
                except (IndexError, ValueError):
                    pass
    return deps


def get_constructs_for_concepts(kg: KnowledgeGraph, concept_ids: list[str]) -> list[dict]:
    constructs = []
    for edge in kg.edges:
        if edge.type == "implements" and edge.target in concept_ids:
            construct = kg.get_node(edge.source)
            concept = kg.get_node(edge.target)
            if construct and concept:
                constructs.append({
                    "construct": construct.attributes.get("name", ""),
                    "construct_id": edge.source,
                    "concept": concept.attributes.get("name", ""),
                    "concept_id": edge.target,
                    "introduced_in": construct.attributes.get("introduced_in", 0),
                })
    return constructs


def graph_distance(kg: KnowledgeGraph, pep_a: int, pep_b: int) -> int:
    source = f"pep-{pep_a}"
    target = f"pep-{pep_b}"
    try:
        return nx.shortest_path_length(kg.graph, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return 999


if __name__ == "__main__":
    print("Traverse module ready")