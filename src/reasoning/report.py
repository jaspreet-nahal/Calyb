import json
from typing import Any
from pathlib import Path
from src.graph.builder import KnowledgeGraph
from src.reasoning.map_input import map_input_text
from src.reasoning.traverse import find_concepts_by_pep,get_objections_for_peps,get_alternatives_for_peps,get_conflicts_for_peps,get_constructs_for_concepts
from src.reasoning.score import rank_precedents, compute_outcome_pattern


def generate_report(
    kg: KnowledgeGraph,
    input_text: str,
    top_k: int = 10,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    input_result = map_input_text(input_text)
    input_concepts = {c.id for c in input_result["concepts"]}
    input_constructs = {c.id for c in input_result["constructs"]}

    ranked = rank_precedents(
        kg, input_concepts, weights
    )

    top_peps = [r["pep"] for r in ranked[:top_k]]

    closest_precedents = []
    for r in ranked[:top_k]:
        pep_node = kg.get_node(f"pep-{r['pep']}")
        if pep_node:
            shared = set(find_concepts_by_pep(kg, r["pep"])) & input_concepts
            closest_precedents.append({
                "pep": r["pep"],
                "title": pep_node.attributes.get("title", ""),
                "score": round(r["score"], 3),
                "score_breakdown": {k: round(v, 3) for k, v in r["score_breakdown"].items()},
                "shared_concepts": list(shared),
                "status": pep_node.attributes.get("status", "Unknown"),
            })

    outcome_pattern = compute_outcome_pattern(kg, top_peps)

    historical_concerns = []
    objections = get_objections_for_peps(kg, top_peps)
    obj_by_category = {}
    for obj in objections:
        cat = obj["category"]
        if cat not in obj_by_category:
            obj_by_category[cat] = {
                "category": cat,
                "evidence_peps": [],
                "evidence_snippets": [],
                "count": 0,
            }
        obj_by_category[cat]["evidence_peps"].append(obj["pep"])
        obj_by_category[cat]["evidence_snippets"].append(obj["summary"])
        obj_by_category[cat]["count"] += 1

    for cat, data in sorted(obj_by_category.items(), key=lambda x: -x[1]["count"]):
        historical_concerns.append({
            "concern": cat.replace("_", " "),
            "category": cat,
            "evidence_peps": data["evidence_peps"],
            "evidence_snippets": data["evidence_snippets"][:3],
            "support_count": data["count"],
        })

    rejected_alternatives = []
    alternatives = get_alternatives_for_peps(kg, top_peps)
    for alt in alternatives:
        rejected_alternatives.append({
            "summary": alt["summary"],
            "rejection_reason": alt["rejection_reason"],
            "source_pep": alt["pep"],
            "section": alt["section"],
        })

    dependencies = []
    constructs = get_constructs_for_concepts(kg, list(input_concepts))
    for c in constructs:
        if c["introduced_in"] > 0:
            dependencies.append({
                "construct": c["construct"],
                "introduced_in": c["introduced_in"],
                "status": f"available_in_{c['introduced_in']}+",
            })

    conflicts = []
    conflict_list = get_conflicts_for_peps(kg, top_peps)
    for c in conflict_list:
        conflicts.append({
            "with_pep": c["conflicts_with"],
            "conflict_type": c["conflict_type"],
            "description": f"PEP {c['pep']} conflicts with PEP {c['conflicts_with']} on {c['conflict_type']}",
        })

    risk_flag = "low"
    if len(historical_concerns) >= 3:
        risk_flag = "high"
    elif len(historical_concerns) >= 1:
        risk_flag = "medium"

    rejected_count = outcome_pattern["status_distribution"].get("Rejected", 0)
    superseded_count = outcome_pattern["status_distribution"].get("Superseded", 0)
    if rejected_count + superseded_count > len(top_peps) / 2:
        risk_flag = "high"

    recommended_next_steps = []
    if historical_concerns:
        top_obj = historical_concerns[0]
        recommended_next_steps.append(
            f"Review the historical {top_obj['category'].replace('_', ' ')} concern first "
            f"(see PEP {top_obj['evidence_peps'][0]})"
        )
    if dependencies:
        recommended_next_steps.append(
            f"Build on PEP {dependencies[0]['introduced_in']} "
            f"({dependencies[0]['construct']}) rather than inventing new syntax"
        )
    if not recommended_next_steps:
        recommended_next_steps.append("Review closest precedents for design patterns")

    graph_citations = {
        "nodes": [c.id for c in input_result["concepts"] + input_result["constructs"]],
        "edges": [e.model_dump() for e in input_result["introduces"]],
    }

    return {
        "input_summary": {
            "concepts": [c.id for c in input_result["concepts"]],
            "constructs": [c.id for c in input_result["constructs"]],
        },
        "closest_precedents": closest_precedents,
        "outcome_history": {
            "accepted": outcome_pattern["status_distribution"].get("Final", 0) + outcome_pattern["status_distribution"].get("Accepted", 0),
            "rejected": outcome_pattern["status_distribution"].get("Rejected", 0),
            "superseded": outcome_pattern["status_distribution"].get("Superseded", 0),
            "pattern": outcome_pattern["pattern_summary"],
        },
        "historical_concerns": historical_concerns,
        "rejected_alternatives": rejected_alternatives,
        "dependencies": dependencies,
        "conflicts": conflicts,
        "risk_flag": risk_flag,
        "recommended_next_steps": recommended_next_steps,
        "graph_citations": graph_citations,
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Proposal Pre-Mortem Report",
        "",
        f"**Heuristic Risk Flag:** {report['risk_flag'].upper()}",
        "",
        "## Input Summary",
        "",
        f"**Concepts:** {', '.join(report['input_summary']['concepts']) or 'None'}",
        f"**Constructs:** {', '.join(report['input_summary']['constructs']) or 'None'}",
        "",
        "## Closest Precedents",
        "",
    ]

    for p in report["closest_precedents"]:
        lines.append(f"### PEP {p['pep']}: {p['title']}")
        lines.append(f"- **Score:** {p['score']}")
        lines.append(f"- **Status:** {p['status']}")
        lines.append(f"- **Shared Concepts:** {', '.join(p['shared_concepts']) or 'None'}")
        lines.append(f"- **Breakdown:** Concept Overlap: {p['score_breakdown']['concept_overlap']}, "
                     f"Graph Proximity: {p['score_breakdown']['graph_proximity']}, "
                     f"Recency: {p['score_breakdown']['recency']}")
        lines.append("")

    lines.extend([
        "## Outcome History",
        "",
        f"- **Accepted/Final:** {report['outcome_history']['accepted']}",
        f"- **Rejected:** {report['outcome_history']['rejected']}",
        f"- **Superseded:** {report['outcome_history']['superseded']}",
        f"- **Pattern:** {report['outcome_history']['pattern']}",
        "",
        "## Historical Concerns Found in Related PEPs",
        "",
    ])

    for obj in report["historical_concerns"]:
        lines.append(f"### {obj['concern'].title()} ({obj['category']})")
        lines.append(f"- **Matched records:** {obj['support_count']}")
        lines.append(f"- **Evidence PEPs:** {', '.join(f'PEP {p}' for p in obj['evidence_peps'])}")
        lines.append(f"- **Evidence:** {'; '.join(obj['evidence_snippets'])}")
        lines.append("")

    lines.extend([
        "## Rejected Alternatives",
        "",
    ])

    for alt in report["rejected_alternatives"]:
        lines.append(f"- **PEP {alt['source_pep']}** ({alt['section']}): {alt['summary']}")
        lines.append(f"  - *Rejection reason:* {alt['rejection_reason']}")
        lines.append("")

    lines.extend([
        "## Dependencies",
        "",
    ])

    for dep in report["dependencies"]:
        lines.append(f"- **{dep['construct']}** — introduced in PEP {dep['introduced_in']} ({dep['status']})")
    if not report["dependencies"]:
        lines.append("No direct dependencies found.")
    lines.append("")

    lines.extend([
        "## Conflicts",
        "",
    ])

    for conf in report["conflicts"]:
        lines.append(f"- **PEP {conf['with_pep']}** ({conf['conflict_type']}): {conf['description']}")
    if not report["conflicts"]:
        lines.append("No known conflicts.")
    lines.append("")

    lines.extend([
        "## Recommended Next Steps",
        "",
    ])

    for i, step in enumerate(report["recommended_next_steps"], 1):
        lines.append(f"{i}. {step}")

    lines.extend([
        "",
        "---",
        "*Report generated from PEP text matched by the project lexicon and graph rules. "
        "Risk is a heuristic flag, not a prediction of proposal outcome.*",
    ])

    return "\n".join(lines)


def save_report(report: dict[str, Any], base_path: Path) -> None:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    base_path.with_suffix(".json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    base_path.with_suffix(".md").write_text(
        render_markdown(report), encoding="utf-8"
    )


if __name__ == "__main__":
    print("Report module ready")