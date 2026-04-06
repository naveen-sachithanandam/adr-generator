"""
Streamlit UI for the ADR generator.

Defines :func:`render_app`, which wires widgets, ``st.session_state``, and
calls into :mod:`adr_service` for example loading, file output, and LLM calls.
No environment loading here — that happens in :mod:`adr_service` on import.
"""

from __future__ import annotations

import streamlit as st

import adr_service as svc


def render_app() -> None:
    """Build the full multi-section Streamlit page (sidebar, inputs, actions, outputs)."""
    st.set_page_config(page_title="ADR Generator", page_icon="📋", layout="wide")

    st.title("ADR Generator")
    st.caption(
        "Draft MADR-style architecture decision records with Anthropic or a local model via Ollama."
    )

    if "adr_markdown" not in st.session_state:
        st.session_state.adr_markdown = ""
    if "decision_brief" not in st.session_state:
        st.session_state.decision_brief = ""
    if "analysis_markdown" not in st.session_state:
        st.session_state.analysis_markdown = ""
    if "review_markdown" not in st.session_state:
        st.session_state.review_markdown = ""
    if "adr_model" not in st.session_state:
        st.session_state.adr_model = svc.default_model_for_initial_session()

    anthropic_key = svc.anthropic_key_from_env()

    # ------------------------------------------------------------------ sidebar
    with st.sidebar:
        st.subheader("Setup")
        llm_choice = st.radio(
            "LLM backend",
            [
                "Auto (Ollama if no API key)",
                "Anthropic",
                "Ollama",
            ],
            help="Auto uses Anthropic when `ANTHROPIC_API_KEY` is set; otherwise Ollama.",
        )
        backend = svc.backend_for_ui_choice(llm_choice, anthropic_key)
        st.caption(f"Active backend for this run: **{backend}**")

        ollama_host = st.text_input(
            "Ollama host",
            value=svc.DEFAULT_OLLAMA_HOST,
            disabled=backend == "anthropic",
            help="Used when backend is Ollama. In Docker on Mac/Windows, try http://host.docker.internal:11434",
        )
        model = st.text_input(
            "Model",
            key="adr_model",
            help="Claude model ID when using Anthropic; Ollama tag (e.g. llama3.2) when using Ollama.",
        )
        use_streaming = st.checkbox("Stream response", value=False)

        if backend == "ollama":
            st.caption("Run `ollama serve`, then `ollama pull` your model.")
        elif llm_choice == "Anthropic" and not anthropic_key.strip():
            st.warning("Set `ANTHROPIC_API_KEY` in `.env` for Anthropic.")
        elif llm_choice.startswith("Auto") and not anthropic_key.strip():
            st.info("No `ANTHROPIC_API_KEY` — using **Ollama**.")

        example_choice = st.selectbox(
            "Sample brief to load",
            ["— Choose —", "Default (tooling)", "Healthcare", "AI integration"],
        )
        if st.button("Load sample into brief"):
            if example_choice == "— Choose —":
                st.warning("Select Healthcare, AI integration, or Default first.")
            else:
                loaded = svc.load_example_brief(example_choice)
                if loaded:
                    st.session_state.decision_brief = loaded
                else:
                    st.error("Example file not found on disk.")
        st.caption(f"Saved ADRs: `{svc.OUTPUT_DIR.relative_to(svc.PACKAGE_ROOT)}`")

    # ------------------------------------------------------------------ inputs
    st.subheader("1 · Inputs")
    decision_brief = st.text_area(
        "Decision brief",
        height=220,
        placeholder="Describe the problem, options you are weighing, and any constraints…",
        key="decision_brief",
    )

    with st.expander("Optional structured hints"):
        title_hint = st.text_input("Title hint")
        adr_number = st.text_input("ADR number (e.g. 001)")
        status = st.text_input("Status (e.g. Proposed, Accepted)")
        extra = st.text_area("Extra constraints / stakeholders / links", height=100)

    hints = svc.BriefHints(
        title_hint=title_hint,
        adr_number=adr_number,
        status=status,
        extra_constraints=extra,
    )

    config = svc.LLMConfig(
        backend=backend,
        model=model,
        ollama_host=ollama_host,
        anthropic_api_key=anthropic_key,
    )

    # ------------------------------------------------------------------ actions
    st.subheader("2 · Actions")
    col_analyse, col_gen, col_clear = st.columns([1, 1, 1])
    analyse_btn = col_analyse.button("Analyse brief", help="Gap analysis before drafting")
    generate = col_gen.button("Generate ADR", type="primary")
    clear = col_clear.button("Clear outputs")

    if clear:
        st.session_state.adr_markdown = ""
        st.session_state.analysis_markdown = ""
        st.session_state.review_markdown = ""

    if analyse_btn:
        if not decision_brief.strip():
            st.warning("Add a decision brief first.")
        elif svc.anthropic_key_required_but_missing(llm_choice, anthropic_key):
            st.error(
                "Set `ANTHROPIC_API_KEY` in `.env` for Anthropic, or switch backend to Ollama / Auto."
            )
        else:
            try:
                with st.spinner(f"Analysing brief ({backend})…"):
                    st.session_state.analysis_markdown = svc.analyse_brief(
                        config, decision_brief
                    )
            except Exception as e:
                st.error(f"Request failed: {e}")

    if generate:
        if not decision_brief.strip():
            st.warning("Add a decision brief first.")
        elif svc.anthropic_key_required_but_missing(llm_choice, anthropic_key):
            st.error(
                "Set `ANTHROPIC_API_KEY` in `.env` for Anthropic, or switch backend to Ollama / Auto."
            )
        else:
            try:
                if use_streaming:
                    placeholder = st.empty()
                    collected: list[str] = []
                    for text in svc.stream_generate_adr(config, decision_brief, hints):
                        collected.append(text)
                        placeholder.markdown("".join(collected))
                    st.session_state.adr_markdown = "".join(collected).strip()
                else:
                    with st.spinner(f"Calling {backend}…"):
                        st.session_state.adr_markdown = svc.generate_adr_markdown(
                            config, decision_brief, hints
                        )
                out_path = svc.save_adr_to_output(
                    st.session_state.adr_markdown,
                    svc.slugify_filename(title_hint, decision_brief),
                )
                st.success(f"Saved a copy to `{out_path.relative_to(svc.PACKAGE_ROOT)}`")
            except Exception as e:
                st.error(f"Request failed: {e}")

    # ------------------------------------------------------------------ analysis
    if st.session_state.analysis_markdown:
        st.divider()
        st.subheader("Brief analysis")
        st.markdown(st.session_state.analysis_markdown)

    # ------------------------------------------------------------------ generated ADR
    if st.session_state.adr_markdown:
        st.divider()
        st.subheader("3 · Generated ADR")
        st.markdown(st.session_state.adr_markdown)
        fname = svc.slugify_filename(title_hint, decision_brief)
        st.download_button(
            "Download .md",
            data=st.session_state.adr_markdown,
            file_name=fname,
            mime="text/markdown",
        )

        review_btn = st.button("Review ADR")
        if review_btn:
            if svc.anthropic_key_required_but_missing(llm_choice, anthropic_key):
                st.error(
                    "Set `ANTHROPIC_API_KEY` in `.env` for Anthropic, or switch backend to Ollama / Auto."
                )
            else:
                try:
                    with st.spinner(f"Reviewing ADR ({backend})…"):
                        st.session_state.review_markdown = svc.review_adr(
                            config, st.session_state.adr_markdown
                        )
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # ------------------------------------------------------------------ review
    if st.session_state.review_markdown:
        st.divider()
        st.subheader("ADR review")
        st.markdown(st.session_state.review_markdown)
