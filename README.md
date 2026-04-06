# ADR Generator

Small **Streamlit** app that turns a decision brief into **MADR-style** Markdown using **[Anthropic](https://www.anthropic.com/)** (cloud) and/or a **local model via [Ollama](https://ollama.com/)**.

Why this exists is documented in [architecture/adr-001-why-we-built-this.md](architecture/adr-001-why-we-built-this.md).

## Prerequisites

- Python 3.12+ recommended
- **Anthropic:** an API key if you use the Anthropic backend or **Auto** with a key set.
- **Ollama:** install, run `ollama serve`, and `ollama pull <model>` (e.g. `llama3.2`) when using Ollama or **Auto** without a key.

## Setup

```bash
cd adr-generator
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Set ANTHROPIC_API_KEY and/or OLLAMA_* — see .env.example
```

## Run locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (default [http://localhost:8501](http://localhost:8501)).

### LLM backend (sidebar)

| Option | Behavior |
|--------|----------|
| **Auto (Ollama if no API key)** | Uses Anthropic when `ANTHROPIC_API_KEY` is set; otherwise **Ollama** (local). |
| **Anthropic** | Cloud only; requires `ANTHROPIC_API_KEY`. |
| **Ollama** | Local only; set **Ollama host** and **model** (e.g. `llama3.2`). |

## Examples

- **Default (tooling):** [examples/example-input.txt](examples/example-input.txt)
- **Healthcare:** [examples/industry-examples/input/healthcare-input-example.txt](examples/industry-examples/input/healthcare-input-example.txt)
- **AI integration:** [examples/industry-examples/input/ai-integration-example.txt](examples/industry-examples/input/ai-integration-example.txt)

Load any of these from the sidebar (“Sample brief to load” → **Load sample into brief**).

Illustrative MADR (human-written reference) for the default brief: [examples/example-output.md](examples/example-output.md).

**Generated ADRs** are also written to the `output/` folder each time you click **Generate ADR**.

## Project layout

| Path | Purpose |
|------|---------|
| `app.py` | Entry: `streamlit run app.py` → loads UI |
| `streamlit_app.py` | Streamlit layout and session wiring only |
| `adr_service.py` | Core logic: paths, save/load examples, LLM calls |
| `llm.py` | Anthropic + Ollama chat (complete + stream) |
| `prompts/` | Package: loads Markdown prompts from `prompts/*.md` at call time (`__init__.py`) |
| `prompts/system-prompt.md` | System prompt (MADR-inspired ADR output rules) |
| `prompts/generator-prompt.md` | User prompt for generation (placeholders filled in code) |
| `prompts/analyser-system-prompt.md` | System prompt for brief analysis |
| `prompts/analyser-prompt.md` | User prompt for pre-flight analysis |
| `prompts/reviewer-system-prompt.md` | System prompt for ADR review |
| `prompts/reviewer-prompt.md` | User prompt for ADR review |
| `requirements.txt` | Python dependencies |
| `examples/` | Sample briefs (default + `industry-examples/input/`) |
| `output/` | Copies of generated ADRs (created on generate; not committed) |
| `architecture/` | ADRs about this tool |

## Security

- Do not commit `.env` or real API keys.
- Ollama keeps generations on your machine; Anthropic sends prompts to Anthropic’s API.
- If you expose the Streamlit app beyond a trusted network, put it behind authentication or a VPN.


## How this was Built?
This application was built using Cursor as a  AI coding assistant. The architechture, prompt design, and problem framing were my own. I used AI tooling to accelrate the implementation - which in itself is consistent with the theme of my project.
