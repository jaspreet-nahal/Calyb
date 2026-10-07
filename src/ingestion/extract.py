import re
import yaml
from pathlib import Path
from src.ingestion.parse_sections import load_and_parse_sections
from src.schema import (
    ConceptNode, ConstructNode, ObjectionNode, ArgumentNode, AlternativeNode,
    IntroducesEdge, RaisedObjectionEdge, RejectedAlternativeEdge, MotivatedByEdge,
    ImplementsEdge, ResolvedByEdge, ExtendsEdge, ConflictsWithEdge, DependsOnEdge
)

LEXICON_PATH = Path("src/schema/lexicon.yaml")


def sentence_context(text: str, start: int, end: int) -> str:
    left = max(text.rfind(".", 0, start), text.rfind("!", 0, start), text.rfind("?", 0, start))
    right_candidates = [p for p in (text.find(".", end), text.find("!", end), text.find("?", end)) if p >= 0]
    right = min(right_candidates) if right_candidates else len(text)
    return re.sub(r"\s+", " ", text[left + 1:right + 1]).strip()[:500]


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
                "type": "concept",
                "concept_id": info["id"],
                "category": info["category"],
                "construct_id": info.get("construct_id"),
            })
    return spans


def find_objection_spans(text: str, lexicon: dict) -> list[dict]:
    spans = []
    objections = lexicon.get("objections", {})
    for term, category in objections.items():
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            spans.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "type": "objection",
                "category": category,
                "evidence": sentence_context(text, match.start(), match.end()),
            })
    return spans


def find_argument_spans(text: str, lexicon: dict) -> list[dict]:
    spans = []
    arguments = lexicon.get("arguments", {})
    for term, info in arguments.items():
        pattern = re.compile(rf"\b{re.escape(term)}\b", re.IGNORECASE)
        for match in pattern.finditer(text):
            spans.append({
                "text": match.group(),
                "start": match.start(),
                "end": match.end(),
                "type": "argument",
                "category": info["category"],
                "stance": info["stance"],
                "evidence": sentence_context(text, match.start(), match.end()),
            })
    return spans


def deduplicate_spans(spans: list[dict], threshold: int = 50) -> list[dict]:
    if not spans:
        return []
    spans.sort(key=lambda s: s["start"])
    result = [spans[0]]
    for span in spans[1:]:
        last = result[-1]
        if span["start"] - last["end"] < threshold and span["type"] == last["type"]:
            continue
        result.append(span)
    return result


def find_cross_references(text: str, current_pep: int) -> list[dict]:
    refs = []
    patterns = [
        r"\b[Pp][Ee][Pp][\s\-:]+(\d{1,4})\b",
        r":pep:`(\d{1,4})`",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            try:
                ref_pep = int(match.group(1))
                if ref_pep != current_pep and 1 <= ref_pep <= 9999:
                    refs.append({
                        "pep": ref_pep,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    })
            except ValueError:
                pass
    seen = set()
    unique_refs = []
    for ref in refs:
        if ref["pep"] not in seen:
            seen.add(ref["pep"])
            unique_refs.append(ref)
    return unique_refs


def find_conflict_patterns(text: str) -> list[dict]:
    conflicts = []
    conflict_patterns = [
        (r"conflicts?\s+with\s+PEP\s+(\d{1,4})", "explicit_conflict"),
        (r"incompatible\s+with\s+PEP\s+(\d{1,4})", "incompatibility"),
        (r"breaks?\s+PEP\s+(\d{1,4})", "breaking_change"),
        (r"contradicts?\s+PEP\s+(\d{1,4})", "contradiction"),
        (r"overrides?\s+PEP\s+(\d{1,4})", "override"),
        (r"cannot\s+be\s+used\s+(?:together|with)\s+PEP\s+(\d{1,4})", "mutual_exclusion"),
        (r"mutually\s+exclusive\s+with\s+PEP\s+(\d{1,4})", "mutual_exclusion"),
        (r"supersedes\s+PEP\s+(\d{1,4})", "supersession"),
        (r"replaces\s+PEP\s+(\d{1,4})", "replacement"),
        (r"deprecates?\s+PEP\s+(\d{1,4})", "deprecation"),
        (r"PEP\s+(\d{1,4})\s+is\s+(?:incompatible|deprecated|superseded)", "backward_reference"),
        (r"conflict\s+between\s+PEP\s+(\d{1,4})", "explicit_conflict"),
    ]
    for pattern, conflict_type in conflict_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                target_pep = int(match.group(1))
                if 1 <= target_pep <= 9999:
                    conflicts.append({
                        "target_pep": target_pep,
                        "conflict_type": conflict_type,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    })
            except ValueError:
                pass
    return conflicts


def find_alternative_spans(text: str, section_name: str) -> list[dict]:
    alternatives = []
    if "rejected" in section_name.lower() or "alternative" in section_name.lower():
        blocks = re.split(r"\n\s*\n", text)
        for block in blocks:
            cleaned = re.sub(r"\s+", " ", block).strip()
            if len(cleaned) < 30:
                continue
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            is_list_item = any(
                re.match(r"^(?:[*-]|\u2022|\d+[.)])\s+", line)
                for line in lines
            )
            mentions_rejection = bool(re.search(
                r"\b(reject(?:ed|s)?|alternative|instead|rather than|we considered)\b",
                cleaned,
                re.IGNORECASE,
            ))
            if is_list_item or mentions_rejection:
                alternatives.append({"text": cleaned[:500], "section": section_name})
    return alternatives


def find_objection_resolution(objection_nodes: dict, argument_nodes: dict, pep_num: int) -> list[dict]:
    
    resolutions = []

    section_order = {
        "abstract": 0,
        "motivation": 1,
        "rationale": 2,
        "rationale_and_goals": 2,
        "backwards_compatibility": 3,
        "open_issues": 4,
        "rejected_ideas": 5,
        "rejected_alternatives": 5,
        "implementation": 6,
        "reference_implementation": 6,
        "security": 7,
        "copyright": 8,
    }

    for objection in objection_nodes.values():
        objection_section = objection.attributes.get("pep_section", "").lower()
        objection_category = objection.attributes.get("category", "")
        objection_order = section_order.get(objection_section, 99)

        for argument in argument_nodes.values():
            if argument.attributes.get("stance") != "pro":
                continue
            arg_section = argument.attributes.get("pep_section", "").lower()
            arg_order = section_order.get(arg_section, 99)

            if arg_order <= objection_order:
                continue

            arg_category = argument.attributes.get("category", "")
            if arg_category == objection_category or \
               (objection_category == "runtime_cost" and arg_category in ("performance", "efficiency")) or \
               (objection_category == "complexity" and arg_category in ("simplicity", "ergonomics")) or \
               (objection_category == "backwards_compat" and arg_category in ("compatibility", "migration")) or \
               (objection_category == "ambiguity" and arg_category in ("clarity", "expressiveness")):

                resolutions.append({
                    "objection_id": objection.id,
                    "argument_id": argument.id,
                    "how": "accepted",
                    "provenance": f"PEP {pep_num} § {argument.attributes.get('pep_section', '')}",
                    "confidence": 0.7,
                })
                break  

    return resolutions


def extract_from_pep(pep_num: int, raw_dir: Path = Path("data/raw")) -> dict:
    sections = load_and_parse_sections(pep_num, raw_dir)
    lexicon = load_lexicon()

    all_spans = []

    for section_name, content in sections.items():
        concept_spans = find_concept_spans(content, lexicon)
        objection_spans = find_objection_spans(content, lexicon)
        argument_spans = find_argument_spans(content, lexicon)

        for span in concept_spans + objection_spans + argument_spans:
            span["section"] = section_name
            all_spans.append(span)

    all_spans = deduplicate_spans(all_spans)

    concept_nodes = {}
    construct_nodes = {}
    objection_nodes = {}
    argument_nodes = {}
    alternative_nodes = {}

    introduces_edges = []
    raised_objection_edges = []
    rejected_alternative_edges = []
    motivated_by_edges = []
    implements_edges = []
    extends_edges = []
    conflicts_with_edges = []
    depends_on_edges = []
    resolved_by_edges = []

    introduces_seen = set()
    implements_seen = set()

    for span in all_spans:
        if span["type"] == "concept":
            cid = span["concept_id"]
            if cid not in concept_nodes:
                concept_nodes[cid] = ConceptNode.create(
                    concept_id=cid,
                    name=span["text"],
                    category=span["category"],
                    provenance=f"PEP {pep_num} § {span['section']}",
                )
            intro_key = (pep_num, cid, span["section"], "uses")
            if intro_key not in introduces_seen:
                introduces_seen.add(intro_key)
                introduces_edges.append(IntroducesEdge.create(
                    source_pep=pep_num,
                    target_id=cid,
                    section=span["section"],
                    role="uses",
                    provenance=f"PEP {pep_num} § {span['section']}",
                ))
            if span.get("construct_id"):
                construct_id = span["construct_id"]
                if construct_id not in construct_nodes:
                    construct_nodes[construct_id] = ConstructNode.create(
                        construct_id=construct_id,
                        name=span["text"],
                        kind="special_form",
                        introduced_in=pep_num,
                        provenance=f"PEP {pep_num} § {span['section']}",
                    )
                impl_key = (construct_id, cid)
                if impl_key not in implements_seen:
                    implements_seen.add(impl_key)
                    implements_edges.append(ImplementsEdge.create(
                        source_construct=construct_id,
                        target_concept=cid,
                        provenance=f"PEP {pep_num} § {span['section']}",
                    ))

        elif span["type"] == "objection":
            oid = f"objection-{pep_num}-{span['category']}-{len(objection_nodes)}"
            objection_nodes[oid] = ObjectionNode.create(
                objection_id=oid,
                summary=span["evidence"],
                category=span["category"],
                raised_by="community",
                pep_section=span["section"],
                evidence=span["evidence"],
                provenance=f"PEP {pep_num} § {span['section']}",
            )
            raised_objection_edges.append(RaisedObjectionEdge.create(
                source_pep=pep_num,
                target_objection=oid,
                section=span["section"],
                provenance=f"PEP {pep_num} § {span['section']}",
            ))

        elif span["type"] == "argument":
            aid = f"argument-{pep_num}-{span['category']}-{span['stance']}-{len(argument_nodes)}"
            argument_nodes[aid] = ArgumentNode.create(
                argument_id=aid,
                summary=span["evidence"],
                stance=span["stance"],
                category=span["category"],
                pep_section=span["section"],
                evidence=span["evidence"],
                provenance=f"PEP {pep_num} § {span['section']}",
            )
            motivated_by_edges.append(MotivatedByEdge.create(
                source_id=f"pep-{pep_num}",
                target_argument=aid,
                section=span["section"],
                provenance=f"PEP {pep_num} § {span['section']}",
            ))

    for section_name, content in sections.items():
        cross_refs = find_cross_references(content, pep_num)
        for ref in cross_refs:
            ref_pep = ref["pep"]
            if section_name.lower() in ("abstract", "motivation", "rationale", "rationale_and_goals"):
                depends_on_edges.append(DependsOnEdge.create(
                    source_pep=pep_num,
                    target_pep=ref_pep,
                    hard=False,
                    source="crossref",
                    provenance=f"PEP {pep_num} § {section_name}",
                    confidence=0.7,
                ))
            elif section_name.lower() in ("rationale", "rationale_and_goals", "implementation", "reference_implementation"):
                extends_edges.append(ExtendsEdge.create(
                    source_pep=pep_num,
                    target_pep=ref_pep,
                    concept="cross_reference",
                    source="crossref",
                    provenance=f"PEP {pep_num} § {section_name}",
                    confidence=0.7,
                ))

    for section_name, content in sections.items():
        conflicts = find_conflict_patterns(content)
        for conflict in conflicts:
            conflicts_with_edges.append(ConflictsWithEdge.create(
                source_pep=pep_num,
                target_pep=conflict["target_pep"],
                conflict_type=conflict["conflict_type"],
                flagged_for_review=True,
                provenance=f"PEP {pep_num} § {section_name}",
                confidence=0.6,
            ))

    for section_name, content in sections.items():
        alternatives = find_alternative_spans(content, section_name)
        for alt in alternatives:
            alt_id = f"alternative-{pep_num}-{len(alternative_nodes)}"
            alternative_nodes[alt_id] = AlternativeNode.create(
                alternative_id=alt_id,
                summary=alt["text"],
                rejection_reason="Listed in a rejected/alternative section; no separate reason was extracted",
                pep_section=alt["section"],
                proposed_by="author",
                provenance=f"PEP {pep_num} § {alt['section']}",
            )
            rejected_alternative_edges.append(RejectedAlternativeEdge.create(
                source_pep=pep_num,
                target_alternative=alt_id,
                section=alt["section"],
                provenance=f"PEP {pep_num} § {alt['section']}",
            ))

    resolutions = find_objection_resolution(objection_nodes, argument_nodes, pep_num)
    for res in resolutions:
        resolved_by_edges.append(ResolvedByEdge.create(
            source_objection=res["objection_id"],
            target_id=res["argument_id"],
            how=res["how"],
            provenance=res["provenance"],
            confidence=res["confidence"],
        ))

    return {
        "concepts": list(concept_nodes.values()),
        "constructs": list(construct_nodes.values()),
        "objections": list(objection_nodes.values()),
        "arguments": list(argument_nodes.values()),
        "alternatives": list(alternative_nodes.values()),
        "introduces": introduces_edges,
        "raised_objections": raised_objection_edges,
        "rejected_alternatives": rejected_alternative_edges,
        "motivated_by": motivated_by_edges,
        "implements": implements_edges,
        "extends": extends_edges,
        "conflicts_with": conflicts_with_edges,
        "depends_on": depends_on_edges,
        "resolved_by": resolved_by_edges,
    }


def extract_all(pep_numbers: list[int], raw_dir: Path = Path("data/raw")) -> dict:
    all_concepts = {}
    all_constructs = {}
    all_objections = {}
    all_arguments = {}
    all_alternatives = {}
    all_introduces = []
    all_raised_objections = []
    all_rejected_alternatives = []
    all_motivated_by = []
    all_implements = []
    all_extends = []
    all_conflicts_with = []
    all_depends_on = []
    all_resolved_by = []

    for num in pep_numbers:
        result = extract_from_pep(num, raw_dir)
        for c in result["concepts"]:
            all_concepts[c.id] = c
        for c in result["constructs"]:
            all_constructs[c.id] = c
        for o in result["objections"]:
            all_objections[o.id] = o
        for a in result["arguments"]:
            all_arguments[a.id] = a
        for a in result["alternatives"]:
            all_alternatives[a.id] = a
        all_introduces.extend(result["introduces"])
        all_raised_objections.extend(result["raised_objections"])
        all_rejected_alternatives.extend(result["rejected_alternatives"])
        all_motivated_by.extend(result["motivated_by"])
        all_implements.extend(result["implements"])
        all_extends.extend(result["extends"])
        all_conflicts_with.extend(result["conflicts_with"])
        all_depends_on.extend(result["depends_on"])
        all_resolved_by.extend(result["resolved_by"])

    return {
        "concepts": list(all_concepts.values()),
        "constructs": list(all_constructs.values()),
        "objections": list(all_objections.values()),
        "arguments": list(all_arguments.values()),
        "alternatives": list(all_alternatives.values()),
        "introduces": all_introduces,
        "raised_objections": all_raised_objections,
        "rejected_alternatives": all_rejected_alternatives,
        "motivated_by": all_motivated_by,
        "implements": all_implements,
        "extends": all_extends,
        "conflicts_with": all_conflicts_with,
        "depends_on": all_depends_on,
        "resolved_by": all_resolved_by,
    }


if __name__ == "__main__":
    result = extract_from_pep(484)
    print(f"Concepts: {len(result['concepts'])}")
    print(f"Constructs: {len(result['constructs'])}")
    print(f"Objections: {len(result['objections'])}")
    print(f"Arguments: {len(result['arguments'])}")
    print(f"Introduces edges: {len(result['introduces'])}")
    print(f"Raised objection edges: {len(result['raised_objections'])}")
    print(f"Motivated by edges: {len(result['motivated_by'])}")
    print(f"Implements edges: {len(result['implements'])}")