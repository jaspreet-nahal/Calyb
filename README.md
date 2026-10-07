# PEP Typing Knowledge Graph

A system for analyzing Python typing-related PEPs and providing "Proposal Pre-Mortem" reports for new typing feature proposals.

## What It Does

Given a rough idea for a new typing-related language feature, the system:
1. Maps the input to known typing concepts from PEP history
2. Finds the closest precedent PEPs (accepted, rejected, superseded)
3. Shows recurring concern terms found in related PEP sections
4. Lists rejected alternatives from related proposals
5. Identifies dependencies and conflicts with current language
6. Suggests what to inspect next based on the matched records

Relationships point back to PEP headers or sections in a knowledge graph built
from 25 typing-related PEPs. The report is a rule-based aid, not a claim that
the system understands the full historical debate.

## Structure

```
pep-typing-kg/
├── README.md              # This file
├── approach.md            # Design document (first-person)
├── requirements.txt       # Python dependencies
├── cli.py                 # Command-line interface
├── knowledge_state/       # Serialized knowledge graph
├── data/raw/              # Cached PEP .rst files
├── src/
│   ├── schema/            # Pydantic models + lexicon
│   ├── ingestion/         # Fetch, parse headers, parse sections, extract
│   ├── graph/             # NetworkX builder + exporters
│   ├── reasoning/         # Input mapping, traversals, scoring, report generation
│   └── utils/             # Small shared helpers
```

## Install

```bash
pip install -r requirements.txt
```

Requires Python 3.10+.

## Build the Knowledge Graph

```bash
python cli.py build
```

This will:
1. Fetch all 25 PEPs from github.com/python/peps (cached in `data/raw/`)
2. Parse headers (Status, Requires, Replaces, Superseded-By, etc.)
3. Parse sections (Abstract, Motivation, Rationale, Rejected Ideas, etc.)
4. Extract lexicon matches and source-text evidence using rules
5. Build NetworkX MultiDiGraph with typed nodes and edges
6. Export the inspectable knowledge state to `knowledge_state/graph.json`.

## Run a Pre-Mortem

```bash
# From command line
python cli.py premortem "I want to add a typing.Frozen for immutable dataclass fields" report

# From a text file
python cli.py premortem-file proposal.txt report
```

Outputs:
- `report.json` — structured report produced by the rules
- `report.md` — human-readable Markdown

## PEP Corpus (25 PEPs)

**Foundations**: 483, 484, 526  
**Structural Typing**: 544  
**Annotation Evaluation**: 563, 649, 749  
**Generics and Syntax**: 585, 604, 612, 646, 695, 696  
**Rejected Syntax**: 677  
**TypedDict Evolution**: 589, 655, 692, 705  
**Type Narrowing**: 647, 724, 742  
**Qualifiers and Forms**: 586, 591, 673, 698  

*Excluded*: 593 (Annotated), 613 (TypeAlias), 675 (LiteralString), 681 (dataclass_transform), 702, 728, and non-typing PEPs.

## Graph Schema

**Nodes** (9 types): `pep`, `concept`, `construct`, `objection`, `argument`, `alternative`, `decision`, `person`, `python_version`  
**Edges** (14 types): `supersedes`, `replaces`, `depends_on`, `extends`, `conflicts_with`, `introduces`, `raised_objection`, `rejected_alternative`, `resolved_by`, `motivated_by`, `authored_by`, `targets_version`, `implements`

Every edge carries provenance (usually the PEP and section where it was found).
Objection and argument nodes also keep the source sentence used to create
them. The numeric support values are hand-set rule metadata, not measured
probabilities.

## Configuration

Key settings in code:
- `src/schema/lexicon.yaml` — the manually written term lexicon
- `src/reasoning/score.py` — concept overlap, graph proximity and recency weights
The premortem command uses the checked-in `knowledge_state/graph.json` and
does not require an external model. Its risk level and ranking are heuristic:
they use matched concepts, graph distance, version metadata and counts of
historical concern matches. The flag is not a prediction of whether a future
proposal will be accepted. Run `python cli.py build` only when regenerating
the knowledge state.

## Known Limitations

1. PEP text only — no mailing list/Discourse mining
2. English-only lexicon
3. Static graph — no incremental updates
4. No temporal reasoning beyond version numbers
5. Scoring weights are heuristic
6. Conflicts are sparsely populated because only explicit text patterns are used

## License

MIT