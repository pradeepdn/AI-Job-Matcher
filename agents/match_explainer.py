"""
agents/match_explainer.py
──────────────────────────
LLM agent that generates a human-readable explanation for a job match.

Input : CandidateProfile + JobPosting + preliminary MatchResult scores
Output: Updated MatchResult with explanation and recommendation
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import config
from models.candidate import CandidateProfile
from models.job import JobPosting
from models.match import MatchResult

logger = logging.getLogger(__name__)

_PROMPT_PATH = config.PROMPTS_DIR / "match_explanation.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    logger.warning("Prompt file not found: %s — using inline fallback.", _PROMPT_PATH)
    return (
        "You are a career coach analyzing how well a candidate fits a job.\n\n"
        "CANDIDATE PROFILE:\n{candidate_summary}\n\n"
        "JOB POSTING:\n{job_summary}\n\n"
        "MATCH SCORES:\n"
        "- Semantic similarity: {semantic_score:.0%}\n"
        "- Matched skills: {matched_skills}\n"
        "- Missing skills: {missing_skills}\n\n"
        "Return JSON with:\n"
        "- explanation: 2-3 sentence human-readable match explanation\n"
        "- recommendation: one of 'Strong Match', 'Good Fit', 'Reach', 'Skip'"
    )


class MatchExplainerAgent:
    """
    Uses Local Ollama or Gemini to generate a human-readable explanation for a MatchResult.
    """

    def __init__(self, model: Optional[str] = None) -> None:
        self.provider = config.LLM_PROVIDER
        if self.provider == "ollama":
            self.model_name = model or config.OLLAMA_MODEL
        elif self.provider == "azure":
            self.model_name = model or config.AZURE_AI_MODEL
        elif self.provider == "groq":
            self.model_name = model or config.GROQ_MODEL
        elif self.provider == "gemini":
            self.model_name = model or config.GEMINI_MODEL
        elif self.provider == "openai":
            self.model_name = model or config.OPENAI_MODEL
        else:
            raise ValueError(
                f"Unsupported LLM_PROVIDER '{self.provider}'. "
                "Choose ollama, gemini, openai, azure, or groq."
            )
        self._prompt_template = _load_prompt()

    def _explain_ollama(self, prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a career coach. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    def _explain_gemini(self, prompt: str) -> str:
        from google import genai
        from google.genai import types

        api_key = config.get_gemini_api_key()
        client = genai.Client(api_key=api_key)
        config_obj = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.4,
            system_instruction="You are a career coach. Respond with valid JSON only.",
        )
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config_obj,
        )
        return response.text or ""

    def _explain_azure(self, prompt: str) -> str:
        client = config.get_azure_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a career coach. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    def _explain_openai(self, prompt: str) -> str:
        client = config.get_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a career coach. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    def _explain_groq(self, prompt: str) -> str:
        client = config.get_groq_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a career coach. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.4,
        )
        return response.choices[0].message.content or ""

    def explain(
        self,
        candidate: CandidateProfile,
        job: JobPosting,
        match: MatchResult,
    ) -> MatchResult:
        """
        Enrich a MatchResult with an explanation and recommendation.
        """
        logger.info(
            "Generating match explanation with provider=%s job='%s' at %s",
            self.provider,
            job.title,
            job.company,
        )

        candidate_summary = (
            f"Role: {candidate.current_title or 'Unknown'}\n"
            f"Skills: {', '.join(candidate.technical_skills[:15])}\n"
            f"Experience: ~{candidate.total_years_experience or '?'} years\n"
        )

        job_summary = (
            f"Title: {job.title}\n"
            f"Company: {job.company}\n"
            f"Location: {job.location or 'N/A'}\n"
            f"Required skills: {', '.join(job.required_skills[:15])}\n"
            f"Description snippet: {(job.description_text or '')[:500]}"
        )

        prompt = self._prompt_template.format(
            candidate_summary=candidate_summary,
            job_summary=job_summary,
            semantic_score=match.semantic_score,
            matched_skills=", ".join(match.matched_skills) or "none identified",
            missing_skills=", ".join(match.missing_skills) or "none identified",
        )

        if self.provider == "gemini":
            raw_json = self._explain_gemini(prompt)
        elif self.provider == "azure":
            raw_json = self._explain_azure(prompt)
        elif self.provider == "groq":
            raw_json = self._explain_groq(prompt)
        elif self.provider == "openai":
            raw_json = self._explain_openai(prompt)
        elif self.provider == "ollama":
            raw_json = self._explain_ollama(prompt)
        else:  # guarded in __init__
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        raw_json = raw_json.strip()

        try:
            data = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            logger.error("LLM returned invalid JSON for match explanation: %s", exc)
            return match

        return match.model_copy(
            update={
                "explanation": data.get("explanation"),
                "recommendation": data.get("recommendation"),
            }
        )
