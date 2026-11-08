from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequirementMatch:
    requirement: str
    status: str
    evidence: str = ""


@dataclass(frozen=True)
class MatchReport:
    score: int
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    requirements: list[RequirementMatch] = field(default_factory=list)
    schedule_risks: list[str] = field(default_factory=list)
    unsupported_claims: list[str] = field(default_factory=list)
    cover_letter: str = ""

