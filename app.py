"""
ADR Generator — Streamlit entry point.

This module exists so ``streamlit run app.py`` has a stable script path. It only
invokes :func:`streamlit_app.render_app`, which builds the full UI. Environment
variables are loaded when :mod:`adr_service` is imported (indirectly via
``streamlit_app`` → ``adr_service``).

See Also:
    streamlit_app: UI layout and session state.
    adr_service: Business logic and LLM orchestration (no Streamlit).
"""

from streamlit_app import render_app

render_app()
