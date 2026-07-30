"""
tests/test_job_parser.py
─────────────────────────
Unit tests for job_sources/greenhouse.py and job_sources/lever.py

Uses pytest-mock to patch HTTP calls — no real API requests are made.

Run with:
    pytest tests/test_job_parser.py -v
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from job_sources.greenhouse import GreenhouseSource
from job_sources.lever import LeverSource
from models.job import JobSource, JobPosting


# ── Fixtures ───────────────────────────────────────────────────────────────────

SAMPLE_GH_JOB = {
    "id": 99001,
    "title": "Senior Software Engineer",
    "location": {"name": "San Francisco, CA"},
    "absolute_url": "https://boards.greenhouse.io/testco/jobs/99001",
    "content": "<p>We need a <b>Python</b> developer with FastAPI experience.</p>",
    "company": {"name": "TestCo"},
}

SAMPLE_LEVER_JOB = {
    "id": "lv-abc-123",
    "text": "Backend Engineer",
    "categories": {
        "location": "Remote",
        "department": "Engineering",
        "team": "Platform",
    },
    "descriptionPlain": "We are hiring a Backend Engineer with Python and Go skills.",
    "lists": [
        {
            "text": "Requirements",
            "content": "<ul><li>3+ years Python</li><li>Experience with Docker</li></ul>",
        }
    ],
    "applyUrl": "https://jobs.lever.co/testco/lv-abc-123/apply",
    "hostedUrl": "https://jobs.lever.co/testco/lv-abc-123",
}


# ── Greenhouse tests ───────────────────────────────────────────────────────────

class TestGreenhouseSource:
    def test_source_name(self):
        assert GreenhouseSource().source_name == "Greenhouse"

    @patch("job_sources.greenhouse.requests.get")
    def test_fetch_jobs_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"jobs": [SAMPLE_GH_JOB]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        source = GreenhouseSource()
        source.DEFAULT_BOARD_TOKENS = ["testco"]  # limit to 1 company

        raw_jobs = source.fetch_jobs(titles=["Software Engineer"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]

        assert len(jobs) == 1
        assert jobs[0].title == "Senior Software Engineer"
        assert jobs[0].source == "greenhouse"
        assert jobs[0].id == "gh_99001"

    @patch("job_sources.greenhouse.requests.get")
    def test_filters_by_title(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"jobs": [SAMPLE_GH_JOB]}
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        source = GreenhouseSource()
        source.DEFAULT_BOARD_TOKENS = ["testco"]

        raw_jobs = source.fetch_jobs(titles=["Data Scientist"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]
        assert len(jobs) == 0  # "Data Scientist" not in title

    @patch("job_sources.greenhouse.requests.get")
    def test_handles_api_error_gracefully(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        source = GreenhouseSource()
        source.DEFAULT_BOARD_TOKENS = ["bad-company"]

        raw_jobs = source.fetch_jobs(titles=["Engineer"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]
        assert jobs == []  # should not raise, just return empty

    def test_strip_html(self):
        source = GreenhouseSource()
        result = source._strip_html("<p>Hello <b>World</b> &amp; more</p>")
        assert "<" not in result
        assert "Hello" in result
        assert "World" in result
        assert "&amp;" not in result


# ── Lever tests ────────────────────────────────────────────────────────────────

class TestLeverSource:
    def test_source_name(self):
        assert LeverSource().source_name == "Lever"

    @patch("job_sources.lever.requests.get")
    def test_fetch_jobs_returns_list(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [SAMPLE_LEVER_JOB]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        source = LeverSource()
        source.DEFAULT_COMPANY_SLUGS = ["testco"]

        raw_jobs = source.fetch_jobs(titles=["Backend Engineer"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]

        assert len(jobs) == 1
        assert jobs[0].title == "Backend Engineer"
        assert jobs[0].source == "lever"
        assert jobs[0].id == "lv_lv-abc-123"
        assert jobs[0].is_remote is True

    @patch("job_sources.lever.requests.get")
    def test_extracts_requirements_from_html(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [SAMPLE_LEVER_JOB]
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp

        source = LeverSource()
        source.DEFAULT_COMPANY_SLUGS = ["testco"]

        raw_jobs = source.fetch_jobs(titles=["Backend Engineer"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]

        assert len(jobs[0].requirements) > 0
        assert any("Python" in r for r in jobs[0].requirements)

    @patch("job_sources.lever.requests.get")
    def test_handles_api_error_gracefully(self, mock_get):
        mock_get.side_effect = Exception("Timeout")
        source = LeverSource()
        source.DEFAULT_COMPANY_SLUGS = ["bad-slug"]

        raw_jobs = source.fetch_jobs(titles=["Engineer"], limit=10)
        jobs = [JobPosting.model_validate(j) for j in raw_jobs]
        assert jobs == []


class TestJobPostingValidation:
    def test_rejects_invalid_application_url(self):
        with pytest.raises(ValueError, match="absolute HTTP"):
            JobPosting(
                source="sample",
                source_job_id="1",
                title="Backend Engineer",
                company="Example",
                description="A complete job description",
                application_url="javascript:alert(1)",
            )

    def test_rejects_blank_required_text(self):
        with pytest.raises(ValueError, match="must not be blank"):
            JobPosting(
                source="sample",
                source_job_id="1",
                title=" ",
                company="Example",
                description="A complete job description",
                application_url="https://example.com/jobs/1",
            )
