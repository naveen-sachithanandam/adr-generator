"""
Low-level chat completions for two backends: **Anthropic** (cloud) and **Ollama** (local).

Responsibilities:
    - Map UI or env to a concrete :data:`Backend`.
    - Run a single ``system`` + ``user`` turn as either a full string
      (:func:`chat_complete`) or a token stream (:func:`chat_stream`).

Anthropic uses the Messages API (system prompt separate from user message).
Ollama uses ``system`` and ``user`` chat roles and ``num_predict`` for length.

Internal helpers (``_*``) isolate client construction and response parsing so
the public functions stay small.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Literal

import anthropic
from anthropic.types import Message
import ollama

Backend = Literal["anthropic", "ollama"]
"""Which provider implements the next request."""


def resolve_backend(choice: str, anthropic_api_key: str) -> Backend:
    """Pick ``anthropic`` or ``ollama`` from UI labels and optional API key.

    Args:
        choice: ``\"Anthropic\"``, ``\"Ollama\"``, or any string starting with
            ``\"Auto\"`` (use Anthropic if a key exists, else Ollama).
        anthropic_api_key: Key passed from env or UI; may be empty.

    Returns:
        ``\"anthropic\"`` or ``\"ollama\"``.
    """
    key = (anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if choice == "Anthropic":
        return "anthropic"
    if choice == "Ollama":
        return "ollama"
    if choice.startswith("Auto"):
        return "anthropic" if key else "ollama"
    return "ollama"


def _anthropic_key(anthropic_api_key: str | None) -> str:
    """Resolve API key from argument or env; raise if missing for Anthropic."""
    key = (anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        raise ValueError("ANTHROPIC_API_KEY is required for the Anthropic backend")
    return key


def _ollama_host(ollama_host: str | None) -> str:
    """Return explicit host or ``OLLAMA_HOST`` or localhost default."""
    return ollama_host or os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")


def _ollama_messages(system: str, user: str) -> list[dict[str, str]]:
    """Build Ollama chat message list with system + user roles."""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def _anthropic_text_from_message(msg: Message) -> str:
    """Concatenate text blocks from an Anthropic assistant message."""
    parts: list[str] = []
    for block in msg.content:
        if block.type == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def _anthropic_client(anthropic_api_key: str | None) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=_anthropic_key(anthropic_api_key))


def _anthropic_complete(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    anthropic_api_key: str | None,
) -> str:
    client = _anthropic_client(anthropic_api_key)
    msg = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return _anthropic_text_from_message(msg)


def _anthropic_stream(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    anthropic_api_key: str | None,
) -> Iterator[str]:
    client = _anthropic_client(anthropic_api_key)
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def _ollama_client(ollama_host: str | None) -> ollama.Client:
    return ollama.Client(host=_ollama_host(ollama_host))


def _ollama_complete(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    ollama_host: str | None,
) -> str:
    client = _ollama_client(ollama_host)
    resp = client.chat(
        model=model,
        messages=_ollama_messages(system, user),
        options={"num_predict": max_tokens},
    )
    return (resp.get("message") or {}).get("content", "").strip()


def _ollama_stream(
    model: str,
    system: str,
    user: str,
    max_tokens: int,
    ollama_host: str | None,
) -> Iterator[str]:
    client = _ollama_client(ollama_host)
    stream = client.chat(
        model=model,
        messages=_ollama_messages(system, user),
        stream=True,
        options={"num_predict": max_tokens},
    )
    for part in stream:
        piece = (part.get("message") or {}).get("content") or ""
        if piece:
            yield piece


def chat_complete(
    backend: Backend,
    model: str,
    system: str,
    user: str,
    *,
    max_tokens: int = 8192,
    ollama_host: str | None = None,
    anthropic_api_key: str | None = None,
) -> str:
    """Return the full assistant text for one system+user turn (no streaming).

    Args:
        backend: Target provider.
        model: Anthropic model name or Ollama model tag.
        system: System instructions (MADR rules, analyser instructions, etc.).
        user: User message body (brief, filled template, or ADR to review).
        max_tokens: Upper bound on generated tokens (``num_predict`` for Ollama).
        ollama_host: Override Ollama base URL; only used when ``backend == \"ollama\"``.
        anthropic_api_key: Override API key; only used for Anthropic.

    Returns:
        Stripped assistant text.
    """
    if backend == "anthropic":
        return _anthropic_complete(model, system, user, max_tokens, anthropic_api_key)
    return _ollama_complete(model, system, user, max_tokens, ollama_host)


def chat_stream(
    backend: Backend,
    model: str,
    system: str,
    user: str,
    *,
    max_tokens: int = 8192,
    ollama_host: str | None = None,
    anthropic_api_key: str | None = None,
) -> Iterator[str]:
    """Yield assistant text chunks as they arrive (provider-native streaming).

    Same arguments as :func:`chat_complete`; use when the UI shows incremental output.
    """
    if backend == "anthropic":
        yield from _anthropic_stream(model, system, user, max_tokens, anthropic_api_key)
    else:
        yield from _ollama_stream(model, system, user, max_tokens, ollama_host)
