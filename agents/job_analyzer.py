"""
agents/job_analyzer.py
───────────────────────
LLM agent that extracts structured requirements from a raw job description.

Input : raw job description text (str)
Output: dict with keys — requirements, nice_to_have, required_skills
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

import config

logger = logging.getLogger(__name__)

_PROMPT_PATH = config.PROMPTS_DIR / "job_analysis.txt"


def _load_prompt() -> str:
    if _PROMPT_PATH.exists():
        return _PROMPT_PATH.read_text(encoding="utf-8")
    logger.warning("Prompt file not found: %s — using inline fallback.", _PROMPT_PATH)
    return (
        "You are an expert at analyzing job descriptions. "
        "Extract the following from the job description below and return JSON:\n"
        "- requirements: list of must-have qualifications\n"
        "- nice_to_have: list of preferred but not required qualifications\n"
        "- required_skills: list of technical skills (languages, frameworks, tools)\n\n"
        "JOB DESCRIPTION:\n{job_description}"
    )


class JobAnalyzerAgent:
    """
    Uses Local Ollama or Gemini to extract structured requirements from a job description.
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
                {"role": "system", "content": "You are an expert at analyzing job descriptions. Respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def _analyze_gemini(self, prompt: str) -> str:
        from google import genai
        from google.genai import types

        api_key = config.get_gemini_api_key()
        client = genai.Client(api_key=api_key)
        config_obj = types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1,
            system_instruction="You are an expert at analyzing job descriptions. Respond with valid JSON.",
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
                {"role": "system", "content": "You are an expert at analyzing job descriptions. Respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def _analyze_openai(self, prompt: str) -> str:
        client = config.get_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions. Respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def _analyze_groq(self, prompt: str) -> str:
        client = config.get_groq_openai_client()
        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are an expert at analyzing job descriptions. Respond with valid JSON."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def analyze(self, job_description: str) -> Dict[str, Any]:
        """
        Extract requirements from a job description.
        """
        logger.info(
            "Analyzing job description with provider=%s model=%s (%d chars)",
            self.provider,
            self.model_name,
            len(job_description),
        )

        prompt = self._prompt_template.replace("{job_description}", job_description)

        if self.provider == "gemini":
            raw_json = self._analyze_gemini(prompt)
        elif self.provider == "azure":
            raw_json = self._analyze_azure(prompt)
        elif self.provider == "groq":
            raw_json = self._analyze_groq(prompt)
        elif self.provider == "openai":
            raw_json = self._analyze_openai(prompt)
        elif self.provider == "ollama":
            raw_json = self._analyze_ollama(prompt)
        else:  # guarded in __init__
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

        raw_json = raw_json.strip()

        try:
            result = json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

        result.setdefault("requirements", [])
        result.setdefault("nice_to_have", [])
        result.setdefault("required_skills", [])

        logger.info(
            "Extracted %d requirements, %d skills",
            len(result["requirements"]),
            len(result["required_skills"]),
        )
        return result
