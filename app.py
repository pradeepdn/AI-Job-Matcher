"""
app.py
──────
Main Streamlit entry point for the AI Resume-to-Job Matching Agent.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

import hashlib
import html

import streamlit as st

import config

# ── Page configuration (must be first Streamlit call) ─────────────────────────
st.set_page_config(
    page_title="AI Job Matcher",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "AI Resume-to-Job Matching Agent — resume analysis, live job retrieval, and semantic ranking",
    },
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Google Font ───────────────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    :root {
        color-scheme: dark;
    }

    /* ── Background ────────────────────────────────────────────────────────── */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #f8fafc;
        min-height: 100vh;
    }

    /* ── Global high-contrast typography ───────────────────────────────────── */
    .stApp h1,
    .stApp h2,
    .stApp h3,
    .stApp h4,
    .stApp h5,
    .stApp h6,
    .stApp p,
    .stApp li,
    .stApp label,
    .stApp [data-testid="stMarkdownContainer"],
    .stApp [data-testid="stMarkdownContainer"] p,
    .stApp [data-testid="stWidgetLabel"] p,
    .stApp [data-testid="stMetricLabel"],
    .stApp [data-testid="stMetricValue"] {
        color: #f8fafc;
    }

    .stApp [data-testid="stCaptionContainer"],
    .stApp [data-testid="stCaptionContainer"] p,
    .stApp small {
        color: #cbd5e1 !important;
    }

    /* Inputs need their own dark surface and visible placeholder text. */
    .stApp input,
    .stApp textarea,
    .stApp [data-baseweb="select"] > div {
        background-color: rgba(15, 12, 41, 0.92) !important;
        color: #f8fafc !important;
        border-color: rgba(255, 255, 255, 0.28) !important;
    }

    .stApp input::placeholder,
    .stApp textarea::placeholder {
        color: #aebbd0 !important;
        opacity: 1;
    }

    /* Keep secondary buttons readable against translucent surfaces. */
    .stApp button:not([kind="primary"]),
    .stApp [data-testid="stLinkButton"] a {
        color: #f8fafc !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    .stApp [data-testid="stExpander"] details,
    .stApp [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* ── Sidebar ────────────────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: rgba(10, 8, 35, 0.92);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(12px);
    }

    /* ── Hero card ──────────────────────────────────────────────────────────── */
    .hero-card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 24px;
        padding: 3rem 3.5rem;
        backdrop-filter: blur(16px);
        margin-bottom: 2rem;
    }

    .hero-title {
        font-size: 3.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0 0 0.5rem 0;
        line-height: 1.15;
    }

    .hero-subtitle {
        font-size: 1.15rem;
        color: rgba(255, 255, 255, 0.86);
        font-weight: 400;
        margin: 0 0 2rem 0;
    }

    /* ── Step cards ─────────────────────────────────────────────────────────── */
    .step-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.2rem;
        margin-top: 1.5rem;
    }

    .step-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.4rem 1.2rem;
        text-align: center;
        transition: all 0.25s ease;
        cursor: default;
    }

    .step-card:hover {
        background: rgba(167, 139, 250, 0.12);
        border-color: rgba(167, 139, 250, 0.4);
        transform: translateY(-4px);
        box-shadow: 0 12px 32px rgba(167, 139, 250, 0.15);
    }

    .step-icon {
        font-size: 2rem;
        margin-bottom: 0.6rem;
    }

    .step-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        margin-bottom: 0.3rem;
    }

    .step-desc {
        font-size: 0.75rem;
        color: rgba(255, 255, 255, 0.74);
    }

    /* ── Status badge ───────────────────────────────────────────────────────── */
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .badge-ready {
        background: rgba(52, 211, 153, 0.15);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.35);
    }

    .badge-soon {
        background: rgba(251, 191, 36, 0.12);
        color: #fbbf24;
        border: 1px solid rgba(251, 191, 36, 0.3);
    }

    /* ── Info section ───────────────────────────────────────────────────────── */
    .info-card {
        background: rgba(96, 165, 250, 0.07);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 16px;
        padding: 1.5rem 2rem;
        margin-top: 1.5rem;
    }

    /* ── Tech pill ──────────────────────────────────────────────────────────── */
    .tech-pill {
        display: inline-block;
        background: rgba(167, 139, 250, 0.12);
        border: 1px solid rgba(167, 139, 250, 0.25);
        border-radius: 8px;
        padding: 0.3rem 0.75rem;
        font-size: 0.78rem;
        color: #c4b5fd;
        margin: 0.2rem;
        font-weight: 500;
    }

    /* ── Divider ────────────────────────────────────────────────────────────── */
    hr {
        border: none;
        border-top: 1px solid rgba(255, 255, 255, 0.08);
        margin: 2rem 0;
    }

    /* ── Sidebar nav ────────────────────────────────────────────────────────── */
    .nav-label {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.72);
        padding: 0.5rem 0 0.25rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 AI Job Matcher")
    st.markdown(
        '<div class="badge badge-ready">Matching Workflow — Ready</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    st.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
    page = st.radio(
        label="Navigate",
        options=["🏠 Home", "📄 Upload Resume", "🔍 Search Jobs", "📊 My Matches"],
        label_visibility="collapsed",
        key="main_navigation",
    )

    st.markdown("---")

    st.markdown('<div class="nav-label">Status</div>', unsafe_allow_html=True)

    st.success("✅ Config loaded")
    st.info("📦 Phases 1–5 foundation complete\n\nUpload a resume to begin.")

    st.markdown("---")
    if config.LLM_PROVIDER == "ollama":
        model_display = config.OLLAMA_MODEL
    elif config.LLM_PROVIDER == "azure":
        model_display = config.AZURE_AI_MODEL
    elif config.LLM_PROVIDER == "groq":
        model_display = config.GROQ_MODEL
    elif config.LLM_PROVIDER == "openai":
        model_display = config.OPENAI_MODEL
    elif config.LLM_PROVIDER == "gemini":
        model_display = config.GEMINI_MODEL
    else:
        model_display = "invalid provider"
    safe_provider = html.escape(config.LLM_PROVIDER.upper())
    safe_model = html.escape(model_display)
    st.markdown(
        f'<div style="font-size:0.72rem;color:rgba(255,255,255,0.72);">'
        f"Built with Streamlit + {safe_provider} ({safe_model})</div>",
        unsafe_allow_html=True,
    )


# ── Page renderers are defined below; routing happens at the bottom of this file.


# ── Page renderers ───────────────────────────────────────────────────────────────
def _render_home():
    # Hero
    st.markdown(
        """
        <div class="hero-card">
            <p class="hero-title">AI Resume Matcher</p>
            <p class="hero-subtitle">
                Upload your resume, set your job preferences, and let AI find<br>
                your best-matching roles from Greenhouse & Lever — in seconds.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Workflow steps
    st.markdown("### How it works")
    st.markdown(
        """
        <div class="step-grid">
            <div class="step-card">
                <div class="step-icon">📄</div>
                <div class="step-title">1. Upload Resume</div>
                <div class="step-desc">PDF or DOCX — we extract everything</div>
            </div>
            <div class="step-card">
                <div class="step-icon">🧠</div>
                <div class="step-title">2. AI Analysis</div>
                <div class="step-desc">Your configured LLM builds a candidate profile</div>
            </div>
            <div class="step-card">
                <div class="step-icon">🔍</div>
                <div class="step-title">3. Job Search</div>
                <div class="step-desc">Fetches 50–100 live job postings</div>
            </div>
            <div class="step-card">
                <div class="step-icon">⚡</div>
                <div class="step-title">4. Semantic Match</div>
                <div class="step-desc">Embedding-based similarity scoring</div>
            </div>
            <div class="step-card">
                <div class="step-icon">🏆</div>
                <div class="step-title">5. Top 10 Jobs</div>
                <div class="step-desc">Ranked results with skill gap analysis</div>
            </div>
            <div class="step-card">
                <div class="step-icon">🚀</div>
                <div class="step-title">6. Apply</div>
                <div class="step-desc">Direct link to the original job posting</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Tech stack
    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown("### Tech Stack")
        techs = [
            "Streamlit", "OpenAI GPT-4o-mini", "PyMuPDF", "python-docx",
            "sentence-transformers", "scikit-learn", "Pydantic v2",
            "SQLite", "Greenhouse API", "Lever API",
        ]
        pills_html = "".join(f'<span class="tech-pill">{t}</span>' for t in techs)
        st.markdown(pills_html, unsafe_allow_html=True)

    with col2:
        st.markdown("### Phase Roadmap")
        phases = [
            ("✅", "Phase 1", "Project scaffold & home page", "ready"),
            ("✅", "Phase 2", "PDF/DOCX resume parsing", "ready"),
            ("✅", "Phase 3", "Validated candidate profile", "ready"),
            ("✅", "Phase 4", "AI analysis & human review", "ready"),
            ("✅", "Phase 5", "Greenhouse + Lever sources", "ready"),
            ("✅", "Matching", "Semantic ranking & explanations", "ready"),
        ]
        for icon, name, desc, status in phases:
            badge_cls = "badge-ready" if status == "ready" else "badge-soon"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:0.6rem;'
                f'margin-bottom:0.5rem;">'
                f'<span style="font-size:1.1rem">{icon}</span>'
                f'<span style="font-weight:600;color:rgba(255,255,255,0.85);'
                f'font-size:0.85rem">{name}</span>'
                f'<span style="font-size:0.75rem;color:rgba(255,255,255,0.45)">'
                f'— {desc}</span></div>',
                unsafe_allow_html=True,
            )

    st.markdown("<hr>", unsafe_allow_html=True)

    # CTA
    st.markdown(
        """
        <div class="info-card">
            <strong style="color:#60a5fa;">👋 Getting Started</strong>
            <ol style="color:rgba(255,255,255,0.75);margin-top:0.75rem;font-size:0.9rem;">
                <li>Copy <code>.env.example</code> → <code>.env</code> and configure your preferred LLM provider</li>
                <li>Click <strong>Upload Resume</strong> in the sidebar to begin</li>
                <li>Enter your preferred job titles and target location</li>
                <li>Hit <strong>Find Matches</strong> and review your top results</li>
            </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_upload():
    from services.resume_parser import parse_upload

    st.markdown("## 📄 Upload Your Resume")
    st.markdown(
        '<div class="badge badge-ready">Phase 2 — Live</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # ── File uploader ──────────────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "Upload your resume",
        type=["pdf", "docx"],
        help="Supports text-based PDF and DOCX files. Scanned / image PDFs are not yet supported.",
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        filename = uploaded_file.name
        fingerprint = hashlib.sha256(file_bytes).hexdigest()

        # Candidate profiles and matches must never leak across different resumes.
        if st.session_state.get("resume_fingerprint") != fingerprint:
            for key in (
                "candidate_profile",
                "profile_reviewed",
                "jobs",
                "matches",
                "job_search_summary",
                "edit_target_roles",
                "new_role_input",
                "edit_technical_skills",
                "new_skills_input",
                "edit_locations",
                "edit_work_pref",
            ):
                st.session_state.pop(key, None)
            st.session_state["resume_fingerprint"] = fingerprint

        with st.spinner(f"Extracting text from **{filename}**…"):
            result = parse_upload(file_bytes, filename)

        if not result.success:
            # ── Error cases ────────────────────────────────────────────────────
            if result.is_scanned:
                st.error(result.user_facing_error, icon="📷")
                st.info(
                    "**Tip:** If you have the original Word document, upload that instead. "
                    "Otherwise, try re-saving the PDF as 'PDF with text' from your word processor.",
                    icon="💡",
                )
            elif result.is_encrypted:
                st.error(result.user_facing_error, icon="🔒")
                st.info(
                    "**Tip:** In Adobe Acrobat: File → Properties → Security → set to No Security. "
                    "In Preview (macOS): File → Export as PDF.",
                    icon="💡",
                )
            elif result.is_too_short:
                st.warning(result.user_facing_error, icon="⚠️")
            else:
                st.error(result.user_facing_error, icon="❌")
            return

        # ── Success ────────────────────────────────────────────────────────────
        st.success(f"✅ Successfully extracted **{result.char_count:,}** characters", icon="✅")

        # Save to session state so other pages can access it
        st.session_state["resume_text"] = result.text
        st.session_state["resume_filename"] = filename

        # ── Stats row ─────────────────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Characters", f"{result.char_count:,}")
        with col2:
            word_count = len(result.text.split())
            st.metric("Words", f"{word_count:,}")
        with col3:
            if result.page_count:
                st.metric("Pages", result.page_count)
            else:
                st.metric("Format", "DOCX")

        st.markdown("---")

        # ── Extracted text preview ─────────────────────────────────────────────
        st.markdown("### 📋 Extracted Text Preview")
        st.markdown(
            '<p style="color:rgba(255,255,255,0.45);font-size:0.8rem;margin-bottom:0.5rem;">'
            "This is the clean text that will be passed to the AI analyzer.</p>",
            unsafe_allow_html=True,
        )

        # Show first ~3000 chars in a scrollable box; toggle full text
        preview_chars = 3000
        short_preview = result.text[:preview_chars]
        show_full = st.checkbox(
            f"Show full text ({result.char_count:,} chars)",
            value=False,
            key="show_full_text",
        )
        display_text = result.text if show_full else (
            short_preview + (f"\n\n… (+{result.char_count - preview_chars:,} more chars)" if result.char_count > preview_chars else "")
        )

        safe_display_text = html.escape(display_text)
        st.markdown(
            f"""
            <div style="
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.10);
                border-radius: 12px;
                padding: 1.25rem 1.5rem;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 0.78rem;
                color: rgba(255,255,255,0.80);
                white-space: pre-wrap;
                overflow-x: auto;
                max-height: 480px;
                overflow-y: auto;
                line-height: 1.65;
            ">{safe_display_text}</div>
            """,
            unsafe_allow_html=True,
        )

        # ── Step 2: AI analysis ────────────────────────────────────────────────
        _render_analyze_section()

        # ── Step 3: Review (shown only after analysis) ────────────────────────
        if "candidate_profile" in st.session_state:
            _render_review_section()


    else:
        # ── Empty state ────────────────────────────────────────────────────────
        st.markdown(
            """
            <div style="
                border: 2px dashed rgba(167,139,250,0.35);
                border-radius: 20px;
                padding: 3rem 2rem;
                text-align: center;
                background: rgba(167,139,250,0.04);
                margin: 1rem 0;
            ">
                <div style="font-size:3rem;margin-bottom:1rem;">📄</div>
                <p style="font-size:1.1rem;font-weight:600;color:rgba(255,255,255,0.85);margin:0;">
                    Drop your resume above
                </p>
                <p style="font-size:0.85rem;color:rgba(255,255,255,0.4);margin-top:0.4rem;">
                    Supports text-based PDF and DOCX files
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### What happens after upload?")
        steps_html = """
        <div class="step-grid" style="grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));">
            <div class="step-card">
                <div class="step-icon">🔍</div>
                <div class="step-title">Text Extraction</div>
                <div class="step-desc">PyMuPDF or python-docx reads every page</div>
            </div>
            <div class="step-card">
                <div class="step-icon">🧹</div>
                <div class="step-title">Text Cleaning</div>
                <div class="step-desc">Removes noise, page numbers, bad chars</div>
            </div>
            <div class="step-card">
                <div class="step-icon">✅</div>
                <div class="step-title">Quality Check</div>
                <div class="step-desc">Detects scanned, encrypted, or empty files</div>
            </div>
            <div class="step-card">
                <div class="step-icon">👁️</div>
                <div class="step-title">Preview</div>
                <div class="step-desc">You review the extracted text before analysis</div>
            </div>
        </div>
        """
        st.markdown(steps_html, unsafe_allow_html=True)

        # Show previously uploaded resume if still in session state
        if "resume_filename" in st.session_state:
            st.markdown("---")
            st.markdown(
                f"📌 **Previously uploaded:** `{st.session_state['resume_filename']}` "
                f"— {len(st.session_state.get('resume_text', '')):,} chars in session.",
                unsafe_allow_html=False,
            )


# ── Phase 4: Analyze section ───────────────────────────────────────────────────

def _render_analyze_section():
    """Step 2 — trigger structured analysis of the extracted resume text."""
    from agents.resume_analyzer import ResumeAnalyzerAgent

    if config.LLM_PROVIDER == "ollama":
        provider_name = f"Local {config.OLLAMA_MODEL}"
    elif config.LLM_PROVIDER == "azure":
        provider_name = f"Azure AI ({config.AZURE_AI_MODEL})"
    elif config.LLM_PROVIDER == "groq":
        provider_name = f"Groq ({config.GROQ_MODEL})"
    elif config.LLM_PROVIDER == "openai":
        provider_name = f"OpenAI ({config.OPENAI_MODEL})"
    elif config.LLM_PROVIDER == "gemini":
        provider_name = f"Gemini ({config.GEMINI_MODEL})"
    else:
        provider_name = config.LLM_PROVIDER
    safe_provider_name = html.escape(provider_name)
    st.markdown("---")
    st.markdown(f"### 🧠 Step 2: Analyze with {provider_name}")
    st.markdown(
        f'<p style="color:rgba(255,255,255,0.45);font-size:0.85rem;">'
        f"Powered by <strong>{safe_provider_name}</strong> — extracts your skills, experience, and target roles "
        f"constrained to facts explicitly present in your resume."
        f"</p>",
        unsafe_allow_html=True,
    )

    # If already analyzed, show a re-analyze option
    already_analyzed = "candidate_profile" in st.session_state
    btn_label = f"🔄 Re-analyze Resume ({provider_name})" if already_analyzed else f"🧠 Analyze Resume with {provider_name}"

    col_btn, col_status = st.columns([2, 3])
    with col_btn:
        analyze_clicked = st.button(btn_label, key="btn_analyze", use_container_width=True)
    with col_status:
        if already_analyzed:
            st.success("✅ Profile extracted — scroll down to review", icon="✅")

    if analyze_clicked:
        raw_text = st.session_state.get("resume_text", "")
        if not raw_text:
            st.error("No resume text found. Please upload a file first.")
            return
        try:
            with st.spinner(f"Analyzing resume with {provider_name}…"):
                agent = ResumeAnalyzerAgent()
                profile = agent.analyze(raw_text)
                st.session_state["candidate_profile"] = profile
            st.success("✅ Profile extracted! Review and edit below.", icon="🎉")
            st.rerun()

        except EnvironmentError as exc:
            st.error(
                f"🔑 **Missing API key:** {exc}\n\n"
                f"Add the API key required by `{config.LLM_PROVIDER}` to the `.env` file.",
                icon="🔑",
            )
        except Exception as exc:  # pylint: disable=broad-except
            exc_str = str(exc)
            if "API_KEY_INVALID" in exc_str or "API key not valid" in exc_str or "AIza..." in exc_str:
                st.error(
                    "🔑 **Invalid Gemini API Key:** The API key in `.env` is a placeholder (`AIza...`).\n\n"
                    "Please get a free key at [Google AI Studio](https://aistudio.google.com/app/apikey), "
                    "add it to your `.env` file (`GEMINI_API_KEY=your_key`), and try again.",
                    icon="🔑",
                )
            else:
                st.error(f"❌ Analysis failed: {exc}", icon="❌")



# ── Phase 4: Review section ────────────────────────────────────────────────────

def _render_review_section():
    """Step 3 — Editable candidate profile review screen."""
    profile = st.session_state["candidate_profile"]

    st.markdown("---")
    st.markdown("### 👤 Step 3: Review Your Profile")
    st.markdown(
        '<p style="color:rgba(255,255,255,0.45);font-size:0.85rem;">'
        "Remove incorrect items, add missing ones, then set your job preferences below."
        "</p>",
        unsafe_allow_html=True,
    )

    # ── Profile header ─────────────────────────────────────────────────────────
    with st.container():
        c1, c2 = st.columns([3, 1])
        with c1:
            title_display = profile.current_title or "Unknown Title"
            st.subheader(title_display)
        with c2:
            yoe = profile.total_years_experience
            yoe_str = f"{yoe:.1f} yrs exp" if yoe else "Experience: ?"
            st.markdown(
                f'<p style="font-size:0.95rem;color:rgba(255,255,255,0.55);margin-top:0.4rem;">{yoe_str}</p>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    with st.form("profile_review_form", border=False):

        # ── Target roles ───────────────────────────────────────────────────────
        st.markdown("#### 🎯 Target Roles")
        st.caption("Roles inferred from your experience. Edit as needed.")
        detected_roles = profile.target_roles or []
        # Allow multiselect from detected + type new ones
        all_role_options = list(dict.fromkeys(detected_roles))  # dedupe, preserve order
        target_roles = st.multiselect(
            "Target Roles",
            options=all_role_options,
            default=all_role_options,
            key="edit_target_roles",
            label_visibility="collapsed",
        )
        new_role = st.text_input(
            "Add a role not listed above",
            placeholder="e.g. ML Engineer, Platform Engineer",
            key="new_role_input",
            label_visibility="collapsed",
        )

        st.markdown("#### 🛠️ Technical Skills")
        st.caption("Deselect skills to remove them. Add missing ones in the box below.")
        detected_skills = profile.technical_skills or []
        technical_skills = st.multiselect(
            "Technical Skills",
            options=list(dict.fromkeys(detected_skills)),
            default=list(dict.fromkeys(detected_skills)),
            key="edit_technical_skills",
            label_visibility="collapsed",
        )
        new_skills_raw = st.text_input(
            "Add skills (comma-separated)",
            placeholder="e.g. Kubernetes, LangChain, Terraform",
            key="new_skills_input",
            label_visibility="collapsed",
        )

        # ── Soft skills (read-only summary) ───────────────────────────────────
        if profile.soft_skills:
            st.markdown("#### 🤝 Soft Skills")
            st.caption(", ".join(profile.soft_skills))

        st.markdown("---")

        # ── Work experience preview ────────────────────────────────────────────
        if profile.work_experience:
            st.markdown("#### 💼 Extracted Work Experience")
            st.caption("Read-only — from your resume. Not editable in this version.")
            for exp in profile.work_experience:
                company_str = f" @ {exp.company}" if exp.company else ""
                years_str = f" · {exp.years:.1f} yrs" if exp.years else ""
                with st.expander(f"**{exp.title}**{company_str}{years_str}"):
                    if exp.responsibilities:
                        for resp in exp.responsibilities[:5]:
                            st.markdown(f"- {resp}")
                    if exp.technologies:
                        st.caption("Tech: " + ", ".join(exp.technologies))

        # ── Skill evidence ─────────────────────────────────────────────────────
        if profile.skill_evidence:
            with st.expander("🔍 Skill Evidence (AI citations from your resume)"):
                for ev in profile.skill_evidence[:8]:
                    st.markdown(f"**{ev.skill}**")
                    for quote in ev.evidence:
                        st.markdown(f"> {quote}")

        st.markdown("---")

        # ── Job search preferences ─────────────────────────────────────────────
        st.markdown("#### 📍 Job Search Preferences")
        pref_col1, pref_col2 = st.columns(2)
        with pref_col1:
            locations_input = st.text_input(
                "Preferred Locations",
                value=", ".join(profile.preferred_locations) if profile.preferred_locations else "",
                placeholder="e.g. San Francisco, CA · Remote · New York",
                key="edit_locations",
            )
        with pref_col2:
            work_pref_options = ["Remote", "Hybrid", "Onsite", "No preference"]
            current_pref = profile.work_preference or "No preference"
            if current_pref not in work_pref_options:
                current_pref = "No preference"
            work_preference = st.radio(
                "Work Arrangement",
                options=work_pref_options,
                index=work_pref_options.index(current_pref),
                horizontal=True,
                key="edit_work_pref",
            )

        # ── Save button ────────────────────────────────────────────────────────
        st.markdown("")
        submitted = st.form_submit_button(
            "✅ Save Profile",
            use_container_width=True,
            type="primary",
        )

    if submitted:
        # Merge manually added roles / skills
        final_roles = list(target_roles)
        if new_role.strip():
            for r in new_role.split(","):
                r = r.strip()
                if r and r not in final_roles:
                    final_roles.append(r)

        final_skills = list(technical_skills)
        if new_skills_raw.strip():
            for s in new_skills_raw.split(","):
                s = s.strip()
                if s and s not in final_skills:
                    final_skills.append(s)

        final_locations = [
            loc.strip() for loc in locations_input.split(",") if loc.strip()
        ] if locations_input.strip() else []

        final_pref = work_preference if work_preference != "No preference" else None

        updated_profile = profile.model_copy(
            update={
                "target_roles": final_roles,
                "technical_skills": final_skills,
                "preferred_locations": final_locations,
                "work_preference": final_pref,
            }
        )
        st.session_state["candidate_profile"] = updated_profile
        st.session_state["profile_reviewed"] = True
        st.success(
            f"✅ Profile saved — {len(final_skills)} skills, "
            f"{len(final_roles)} target roles, "
            f"location: {', '.join(final_locations) or 'any'}",
            icon="✅",
        )
        st.markdown(
            '<div class="info-card">'
            "<strong style='color:#60a5fa;'>⏭️ Ready for Job Search</strong>"
            "<p style='color:rgba(255,255,255,0.7);margin-top:0.5rem;font-size:0.9rem;'>"
            "Head to <strong>🔍 Search Jobs</strong> in the sidebar to fetch matching "
            "live job postings from Greenhouse and Lever."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_search():
    from services.job_search import JobSearchService

    st.markdown("## 🔍 Job Search Settings")
    st.markdown(
        '<div class="badge badge-ready">Phase 5 — Live</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    profile = st.session_state.get("candidate_profile")
    if profile is None:
        st.warning("Upload and analyze a resume before searching for jobs.")
        return
    if not st.session_state.get("profile_reviewed"):
        st.info("You can search now, but reviewing and saving the extracted profile first is recommended.")

    with st.form("job_search_form"):
        col1, col2 = st.columns(2)
        with col1:
            titles_input = st.text_input(
                "Preferred Job Titles (comma-separated)",
                value=", ".join(profile.target_roles),
                placeholder="e.g. Software Engineer, Backend Developer",
            )
        with col2:
            location_input = st.text_input(
                "Preferred Location",
                value=profile.preferred_locations[0] if profile.preferred_locations else "",
                placeholder="e.g. San Francisco, CA or Remote",
                help="The first preferred location is used for this search.",
            )

        source_col, limit_col = st.columns(2)
        with source_col:
            use_greenhouse = st.checkbox("Greenhouse", value=True)
            use_lever = st.checkbox("Lever", value=True)
        with limit_col:
            configured_limit = max(10, min(100, config.MAX_JOBS_TO_FETCH))
            limit = st.slider(
                "Maximum jobs",
                min_value=10,
                max_value=configured_limit,
                value=min(50, configured_limit),
                step=10,
            )

        submitted = st.form_submit_button(
            "🔍 Fetch Live Jobs",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        titles = [title.strip() for title in titles_input.split(",") if title.strip()]
        if not titles:
            st.error("Enter at least one preferred job title.")
        elif not use_greenhouse and not use_lever:
            st.error("Select at least one job source.")
        else:
            with st.spinner("Fetching and normalizing live job descriptions…"):
                service = JobSearchService(
                    use_greenhouse=use_greenhouse,
                    use_lever=use_lever,
                )
                jobs = service.search(
                    titles=titles,
                    location=location_input.strip() or None,
                    limit=limit,
                )

            # Enforce the reviewed work-arrangement preference after normalization.
            if profile.work_preference == "Remote":
                jobs = [job for job in jobs if job.is_remote]
            elif profile.work_preference == "Hybrid":
                jobs = [
                    job for job in jobs
                    if (job.workplace_type or "").lower() == "hybrid"
                ]
            elif profile.work_preference == "Onsite":
                jobs = [
                    job for job in jobs
                    if not job.is_remote
                    and (job.workplace_type or "").lower() != "hybrid"
                ]

            st.session_state["jobs"] = jobs
            st.session_state.pop("matches", None)
            st.session_state["job_search_summary"] = {
                "titles": titles,
                "location": location_input.strip(),
                "count": len(jobs),
            }

            if jobs:
                st.success(f"Found {len(jobs)} normalized job postings.")
            else:
                st.warning(
                    "No matching jobs were returned. Try broader titles, no location, "
                    "or a different work-arrangement preference."
                )

    jobs = st.session_state.get("jobs", [])
    if jobs:
        st.markdown("### Retrieved Jobs")
        for job in jobs[:10]:
            with st.container(border=True):
                details_col, apply_col = st.columns([5, 1])
                with details_col:
                    location = job.location or "Location not listed"
                    st.markdown(f"**{job.title}** — {job.company}")
                    st.caption(f"{location} · {job.source.title()}")
                with apply_col:
                    st.link_button(
                        "View & Apply ↗",
                        job.application_url,
                        use_container_width=True,
                        type="primary",
                    )
        if len(jobs) > 10:
            st.caption(f"Showing 10 of {len(jobs)} jobs. All will be included in matching.")
        st.info("Open **📊 My Matches** to rank these jobs against your profile.")


def _render_matches():
    st.markdown("## 📊 My Top Matches")
    st.markdown(
        '<div class="badge badge-ready">Semantic Matching — Live</div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    profile = st.session_state.get("candidate_profile")
    if profile is None:
        st.warning("Upload and analyze a resume before calculating matches.")
        return

    jobs = st.session_state.get("jobs", [])
    if not jobs:
        st.info("Fetch jobs from **🔍 Search Jobs** before calculating matches.")
        return

    with st.form("match_options_form"):
        explain_matches = st.checkbox(
            "Generate AI explanations",
            value=False,
            help="This makes one additional LLM request for each displayed match.",
        )
        calculate = st.form_submit_button(
            f"⚡ Rank {len(jobs)} Jobs",
            type="primary",
            use_container_width=True,
        )

    if calculate:
        from services.matcher import MatcherService

        try:
            with st.spinner("Loading the embedding model and ranking jobs…"):
                matches = MatcherService().match(
                    profile,
                    jobs,
                    top_n=config.TOP_MATCHES_TO_SHOW,
                )

            if explain_matches and matches:
                from agents.match_explainer import MatchExplainerAgent

                explainer = MatchExplainerAgent()
                enriched = []
                progress = st.progress(0, text="Generating match explanations…")
                for index, match in enumerate(matches, start=1):
                    try:
                        match = explainer.explain(profile, match.job, match)
                    except Exception as exc:  # keep ranking useful if one LLM call fails
                        match = match.model_copy(
                            update={"explanation": f"Explanation unavailable: {exc}"}
                        )
                    enriched.append(match)
                    progress.progress(
                        index / len(matches),
                        text=f"Generated {index} of {len(matches)} explanations",
                    )
                progress.empty()
                matches = enriched

            st.session_state["matches"] = matches
        except Exception as exc:  # pylint: disable=broad-except
            st.error(f"Could not calculate matches: {exc}")

    matches = st.session_state.get("matches", [])
    if not matches:
        return

    st.markdown(f"### Top {len(matches)} Matches")
    for match in matches:
        with st.container(border=True):
            title_col, score_col, apply_col = st.columns([4, 1, 1])
            with title_col:
                st.markdown(f"**#{match.rank} · {match.job.title}**")
                st.caption(
                    f"{match.job.company} · {match.job.location or 'Location not listed'} "
                    f"· {match.job.source.title()}"
                )
            with score_col:
                st.metric("Match", match.display_score_pct)
            with apply_col:
                if match.job.application_url:
                    st.link_button(
                        "View & Apply ↗",
                        match.job.application_url,
                        use_container_width=True,
                        type="primary",
                    )

            st.progress(max(0.0, min(1.0, match.display_score)))
            if match.matched_skills:
                st.success("Matched skills: " + ", ".join(match.matched_skills))
            if match.missing_skills:
                st.warning("Potential gaps: " + ", ".join(match.missing_skills))
            if match.recommendation:
                st.markdown(f"**{match.recommendation}**")
            if match.explanation:
                st.write(match.explanation)


# ── Route pages (after all renderer functions are defined) ─────────────────────
if page == "🏠 Home":
    _render_home()
elif page == "📄 Upload Resume":
    _render_upload()
elif page == "🔍 Search Jobs":
    _render_search()
elif page == "📊 My Matches":
    _render_matches()
