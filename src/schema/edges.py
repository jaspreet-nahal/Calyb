from pydantic import BaseModel, Field
from typing import Literal


class BaseEdge(BaseModel):
    source: str
    target: str
    type: str
    attributes: dict = Field(default_factory=dict)
    provenance: str = ""
    extraction_method: Literal["rule"] = "rule"
    confidence: float = 1.0


class SupercedesEdge(BaseEdge):
    type: str = "supersedes"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_pep: int,
        explicit: bool = True,
        provenance: str = "PEP header",
    ) -> "SupercedesEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"pep-{target_pep}",
            attributes={"explicit": explicit},
            provenance=provenance,
            extraction_method="rule",
            confidence=1.0,
        )


class ReplacesEdge(BaseEdge):
    type: str = "replaces"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_pep: int,
        partial: bool = True,
        provenance: str = "PEP header",
    ) -> "ReplacesEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"pep-{target_pep}",
            attributes={"partial": partial},
            provenance=provenance,
            extraction_method="rule",
            confidence=1.0,
        )


class DependsOnEdge(BaseEdge):
    type: str = "depends_on"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_pep: int,
        hard: bool = True,
        source: str = "header",
        provenance: str = "PEP header",
        confidence: float = 1.0,
    ) -> "DependsOnEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"pep-{target_pep}",
            attributes={"hard": hard, "source": source},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class ExtendsEdge(BaseEdge):
    type: str = "extends"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_pep: int,
        concept: str,
        source: str = "header",
        provenance: str = "PEP header",
        confidence: float = 1.0,
    ) -> "ExtendsEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"pep-{target_pep}",
            attributes={"concept": concept, "source": source},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class ConflictsWithEdge(BaseEdge):
    type: str = "conflicts_with"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_pep: int,
        conflict_type: str,
        flagged_for_review: bool = True,
        provenance: str = "PEP section",
        confidence: float = 0.6,
    ) -> "ConflictsWithEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"pep-{target_pep}",
            attributes={"conflict_type": conflict_type, "flagged_for_review": flagged_for_review},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class IntroducesEdge(BaseEdge):
    type: str = "introduces"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_id: str,
        section: str,
        role: Literal["origin", "uses"] = "origin",
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "IntroducesEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=target_id,
            attributes={"section": section, "role": role},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class RaisedObjectionEdge(BaseEdge):
    type: str = "raised_objection"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_objection: str,
        section: str,
        resolved: bool = False,
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "RaisedObjectionEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=target_objection,
            attributes={"section": section, "resolved": resolved},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class RejectedAlternativeEdge(BaseEdge):
    type: str = "rejected_alternative"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_alternative: str,
        section: str,
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "RejectedAlternativeEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=target_alternative,
            attributes={"section": section},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class ResolvedByEdge(BaseEdge):
    type: str = "resolved_by"

    @classmethod
    def create(
        cls,
        source_objection: str,
        target_id: str,
        how: Literal["accepted", "mitigated", "deferred"],
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "ResolvedByEdge":
        return cls(
            source=source_objection,
            target=target_id,
            attributes={"how": how},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class MotivatedByEdge(BaseEdge):
    type: str = "motivated_by"

    @classmethod
    def create(
        cls,
        source_id: str,
        target_argument: str,
        section: str,
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "MotivatedByEdge":
        return cls(
            source=source_id,
            target=target_argument,
            attributes={"section": section},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )


class AuthoredByEdge(BaseEdge):
    type: str = "authored_by"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_person: str,
        role: str,
        provenance: str = "PEP header",
    ) -> "AuthoredByEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=target_person,
            attributes={"role": role},
            provenance=provenance,
            extraction_method="rule",
            confidence=1.0,
        )


class TargetsVersionEdge(BaseEdge):
    type: str = "targets_version"

    @classmethod
    def create(
        cls,
        source_pep: int,
        target_version: str,
        provenance: str = "PEP header",
    ) -> "TargetsVersionEdge":
        return cls(
            source=f"pep-{source_pep}",
            target=f"python-{target_version}",
            attributes={},
            provenance=provenance,
            extraction_method="rule",
            confidence=1.0,
        )


class ImplementsEdge(BaseEdge):
    type: str = "implements"

    @classmethod
    def create(
        cls,
        source_construct: str,
        target_concept: str,
        provenance: str = "PEP section",
        confidence: float = 0.9,
    ) -> "ImplementsEdge":
        return cls(
            source=source_construct,
            target=target_concept,
            attributes={},
            provenance=provenance,
            extraction_method="rule",
            confidence=confidence,
        )