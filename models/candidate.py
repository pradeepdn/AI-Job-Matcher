"""
models/candidate.py
────────────────────
Phase 3 — Candidate profile schema.

Rules enforced by the schema:
  - Only extract facts explicitly supported by the resume text.
  - Use None or [] when information is unavailable.
  - Do not infer duration from project count — use evidence.
"""

from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


# ── Sub-models ─────────────────────────────────────────────────────────────────

class WorkExperience(BaseModel):
    """A single work history entry extracted from the resume."""

    title: Optional[str] = Field(default="Position", description="Job title, e.g. 'Senior Backend Engineer'")
    company: Optional[str] = Field(default=None, description="Employer name")
    responsibilities: list[str] = Field(
        default_factory=list,
        description="Bullet-point responsibilities and achievements, verbatim or lightly paraphrased",
    )
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies, languages, and tools explicitly mentioned in this role",
    )
    years: Optional[float] = Field(
        default=None,
        description="Duration in years at this role, derived from dates if present",
    )


class Project(BaseModel):
    """A personal, open-source, or portfolio project from the resume."""

    name: Optional[str] = Field(default="Project", description="Project name")
    description: Optional[str] = Field(default="", description="What the project does, as stated on the resume")
    technologies: list[str] = Field(
        default_factory=list,
        description="Technologies used in this project",
    )


class SkillEvidence(BaseModel):
    """
    Links a skill to concrete resume evidence.

    Makes AI recommendations explainable — every surfaced skill has a
    citation from the actual resume text.
    """

    skill: str = Field(default="", description="The skill name, e.g. 'AWS'")
    evidence: list[str] = Field(
        default_factory=list,
        description=(
            "Verbatim or lightly paraphrased sentences from the resume that "
            "demonstrate this skill."
        ),
    )


# ── Main profile ───────────────────────────────────────────────────────────────

class CandidateProfile(BaseModel):
    """
    Structured representation of a candidate, built by ResumeAnalyzerAgent.

    All fields are extracted from the resume text only.
    Contact information is intentionally excluded — only career-relevant
    data is captured here.
    """

    @model_validator(mode="before")
    @classmethod
    def clean_and_heal_profile(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Heal skill_evidence if it was output as a flat list of strings or as a dictionary
        evidence = data.get("skill_evidence")
        if isinstance(evidence, list):
            healed_evidence = []
            tech_skills = data.get("technical_skills", [])
            if not isinstance(tech_skills, list):
                tech_skills = []

            for item in evidence:
                if isinstance(item, str):
                    # Find a matching technical skill from candidate's skills
                    matched_skill = ""
                    item_lower = item.lower()
                    for skill in tech_skills:
                        if isinstance(skill, str) and skill.strip():
                            if skill.lower() in item_lower:
                                matched_skill = skill
                                break
                    if not matched_skill:
                        matched_skill = "General"

                    healed_evidence.append({
                        "skill": matched_skill,
                        "evidence": [item]
                    })
                elif isinstance(item, dict):
                    healed_evidence.append(item)
                else:
                    healed_evidence.append(item)
            data["skill_evidence"] = healed_evidence
        elif isinstance(evidence, dict):
            healed_evidence = []
            for skill_name, skill_val in evidence.items():
                if isinstance(skill_val, list):
                    healed_evidence.append({
                        "skill": skill_name,
                        "evidence": [str(x) for x in skill_val]
                    })
                elif isinstance(skill_val, str):
                    healed_evidence.append({
                        "skill": skill_name,
                        "evidence": [skill_val]
                    })
            data["skill_evidence"] = healed_evidence

        return data

    # ── Career identity ────────────────────────────────────────────────────────
    current_title: Optional[str] = Field(
        default=None,
        description="Most recent or current job title, exactly as stated on the resume",
    )
    target_roles: list[str] = Field(
        default_factory=list,
        description=(
            "Job titles the candidate is clearly suited for, inferred from experience. "
            "E.g. ['Backend Engineer', 'Python Developer', 'AI Application Engineer']"
        ),
    )
    total_years_experience: Optional[float] = Field(
        default=None,
        description="Total professional experience in years, calculated from date ranges",
    )
    # ── Skills ────────────────────────────────────────────────────────────────
    technical_skills: list[str] = Field(
        default_factory=list,
        description="Programming languages, frameworks, tools, databases, cloud platforms",
    )
    soft_skills: list[str] = Field(
        default_factory=list,
        description="Communication, leadership, problem-solving skills as stated in the resume",
    )

    # ── Experience & projects ─────────────────────────────────────────────────
    work_experience: list[WorkExperience] = Field(
        default_factory=list,
        description="Work history, most recent first",
    )
    projects: list[Project] = Field(
        default_factory=list,
        description="Personal, open-source, or portfolio projects",
    )

    # ── Education & credentials ────────────────────────────────────────────────
    education: list[str] = Field(
        default_factory=list,
        description=(
            "Education entries as descriptive strings, "
            "e.g. 'B.S. Computer Science, Stanford University, 2018'"
        ),
    )
    certifications: list[str] = Field(
        default_factory=list,
        description="Certifications and licenses, e.g. 'AWS Certified Solutions Architect'",
    )

    # ── Domain context ─────────────────────────────────────────────────────────
    industries: list[str] = Field(
        default_factory=list,
        description="Industry verticals the candidate has worked in, e.g. ['FinTech', 'SaaS']",
    )

    # ── Evidence layer (Phase 4) ───────────────────────────────────────────────
    skill_evidence: list[SkillEvidence] = Field(
        default_factory=list,
        description=(
            "Evidence citations for the most important technical skills. "
            "Covers the top 5–10 skills. Omit skills with no concrete resume evidence."
        ),
    )

    # ── User preferences (set during review, NOT extracted from resume) ────────
    preferred_locations: list[str] = Field(
        default_factory=list,
        description="Target locations entered by the user during the review step",
    )
    work_preference: Optional[str] = Field(
        default=None,
        description="'Remote', 'Hybrid', or 'Onsite' — set by user during review",
    )
