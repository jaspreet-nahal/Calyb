import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class Section:
    name: str
    level: int
    content: str
    start_line: int
    end_line: int

SECTION_TITLE_PATTERN = re.compile(r"^(\w[\w\s]*)$")
SECTION_UNDERLINE_PATTERN = re.compile(r"^([=-]{3,})$")

KNOWN_SECTIONS = {
    "abstract": "abstract",
    "motivation": "motivation",
    "rationale": "rationale",
    "rationale and goals": "rationale",
    "rejected ideas": "rejected_ideas",
    "rejected alternatives": "rejected_alternatives",
    "backwards compatibility": "backwards_compatibility",
    "backward compatibility": "backwards_compatibility",
    "open issues": "open_issues",
    "contentious issues": "open_issues",
    "implementation": "implementation",
    "reference implementation": "implementation",
    "security implications": "security",
    "copyright": "copyright",
}


def extract_sections(content: str) -> list[Section]:
    sections = []
    lines = content.split("\n")
    current_section = None
    current_level = 1
    section_start = 0
    section_content = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if (i + 1 < len(lines) and
            SECTION_TITLE_PATTERN.match(line) and
            SECTION_UNDERLINE_PATTERN.match(lines[i + 1])):
            title = line.strip()
            underline = lines[i + 1]
            level = 1 if underline.startswith("=") else 2

            if current_section is not None:
                sections.append(Section(
                    name=current_section,
                    level=current_level,
                    content="\n".join(section_content).strip(),
                    start_line=section_start,
                    end_line=i - 1,
                ))

            current_section = title
            current_level = level
            section_start = i + 2
            section_content = []
            i += 2  
            continue

        if current_section is not None:
            section_content.append(line)

        i += 1

    if current_section is not None:
        sections.append(Section(
            name=current_section,
            level=current_level,
            content="\n".join(section_content).strip(),
            start_line=section_start,
            end_line=len(lines) - 1,
        ))

    return sections


def normalize_section_name(name: str) -> str:
    name = name.lower().strip()
    return KNOWN_SECTIONS.get(name, name.replace(" ", "_"))


def parse_sections_file(content: str) -> dict[str, str]:
    sections = extract_sections(content)
    result = {}
    for sec in sections:
        norm_name = normalize_section_name(sec.name)
        if norm_name in result:
            result[norm_name] += "\n\n" + sec.content
        else:
            result[norm_name] = sec.content
    return result


def load_and_parse_sections(pep_num: int, raw_dir: Path = Path("data/raw")) -> dict[str, str]:
    path = raw_dir / f"pep-{pep_num:04d}.rst"
    content = path.read_text(encoding="utf-8")
    return parse_sections_file(content)


if __name__ == "__main__":
    import sys
    sections = parse_sections_file(Path("data/raw/pep-0484.rst").read_text())
    for name, content in sections.items():
        print(name)
        print(content[:200])
        print()