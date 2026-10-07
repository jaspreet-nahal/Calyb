from pathlib import Path
from src.ingestion import parse_all
from src.ingestion.fetch import main as fetch_main
from src.ingestion.extract import extract_all
import sys
import json
from src.graph import build_graph, export_all, load_graph
from src.reasoning import generate_report, save_report
from src.schema.nodes import PEPNode, PersonNode, PythonVersionNode, DecisionNode
from src.schema.edges import ReplacesEdge, SupercedesEdge, DependsOnEdge, TargetsVersionEdge, AuthoredByEdge


PEP_NUMBERS = [
    483, 484, 526,
    544,
    563, 649, 749,
    585, 604, 612, 646, 695, 696,
    677,
    589, 655, 692, 705,
    647, 724, 742,
    586, 591, 673, 698,
]


def build_knowledge_graph() -> None:
    print("Building knowledge graph...")

    print("Fetching PEPs...")
    fetch_main()

    pep_headers = parse_all()
    print(f"Parsed {len(pep_headers)} PEP headers")

    pep_nodes = []
    for h in pep_headers:
        lineage = get_lineage(h.number)
        node = PEPNode.create(
            number=h.number,
            title=h.title,
            status=h.status,
            pep_type=h.pep_type,
            created=h.created,
            python_version=h.python_version,
            replaces=h.replaces,
            superseded_by=h.superseded_by,
            requires=h.requires,
            post_history=h.post_history,
            authors=h.authors,
            discussions_to=h.discussions_to,
            resolution=h.resolution,
            bdfl_delegate=h.bdfl_delegate,
            topic=h.topic,
            lineage=lineage,
        )
        pep_nodes.append(node)

    extraction = extract_all(PEP_NUMBERS)
    print(f"Extracted: {len(extraction['concepts'])} concepts, "
          f"{len(extraction['constructs'])} constructs, "
          f"{len(extraction['objections'])} objections, "
          f"{len(extraction['arguments'])} arguments")

    header_edges = []
    person_nodes_dict = {}
    version_nodes_dict = {}
    for h in pep_headers:
        for r in h.replaces:
            header_edges.append(ReplacesEdge.create(source_pep=h.number, target_pep=r))
        for r in h.superseded_by:
            header_edges.append(SupercedesEdge.create(source_pep=r, target_pep=h.number))
        for r in h.requires:
            header_edges.append(DependsOnEdge.create(source_pep=h.number, target_pep=r, source="header"))
        if h.python_version:
            header_edges.append(TargetsVersionEdge.create(source_pep=h.number, target_version=h.python_version))
            version_id = f"python-{h.python_version}"
            if version_id not in version_nodes_dict:
                version_nodes_dict[version_id] = PythonVersionNode.create(
                    version=h.python_version,
                    provenance="PEP header",
                )
        for author in h.authors:
            person_id = f"person-{author.lower().replace(' ', '-')}"
            header_edges.append(AuthoredByEdge.create(source_pep=h.number, target_person=person_id, role="author"))
            if person_id not in person_nodes_dict:
                person_nodes_dict[person_id] = PersonNode.create(
                    person_id=person_id,
                    name=author,
                    role="author",
                    peps=[h.number],
                    provenance="PEP header",
                )

    person_nodes = list(person_nodes_dict.values())
    version_nodes = list(version_nodes_dict.values())
    decision_nodes = [
        DecisionNode.create(
            decision_id=f"decision-{h.number}",
            outcome=h.status.lower(),
            rationale_summary=f"PEP {h.number} status: {h.status}",
            decided_by="PEP status",
            pep_section="header",
            provenance=f"PEP {h.number} header",
        )
        for h in pep_headers
    ]

    all_edges = header_edges
    all_edges.extend(extraction["introduces"])
    all_edges.extend(extraction["raised_objections"])
    all_edges.extend(extraction["rejected_alternatives"])
    all_edges.extend(extraction["motivated_by"])
    all_edges.extend(extraction["implements"])
    all_edges.extend(extraction.get("extends", []))
    all_edges.extend(extraction.get("conflicts_with", []))
    all_edges.extend(extraction.get("depends_on", []))
    all_edges.extend(extraction.get("resolved_by", []))

    kg = build_graph(
        pep_nodes=pep_nodes,
        concept_nodes=extraction["concepts"],
        construct_nodes=extraction["constructs"],
        objection_nodes=extraction["objections"],
        argument_nodes=extraction["arguments"],
        alternative_nodes=extraction["alternatives"],
        decision_nodes=decision_nodes,
        person_nodes=person_nodes,
        version_nodes=version_nodes,
        edges=all_edges,
    )

    export_all(kg)
    print("Knowledge graph exported to knowledge_state/")
    return kg


def get_lineage(pep_num: int) -> str:
    if pep_num in [483, 484, 526]:
        return "foundations"
    elif pep_num == 544:
        return "structural_typing"
    elif pep_num in [563, 649, 749]:
        return "annotation_evaluation"
    elif pep_num in [585, 604, 612, 646, 695, 696]:
        return "generics_and_syntax"
    elif pep_num == 677:
        return "rejected_syntax"
    elif pep_num in [589, 655, 692, 705]:
        return "typeddict_evolution"
    elif pep_num in [647, 724, 742]:
        return "type_narrowing"
    elif pep_num in [586, 591, 673, 698]:
        return "qualifiers_and_forms"
    return "other"


def run_premortem(
    input_text: str,
    output_path: Path | None = None,
    graph_path: Path = Path("knowledge_state/graph.json"),
) -> None:
    kg = load_graph(graph_path)
    report = generate_report(kg, input_text)

    if output_path:
        save_report(report, output_path)
        print(f"Report saved to {output_path}.json and {output_path}.md")
    else:
        print(json.dumps(report, indent=2))


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python cli.py <command> [args]")
        print("Commands:")
        print("  build          Build the knowledge graph")
        print("  premortem      Run pre-mortem using knowledge_state/graph.json")
        print("  premortem-file Run pre-mortem on input from file")
        return 1

    cmd = sys.argv[1]

    if cmd == "build":
        build_knowledge_graph()
        return 0

    elif cmd == "premortem":
        if len(sys.argv) < 3:
            print("Usage: python cli.py premortem \"<proposal text>\" [output_path]")
            return 1
        input_text = sys.argv[2]
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        run_premortem(input_text, output_path)
        return 0

    elif cmd == "premortem-file":
        if len(sys.argv) < 3:
            print("Usage: python cli.py premortem-file <input_file> [output_path]")
            return 1
        input_path = Path(sys.argv[2])
        input_text = input_path.read_text(encoding="utf-8")
        output_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
        run_premortem(input_text, output_path)
        return 0

    else:
        print(f"Unknown command: {cmd}")
        return 1


if __name__ == "__main__":
    sys.exit(main())