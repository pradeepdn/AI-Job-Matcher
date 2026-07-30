"""Streamlit smoke tests for routes that do not require external services."""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize(
    "page",
    ["🏠 Home", "📄 Upload Resume", "🔍 Search Jobs", "📊 My Matches"],
)
def test_primary_routes_render_without_exception(page):
    app = AppTest.from_file("app.py", default_timeout=20)
    app.run()
    app.sidebar.radio[0].set_value(page)
    app.run()

    assert not app.exception


def test_streamlit_theme_uses_high_contrast_dark_colors():
    theme_path = Path(".streamlit/config.toml")
    theme = tomllib.loads(theme_path.read_text(encoding="utf-8"))["theme"]

    assert theme["base"] == "dark"
    assert theme["backgroundColor"] == "#0f0c29"
    assert theme["textColor"] == "#f8fafc"
