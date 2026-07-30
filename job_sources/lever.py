"""
job_sources/lever.py
─────────────────────
Fetches job postings from the Lever public Postings API.
"""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from job_sources.base import JobSource

logger = logging.getLogger(__name__)

LEVER_POSTINGS_API = "https://api.lever.co/v0/postings/{company}"
REQUEST_TIMEOUT = 10  # seconds


class LeverJobSource(JobSource):
    """
    Adapter for the Lever public Postings API.
    """

    DEFAULT_COMPANY_SLUGS: List[str] = [
        "netflix",
        "shopify",
        "plaid",
        "scale-ai",
        "ramp",
        "deel",
        "rippling",
        "brex",
        "anduril",
        "lattice",
    ]

    @property
    def source_name(self) -> str:
        return "Lever"

    def fetch_jobs(
        self,
        titles: Optional[List[str]] = None,
        location: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """
        Fetch published postings from Lever company boards.
        """
        title_keywords = [t.lower() for t in titles] if titles else []
        location_kw = location.lower().strip() if location else None

        collected: List[dict] = []

        for company_slug in self.DEFAULT_COMPANY_SLUGS:
            if len(collected) >= limit:
                break
            try:
                postings = self._fetch_company(company_slug)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Lever company '%s' failed: %s", company_slug, exc)
                continue

            for raw in postings:
                if len(collected) >= limit:
                    break
                if title_keywords and not self._matches_title(raw.get("text", ""), title_keywords):
                    continue

                raw_location = (
                    raw.get("categories", {}).get("location", "")
                    or raw.get("workplaceType", "")
                )
                if location_kw and not self._matches_location(raw_location, location_kw):
                    if "remote" not in raw_location.lower():
                        continue

                posting = self._normalize(raw, company_slug)
                if posting:
                    collected.append(posting)

        logger.info("Lever: collected %d jobs", len(collected))
        return collected

    # ── Private helpers ────────────────────────────────────────────────────────

    def _fetch_company(self, company_slug: str) -> List[Dict[str, Any]]:
        """Call the Lever API for a single company."""
        url = LEVER_POSTINGS_API.format(company=company_slug)
        logger.debug("Fetching Lever postings: %s", url)
        resp = requests.get(
            url,
            params={"mode": "json", "limit": 100},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def _normalize(self, raw: Dict[str, Any], company_slug: str) -> Optional[dict]:
        """Map a raw Lever API posting to a normalized dict."""
        try:
            posting_id = raw.get("id", "")
            categories = raw.get("categories", {})
            location_name = (
                categories.get("location")
                or raw.get("workplaceType")
                or ""
            )
            description_plain = raw.get("descriptionPlain") or self._strip_html(
                raw.get("description", "")
            )

            # Map departments
            departments = []
            if categories.get("department"):
                departments.append(categories["department"])
            if categories.get("team"):
                departments.append(categories["team"])

            # Map workplace type
            workplace_type = str(raw.get("workplaceType", "")).lower() or None
            if not workplace_type and location_name and "remote" in location_name.lower():
                workplace_type = "remote"

            # Parse posted_at from Lever's createdAt timestamp
            posted_at = None
            raw_created = raw.get("createdAt")
            if raw_created:
                try:
                    posted_at = datetime.fromtimestamp(float(raw_created) / 1000.0, tz=timezone.utc)
                except (ValueError, TypeError):
                    pass

            # Extract requirements from lists
            lists = raw.get("lists", [])
            requirements: List[str] = []
            for lst in lists:
                if "require" in lst.get("text", "").lower():
                    items_html = lst.get("content", "")
                    requirements.extend(self._extract_list_items(items_html))

            apply_url = raw.get("applyUrl") or raw.get("hostedUrl") or ""

            return {
                "source": "lever",
                "source_job_id": posting_id,
                "title": raw.get("text", "Unknown Title"),
                "company": raw.get("company") or company_slug.replace("-", " ").title(),
                "location": location_name or None,
                "workplace_type": workplace_type,
                "description": description_plain,
                "application_url": apply_url,
                "posted_at": posted_at,
                "departments": departments,
                "requirements": requirements[:20],
            }
        except (KeyError, TypeError) as exc:
            logger.debug("Could not normalize Lever posting: %s — %s", raw.get("id"), exc)
            return None

    @staticmethod
    def _strip_html(html_text: str) -> str:
        clean = re.sub(r"<[^>]+>", " ", html_text)
        clean = html.unescape(clean)
        clean = re.sub(r"\s+", " ", clean)
        return clean.strip()

    @staticmethod
    def _extract_list_items(html_content: str) -> List[str]:
        """Extract <li> text items from an HTML list string."""
        items = re.findall(r"<li[^>]*>(.*?)</li>", html_content, re.DOTALL)
        return [re.sub(r"<[^>]+>", "", item).strip() for item in items if item.strip()]

    @staticmethod
    def _matches_title(job_title: str, keywords: List[str]) -> bool:
        title_lower = job_title.lower()
        return any(kw in title_lower for kw in keywords)

    @staticmethod
    def _matches_location(job_location: str, location_kw: str) -> bool:
        return location_kw in job_location.lower()


# Export LeverSource alias for backwards compatibility
LeverSource = LeverJobSource
