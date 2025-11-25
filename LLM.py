"""
Simple local Ollama client for llama3.1:8b-instruct-q4_K_M.

Usage:
  python LLM.py "What is 100 + 5?"
  echo "Summarize this text..." | python LLM.py

Env overrides:
  OLLAMA_BASE_URL   (default: http://localhost:11434)
  OLLAMA_MODEL      (default: llama3.1:8b-instruct-q4_K_M)
  OLLAMA_SYSTEM     (optional system prompt)
  OLLAMA_STREAM     ("true" to stream)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Generator, Iterable

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")


def call_ollama_chat(
    prompt: str,
    *,
    system: str | None = None,
    model: str | None = None,
    temperature: float = 0.2,
    stream: bool = False,
) -> Iterable[str]:
    """Send a chat request to the local Ollama server."""
    payload = {
        "model": model or OLLAMA_MODEL,
        "messages": [],
        "stream": stream,
        "options": {
            "temperature": temperature,
        },
    }
    if system:
        payload["messages"].append({"role": "system", "content": system})
    payload["messages"].append({"role": "user", "content": prompt})

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_BASE_URL}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            if stream:
                for raw in resp:
                    if not raw.strip():
                        continue
                    chunk = json.loads(raw.decode("utf-8"))
                    content = chunk.get("message", {}).get("content")
                    if content:
                        yield content
                return

            body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            content = parsed.get("message", {}).get("content", "")
            yield content
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        yield f"[ollama error] {exc}"


def main() -> None:
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:]).strip()
    else:
        prompt = sys.stdin.read().strip()

    if not prompt:
        print("No prompt provided. Pass text as an argument or via stdin.", file=sys.stderr)
        sys.exit(1)

    system_prompt = os.environ.get("OLLAMA_SYSTEM", "You are a concise assistant.")
    stream = os.environ.get("OLLAMA_STREAM", "false").lower() == "true"

    for chunk in call_ollama_chat(prompt, system=system_prompt, stream=stream):
        if chunk is None:
            continue
        sys.stdout.write(chunk)
        sys.stdout.flush()

    if stream:
        sys.stdout.write("\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
