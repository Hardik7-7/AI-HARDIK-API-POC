"""
LLM client wrapper — uses the official Google GenAI SDK.

Reads configuration from environment variables:
  GEMINI_API_KEY     — required
  LLM_MODEL          — optional (default: gemini-2.0-flash)
  LLM_TEMPERATURE    — optional (default: 0.2)
  LLM_MAX_TOKENS     — optional (default: 8192)
"""
from __future__ import annotations

import os
import time

from dotenv import load_dotenv
from google import genai
from rich.console import Console

load_dotenv()
console = Console()

_MAX_RETRIES = 3
_RETRY_DELAY_SECONDS = 5


def get_client() -> genai.Client:
    """Create a Google GenAI client from environment config."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and fill in your key."
        )
    return genai.Client(api_key=api_key)


def call_llm(prompt: str, system_message: str | None = None, expect_json: bool = False) -> str:
    """Send a prompt to Gemini and return the response text.

    Retries up to _MAX_RETRIES times if the API returns an empty response
    (a known intermittent issue with gemini-2.5-pro and similar models).

    Args:
        prompt: The user prompt to send.
        system_message: Optional system instructions.
        expect_json: If True, forces the model to return valid JSON.

    Returns:
        Raw text response from the LLM.

    Raises:
        RuntimeError: If all retry attempts return empty responses.
    """
    client = get_client()
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("LLM_MAX_TOKENS", "8192"))

    config = genai.types.GenerateContentConfig(
        temperature=temperature,
        max_output_tokens=max_tokens,
        system_instruction=system_message,
        response_mime_type="application/json" if expect_json else "text/plain",
    )

    console.print(
        f"[dim]→ Calling LLM ([bold]{model}[/bold], temp={temperature}, max_tokens={max_tokens})[/dim]"
    )

    for attempt in range(1, _MAX_RETRIES + 1):
        if attempt > 1:
            console.print(
                f"[yellow]↻ Retry {attempt}/{_MAX_RETRIES} — waiting {_RETRY_DELAY_SECONDS}s...[/yellow]"
            )
            time.sleep(_RETRY_DELAY_SECONDS)

        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=config,
        )

        # response.text is None when finish_reason is MAX_TOKENS or SAFETY,
        # or due to an intermittent SDK bug with gemini-2.5-pro.
        content = response.text
        if content is None:
            try:
                candidate = response.candidates[0]
                finish_reason = candidate.finish_reason
                console.print(
                    f"[yellow]⚠ response.text is None (finish_reason={finish_reason})[/yellow]"
                )
                parts = candidate.content.parts if candidate.content else []
                content = "".join(p.text for p in parts if hasattr(p, "text") and p.text) or ""
                if content:
                    console.print("[yellow]⚠ Recovered partial text from candidates.[/yellow]")
            except (IndexError, AttributeError):
                content = ""

        if content:
            console.print(f"[dim]← Received {len(content)} chars from LLM[/dim]")
            return content

        console.print(
            f"[yellow]⚠ Attempt {attempt}/{_MAX_RETRIES} returned empty response.[/yellow]"
        )

    raise RuntimeError(
        f"LLM returned an empty response after {_MAX_RETRIES} attempts.\n"
        "Possible causes:\n"
        "  • Output hit max_output_tokens — try increasing LLM_MAX_TOKENS in .env\n"
        "  • Response blocked by a safety filter (check response.prompt_feedback)\n"
        "  • Transient API issue — try again in a moment"
    )
