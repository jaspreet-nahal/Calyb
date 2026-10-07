Approach for the PEP Typing Knowledge Graph

What I built

I built a small knowledge graph about the history of Python typing PEPs. The
practical question it answers is:

    If I propose a new typing feature, what similar proposals came before,
    what concern terms appear in those PEPs, and what should I inspect next?

This is not intended to be a general search engine. It is a proposal
pre-mortem tool. It shows a small, inspectable slice of design history so a
developer can decide what to read next.

Data subset

I selected 25 PEPs from the Python PEP repository. The set is focused on the
typing lineage instead of trying to include every PEP.

The main groups are:

- foundations: PEP 483, 484 and 526
- structural typing: PEP 544
- annotation evaluation: PEP 563, 649 and 749
- generics and syntax: PEP 585, 604, 612, 646, 695 and 696
- rejected syntax: PEP 677
- TypedDict evolution: PEP 589, 655, 692 and 705
- type narrowing: PEP 647, 724 and 742
- qualifiers and forms: PEP 586, 591, 673 and 698

I chose this subset because it has both successful and unsuccessful design
decisions. PEP 677 is especially useful because it contains a rejected syntax
proposal. PEPs 649 and 749 are useful for understanding how the approach to
annotation evaluation changed over time.

I did not include every typing PEP. PEPs such as 593, 613, 675, 681, 702 and
728 were left out to keep the graph small enough to inspect and the question
focused enough to be useful.

Entities in the graph

The graph has these entity types:

- `pep`: the main proposal, with status, title, authors, version and lineage
- `concept`: an abstract area such as generics or structural subtyping
- `construct`: a user-facing thing such as TypeVar, Protocol or TypeGuard
- `objection`: a lexicon-triggered concern mention with source text
- `argument`: a lexicon-triggered rationale mention with source text
- `alternative`: an approach that was rejected or withdrawn
- `decision`: the outcome represented by a PEP status
- `person`: an author or other person in the PEP headers
- `python_version`: a Python version connected to a proposal

I used separate Concept and Construct nodes because they answer different
questions. A concept is the general idea, while a construct is what a Python
user actually writes or uses.

Relationships

The important relationship types are:

- `supersedes` and `replaces` connect later PEPs to earlier ones
- `depends_on` represents a required or referenced earlier proposal
- `extends` connects a proposal to an earlier related proposal
- `introduces` connects a PEP to a concept or construct
- `raised_objection` connects a PEP to a concern
- `rejected_alternative` connects a PEP to an alternative
- `resolved_by` connects a concern to an argument or decision
- `motivated_by` connects a PEP to an argument
- `authored_by` connects a PEP to a person
- `targets_version` connects a PEP to a Python version
- `implements` connects a construct to its concept
- `conflicts_with` records explicit incompatibility language

Each edge stores provenance, the rules extraction method and a hand-set
support value. These values are not learned confidence estimates. They are
only a rough distinction between header matches and weaker text patterns.

Building the knowledge state

The raw PEP files are stored in data/raw. The ingestion code first parses the
PEP headers. This creates the PEP nodes and the strongest structural edges,
such as Requires, Replaces, Superseded-By and Author.

The section parser then separates sections such as Motivation, Rationale,
Rejected Ideas, Backwards Compatibility and Implementation.

The extraction is mainly rules based. I created a lexicon in
src/schema/lexicon.yaml. It maps terms to the concept and construct IDs that
I defined. Regular expressions find those terms in the PEP sections. Similar
matches are deduplicated and then converted into nodes and edges.

Concern records are found using objection terms and section context. This does
not prove that every match is a distinct objection. Alternatives are collected
from rejected-idea and rejected-alternative sections. The source paragraph is
kept, but a separate rejection reason is not inferred.

The graph is assembled as a NetworkX MultiDiGraph. A MultiDiGraph lets the
same two nodes have more than one relationship where that is needed. The
final graph is exported as JSON. This JSON file is the inspectable knowledge
state required for the project.

I did not use an automatic entity and relationship extraction product. The
entity definitions, relationship types, lexicon and mapping rules are the
important part of this project. The build and report path is deliberately
rules based so the result can be inspected without a model.

How a new input is handled

The user gives the system a new proposal, not one of the original PEP files.
The input is matched to the same concepts and constructs in the lexicon.
The system then:

1. finds PEPs that introduced related concepts
2. follows relevant graph relationships
3. ranks related PEPs with a hand-written heuristic
4. collects concern evidence connected to those precedents
5. collects rejected alternatives
6. reports dependencies and explicit conflicts
7. produces a heuristic risk flag and reading-oriented next steps

The ranking uses concept overlap, graph proximity and recency. I left out
semantic embeddings because the lexicon and graph relationships should be
visible reasons for a ranking, not a hidden model score.

The output is a JSON report and a Markdown report. The report includes the
input concepts, related precedents, scores, historical concern evidence,
alternatives, dependencies, conflicts, outcome history, a heuristic risk flag
and recommendations for further reading.

Tradeoffs and limitations

I chose explainability over broad coverage. A smaller graph with explicit
provenance is more useful for this assignment than thousands of shallow
entities.

The main limitation is that PEP files summarise discussions. They do not
contain every message from the mailing lists, so some concerns and rationales
are missing. The extraction is rule based and can over-match common words.
It records evidence around terms; it does not resolve the discourse or prove
the author's stance.

The graph is static until the build command is run again. There is no
incremental update system yet. The lexicon is English-only, and the scoring
weights are heuristics rather than learned weights.

What I would build next

First I would improve the argument and alternative extraction with better
section-aware rules and a larger hand-checked gold set. I would then add
mailing-list or Discourse data so that the graph contains the debate behind
the PEP summaries.

After that I would add incremental updates for new PEPs and temporal
reasoning. For example, the graph should be able to represent how the meaning
or status of a proposal changed across Python versions. I would also like to
learn the ranking weights from examples of real proposal outcomes.

These choices are not perfect, but they give a inspectable knowledge state and
a testable reasoning path instead of only searching the original documents.
