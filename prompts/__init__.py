"""
Prompt loading and user-message assembly for the ADR generator.

Markdown prompts live in this package directory (``prompts/*.md``). Public getters
**read from disk on each call** so edits apply on the next request without
restarting the process.

Files:

- ``system-prompt.md`` — MADR-shaped ADR rules (*system* for generation).
- ``generator-prompt.md`` — user message for generation (placeholders filled by
  :func:`build_user_prompt`).
- ``analyser-system-prompt.md`` / ``analyser-prompt.md`` — system + user for brief analysis.
- ``reviewer-system-prompt.md`` / ``reviewer-prompt.md`` — system + user for ADR review.

Placeholder values like ``{domain}`` that are not collected in the UI default to
the string ``\"Not provided\"``.
"""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent
_SYSTEM_PROMPT_PATH = _PROMPTS_DIR / "system-prompt.md"
_GENERATOR_PROMPT_PATH = _PROMPTS_DIR / "generator-prompt.md"
_ANALYSER_SYSTEM_PATH = _PROMPTS_DIR / "analyser-system-prompt.md"
_ANALYSER_PROMPT_PATH = _PROMPTS_DIR / "analyser-prompt.md"
_REVIEWER_SYSTEM_PATH = _PROMPTS_DIR / "reviewer-system-prompt.md"
_REVIEWER_PROMPT_PATH = _PROMPTS_DIR / "reviewer-prompt.md"

_MISSING = "Not provided"


def get_system_prompt() -> str:
    """Load and return the main ADR system prompt (MADR structure and grounding rules).

    Raises:
        RuntimeError: If the file is missing or empty.
    """
    text = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"System prompt file is empty: {_SYSTEM_PROMPT_PATH}")
    return text


def _read_prompt(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise RuntimeError(f"Prompt file is empty: {path}")
    return text


def get_analyser_system_prompt() -> str:
    """Load ``analyser-system-prompt.md`` from disk (each call re-reads the file)."""
    return _read_prompt(_ANALYSER_SYSTEM_PATH)


def get_reviewer_system_prompt() -> str:
    """Load ``reviewer-system-prompt.md`` from disk (each call re-reads the file)."""
    return _read_prompt(_REVIEWER_SYSTEM_PATH)


def get_generator_prompt() -> str:
    """Return the contents of ``generator-prompt.md`` (before placeholder substitution)."""
    return _read_prompt(_GENERATOR_PROMPT_PATH)


def get_analyser_prompt() -> str:
    """Return the contents of ``analyser-prompt.md`` (before ``{notes}`` substitution)."""
    return _read_prompt(_ANALYSER_PROMPT_PATH)


def get_reviewer_prompt() -> str:
    """Return the contents of ``reviewer-prompt.md`` (before ``{adr}`` substitution)."""
    return _read_prompt(_REVIEWER_PROMPT_PATH)


def _filled(s: str) -> str:
    """Return stripped *s* or :data:`_MISSING` if blank."""
    s = (s or "").strip()
    return s if s else _MISSING


def build_user_prompt(
    *,
    decision_brief: str,
    title_hint: str = "",
    status: str = "",
    adr_number: str = "",
    extra_constraints: str = "",
    domain: str = "",
    scale: str = "",
    constraints: str = "",
    tradeoffs: str = "",
) -> str:
    """Fill ``generator-prompt.md`` with the brief and optional structured fields.

    Merges title, ADR number, status, and extra lines into an *Additional context*
    block. Replaces ``{notes}``, ``{context}``, ``{domain}``, ``{scale}``,
    ``{constraints}``, ``{tradeoffs}`` via string substitution (no ``str.format``
    to avoid brace issues in user text).
    """
    body = get_generator_prompt()
    parts: list[str] = []
    if title_hint.strip():
        parts.append(f"**Title hint:** {title_hint.strip()}")
    if adr_number.strip():
        parts.append(f"**ADR number:** {adr_number.strip()}")
    if status.strip():
        parts.append(f"**Status:** {status.strip()}")
    if extra_constraints.strip():
        parts.append(f"**Extra constraints / links:** {extra_constraints.strip()}")
    context = "\n\n".join(parts) if parts else "*No additional structured hints.*"

    return (
        body.replace("{notes}", decision_brief.strip())
        .replace("{context}", context)
        .replace("{domain}", _filled(domain))
        .replace("{scale}", _filled(scale))
        .replace("{constraints}", _filled(constraints))
        .replace("{tradeoffs}", _filled(tradeoffs))
    )


def build_analyser_prompt(*, notes: str) -> str:
    """Insert *notes* into ``analyser-prompt.md`` at ``{notes}``."""
    return get_analyser_prompt().replace("{notes}", notes.strip())


def build_reviewer_prompt(*, adr: str) -> str:
    """Insert the ADR Markdown *adr* into ``reviewer-prompt.md`` at ``{adr}``."""
    return get_reviewer_prompt().replace("{adr}", adr.strip())
