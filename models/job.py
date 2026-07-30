"""
models/job.py
─────────────
Pydantic model representing a job posting fetched from Greenhouse or Lever.
"""

from __future__ import annotations

from enum import Enum
from typing import Any
from datetime import datetime, timezone
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class JobSource(str, Enum):
    """Which job board API the posting came from."""

    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    SAMPLE = "sample"  # used for offline testing


class JobPosting(BaseModel):
    """
    A normalized job posting from any supported source (Greenhouse, Lever).
    """

    # ── Required fields by Phase 5 spec ────────────────────────────────────────
    source: str
    source_job_id: str
    title: str
    company: str
    location: str | None = None
    workplace_type: str | None = None
    description: str
    application_url: str
    posted_at: datetime | None = None
    departments: list[str] = Field(default_factory=list)

    # ── Backward compatibility / matching engine fields ────────────────────────
    id: str | None = None
    external_id: str | None = None
    is_remote: bool = False
    description_raw: str | None = None
    description_text: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)

    @field_validator("source", "source_job_id", "title", "company", "description")
    @classmethod
    def required_text_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("application_url")
    @classmethod
    def application_url_must_be_http(cls, value: str) -> str:
        parsed = urlparse(value.strip())
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("must be an absolute HTTP(S) URL")
        return value.strip()

    @model_validator(mode="before")
    @classmethod
    def populate_compat_fields(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Translate JobSource enum if passed as source
        if "source" in data and isinstance(data["source"], Enum):
            data["source"] = data["source"].value

        # source_job_id logic
        if "source_job_id" not in data:
            if "external_id" in data:
                data["source_job_id"] = str(data["external_id"])
            elif "id" in data and "_" in str(data["id"]):
                data["source_job_id"] = str(data["id"]).split("_", 1)[1]
            else:
                data["source_job_id"] = "unknown"

        # id logic
        if "id" not in data or data["id"] is None:
            prefix = "gh" if str(data.get("source", "")).lower() == "greenhouse" else "lv"
            data["id"] = f"{prefix}_{data.get('source_job_id', '')}"

        # external_id logic
        if "external_id" not in data or data["external_id"] is None:
            data["external_id"] = data.get("source_job_id")

        # description logic
        if "description" not in data:
            if "description_text" in data:
                data["description"] = data["description_text"]
            elif "description_raw" in data:
                data["description"] = data["description_raw"]
            else:
                data["description"] = ""

        # description_text logic
        if "description_text" not in data or data["description_text"] is None:
            data["description_text"] = data["description"]

        # description_raw logic
        if "description_raw" not in data or data["description_raw"] is None:
            data["description_raw"] = data["description"]

        # is_remote logic
        if "is_remote" not in data or not data["is_remote"]:
            workplace = str(data.get("workplace_type", "")).lower()
            loc = str(data.get("location", "")).lower()
            data["is_remote"] = (workplace == "remote" or "remote" in loc)

        return data

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "greenhouse",
                "source_job_id": "123456",
                "title": "Senior Backend Engineer",
                "company": "Acme Corp",
                "location": "San Francisco, CA",
                "workplace_type": "hybrid",
                "description": "We are looking for a Senior Backend Engineer...",
                "application_url": "https://boards.greenhouse.io/acmecorp/jobs/123456",
                "posted_at": "2026-07-28T22:00:00Z",
                "departments": ["Engineering"],
            }
        }
    )
