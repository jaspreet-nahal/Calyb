from typing import Any
from src.graph.builder import KnowledgeGraph
from src.reasoning.traverse import (
    find_peps_by_concept,
    find_concepts_by_pep,
    get_objections_for_peps,
    get_alternatives_for_peps,
    get_conflicts_for_peps,
    get_dependencies,
    graph_distance,
)
DEFAULT_WEIGHTS = {
    "concept_overlap": 0.5,
    "graph_proximity": 0.3,
    "recency": 0.2,
}


def jaccard_similarity(set_a: set, set_b: set) -> float:
    if not set_a and not set_b:
        return 1.0
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    return intersection / union


def compute_concept_overlap(kg: KnowledgeGraph, pep_num: int, input_concepts: set[str]) -> float:
    pep_concepts = set(find_concepts_by_pep(kg, pep_num))
    return jaccard_similarity(pep_concepts, input_concepts)


def compute_graph_proximity(kg: KnowledgeGraph, pep_num: int, input_concepts: set[str]) -> float:
    input_peps = find_peps_by_concept(kg, list(input_concepts))
    if not input_peps:
        return 0.0

    min_dist = min(graph_distance(kg, pep_num, ip) for ip in input_peps)
    if min_dist >= 999:
        return 0.0
    return 1.0 / (1.0 + min_dist)


def compute_recency_score(python_version: str | None) -> float:
    if not python_version:
        return 0.0
    try:
        version_tuple = tuple(map(int, python_version.split(".")))
        if len(version_tuple) >= 2:
            major, minor = version_tuple[0], version_tuple[1]
            return min(1.0, (major * 10 + minor) / 313.0)
    except ValueError:
        pass
    return 0.0


def score_precedent(
    kg: KnowledgeGraph,
    pep_num: int,
    input_concepts: set[str],
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    w = weights or DEFAULT_WEIGHTS

    concept_overlap = compute_concept_overlap(kg, pep_num, input_concepts)
    graph_proximity = compute_graph_proximity(kg, pep_num, input_concepts)

    recency = 0.0
    pep_node = kg.get_node(f"pep-{pep_num}")
    if pep_node:
        python_version = pep_node.attributes.get("python_version")
        recency = compute_recency_score(python_version)

    total = (
        w["concept_overlap"] * concept_overlap +
        w["graph_proximity"] * graph_proximity +
        w["recency"] * recency
    )

    return {
        "pep": pep_num,
        "score": total,
        "score_breakdown": {
            "concept_overlap": concept_overlap,
            "graph_proximity": graph_proximity,
            "recency": recency,
        },
        "weights": w,
    }


def rank_precedents(
    kg: KnowledgeGraph,
    input_concepts: set[str],
    weights: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    all_peps = set()
    for edge in kg.edges:
        if edge.type == "introduces":
            try:
                pep_num = int(edge.source.split("-")[1])
                all_peps.add(pep_num)
            except (IndexError, ValueError):
                pass

    scored = []
    for pep_num in sorted(all_peps):
        scored.append(score_precedent(
            kg, pep_num, input_concepts,
            weights
        ))

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def compute_outcome_pattern(kg: KnowledgeGraph, top_peps: list[int]) -> dict[str, Any]:
    status_counts = {"Final": 0, "Accepted": 0, "Superseded": 0, "Rejected": 0, "Withdrawn": 0, "Draft": 0}
    objection_categories = {}

    for pep_num in top_peps:
        pep_node = kg.get_node(f"pep-{pep_num}")
        if pep_node:
            status = pep_node.attributes.get("status", "Unknown")
            if status in status_counts:
                status_counts[status] += 1
            elif "accepted" in status.lower():
                status_counts["Accepted"] += 1

        objections = get_objections_for_peps(kg, [pep_num])
        for obj in objections:
            cat = obj["category"]
            objection_categories[cat] = objection_categories.get(cat, 0) + 1

    total = sum(status_counts.values())
    pattern_parts = []
    for status, count in status_counts.items():
        if count > 0:
            pattern_parts.append(f"{count} {status.lower()}")

    objection_pattern = []
    for cat, count in sorted(objection_categories.items(), key=lambda x: -x[1]):
        if count > 1:
            objection_pattern.append(f"{count} over {cat}")

    return {
        "status_distribution": status_counts,
        "top_objections": objection_pattern,
        "pattern_summary": ", ".join(pattern_parts) if pattern_parts else "No clear pattern",
        "objection_summary": "; ".join(objection_pattern) if objection_pattern else "No dominant objection category",
    }


if __name__ == "__main__":
    print("Score module ready")