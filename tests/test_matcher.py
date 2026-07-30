"""
tests/test_matcher.py
──────────────────────
Unit tests for services/matcher.py

Uses a mock EmbeddingService to avoid loading the actual sentence-transformers
model during unit tests (which would require a large model download).

Run with:
    pytest tests/test_matcher.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from models.candidate import CandidateProfile, WorkExperience
from models.job import JobPosting, JobSource
from models.match import MatchResult
from services.matcher import MatcherService


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_embedding_service():
    """EmbeddingService that returns deterministic random vectors."""
    svc = MagicMock()
    rng = np.random.default_rng(seed=42)

    def fake_encode(text: str) -> np.ndarray:
        vec = rng.random(384).astype(np.float32)
        vec /= np.linalg.norm(vec)
        return vec

    def fake_encode_batch(texts, **kwargs) -> np.ndarray:
        rng2 = np.random.default_rng(seed=0)
        matrix = rng2.random((len(texts), 384)).astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        return matrix / norms

    svc.encode.side_effect = fake_encode
    svc.encode_batch.side_effect = fake_encode_batch
    return svc


@pytest.fixture
def sample_candidate() -> CandidateProfile:
    return CandidateProfile(
        current_title="Senior Backend Engineer",
        target_roles=["Backend Engineer", "Software Engineer"],
        total_years_experience=5.0,
        technical_skills=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Redis"],
        preferred_locations=["Remote"],
        work_preference="Remote",
        work_experience=[
            WorkExperience(
                title="Senior Backend Engineer",
                company="Acme Corp",
                responsibilities=[
                    "Built scalable APIs with FastAPI and PostgreSQL serving 2M users.",
                    "Led migration of monolith to microservices on AWS ECS.",
                ],
                technologies=["Python", "FastAPI", "PostgreSQL", "AWS"],
                years=3.0,
            )
        ],
    )



@pytest.fixture
def sample_jobs() -> list[JobPosting]:
    return [
        JobPosting(
            id="gh_001",
            source=JobSource.GREENHOUSE,
            external_id="001",
            title="Senior Backend Engineer",
            company="Acme Corp",
            location="Remote",
            is_remote=True,
            required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            description_text="We need a Python engineer with FastAPI and PostgreSQL experience.",
            application_url="https://example.com/jobs/001",
        ),
        JobPosting(
            id="gh_002",
            source=JobSource.GREENHOUSE,
            external_id="002",
            title="Data Scientist",
            company="DataCo",
            location="New York, NY",
            is_remote=False,
            required_skills=["Python", "R", "TensorFlow", "Spark"],
            description_text="Looking for a data scientist with ML and statistical modeling experience.",
            application_url="https://example.com/jobs/002",
        ),
        JobPosting(
            id="lv_003",
            source=JobSource.LEVER,
            external_id="003",
            title="Frontend Engineer",
            company="UICo",
            location="Remote",
            is_remote=True,
            required_skills=["React", "TypeScript", "CSS", "GraphQL"],
            description_text="Building beautiful user interfaces with React and TypeScript.",
            application_url="https://example.com/jobs/003",
        ),
    ]


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestMatcherServiceInit:
    def test_creates_with_custom_embedding_service(self, mock_embedding_service):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        assert matcher.embeddings is mock_embedding_service


class TestMatcherServiceMatch:
    def test_returns_list_of_match_results(self, mock_embedding_service, sample_candidate, sample_jobs):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, sample_jobs, top_n=3)

        assert isinstance(results, list)
        assert all(isinstance(r, MatchResult) for r in results)

    def test_returns_at_most_top_n(self, mock_embedding_service, sample_candidate, sample_jobs):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, sample_jobs, top_n=2)
        assert len(results) <= 2

    def test_results_have_semantic_score(self, mock_embedding_service, sample_candidate, sample_jobs):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, sample_jobs, top_n=3)

        for r in results:
            assert 0.0 <= r.semantic_score <= 1.0

    def test_skill_overlap_calculated(self, mock_embedding_service, sample_candidate, sample_jobs):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, sample_jobs, top_n=3)

        # The backend job shares Python, FastAPI, PostgreSQL, Docker with candidate
        backend_result = next(r for r in results if r.job.id == "gh_001")
        assert "python" in backend_result.matched_skills or "Python" in backend_result.matched_skills

    def test_missing_skills_identified(self, mock_embedding_service, sample_candidate, sample_jobs):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, sample_jobs, top_n=3)

        # Frontend job requires React, TypeScript, CSS, GraphQL — candidate has none of these
        frontend_result = next(r for r in results if r.job.id == "lv_003")
        missing_lower = [s.lower() for s in frontend_result.missing_skills]
        assert "react" in missing_lower or "typescript" in missing_lower

    def test_empty_jobs_returns_empty_list(self, mock_embedding_service, sample_candidate):
        matcher = MatcherService(embedding_service=mock_embedding_service)
        results = matcher.match(sample_candidate, [], top_n=5)
        assert results == []

    def test_negative_cosine_similarity_is_clamped(self, sample_candidate, sample_jobs):
        embeddings = MagicMock()
        embeddings.encode.return_value = np.array([1.0, 0.0], dtype=np.float32)
        embeddings.encode_batch.return_value = np.array(
            [[-1.0, 0.0]], dtype=np.float32
        )

        matcher = MatcherService(embedding_service=embeddings)
        result = matcher.match(sample_candidate, [sample_jobs[0]], top_n=1)[0]

        assert result.semantic_score == 0.0
        assert 0.0 <= result.display_score <= 1.0


class TestMatcherTextBuilders:
    def test_build_candidate_text_includes_skills(self, sample_candidate):
        text = MatcherService._build_candidate_text(sample_candidate)
        assert "Python" in text

    def test_build_candidate_text_includes_summary(self, sample_candidate):
        text = MatcherService._build_candidate_text(sample_candidate)
        # current_title replaces professional_summary in Phase 3
        assert "backend engineer" in text.lower() or "senior" in text.lower()


    def test_build_job_text_includes_title(self, sample_jobs):
        text = MatcherService._build_job_text(sample_jobs[0])
        assert "Senior Backend Engineer" in text

    def test_build_job_text_includes_skills(self, sample_jobs):
        text = MatcherService._build_job_text(sample_jobs[0])
        assert "FastAPI" in text
