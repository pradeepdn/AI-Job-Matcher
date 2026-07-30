"""
services/matcher.py
────────────────────
Semantic matching pipeline: compares a CandidateProfile against a list of
JobPosting objects using sentence-transformer embeddings + cosine similarity,
then ranks and returns MatchResult objects.

Usage:
    svc = MatcherService()
    results = svc.match(candidate, jobs)   # returns top-N MatchResult objects
"""

from __future__ import annotations

import logging
from typing import List, Optional

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

import config
from models.candidate import CandidateProfile
from models.job import JobPosting
from models.match import MatchResult
from services.embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class MatcherService:
    """
    Computes semantic similarity between a candidate profile and job postings,
    enriches results with skill overlap analysis, and returns a ranked list.
    """

    def __init__(self, embedding_service: Optional[EmbeddingService] = None) -> None:
        self.embeddings = embedding_service or EmbeddingService()

    def match(
        self,
        candidate: CandidateProfile,
        jobs: List[JobPosting],
        top_n: Optional[int] = None,
    ) -> List[MatchResult]:
        """
        Rank jobs by semantic similarity to the candidate profile.

        Args:
            candidate: The parsed candidate profile.
            jobs:      List of job postings to compare against.
            top_n:     Number of top results to return. Defaults to config.TOP_MATCHES_TO_SHOW.

        Returns:
            Sorted list of MatchResult (best match first), limited to top_n.
        """
        top_n = top_n or config.TOP_MATCHES_TO_SHOW

        if not jobs:
            logger.warning("No jobs to match against.")
            return []

        # ── Build candidate text representation ──────────────────────────────
        candidate_text = self._build_candidate_text(candidate)
        if not candidate_text.strip():
            raise ValueError(
                "The candidate profile has no matchable title, skills, roles, or experience."
            )
        logger.info("Matching candidate against %d jobs", len(jobs))

        # ── Encode candidate ──────────────────────────────────────────────────
        candidate_vec = self.embeddings.encode(candidate_text).reshape(1, -1)

        # ── Encode all job descriptions ───────────────────────────────────────
        job_texts = [self._build_job_text(job) for job in jobs]
        job_matrix = self.embeddings.encode_batch(job_texts)  # shape: (N, dim)

        # ── Compute cosine similarities ───────────────────────────────────────
        similarities = cosine_similarity(candidate_vec, job_matrix)[0]  # shape: (N,)

        # ── Build MatchResult objects ─────────────────────────────────────────
        results: List[MatchResult] = []
        candidate_skill_map = {
            skill.strip().lower(): skill.strip()
            for skill in candidate.technical_skills
            if skill.strip()
        }

        for job, raw_score in zip(jobs, similarities):
            # Cosine similarity is mathematically [-1, 1], while the UI score
            # and MatchResult contract are [0, 1].
            score = max(0.0, min(1.0, float(raw_score)))
            job_skill_map = {
                skill.strip().lower(): skill.strip()
                for skill in job.required_skills
                if skill.strip()
            }
            candidate_skill_keys = set(candidate_skill_map)
            job_skill_keys = set(job_skill_map)

            matched = sorted(
                (candidate_skill_map[key] for key in candidate_skill_keys & job_skill_keys),
                key=str.lower,
            )
            missing = sorted(
                (job_skill_map[key] for key in job_skill_keys - candidate_skill_keys),
                key=str.lower,
            )
            bonus = sorted(
                (candidate_skill_map[key] for key in candidate_skill_keys - job_skill_keys),
                key=str.lower,
            )[:10]  # cap bonus skills list

            overlap_ratio = (
                len(matched) / len(job_skill_keys) if job_skill_keys else None
            )

            # Composite score: 70% semantic + 30% skill overlap
            composite: Optional[float] = None
            if overlap_ratio is not None:
                composite = round(0.70 * score + 0.30 * overlap_ratio, 4)

            results.append(
                MatchResult(
                    job=job,
                    semantic_score=round(score, 4),
                    composite_score=composite,
                    matched_skills=matched,
                    missing_skills=missing,
                    bonus_skills=bonus,
                    skill_overlap_ratio=round(overlap_ratio, 4) if overlap_ratio is not None else None,
                )
            )

        # ── Sort and rank ─────────────────────────────────────────────────────
        results.sort(key=lambda r: r.display_score, reverse=True)
        ranked = [
            result.model_copy(update={"rank": rank})
            for rank, result in enumerate(results, start=1)
        ]

        logger.info("Top match: '%s' (%.1f%%)", ranked[0].job.title, ranked[0].display_score * 100)
        return ranked[:top_n]

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_candidate_text(c: CandidateProfile) -> str:
        """Build a single text representation of the candidate for embedding."""
        parts = []
        if c.current_title:
            parts.append(f"Current role: {c.current_title}")
        if c.technical_skills:
            parts.append("Skills: " + ", ".join(c.technical_skills))
        if c.target_roles:
            parts.append("Targeting: " + ", ".join(c.target_roles))
        for exp in c.work_experience[:3]:  # top 3 roles
            role_line = f"{exp.title}" + (f" at {exp.company}" if exp.company else "")
            if exp.responsibilities:
                role_line += ": " + " ".join(exp.responsibilities[:2])[:200]
            parts.append(role_line)
        if c.industries:
            parts.append("Industries: " + ", ".join(c.industries))
        return "\n".join(parts)


    @staticmethod
    def _build_job_text(job: JobPosting) -> str:
        """Build a single text representation of the job for embedding."""
        parts = [f"{job.title} at {job.company}"]
        if job.location:
            parts.append(f"Location: {job.location}")
        if job.required_skills:
            parts.append("Required skills: " + ", ".join(job.required_skills))
        if job.requirements:
            parts.append("Requirements: " + " ".join(job.requirements[:5]))
        if job.description_text:
            parts.append(job.description_text[:800])
        return "\n".join(parts)
