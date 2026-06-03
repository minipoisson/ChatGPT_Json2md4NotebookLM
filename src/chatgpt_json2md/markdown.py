"""Markdown rendering helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .timeutils import format_epoch


_ARTIFACT_RE = re.compile(r"\ue200([^\ue201\ue202]*)\ue202([^\ue201]*)\ue201")
_ROLE_LABELS: dict[str, str] = {"user": "User", "assistant": "Assistant"}
_STANDALONE_ARTIFACT_CHARS_RE = re.compile(r"[\ue200-\ue206]")


@dataclass(frozen=True)
class ChatMessage:
    role: str
    text: str
    create_time: object = None


@dataclass(frozen=True)
class Conversation:
    title: str
    create_time: object
    update_time: object
    messages: list[ChatMessage]


def escape_angle_brackets(text: str) -> str:
    """Escape literal angle brackets so NotebookLM does not treat them as HTML."""
    return text.replace("<", "&lt;").replace(">", "&gt;")


def normalize_blank_lines(text: str) -> str:
    """Trim and collapse excessive blank lines without otherwise rewriting text."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_chatgpt_artifacts(text: str) -> str:
    """Convert ChatGPT UI markers to NotebookLM-friendly text notes."""

    def replace_artifact(match: re.Match[str]) -> str:
        kind = match.group(1).strip()
        raw_items = match.group(2)
        items = [item for item in raw_items.split("\ue202") if item]

        if kind == "cite":
            label = _count_label(len(items), "reference", "references")
            replacement = f"[Web citations: {label}]"
        elif kind in {"i", "image"}:
            label = _count_label(len(items), "image", "images")
            replacement = f"[Image references: {label}]"
        else:
            label = _count_label(len(items), "item", "items")
            replacement = f"[ChatGPT UI artifact: {kind or 'unknown'}, {label}]"

        return f"\n\n{replacement}\n\n"

    text = _ARTIFACT_RE.sub(replace_artifact, text)
    text = _STANDALONE_ARTIFACT_CHARS_RE.sub("", text)
    return normalize_blank_lines(text)


def _count_label(count: int, singular: str, plural: str) -> str:
    noun = singular if count == 1 else plural
    return f"{count} {noun}"


def normalize_title(title: object) -> str:
    raw = str(title).strip() if title is not None else ""
    if not raw:
        raw = "(Untitled)"
    raw = re.sub(r"\s+", " ", raw)
    return escape_angle_brackets(raw)


def render_header(generated_at: str) -> str:
    return f"# ChatGPT Conversation History\n\nGenerated at: {generated_at}\n\n"


def render_conversation(conversation: Conversation) -> str:
    lines = [
        f"## Conversation: {normalize_title(conversation.title)}",
        "",
        f"- Created: {format_epoch(conversation.create_time)}",
        f"- Updated: {format_epoch(conversation.update_time)}",
        "",
    ]

    for message in conversation.messages:
        label = _ROLE_LABELS.get(message.role, message.role.capitalize())
        text = normalize_chatgpt_artifacts(message.text)
        text = escape_angle_brackets(text)
        if not text:
            continue
        lines.extend([f"### {label}", "", f"- Time: {format_epoch(message.create_time)}", "", text, ""])

    lines.extend(["---", ""])
    return "\n".join(lines) + "\n"
