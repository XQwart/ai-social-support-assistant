"""Post-process the model's final answer before returning it to the user.

Some GigaChat checkpoints (in particular GigaChat-2 regular) occasionally
emit text that *looks* like a tool call — verbatim strings such as
``search_knowledge_base`` followed by ``query: ...`` / ``region_name: ...``
lines — instead of producing a structured tool call. The scaffolding never
sees a real tool invocation for these, so the garbage flows straight to
the chat.

This module strips these leaks while leaving the genuine Markdown answer
intact. It is conservative: if after cleanup nothing is left, we return
an empty string so the caller can fall back to the raw state (or to the
fallback message).
"""

from __future__ import annotations

import re


TOOL_NAMES = ("search_knowledge_base", "save_user_facts", "think")

# Lines like "query: ...", "region_name: ...", "memory: ...", "region: ...",
# "tool_call: ..." or "thought: ..." that appear on their own — i.e. not
# inside a blockquote or code fence — are almost always leaked tool args.
_LEAKED_ARG_KEYS = r"(?:query|region_name|region|memory|thought|tool_call|arguments|name|input)"
_ARG_LINE = re.compile(
    rf"^\s*{_LEAKED_ARG_KEYS}\s*[:=]\s*.+$",
    re.IGNORECASE | re.MULTILINE,
)

# A bare tool name sitting on its own line is never part of a legitimate
# answer — real answers would wrap the reference in Markdown prose.
_BARE_TOOL_LINE = re.compile(
    r"^\s*(?:" + "|".join(re.escape(t) for t in TOOL_NAMES) + r")\s*$",
    re.IGNORECASE | re.MULTILINE,
)

# Fenced blocks that contain ONLY tool-call-like JSON/YAML. We intentionally
# do NOT strip arbitrary code fences — only those consisting of leak patterns.
_TOOL_FENCE = re.compile(
    r"```(?:json|yaml|tool|tool_call)?\s*\n"
    r"(?:\s*(?:"
    + "|".join(re.escape(t) for t in TOOL_NAMES)
    + r"|" + _LEAKED_ARG_KEYS + r")[^\n]*\n)+"
    r"\s*```",
    re.IGNORECASE,
)

# "Функция search_knowledge_base возвращает..." / "Я вызову search_knowledge_base..."
# Sentence-level mentions are still OK inside prose; we only clean when the
# mention is obviously a machine artifact (immediately followed by JSON-ish
# argument lines). Handled via _ARG_LINE + _BARE_TOOL_LINE combination.

_MULTIBLANK = re.compile(r"\n{3,}")


def sanitize_final_message(text: str) -> str:
    """Strip tool-call leakage from a user-facing message.

    Safe to call on any Markdown string. Returns the cleaned text with
    leading/trailing whitespace removed.
    """
    if not text:
        return ""

    cleaned = _TOOL_FENCE.sub("", text)
    cleaned = _BARE_TOOL_LINE.sub("", cleaned)
    cleaned = _ARG_LINE.sub("", cleaned)
    cleaned = _MULTIBLANK.sub("\n\n", cleaned)
    return cleaned.strip()
