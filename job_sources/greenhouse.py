"""
job_sources/greenhouse.py
──────────────────────────
Fetches job postings from the Greenhouse Job Board API.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from job_sources.base import JobSource
from models.job import JobPosting

logger = logging.getLogger(__name__)

GREENHOUSE_BOARD_API = "https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs"
REQUEST_TIMEOUT = 10  # seconds


class GreenhouseJobSource(JobSource):
    """
    Adapter for the Greenhouse public Job Board API.
    """

    DEFAULT_BOARD_TOKENS: List[str] = [
        "airbnb",
        "figma",
        "notion",
        "vercel",
        "stripe",
        "linear",
        "anthropic",
        "openai",
        "databricks",
        "hashicorp",
    ]

    @property
    def source_name(self) -> str:
        return "Greenhouse"

    def fetch_jobs(
        self,
        titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        Fetch published jobs from Greenhouse board tokens.
        """
        title_keywords = [t.lower() for t in titles] if titles else []
        location_kw = location.lower().strip() if location else None

        collected: List[dict] = []

        for board_token in self.DEFAULT_BOARD_TOKENS:
            if len(collected) >= limit:
                break
            try:
                postings = self._fetch_board(board_token)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Greenhouse board '%s' failed: %s", board_token, exc)
                continue

            for raw in postings:
                if len(collected) >= limit:
                    break
                if title_keywords and not self._matches_title(raw.get("title", ""), title_keywords):
                    continue

                location_name = raw.get("location", {}).get("name", "")
                if location_kw and not self._matches_location(location_name, location_kw):
                    # Allow "Remote" jobs regardless of location filter
                    if "remote" not in location_name.lower():
                        continue

                posting = self._normalize(raw, board_token)
                if posting:
                    collected.append(posting)

        logger.info("Greenhouse: collected %d jobs", len(collected))
        return collected

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch_board(self, board_token: str) -> List[Dict[str, Any]]:
        """Call the Greenhouse API for a single company board."""
        url = GREENHOUSE_BOARD_API.format(board_token=board_token)
        logger.debug("Fetching Greenhouse board: %s", url)
        resp = requests.get(url, params={"content": "true"}, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("jobs", [])

    def _normalize(self, raw: Dict[str, Any], company: str) -> Optional[dict]:
        """Map a raw Greenhouse API job object to a normalized dict."""
        try:
            job_id = str(raw["id"])

            # Map departments
            departments = []
            raw_depts = raw.get("departments")
            if isinstance(raw_depts, list):
                for d in raw_depts:
                    if isinstance(d, dict) and d.get("name"):
                        departments.append(d["name"])
            elif isinstance(raw_depts, dict) and raw_depts.get("name"):
                departments.append(raw_depts["name"])

            # Map workplace type / remote
            location_name = raw.get("location", {}).get("name")
            workplace_type = "remote" if location_name and "remote" in location_name.lower() else "onsite"

            # Parse posted_at
            posted_at = None
            raw_updated = raw.get("updated_at")
            if raw_updated:
                try:
                    posted_at = datetime.fromisoformat(raw_updated.replace("Z", "+00:00"))
                except ValueError:
                    pass

            return {
                "source": "greenhouse",
                "source_job_id": job_id,
                "title": raw.get("title", "Unknown Title"),
                "company": raw.get("company", {}).get("name") or company.title(),
                "location": location_name or None,
                "workplace_type": workplace_type,
                "description": self._strip_html(raw.get("content", "")),
                "application_url": raw.get("absolute_url", ""),
                "posted_at": posted_at,
                "departments": departments,
            }
        except (KeyError, TypeError) as exc:
            logger.debug("Could not normalize Greenhouse job: %s — %s", raw.get("id"), exc)
            return None

    @staticmethod
    def _strip_html(html_text: str) -> str:
        """Remove HTML tags and decode entities."""
        clean = re.sub(r"<[^>]+>", " ", html_text)
        clean = html.unescape(clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _matches_title(job_title: str, keywords: List[str]) -> bool:
        title_lower = job_title.lower()
        return any(kw in title_lower for kw in keywords)

    @staticmethod
    def _matches_location(job_location: str, location_kw: str) -> bool:
        return location_kw in job_location.lower()


# Export GreenhouseSource alias for backwards compatibility
GreenhouseSource = GreenhouseJobSource
