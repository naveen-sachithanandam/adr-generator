"""
Core ADR generator service layer.

Loads ``.env`` on import, exposes paths, example briefs, Markdown output, and
high-level operations (analyse, generate, review) that call :mod:`llm` and
:mod:`prompts`. This module has **no** Streamlit dependency — use it from tests,
CLI, or alternate frontends.

Typical flow:
    1. Build :class:`LLMConfig` and optional :class:`BriefHints` from user input.
    2. Call :func:`analyse_brief`, :func:`generate_adr_markdown` /
       :func:`stream_generate_adr`, or :func:`review_adr`.
    3. Optionally :func:`save_adr_to_output` for a disk copy of generated Markdown.
"""

from __future__ import annotations

import os
import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

from llm import Backend, chat_complete, chat_stream, resolve_backend
from prompts import (
    build_analyser_prompt,
    build_reviewer_prompt,
    build_user_prompt,
    get_analyser_system_prompt,
    get_reviewer_system_prompt,
    get_system_prompt,
)

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parent
"""Repository root (directory containing this package's modules)."""

OUTPUT_DIR = PACKAGE_ROOT / "output"
"""Directory where generated ADR Markdown copies are written."""

DEFAULT_ANTHROPIC_MODEL = os.environ.get("ADR_ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
DEFAULT_OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1")
DEFAULT_OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")

_EXAMPLE_PATHS = {
    "Default (tooling)": PACKAGE_ROOT / "examples" / "example-input.txt",
    "Healthcare": PACKAGE_ROOT
    / "examples"
    / "industry-examples"
    / "input"
    / "healthcare-input-example.txt",
    "AI integration": PACKAGE_ROOT
    / "examples"
    / "industry-examples"
    / "input"
    / "ai-integration-example.txt",
}


@dataclass(frozen=True)
class LLMConfig:
    """Immutable connection settings for a single LLM call (any of analyse / generate / review).

    Attributes:
        backend: Resolved provider, ``\"anthropic\"`` or ``\"ollama\"``.
        model: Model identifier (Claude model name or Ollama tag).
        ollama_host: HTTP base URL for the Ollama API (ignored when backend is Anthropic).
        anthropic_api_key: API key for Anthropic (may be empty when using Ollama only).
    """

    backend: Backend
    model: str
    ollama_host: str
    anthropic_api_key: str


@dataclass
class BriefHints:
    """Optional structured fields merged into the generator user prompt.

    Attributes:
        title_hint: Suggested ADR title.
        adr_number: Optional numeric or string label (e.g. ``001``).
        status: Proposed / Accepted / etc.
        extra_constraints: Free text for links, stakeholders, or constraints.
    """

    title_hint: str = ""
    adr_number: str = ""
    status: str = ""
    extra_constraints: str = ""


def default_model_for_initial_session() -> str:
    """Return the default model name for a fresh Streamlit session.

    Prefers the Anthropic default model env value when ``ANTHROPIC_API_KEY`` is
    set; otherwise the Ollama default model.
    """
    if (os.environ.get("ANTHROPIC_API_KEY") or "").strip():
        return DEFAULT_ANTHROPIC_MODEL
    return DEFAULT_OLLAMA_MODEL


def anthropic_key_from_env() -> str:
    """Return ``ANTHROPIC_API_KEY`` from the environment (empty string if unset)."""
    return os.environ.get("ANTHROPIC_API_KEY", "")


def slugify_filename(title_hint: str, brief: str) -> str:
    """Derive a safe ``*.md`` filename from title hint or first line of the brief.

    Strips a leading ``#``, collapses non-alphanumeric runs to hyphens, and
    truncates length for filesystem safety.
    """
    base = title_hint.strip() or brief.strip() or "adr"
    first_line = base.splitlines()[0] if base else "adr"
    first_line = re.sub(r"^#\s*", "", first_line).strip()
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", first_line).strip("-").lower()
    if not slug:
        slug = "adr"
    return f"{slug[:80]}.md"


def load_example_brief(example_label: str) -> str:
    """Load a sample decision brief text by sidebar label (e.g. ``\"Healthcare\"``).

    Returns:
        File contents as UTF-8 text, or ``\"\"`` if the label is unknown or the file is missing.
    """
    path = _EXAMPLE_PATHS.get(example_label)
    if not path or not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def save_adr_to_output(markdown: str, filename: str) -> Path:
    """Write Markdown to :attr:`OUTPUT_DIR` / ``filename``.

    Creates ``output/`` if needed. If a file at that path already exists, writes
    to a new name with a UTC timestamp suffix to avoid overwriting.

    Returns:
        Path to the file actually written.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    if path.exists():
        stem = path.stem
        suffix = path.suffix or ".md"
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = OUTPUT_DIR / f"{stem}-{ts}{suffix}"
    path.write_text(markdown, encoding="utf-8")
    return path


def backend_for_ui_choice(llm_choice: str, anthropic_api_key: str) -> Backend:
    """Map UI radio label to a concrete backend using :func:`llm.resolve_backend`."""
    return resolve_backend(llm_choice, anthropic_api_key)


def anthropic_key_required_but_missing(llm_choice: str, anthropic_api_key: str) -> bool:
    """Return True when the user forced Anthropic but no API key is available."""
    return llm_choice == "Anthropic" and not anthropic_api_key.strip()


def analyse_brief(config: LLMConfig, notes: str) -> str:
    """Run the analyser prompt: gaps, clarity, and suggested questions (not the ADR itself)."""
    return chat_complete(
        config.backend,
        config.model,
        get_analyser_system_prompt(),
        build_analyser_prompt(notes=notes),
        max_tokens=4096,
        ollama_host=config.ollama_host,
        anthropic_api_key=config.anthropic_api_key,
    )


def generate_adr_markdown(
    config: LLMConfig,
    decision_brief: str,
    hints: BriefHints,
) -> str:
    """Generate the full MADR-style ADR in one non-streaming response."""
    user_prompt = build_user_prompt(
        decision_brief=decision_brief,
        title_hint=hints.title_hint,
        status=hints.status,
        adr_number=hints.adr_number,
        extra_constraints=hints.extra_constraints,
    )
    return chat_complete(
        config.backend,
        config.model,
        get_system_prompt(),
        user_prompt,
        max_tokens=8192,
        ollama_host=config.ollama_host,
        anthropic_api_key=config.anthropic_api_key,
    )


def stream_generate_adr(
    config: LLMConfig,
    decision_brief: str,
    hints: BriefHints,
) -> Iterator[str]:
    """Stream the generated ADR token-by-token (same prompts as :func:`generate_adr_markdown`)."""
    user_prompt = build_user_prompt(
        decision_brief=decision_brief,
        title_hint=hints.title_hint,
        status=hints.status,
        adr_number=hints.adr_number,
        extra_constraints=hints.extra_constraints,
    )
    yield from chat_stream(
        config.backend,
        config.model,
        get_system_prompt(),
        user_prompt,
        max_tokens=8192,
        ollama_host=config.ollama_host,
        anthropic_api_key=config.anthropic_api_key,
    )


def review_adr(config: LLMConfig, adr_markdown: str) -> str:
    """Produce structured review feedback (blind spot, risk, future reader question)."""
    return chat_complete(
        config.backend,
        config.model,
        get_reviewer_system_prompt(),
        build_reviewer_prompt(adr=adr_markdown),
        max_tokens=4096,
        ollama_host=config.ollama_host,
        anthropic_api_key=config.anthropic_api_key,
    )
