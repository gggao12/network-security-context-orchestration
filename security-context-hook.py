#!/usr/bin/env python3
"""Detect security-research prompts and inject a focused Claude context.

The hook is intentionally small and explainable: strong identity signals trigger
immediately; technical signals trigger unless an explicit non-security context is
present. It accepts either a JSON string or a JSON object with a ``prompt`` field.
"""

from __future__ import annotations

import json
import os
import re
import sys
from typing import Any

DEBUG = os.getenv("CLAUDE_HOOK_DEBUG") == "1"

STRONG_SIGNALS = (
    "赏金猎人", "bug bounty", "漏洞挖掘", "安全测试", "security research",
    "已授权", "渗透测试", "src",
)
WEAK_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bcve\b", r"\bvuln(?:erability)?\b", r"\bexploit\b", r"\bxss\b",
    r"\bssrf\b", r"\bsqli\b", r"\brce\b", r"\bidor\b",
    r"\bauth(?:orization|entication)?\s*(?:bypass|绕过)?\b",
    r"\bpentest\b", r"漏洞", r"注入", r"逆向", r"加密",
))
NEGATIVE_PATTERNS = tuple(re.compile(pattern, re.IGNORECASE) for pattern in (
    r"\bdebug(?:ging)?\b", r"\bbug fix\b", r"authorization header",
    r"\bauthorized_keys\b", r"\bsource code\b", r"\bcommerce\b",
))


def _matches(patterns: tuple[re.Pattern[str], ...], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


def classify(prompt: str) -> tuple[bool, str]:
    """Return ``(should_inject, reason)`` for observability and debugging."""
    normalized = prompt.casefold()
    if _matches(NEGATIVE_PATTERNS, normalized):
        return False, "explicit_non_security_context"
    if any(signal.casefold() in normalized for signal in STRONG_SIGNALS):
        return True, "strong_identity_signal"
    if _matches(WEAK_PATTERNS, normalized):
        return True, "technical_security_signal"
    return False, "no_security_signal"


def _extract_prompt(payload: Any) -> str | None:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("prompt"), str):
        return payload["prompt"]
    return None


def main() -> None:
    raw = sys.stdin.read()
    if not raw.strip():
        return
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        print(raw)
        return

    prompt = _extract_prompt(payload)
    if prompt is None:
        print(raw)
        return

    should_inject, reason = classify(prompt)
    if not should_inject:
        print(raw)
        return

    context = (
        "[bounty] 已进入安全研究上下文：优先关注可利用性、真实影响、可复现证据，"
        "并使用非破坏性验证。"
    )
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    if DEBUG:
        output["hookSpecificOutput"]["debug"] = {"reason": reason}
    print(json.dumps(output, ensure_ascii=False))


if __name__ == "__main__":
    main()
