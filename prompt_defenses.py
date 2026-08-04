"""Prompt injection defenses and sanitization utilities for Agent PitStop.

This module provides deterministic, dependency-free helpers:
- normalize_text: Unicode normalization and basic cleaning
- sanitize_messages: sanitize user-supplied message contents
- detect_injection: heuristic detector for common injection patterns
- enforce_system_guardrail: ensures system message contains guardrails
- validate_output_json: attempts to parse output as JSON and returns whether valid

Keep these deterministic and small so they can run in constrained environments.
"""

import re
import json
import unicodedata
from typing import List, Dict, Tuple, Optional

# Heuristic patterns that often indicate instruction-overrides or encoded payloads.
INJECTION_PATTERNS = [
    r"ignore (all )?previous instructions",
    r"disregard (all )?previous instructions",
    r"disobey.*system",
    r"forget your (system|developer) instructions",
    r"ignore the above",
    r"\bplease execute the following\b",
    r"^\s*system:\s*",
    r"base64,",
    r"[A-Za-z0-9+/]{40,}=+",  # long base64-like sequences
]
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

TRIM_MAX = 32_000  # avoid excessively long prompts reaching models


def normalize_text(s: str) -> str:
    """Normalize unicode and remove control characters."""
    if not isinstance(s, str):
        return s
    s = unicodedata.normalize("NFKC", s)
    # Remove non-printable/control characters except sensible whitespace
    s = "".join(ch for ch in s if ch.isprintable() or ch in "\t\n\r")
    return s


def sanitize_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Return a sanitized copy of messages.

    - Normalizes text
    - Truncates overly long messages
    - Removes simple inline instruction overrides (heuristic)
    """
    sanitized = []
    for m in messages:
        role = m.get("role")
        content = m.get("content", "")
        content = normalize_text(content)

        # Truncate to a safe maximum length per message
        if len(content) > TRIM_MAX:
            content = content[:TRIM_MAX] + "\n...[truncated]..."

        # Remove explicit "system:" prefix attempts inside user text
        content = re.sub(r"^\s*system:\s*", "", content, flags=re.IGNORECASE)

        # Neutralize obvious override phrases by quoting them (so model treats as data)
        for p in _COMPILED_PATTERNS:
            content = p.sub(lambda m: f"[{m.group(0)}]", content)

        sanitized.append({"role": role, "content": content})
    return sanitized


def detect_injection(messages: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
    """Return (is_injection, example_match).

    This is intentionally conservative: it's a heuristic signal, not a blocker.
    """
    for m in messages:
        text = m.get("content", "")
        for p in _COMPILED_PATTERNS:
            if p.search(text):
                return True, p.pattern
    return False, None


def enforce_system_guardrail(messages: List[Dict[str, str]], guardrail_text: str) -> List[Dict[str, str]]:
    """Ensure system message exists and append guardrail_text to it.

    The guardrail_text should be considered deterministic and not include secrets.
    """
    if not messages:
        return [{"role": "system", "content": guardrail_text}]

    enriched = [dict(m) for m in messages]
    system_found = False
    for msg in enriched:
        if msg.get("role") == "system":
            msg["content"] = str(msg.get("content", "")) + "\n\n" + guardrail_text
            system_found = True
            break
    if not system_found:
        enriched.insert(0, {"role": "system", "content": guardrail_text})
    return enriched


def validate_output_json(text: str) -> Tuple[bool, Optional[object]]:
    """Try parsing output as JSON; return (is_json, parsed_object or None).

    Use this as a deterministic post-check when a structured response was expected.
    """
    if not isinstance(text, str):
        return False, None
    try:
        obj = json.loads(text)
        return True, obj
    except Exception:
        return False, None
