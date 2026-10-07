import re
import yaml
from pathlib import Path
from typing import Optional
from src.schema import ConceptNode, ConstructNode, IntroducesEdge

LEXICON_PATH = Path("src/schema/lexicon.yaml")

def load_lexicon() -> dict:
    with open(LEXICON_PATH) as f:
        return yaml.safe_load(f)


def find_concept_spans(text: str, lexicon: dict) -> list[dict]:
    spans = []
    concepts = lexicon.get("concepts", {})
    for term, info in concepts.items():
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            spans.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "concept_id": info["id"],
                "category": info["category"],
                "construct_id": info.get("construct_id"),
            })
    return spans


def find_construct_spans(text: str, lexicon: dict) -> list[dict]:
    spans = []
    concepts = lexicon.get("concepts", {})
    for term, info in concepts.items():
        if "construct_id" in info:
            pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
            for match in pattern.finditer(text):
                spans.append({
                    "text": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "construct_id": info["construct_id"],
                    "concept_id": info["id"],
                })
    return spans


def deduplicate_spans(spans: list[dict], threshold: int = 50) -> list[dict]:
    if not spans:
        return []
    spans.sort(key=lambda s: s["start"])
    result = [spans[0]]
    for span in spans[1:]:
        last = result[-1]
        if span["start"] - last["end"] < threshold and span.get("concept_id") == last.get("concept_id"):
            continue
        result.append(span)
    return result


def map_input_text(text: str) -> dict:
    lexicon = load_lexicon()

    concept_spans = find_concept_spans(text, lexicon)
    construct_spans = find_construct_spans(text, lexicon)

    concept_spans = deduplicate_spans(concept_spans)
    construct_spans = deduplicate_spans(construct_spans)

    concept_nodes = {}
    construct_nodes = {}
    introduces_edges = []

    for span in concept_spans:
        cid = span["concept_id"]
        if cid not in concept_nodes:
            concept_nodes[cid] = ConceptNode.create(
                concept_id=cid,
                name=span["text"],
                category=span["category"],
                provenance="input",
            )

    for span in construct_spans:
        construct_id = span["construct_id"]
        if construct_id not in construct_nodes:
            construct_nodes[construct_id] = ConstructNode.create(
                construct_id=construct_id,
                name=span["text"],
                kind="special_form",
                introduced_in=0,
                provenance="input",
            )
        cid = span["concept_id"]
        introduces_edges.append(IntroducesEdge.create(
            source_pep=0,
            target_id=cid,
            section="input",
            role="uses",
            provenance="input",
        ))

    return {
        "concepts": list(concept_nodes.values()),
        "constructs": list(construct_nodes.values()),
        "introduces": introduces_edges,
    }


if __name__ == "__main__":
    test_input = "I want to add a typing.Frozen for immutable dataclass fields"
    result = map_input_text(test_input)
    print(f"Concepts: {[c.id for c in result['concepts']]}")
    print(f"Constructs: {[c.id for c in result['constructs']]}")