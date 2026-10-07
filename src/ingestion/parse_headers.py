import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from src.schema.nodes import PEPNode

HEADER_PATTERN = re.compile(r"^:?(\w+(?:-\w+)?):\s*(.+)$", re.MULTILINE)

HEADER_ALIASES = {
    "pep": "number",
    "title": "title",
    "status": "status",
    "type": "pep_type",
    "created": "created",
    "python-version": "python_version",
    "replaces": "replaces",
    "superseded-by": "superseded_by",
    "requires": "requires",
    "post-history": "post_history",
    "author": "authors",
    "author-name": "authors",
    "discussions-to": "discussions_to",
    "resolution": "resolution",
    "bdfl-delegate": "bdfl_delegate",
    "topic": "topic",
}

@dataclass
class ParsedPEPHeader:
    number: int
    title: str
    status: str
    pep_type: str
    created: str
    python_version: Optional[str] = None
    replaces: list[int] = field(default_factory=list)
    superseded_by: list[int] = field(default_factory=list)
    requires: list[int] = field(default_factory=list)
    post_history: list[str] = field(default_factory=list)
    authors: list[str] = field(default_factory=list)
    discussions_to: Optional[str] = None
    resolution: Optional[str] = None
    bdfl_delegate: Optional[str] = None
    topic: Optional[str] = None
    raw_headers: dict[str, str] = field(default_factory=dict)

    def to_node(self) -> PEPNode:
        return PEPNode(
            id=f"pep-{self.number}",
            label=f"PEP {self.number}: {self.title}",
            attributes={
                "number": self.number,
                "title": self.title,
                "status": self.status,
                "type": self.pep_type,
                "created": self.created,
                "python_version": self.python_version,
                "replaces": self.replaces,
                "superseded_by": self.superseded_by,
                "requires": self.requires,
                "post_history": self.post_history,
                "authors": self.authors,
                "discussions_to": self.discussions_to,
                "resolution": self.resolution,
                "bdfl_delegate": self.bdfl_delegate,
                "topic": self.topic,
            },
            source_peps=[self.number],
            provenance="PEP headers",
        )


def parse_pep_list(value: str) -> list[int]:
    if not value.strip():
        return []
    parts = re.split(r"[,\s]+", value.strip())
    result = []
    for part in parts:
        if part.isdigit():
            result.append(int(part))
    return result


def parse_authors(value: str) -> list[str]:
    if not value.strip():
        return []
    authors = []
    for a in re.split(r",\s*", value):
        a = a.strip()
        if not a:
            continue
        a = re.sub(r"\s*<[^>]+>", "", a).strip()
        if a:
            authors.append(a)
    return authors


def parse_header_file(content: str) -> ParsedPEPHeader:
    lines = content.split("\n")
    header_lines = []
    for line in lines:
        if line.strip() == "":
            break
        header_lines.append(line)
    header_text = "\n".join(header_lines)

    matches = HEADER_PATTERN.findall(header_text)
    raw = {}
    for key, val in matches:
        raw[key.lower()] = val.strip()

    number = int(raw.get("pep", "0"))
    title = raw.get("title", "")
    status = raw.get("status", "")
    pep_type = raw.get("type", "")
    created = raw.get("created", "")

    python_version = raw.get("python-version")
    if python_version:
        python_version = python_version.strip()

    replaces = parse_pep_list(raw.get("replaces", ""))
    superseded_by = parse_pep_list(raw.get("superseded-by", ""))
    requires = parse_pep_list(raw.get("requires", ""))

    post_history = []
    ph = raw.get("post-history", "")
    if ph:
        post_history = [h.strip() for h in ph.split(",") if h.strip()]

    authors = parse_authors(raw.get("author", ""))

    discussions_to = raw.get("discussions-to")
    resolution = raw.get("resolution")
    bdfl_delegate = raw.get("bdfl-delegate")
    topic = raw.get("topic")

    return ParsedPEPHeader(
        number=number,
        title=title,
        status=status,
        pep_type=pep_type,
        created=created,
        python_version=python_version,
        replaces=replaces,
        superseded_by=superseded_by,
        requires=requires,
        post_history=post_history,
        authors=authors,
        discussions_to=discussions_to,
        resolution=resolution,
        bdfl_delegate=bdfl_delegate,
        topic=topic,
        raw_headers=raw,
    )


def load_and_parse(pep_num: int, raw_dir: Path = Path("data/raw")) -> ParsedPEPHeader:
    path = raw_dir / f"pep-{pep_num:04d}.rst"
    content = path.read_text(encoding="utf-8")
    return parse_header_file(content)


def parse_all(raw_dir: Path = Path("data/raw")) -> list[ParsedPEPHeader]:
    results = []
    for path in sorted(raw_dir.glob("pep-*.rst")):
        match = re.match(r"pep-(\d+)\.rst", path.name)
        if match:
            num = int(match.group(1))
            try:
                parsed = load_and_parse(num, raw_dir)
                results.append(parsed)
            except Exception as e:
                print(f"Failed to parse PEP {num}: {e}")
    return results


if __name__ == "__main__":
    import sys
    results = parse_all()
    for p in results:
        print(f"PEP {p.number}: {p.title} | Status: {p.status} | Type: {p.pep_type} | Python: {p.python_version}")
        print(f"  Replaces: {p.replaces} | Superseded-By: {p.superseded_by} | Requires: {p.requires}")
        print(f"  Authors: {p.authors}")
        if p.bdfl_delegate:
            print(f"  BDFL-Delegate: {p.bdfl_delegate}")
        if p.topic:
            print(f"  Topic: {p.topic}")