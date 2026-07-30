"""Provider-selection tests for the LLM-backed agents."""

from __future__ import annotations

import pytest

import config
from agents.job_analyzer import JobAnalyzerAgent
from agents.match_explainer import MatchExplainerAgent
from agents.resume_analyzer import ResumeAnalyzerAgent


@pytest.mark.parametrize(
    "agent_class",
    [ResumeAnalyzerAgent, JobAnalyzerAgent, MatchExplainerAgent],
)
def test_openai_provider_selects_openai_model(monkeypatch, agent_class):
    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(config, "OPENAI_MODEL", "test-openai-model")

    agent = agent_class()

    assert agent.provider == "openai"
    assert agent.model_name == "test-openai-model"


@pytest.mark.parametrize(
    "agent_class",
    [ResumeAnalyzerAgent, JobAnalyzerAgent, MatchExplainerAgent],
)
def test_invalid_provider_fails_fast(monkeypatch, agent_class):
    monkeypatch.setattr(config, "LLM_PROVIDER", "not-a-provider")

    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        agent_class()


def test_resume_analyzer_dispatches_to_openai(monkeypatch):
    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    agent = ResumeAnalyzerAgent(model="test-model")
    monkeypatch.setattr(
        agent,
        "_analyze_openai",
        lambda _prompt: (
            '{"current_title":"Backend Engineer",'
            '"technical_skills":["Python"],'
            '"target_roles":["Backend Engineer"]}'
        ),
    )
    monkeypatch.setattr(
        agent,
        "_analyze_ollama",
        lambda _prompt: pytest.fail("OpenAI must not use the Ollama dispatch path"),
    )

    profile = agent.analyze("Backend Engineer with Python experience.")

    assert profile.current_title == "Backend Engineer"
    assert profile.technical_skills == ["Python"]
