"""Extract visible ChatGPT conversation text from conversations.json data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .markdown import ChatMessage, Conversation, normalize_blank_lines, render_conversation
from .timeutils import parse_epoch


@dataclass
class ConversionResult:
    blocks: list[str]
    warnings: list[str] = field(default_factory=list)


def convert_conversations(data: list[dict[str, Any]]) -> ConversionResult:
    warnings: list[str] = []
    blocks: list[str] = []

    for conv in sorted(_indexed_conversations(data), key=_conversation_sort_key):
        conversation = _extract_conversation(conv["conversation"], warnings)
        if conversation is None:
            continue
        blocks.append(render_conversation(conversation))

    return ConversionResult(blocks=blocks, warnings=warnings)


def _indexed_conversations(data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"index": index, "conversation": conversation}
        for index, conversation in enumerate(data)
        if isinstance(conversation, dict)
    ]


def _conversation_sort_key(item: dict[str, Any]) -> tuple[float, int]:
    conv = item["conversation"]
    timestamp = parse_epoch(conv.get("update_time"))
    if timestamp is None:
        timestamp = parse_epoch(conv.get("create_time"))
    if timestamp is None:
        timestamp = float("inf")
    return timestamp, item["index"]


def _extract_conversation(conv: dict[str, Any], warnings: list[str]) -> Conversation | None:
    mapping = conv.get("mapping")
    if not isinstance(mapping, dict):
        warnings.append(f"Skipping conversation with invalid mapping: {_conversation_name(conv)}")
        return None

    nodes = _main_path_nodes(conv, mapping, warnings)
    messages = [_extract_message(node) for node in nodes]
    visible_messages = [message for message in messages if message is not None]

    if not visible_messages:
        warnings.append(f"Skipping conversation with no visible messages: {_conversation_name(conv)}")
        return None

    return Conversation(
        title=conv.get("title") or "(Untitled)",
        create_time=conv.get("create_time"),
        update_time=conv.get("update_time"),
        messages=visible_messages,
    )


def _main_path_nodes(
    conv: dict[str, Any], mapping: dict[str, Any], warnings: list[str]
) -> list[dict[str, Any]]:
    current_node = conv.get("current_node")
    if current_node in mapping:
        path = []
        visited = set()
        node_id = current_node
        while node_id is not None:
            if node_id in visited:
                warnings.append(f"Cycle detected while reading conversation: {_conversation_name(conv)}")
                break
            visited.add(node_id)

            node = mapping.get(node_id)
            if not isinstance(node, dict):
                warnings.append(f"Broken node reference in conversation: {_conversation_name(conv)}")
                break
            path.append(node)
            node_id = node.get("parent")

        path.reverse()
        return path

    warnings.append(
        f"current_node missing or not found; falling back to message.create_time order: {_conversation_name(conv)}"
    )
    nodes = [node for node in mapping.values() if isinstance(node, dict)]
    return sorted(nodes, key=_node_sort_key)


def _node_sort_key(node: dict[str, Any]) -> tuple[float, str]:
    message = node.get("message")
    timestamp = None
    message_id = ""
    if isinstance(message, dict):
        timestamp = parse_epoch(message.get("create_time"))
        message_id = str(message.get("id") or "")
    if timestamp is None:
        timestamp = float("inf")
    return timestamp, message_id


def _extract_message(node: dict[str, Any]) -> ChatMessage | None:
    message = node.get("message")
    if not isinstance(message, dict):
        return None

    recipient = message.get("recipient", None)
    if "recipient" in message and recipient != "all":
        return None

    metadata = message.get("metadata")
    if isinstance(metadata, dict) and (
        metadata.get("is_visually_hidden_from_conversation") is True
        or metadata.get("is_hidden") is True
    ):
        return None

    author = message.get("author")
    role = author.get("role") if isinstance(author, dict) else None
    if role not in {"user", "assistant"}:
        return None

    text = _extract_text(message.get("content"))
    if not text:
        return None

    return ChatMessage(role=role, text=text, create_time=message.get("create_time"))


def _extract_text(content: Any) -> str:
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""

    texts: list[str] = []
    for part in parts:
        if isinstance(part, str):
            candidate = part
        elif isinstance(part, dict) and isinstance(part.get("text"), str):
            candidate = part["text"]
        else:
            continue

        candidate = normalize_blank_lines(candidate)
        if candidate:
            texts.append(candidate)

    return normalize_blank_lines("\n".join(texts))


def _conversation_name(conv: dict[str, Any]) -> str:
    return str(conv.get("title") or conv.get("id") or "(unknown)")
