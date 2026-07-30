"""
job_sources/base.py
────────────────────
Abstract base class for all job board source adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional


class JobSource(ABC):
    """
    Abstract interface for a job board data source.
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name for this source (e.g. 'Greenhouse')."""
        raise NotImplementedError

    @abstractmethod
    def fetch_jobs(
        self,
        titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        Fetch job postings and return a list of normalized job posting dictionaries.
        """
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} source='{self.source_name}'>"


# Keep BaseJobSource alias to prevent breaking any imports not refactored yet
BaseJobSource = JobSource
