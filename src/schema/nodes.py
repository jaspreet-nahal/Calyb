from pydantic import BaseModel, Field
from typing import Optional
class BaseNode(BaseModel):
    id: str
    label: str
    type: str
    attributes: dict = Field(default_factory=dict)
    source_peps: list[int] = Field(default_factory=list)
    provenance: str = ""


class PEPNode(BaseNode):
    type: str = "pep"

    @classmethod
    def create(
        cls,
        number: int,
        title: str,
        status: str,
        pep_type: str,
        created: str,
        python_version: Optional[str] = None,
        replaces: Optional[list[int]] = None,
        superseded_by: Optional[list[int]] = None,
        requires: Optional[list[int]] = None,
        post_history: Optional[list[str]] = None,
        authors: Optional[list[str]] = None,
        discussions_to: Optional[str] = None,
        resolution: Optional[str] = None,
        bdfl_delegate: Optional[str] = None,
        topic: Optional[str] = None,
        lineage: Optional[str] = None,
        provenance: str = "PEP headers",
    ) -> "PEPNode":
        attrs = {
            "number": number,
            "title": title,
            "status": status,
            "pep_type": pep_type,
            "created": created,
            "python_version": python_version,
            "replaces": replaces or [],
            "superseded_by": superseded_by or [],
            "requires": requires or [],
            "post_history": post_history or [],
            "authors": authors or [],
            "discussions_to": discussions_to,
            "resolution": resolution,
            "bdfl_delegate": bdfl_delegate,
            "topic": topic,
            "lineage": lineage,
        }
        return cls(
            id=f"pep-{number}",
            label=f"PEP {number}: {title}",
            attributes=attrs,
            source_peps=[number],
            provenance=provenance,
        )


class ConceptNode(BaseNode):
    type: str = "concept"

    @classmethod
    def create(
        cls,
        concept_id: str,
        name: str,
        category: str,
        description: str = "",
        provenance: str = "lexicon",
    ) -> "ConceptNode":
        return cls(
            id=concept_id,
            label=name,
            attributes={
                "name": name,
                "category": category,
                "description": description,
            },
            provenance=provenance,
        )


class ConstructNode(BaseNode):
    type: str = "construct"

    @classmethod
    def create(
        cls,
        construct_id: str,
        name: str,
        kind: str,
        introduced_in: int,
        signature: str = "",
        example: str = "",
        provenance: str = "PEP section",
    ) -> "ConstructNode":
        return cls(
            id=construct_id,
            label=name,
            attributes={
                "name": name,
                "kind": kind,
                "introduced_in": introduced_in,
                "signature": signature,
                "example": example,
            },
            source_peps=[introduced_in],
            provenance=provenance,
        )


class ObjectionNode(BaseNode):
    type: str = "objection"

    @classmethod
    def create(
        cls,
        objection_id: str,
        summary: str,
        category: str,
        raised_by: str = "community",
        pep_section: str = "",
        evidence: str = "",
        provenance: str = "PEP section",
    ) -> "ObjectionNode":
        return cls(
            id=objection_id,
            label=summary[:80],
            attributes={
                "summary": summary,
                "category": category,
                "raised_by": raised_by,
                "pep_section": pep_section,
                "evidence": evidence,
            },
            provenance=provenance,
        )


class ArgumentNode(BaseNode):
    type: str = "argument"

    @classmethod
    def create(
        cls,
        argument_id: str,
        summary: str,
        stance: str,
        category: str,
        pep_section: str = "",
        evidence: str = "",
        provenance: str = "PEP section",
    ) -> "ArgumentNode":
        return cls(
            id=argument_id,
            label=summary[:80],
            attributes={
                "summary": summary,
                "stance": stance,
                "category": category,
                "pep_section": pep_section,
                "evidence": evidence,
            },
            provenance=provenance,
        )


class AlternativeNode(BaseNode):
    type: str = "alternative"

    @classmethod
    def create(
        cls,
        alternative_id: str,
        summary: str,
        rejection_reason: str = "",
        pep_section: str = "",
        proposed_by: str = "author",
        provenance: str = "PEP section",
    ) -> "AlternativeNode":
        return cls(
            id=alternative_id,
            label=summary[:80],
            attributes={
                "summary": summary,
                "rejection_reason": rejection_reason,
                "pep_section": pep_section,
                "proposed_by": proposed_by,
            },
            provenance=provenance,
        )


class DecisionNode(BaseNode):
    type: str = "decision"

    @classmethod
    def create(
        cls,
        decision_id: str,
        outcome: str,
        rationale_summary: str = "",
        decided_by: str = "",
        pep_section: str = "",
        provenance: str = "PEP section",
    ) -> "DecisionNode":
        return cls(
            id=decision_id,
            label=outcome,
            attributes={
                "outcome": outcome,
                "rationale_summary": rationale_summary,
                "decided_by": decided_by,
                "pep_section": pep_section,
            },
            provenance=provenance,
        )


class PersonNode(BaseNode):
    type: str = "person"

    @classmethod
    def create(
        cls,
        person_id: str,
        name: str,
        role: str,
        peps: Optional[list[int]] = None,
        provenance: str = "PEP header",
    ) -> "PersonNode":
        return cls(
            id=person_id,
            label=name,
            attributes={
                "name": name,
                "role": role,
                "peps": peps or [],
            },
            provenance=provenance,
        )


class PythonVersionNode(BaseNode):
    type: str = "python_version"

    @classmethod
    def create(
        cls,
        version: str,
        release_date: str = "",
        peps_included: Optional[list[int]] = None,
        provenance: str = "PEP header",
    ) -> "PythonVersionNode":
        return cls(
            id=f"python-{version}",
            label=f"Python {version}",
            attributes={
                "version": version,
                "release_date": release_date,
                "peps_included": peps_included or [],
            },
            provenance=provenance,
        )