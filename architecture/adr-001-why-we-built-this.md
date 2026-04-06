# ADR-001: Why we built this ADR generator

## Status

Accepted

## Context

Architecture decisions were recorded inconsistently: some as long design docs, some as chat threads, some not at all. Onboarding and audits suffered because there was no single place or format to read “why we chose X.”

Teams that adopt ADRs often stall on formatting and wording. A lightweight tool lowers the friction to produce a **MADR-compatible** record while still leaving humans in control of the substance.

## Decision Drivers

- Encourage a **standard ADR shape** (MADR sections) across repositories.
- Reduce time from rough notes to a reviewable Markdown file.
- Use **Python** and a **simple UI** so the project is easy to run and deploy internally.
- Allow **optional AI assistance** (Anthropic) without requiring it for every workflow.

## Considered Options

### Do nothing (manual Markdown only)

- **Pros**: No dependencies, no cost.
- **Cons**: Format drift; slower authoring; weaker adoption.

### Template repository + copy-paste

- **Pros**: No runtime; clear structure.
- **Cons**: Still manual; easy to skip sections or diverge from MADR.

### This project: Streamlit + Anthropic SDK

- **Pros**: Fast path from brief to draft; preview and download in one screen; Docker-friendly.
- **Cons**: External API dependency; keys and usage must be managed responsibly.

## Decision Outcome

We built a small **Streamlit** application that calls the **Anthropic Messages API** with prompts constrained to **MADR-style Markdown**. The repository includes **examples** and this ADR so newcomers understand intent and format.

## Consequences

- **Positive**: Lower barrier to writing ADRs; consistent headings; easy to paste into `docs/adr/` or similar.
- **Negative**: Reliance on Anthropic availability and API keys; model output should still be reviewed by humans before “Accepted.”

## Compliance

- Secrets via environment variables (see `.env.example`); never commit real keys.

## Notes

- See `examples/example-input.txt` and `examples/example-output.md` for a concrete brief-to-ADR illustration.
