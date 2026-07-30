"""
services/job_search.py
───────────────────────
Orchestrates fetching job postings from all enabled sources (Greenhouse + Lever),
deduplicates results, and returns a unified list of JobPosting objects.
"""

from __future__ import annotations

import logging
from typing import List, Optional

import config
from models.job import JobPosting
from job_sources import GreenhouseJobSource, LeverJobSource

logger = logging.getLogger(__name__)


class JobSearchService:
    """
    High-level service that aggregates jobs from all configured sources.

    Sources can be toggled via constructor flags. Results are deduplicated
    by (company, title, location) to avoid showing the same role twice.
    """

    def __init__(
        self,
        use_greenhouse: bool = True,
        use_lever: bool = True,
    ) -> None:
        self.sources = []
        if use_greenhouse:
            self.sources.append(GreenhouseJobSource())
        if use_lever:
            self.sources.append(LeverJobSource())

        logger.info(
            "JobSearchService initialized with sources: %s",
            [type(s).__name__ for s in self.sources],
        )

    def search(
        self,
        titles: List[str],
        location: Optional[str] = None,
        limit: int | None = None,
    ) -> List[JobPosting]:
        """
        Fetch and aggregate job postings matching the given titles and location.
        """
        limit = limit or config.MAX_JOBS_TO_FETCH
        per_source = max(1, limit // max(1, len(self.sources)))

        all_jobs: List[JobPosting] = []
        for source in self.sources:
            try:
                raw_jobs = source.fetch_jobs(titles=titles, location=location, limit=per_source)
                logger.info("%s returned %d jobs", type(source).__name__, len(raw_jobs))
                for rj in raw_jobs:
                    try:
                        all_jobs.append(JobPosting.model_validate(rj))
                    except Exception as val_exc:
                        logger.warning("Could not validate job dictionary: %s", val_exc)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error("Error fetching from %s: %s", type(source).__name__, exc)

        deduplicated = self._deduplicate(all_jobs)
        logger.info(
            "Total after deduplication: %d / %d", len(deduplicated), len(all_jobs)
        )
        return deduplicated[:limit]

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _deduplicate(jobs: List[JobPosting]) -> List[JobPosting]:
        """Remove near-duplicate postings by (company_lower, title_lower)."""
        seen: set[tuple[str, str]] = set()
        unique: List[JobPosting] = []
        for job in jobs:
            key = (job.company.lower().strip(), job.title.lower().strip())
            if key not in seen:
                seen.add(key)
                unique.append(job)
        return unique
