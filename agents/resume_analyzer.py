"""
agents/resume_analyzer.py
──────────────────────────
Phase 4 — Resume Analyzer Agent.

Extracts a structured CandidateProfile from raw resume text.

Supports:
  - Local LLM via Ollama (Llama 3 / Qwen) — Default, 100% offline & local
  - Google Gemini via google.genai
  - OpenAI via openai
"""

from __future__ import annotations

import json
import logging
import re
from typing import Optional

import config
from models.candidate import CandidateProfile

logger = logging.getLogger(__name__)

_PROMPT_PATH = config.PROMPTS_DIR / "resume_analysis.txt"

SYSTEM_PROMPT = """
You are an expert resume parser and career analyst. Your goal is to extract all career-relevant information from the resume text and return it as a structured JSON object matching the CandidateProfile schema.

CRITICAL RULES — follow these without exception:
1. Only extract facts that are explicitly present in the resume text. Do not invent any experience, technology, or company.
2. Use null for missing strings/numbers and [] for missing lists.
3. Extract up to 15 key technical skills, technologies, platforms, frameworks, libraries, databases, or cloud services explicitly mentioned in the resume. Do not summarize or combine multiple skills.
4. For target_roles, infer only 2-3 roles the candidate's actual experience supports.
5. For work_experience, extract title, company, duration, and limit responsibilities to the top 2-3 most important bullet points (strictly 1 sentence per bullet point).
6. For projects, list up to 3 projects with a 1-sentence description and technologies used.
7. For skill_evidence, provide direct resume quotes demonstrating strictly the top 5 technical skills only (exactly 1 quote per skill).
8. ALWAYS return valid JSON matching the CandidateProfile schema. Be extremely concise to fit token limits.
""".strip()


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    logger.warning("Prompt file not found: %s — using inline fallback.", _PROMPT_PATH)
    return (
        "Extract all career-relevant information from the resume text below "
        "and return it as a structured JSON object matching the required schema.\n\n"
        "RESUME TEXT:\n{resume_text}"
    )


def _clean_json_response(raw: str) -> str:
    """Strip markdown formatting or stray backticks from model output."""
    if not raw:
        return ""
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


class ResumeAnalyzerAgent:
    """
    Converts raw resume text into a validated CandidateProfile.
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

    def _analyze_ollama(self, prompt: str) -> str:
        from openai import OpenAI

        client = OpenAI(base_url=config.OLLAMA_BASE_URL, api_key="ollama")
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=3072,
        )
        return response.choices[0].message.content or ""

    def _analyze_gemini(self, prompt: str) -> str:
        from google import genai
        from google.genai import types

        api_key = config.get_gemini_api_key()
        client = genai.Client(api_key=api_key)
        config_obj = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CandidateProfile,
            temperature=0.1,
            system_instruction=SYSTEM_PROMPT,
        )
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=config_obj,
        )
        return response.text or ""

    def _analyze_azure(self, prompt: str) -> str:
        client = config.get_azure_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=3072,
        )
        return response.choices[0].message.content or ""

    def _analyze_openai(self, prompt: str) -> str:
        client = config.get_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=3072,
        )
        return response.choices[0].message.content or ""

    def _analyze_groq(self, prompt: str) -> str:
        client = config.get_groq_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=3072,
        )
        return response.choices[0].message.content or ""

    def analyze(self, raw_text: str) -> CandidateProfile:
        """
        Extract a CandidateProfile from raw resume text.
        """
        logger.info(
            "Analyzing resume with provider=%s model=%s (%d chars)",
            self.provider,
            self.model_name,
            len(raw_text),
        )

        prompt = self._prompt_template.replace("{resume_text}", raw_text)

        if self.provider == "gemini":
            raw_output = self._analyze_gemini(prompt)
        else:
            # Clean, type-hinted template layout is much easier for non-Gemini models to generate correctly than full nested schemas
            template = {
                "current_title": "Most recent job title (string or null)",
                "target_roles": ["Suited job titles (list of strings)"],
                "total_years_experience": "Estimated total professional experience in years (number or null)",
                "technical_skills": ["Programming languages, databases, tools (list of strings)"],
                "soft_skills": ["Leadership, communication skills (list of strings)"],
                "work_experience": [
                    {
                        "title": "Role title (string or null)",
                        "company": "Employer name (string or null)",
                        "responsibilities": ["bullet list of achievements (list of strings)"],
                        "technologies": ["technologies explicitly named in this role (list of strings)"],
                        "years": "duration in years (number or null)"
                    }
                ],
                "projects": [
                    {
                        "name": "Project name (string or null)",
                        "description": "Short description of project (string or null)",
                        "technologies": ["technologies used (list of strings)"]
                    }
                ],
                "education": ["Education history (list of strings)"],
                "certifications": ["Certifications held (list of strings)"],
                "industries": ["Industries worked in, e.g. SaaS (list of strings)"],
                "skill_evidence": [
                    {
                        "skill": "Name of skill (string)",
                        "evidence": ["Direct verbatim quotes from resume demonstrating this skill (list of strings)"]
                    }
                ],
                "preferred_locations": ["Target locations (list of strings)"],
                "work_preference": "'Remote', 'Hybrid', or 'Onsite' (string or null)"
            }
            template_json = json.dumps(template, indent=2)
            prompt_with_schema = (
                f"{prompt}\n\n"
                f"You MUST return a single, valid JSON object matching the following structure.\n"
                f"Do not include any conversation, preamble, explanations, or markdown code block wrapper backticks (e.g. do NOT use ```json).\n"
                f"Start your response directly with the character '{{' and end with '}}'.\n\n"
                f"REQUIRED JSON FORMAT TEMPLATE:\n{template_json}\n\n"
                f"JSON Output:"
            )
            if self.provider == "azure":
                raw_output = self._analyze_azure(prompt_with_schema)
            elif self.provider == "groq":
                raw_output = self._analyze_groq(prompt_with_schema)
            elif self.provider == "openai":
                raw_output = self._analyze_openai(prompt_with_schema)
            elif self.provider == "ollama":
                raw_output = self._analyze_ollama(prompt_with_schema)
            else:  # guarded in __init__; keeps dispatch exhaustive
                raise ValueError(f"Unsupported LLM provider: {self.provider}")

        raw_output = _clean_json_response(raw_output)
        logger.debug("Raw LLM response: %s", raw_output[:300])

        try:
            profile = CandidateProfile.model_validate_json(raw_output)
        except Exception as exc:
            try:
                data = json.loads(raw_output)
                profile = CandidateProfile.model_validate(data)
            except Exception as inner_exc:
                logger.error(
                    "Failed to parse LLM response: %s\nRaw output:\n%s",
                    inner_exc,
                    raw_output,
                )
                raise ValueError(
                    f"Could not parse CandidateProfile: {inner_exc}\n"
                    f"Snippet: {raw_output[:200]}"
                ) from exc

        logger.info(
            "Profile extracted: title=%r, skills=%d, experience=%d roles",
            profile.current_title,
            len(profile.technical_skills),
            len(profile.work_experience),
        )
        return profile
