# ADR tooling — Streamlit and Anthropic for MADR-style drafts

## Context

The team needs a repeatable way to author Architecture Decision Records (ADRs) in a consistent shape (MADR-style Markdown) without manually reformatting notes every time. Engineers are comfortable with Python. Some stakeholders may prefer a browser UI over IDE-only workflows. Deployment should stay simple for internal use, and API keys must never be baked into container images. The brief states a **Proposed** status until a pilot with two teams completes.

## Decision Drivers

- **Consistency**: Enforce a shared ADR structure across decisions.
- **Time-to-value**: Ship something useful quickly without a large frontend build.
- **Optional AI assist**: Turn rough bullets into structured sections, not unstructured essays.
- **Operability**: Single-container deployment is acceptable; configuration via environment variables.
- **Security**: Secrets supplied at runtime, not committed or embedded in images.

## Considered Options

### Internal web app (forms + Markdown export)

- **Pros**: Accessible in a browser; guided input; preview and download in one place.
- **Cons**: Requires UI framework choice and maintenance; easy to over-build.

### IDE snippets / Copilot-only

- **Pros**: No deployable surface; lives in the developer workflow.
- **Cons**: Weak enforcement of structure; quality varies by author; weaker for people who do not use the IDE.

### CLI that scaffolds empty MADR files

- **Pros**: Fast, scriptable, no network dependency.
- **Cons**: Does not help draft content from notes; still heavy manual editing.

### Streamlit + Anthropic API (browser UI)

- **Pros**: Fast to implement in Python; built-in widgets for brief, preview, and download; model can expand notes into sections behind explicit prompts.
- **Cons**: Depends on an external LLM API; API key handling and usage cost must be operated deliberately; less customizable than a bespoke SPA.

## Decision Outcome

**Chosen:** Streamlit + Anthropic API for an internal ADR generator.

**Not selected:**

- **Internal web app (generic)**: Rejected for this iteration in favor of Streamlit’s faster path in Python and built-in UI primitives; a custom SPA remains a later option if requirements outgrow Streamlit.
- **IDE snippets / Copilot-only**: Rejected because structure enforcement is weak and not everyone lives in the IDE.
- **CLI-only scaffold**: Rejected because it does not meet the goal of assistive drafting from rough notes.

The app should default to MADR-style Markdown output and load secrets from the environment at runtime, not from the image.

## Consequences

- **Positive**: Faster ADR authoring; one flow to run locally or in Docker; easier onboarding for people who prefer a browser.
- **Negative**: Dependency on an external LLM API; ongoing need to rotate keys and monitor usage and cost.
- **Neutral**: If needs grow (auth, multi-tenant workflows), the team may split UI and API or replace Streamlit.

## Compliance

- Do not commit `.env` or real keys; use `.env.example` as documentation only.
- Prefer a private network or authenticated reverse proxy if the app is exposed beyond the intended team.

## Notes

**Open gaps:** The brief does not specify spend limits, model selection policy, or retention of prompts—those should be decided before org-wide rollout.

**Explicit inferences:** None. Wording above stays within the stated brief and constraints.

**Meta:** Files under `examples/` illustrate intended section shape; live model output may differ in wording while preserving the same `##` headings.
